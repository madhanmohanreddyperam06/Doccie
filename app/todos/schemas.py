"""Pydantic schemas for Todo / Task items."""

from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

TodoStatus = Literal["pending", "in_progress", "completed", "cancelled"]
TodoPriority = Literal["low", "medium", "high"]


class TodoBase(BaseModel):
    """Base fields for a Todo item."""

    title: str = Field(..., min_length=1, max_length=255, description="Todo title or task summary")
    description: Optional[str] = Field(None, description="Detailed task description")
    priority: TodoPriority = Field(default="medium", description="Priority level: low, medium, high")
    due_date: Optional[datetime] = Field(None, description="Optional due date/time")


class TodoCreate(TodoBase):
    """Payload to create a new Todo item."""
    status: Optional[TodoStatus] = Field(default="pending", description="Initial task status")


class TodoUpdate(BaseModel):
    """Payload to update an existing Todo item."""

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[TodoStatus] = None
    priority: Optional[TodoPriority] = None
    due_date: Optional[datetime] = None


class TodoOut(TodoBase):
    """Todo item response representation."""

    id: int
    user_id: int
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TodoListResponse(BaseModel):
    """Paginated list of Todo items."""

    items: List[TodoOut]
    total: int
    completed: int
    pending: int

