"""Google Tasks implementation of :class:`frame.data.TasksAPI`."""

from collections.abc import Sequence
from datetime import datetime

from frame.data.tasks import Task, TaskList, TaskPriority, TasksAPI, TaskStatus

from .client import GoogleClient

_BASE_URL = "https://tasks.googleapis.com/tasks/v1"


def _timestamp(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


class GoogleTasksAPI(GoogleClient, TasksAPI):
    async def list_task_lists(self) -> Sequence[TaskList]:
        payload = await self.request("GET", f"{_BASE_URL}/users/@me/lists")
        return tuple(
            TaskList(id=str(item["id"]), name=str(item.get("title", "")))
            for item in payload.get("items", [])
        )

    async def list_tasks(
        self,
        *,
        list_ids: Sequence[str] | None = None,
        include_completed: bool = False,
    ) -> Sequence[Task]:
        ids = list_ids or tuple(item.id for item in await self.list_task_lists())
        tasks: list[Task] = []
        for list_id in ids:
            payload = await self.request(
                "GET",
                f"{_BASE_URL}/lists/{list_id}/tasks",
                params={"showCompleted": str(include_completed).lower()},
            )
            tasks.extend(
                Task(
                    id=str(item["id"]),
                    list_id=list_id,
                    title=str(item.get("title", "")),
                    status=TaskStatus(item.get("status", "needsAction").replace("needsAction", "needs_action")),
                    due_at=_timestamp(item.get("due")),
                    completed_at=_timestamp(item.get("completed")),
                    priority=TaskPriority.MEDIUM,
                    notes=item.get("notes"),
                    url=item.get("webViewLink"),
                )
                for item in payload.get("items", [])
            )
        return tuple(tasks)
