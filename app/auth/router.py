"""Authentication API endpoints for registration, login, and user profile management."""

from datetime import timedelta
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_active_user
from app.auth.schemas import (
    PasswordChange,
    Token,
    UserCreate,
    UserLogin,
    UserOut,
    UserUpdate,
)
from app.core.config import settings
from app.core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
)
from app.db.models import User
from app.db.session import get_db

logger = logging.getLogger("app.auth")
router = APIRouter(prefix="/auth", tags=["Authentication"])


def _authenticate_user(
    db: Session, username_or_email: str, password: str
) -> User:
    """Validate credentials and return User model or raise 401."""
    user = db.scalar(
        select(User).where(
            or_(
                User.username == username_or_email.strip(),
                User.email == username_or_email.strip().lower(),
            )
        )
    )

    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account.",
        )

    return user


def _build_token_response(user: User) -> Token:
    """Generate signed JWT and construct Token response schema."""
    expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username, "email": user.email},
        expires_delta=expires_delta,
    )
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserOut.model_validate(user),
    )


@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
def register_user(payload: UserCreate, db: Session = Depends(get_db)) -> User:
    """Create a new user with unique email and username, securely hashing password."""
    # Check if email is already in use
    existing_email = db.scalar(
        select(User).where(User.email == payload.email.lower().strip())
    )
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists.",
        )

    # Check if username is already in use
    existing_username = db.scalar(
        select(User).where(User.username == payload.username.strip())
    )
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This username is already taken.",
        )

    # First user can automatically be granted superuser privileges
    is_first_user = db.scalar(select(User).limit(1)) is None

    new_user = User(
        email=payload.email.lower().strip(),
        username=payload.username.strip(),
        full_name=payload.full_name.strip() if payload.full_name else None,
        hashed_password=get_password_hash(payload.password),
        is_active=True,
        is_superuser=is_first_user,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    logger.info("User registered successfully: id=%d username='%s'", new_user.id, new_user.username)
    return new_user


@router.post(
    "/login",
    response_model=Token,
    summary="Authenticate with JSON credentials",
)
def login_json(payload: UserLogin, db: Session = Depends(get_db)) -> Token:
    """Log in using JSON body with username/email and password, returning JWT access token."""
    user = _authenticate_user(db, payload.username_or_email, payload.password)
    return _build_token_response(user)


@router.post(
    "/token",
    response_model=Token,
    summary="OAuth2 compatible token login for Swagger UI",
)
def login_oauth2(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Token:
    """Authenticate via OAuth2 Password specification (used by Swagger /docs 'Authorize' button)."""
    user = _authenticate_user(db, form_data.username, form_data.password)
    return _build_token_response(user)


@router.get(
    "/me",
    response_model=UserOut,
    summary="Get current user profile",
)
def get_user_profile(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Retrieve details of the currently logged-in user."""
    return current_user


@router.put(
    "/me",
    response_model=UserOut,
    summary="Update current user profile",
)
def update_user_profile(
    payload: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> User:
    """Update profile information for the authenticated user."""
    if payload.full_name is not None:
        current_user.full_name = payload.full_name.strip() or None

    if payload.email is not None and payload.email.lower().strip() != current_user.email:
        new_email = payload.email.lower().strip()
        existing = db.scalar(
            select(User).where(User.email == new_email, User.id != current_user.id)
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email address is already in use by another account.",
            )
        current_user.email = new_email

    db.commit()
    db.refresh(current_user)
    return current_user


@router.post(
    "/change-password",
    status_code=status.HTTP_200_OK,
    summary="Change account password",
)
def change_password(
    payload: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Change user password after verifying existing password."""
    if not verify_password(payload.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect.",
        )

    current_user.hashed_password = get_password_hash(payload.new_password)
    db.commit()
    return {"message": "Password changed successfully."}

