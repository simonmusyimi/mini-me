from __future__ import annotations

from core.planner import Planner


class Supervisor:
    """V1 facade for the future multi-agent supervisor."""

    def __init__(self, planner: Planner) -> None:
        self.planner = planner

    def plan_today(self) -> str:
        return self.planner.generate_plan()
