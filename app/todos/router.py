"""API endpoints for managing user TODOs / tasks in PostgreSQL."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_active_user
from app.db.models import TodoItem, User
from app.db.session import get_db
from app.todos.schemas import TodoCreate, TodoListResponse, TodoOut, TodoUpdate

router = APIRouter(prefix="/todos", tags=["TODOs"])


@router.get("", response_model=TodoListResponse, summary="List user TODOs")
def list_todos(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    priority_filter: Optional[str] = Query(None, alias="priority", description="Filter by priority"),
    search: Optional[str] = Query(None, description="Search term in title or description"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> TodoListResponse:
    """Retrieve all TODO items owned by the authenticated user with optional filtering."""
    query = select(TodoItem).where(TodoItem.user_id == current_user.id)

    if status_filter:
        query = query.where(TodoItem.status == status_filter.lower())
    if priority_filter:
        query = query.where(TodoItem.priority == priority_filter.lower())
    if search:
        search_pattern = f"%{search.strip()}%"
        query = query.where(
            (TodoItem.title.ilike(search_pattern))
            | (TodoItem.description.ilike(search_pattern))
        )

    query = query.order_by(TodoItem.created_at.desc())
    items = list(db.scalars(query).all())

    # Count statistics
    total = len(items)
    completed_count = sum(1 for item in items if item.status == "completed")
    pending_count = sum(1 for item in items if item.status != "completed")

    return TodoListResponse(
        items=[TodoOut.model_validate(item) for item in items],
        total=total,
        completed=completed_count,
        pending=pending_count,
    )


@router.post(
    "",
    response_model=TodoOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new TODO item",
)
def create_todo(
    payload: TodoCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> TodoItem:
    """Create a new TODO item associated with the authenticated user."""
    todo = TodoItem(
        user_id=current_user.id,
        title=payload.title.strip(),
        description=payload.description.strip() if payload.description else None,
        status=payload.status or "pending",
        priority=payload.priority,
        due_date=payload.due_date,
    )
    db.add(todo)
    db.commit()
    db.refresh(todo)
    return todo


@router.get("/{todo_id}", response_model=TodoOut, summary="Get single TODO item")
def get_todo(
    todo_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> TodoItem:
    """Retrieve a specific TODO item owned by the authenticated user."""
    todo = db.scalar(
        select(TodoItem).where(
            TodoItem.id == todo_id,
            TodoItem.user_id == current_user.id,
        )
    )
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Todo #{todo_id} not found.",
        )
    return todo


@router.put("/{todo_id}", response_model=TodoOut, summary="Update a TODO item")
def update_todo(
    todo_id: int,
    payload: TodoUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> TodoItem:
    """Update status, title, description, or priority of an existing TODO."""
    todo = db.scalar(
        select(TodoItem).where(
            TodoItem.id == todo_id,
            TodoItem.user_id == current_user.id,
        )
    )
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Todo #{todo_id} not found.",
        )

    if payload.title is not None:
        todo.title = payload.title.strip()
    if payload.description is not None:
        todo.description = payload.description.strip() or None
    if payload.status is not None:
        todo.status = payload.status
    if payload.priority is not None:
        todo.priority = payload.priority
    if payload.due_date is not None:
        todo.due_date = payload.due_date

    db.commit()
    db.refresh(todo)
    return todo


@router.delete(
    "/{todo_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a TODO item",
)
def delete_todo(
    todo_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Delete a TODO item owned by the authenticated user."""
    todo = db.scalar(
        select(TodoItem).where(
            TodoItem.id == todo_id,
            TodoItem.user_id == current_user.id,
        )
    )
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Todo #{todo_id} not found.",
        )

    db.delete(todo)
    db.commit()
    return {"message": f"Todo #{todo_id} deleted successfully."}

