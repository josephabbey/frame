"""Task domain models and the contract implemented by task providers."""

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class TaskStatus(StrEnum):
    NEEDS_ACTION = "needs_action"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskPriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True, slots=True)
class TaskList:
    id: str
    name: str


@dataclass(frozen=True, slots=True)
class Task:
    id: str
    list_id: str
    title: str
    status: TaskStatus = TaskStatus.NEEDS_ACTION
    due_at: datetime | None = None
    completed_at: datetime | None = None
    priority: TaskPriority = TaskPriority.MEDIUM
    notes: str | None = None
    url: str | None = None


class TasksAPI(ABC):
    """The read operations required from a task provider."""

    @abstractmethod
    async def list_task_lists(self) -> Sequence[TaskList]: ...

    @abstractmethod
    async def list_tasks(
        self,
        *,
        list_ids: Sequence[str] | None = None,
        include_completed: bool = False,
    ) -> Sequence[Task]: ...
