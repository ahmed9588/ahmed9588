from __future__ import annotations

from collections import defaultdict
from typing import Dict, List

from app.models import AuditEvent, Blueprint, PublishRecord, TestRun, TestScenario, ToolDefinition


class InMemoryStore:
    def __init__(self) -> None:
        self.blueprints: Dict[str, Blueprint] = {}
        self.tools: Dict[str, ToolDefinition] = {}
        self.test_scenarios: Dict[str, TestScenario] = {}
        self.test_runs: Dict[str, TestRun] = {}
        self.publications: Dict[str, PublishRecord] = {}
        self.audit_events: Dict[str, AuditEvent] = {}
        self.metrics = defaultdict(int)

    def log_metric(self, name: str, value: int = 1) -> None:
        self.metrics[name] += value

    def export_metrics(self) -> Dict[str, int]:
        return dict(self.metrics)

    def list_audit_events(self) -> List[AuditEvent]:
        return sorted(self.audit_events.values(), key=lambda item: item.timestamp)


store = InMemoryStore()
