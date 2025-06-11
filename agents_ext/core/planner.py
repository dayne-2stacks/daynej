class Planner:
    """Manage a simple list of tasks for an agent."""

    def __init__(self) -> None:
        self.tasks: list[str] = []

    def add_task(self, task: str) -> None:
        self.tasks.append(task)

    def next_task(self) -> str | None:
        if self.tasks:
            return self.tasks.pop(0)
        return None
