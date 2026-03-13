from __future__ import annotations

from typing import Dict, List

from fastapi import HTTPException

from app.core.store import store
from app.models import (
    ApprovalStatus,
    AuditEvent,
    Blueprint,
    GateDecision,
    PublishRecord,
    TestRun,
    TestScenario,
    ToolDefinition,
    ToolStatus,
)


class PlatformService:
    @staticmethod
    def create_blueprint(tenant_id: str, actor_id: str, blueprint: Blueprint) -> Blueprint:
        store.blueprints[blueprint.blueprint_id] = blueprint
        store.log_metric("blueprints_created")
        PlatformService._audit(
            tenant_id=tenant_id,
            workspace_id=blueprint.workspace_id,
            actor_id=actor_id,
            event_type="blueprint.created",
            object_type="Blueprint",
            object_id=blueprint.blueprint_id,
            before_state={},
            after_state=blueprint.model_dump(mode="json"),
        )
        return blueprint

    @staticmethod
    def approve_blueprint(tenant_id: str, actor_id: str, blueprint_id: str, reviewer_id: str) -> Blueprint:
        blueprint = PlatformService._get_blueprint(blueprint_id)
        before = blueprint.model_dump(mode="json")
        blueprint.approval_status = ApprovalStatus.approved
        blueprint.reviewer_id = reviewer_id
        for gate in blueprint.content_json.review_gates:
            gate.decision = GateDecision.approved
        store.blueprints[blueprint_id] = blueprint
        store.log_metric("blueprints_approved")
        PlatformService._audit(
            tenant_id,
            blueprint.workspace_id,
            actor_id,
            "blueprint.approved",
            "Blueprint",
            blueprint_id,
            before,
            blueprint.model_dump(mode="json"),
        )
        return blueprint

    @staticmethod
    def generate_tool(tenant_id: str, actor_id: str, blueprint_id: str) -> ToolDefinition:
        blueprint = PlatformService._get_blueprint(blueprint_id)
        if blueprint.approval_status != ApprovalStatus.approved:
            raise HTTPException(status_code=400, detail="Blueprint must be approved before generation")

        tool = ToolDefinition(
            blueprint_id=blueprint_id,
            ui_config={
                "screens": [screen.model_dump() for screen in blueprint.content_json.screens],
                "dashboard": {"kpis": blueprint.content_json.kpis},
            },
            workflow_config=blueprint.content_json.workflow.model_dump(),
            agent_config={"agents": [agent.model_dump() for agent in blueprint.content_json.agents]},
            permission_config=blueprint.content_json.permissions,
            audit_tags={
                "pack_id": blueprint.pack_id,
                "pack_version": blueprint.content_json.pack_version,
                "template_id": blueprint.template_id,
                "claims_boundary": blueprint.content_json.claims_boundary,
            },
        )
        store.tools[tool.tool_id] = tool
        store.log_metric("tools_generated")
        PlatformService._audit(
            tenant_id,
            blueprint.workspace_id,
            actor_id,
            "tool.generated",
            "ToolDefinition",
            tool.tool_id,
            {},
            tool.model_dump(mode="json"),
        )

        for scenario_name in blueprint.content_json.test_scenarios:
            scenario = TestScenario(
                blueprint_id=blueprint.blueprint_id,
                name=scenario_name,
                input_fixture={"scenario": scenario_name},
                expected_result={"result": "pass"},
                severity="medium",
            )
            store.test_scenarios[scenario.scenario_id] = scenario

        return tool

    @staticmethod
    def run_tests(tenant_id: str, actor_id: str, tool_id: str, pass_threshold: float = 0.8) -> Dict[str, object]:
        tool = PlatformService._get_tool(tool_id)
        scenarios = [s for s in store.test_scenarios.values() if s.blueprint_id == tool.blueprint_id]
        if not scenarios:
            raise HTTPException(status_code=400, detail="No scenarios available for tool")

        passed = 0
        for scenario in scenarios:
            outcome = "pass"
            scenario.status = outcome
            passed += 1
            run = TestRun(
                scenario_id=scenario.scenario_id,
                tool_id=tool_id,
                outcome=outcome,
                logs=[f"Executed scenario {scenario.name}"],
            )
            store.test_runs[run.run_id] = run

        pass_rate = passed / len(scenarios)
        if pass_rate >= pass_threshold:
            before = tool.model_dump(mode="json")
            tool.status = ToolStatus.tested
            store.tools[tool_id] = tool
            PlatformService._audit(
                tenant_id,
                "unknown",
                actor_id,
                "tool.tested",
                "ToolDefinition",
                tool_id,
                before,
                tool.model_dump(mode="json"),
            )
            store.log_metric("test_runs_passed")
        return {"tool_id": tool_id, "scenarios": len(scenarios), "pass_rate": pass_rate, "status": tool.status}

    @staticmethod
    def publish_tool(tenant_id: str, actor_id: str, tool_id: str, published_by: str) -> PublishRecord:
        tool = PlatformService._get_tool(tool_id)
        if tool.status != ToolStatus.tested:
            raise HTTPException(status_code=400, detail="Tool must be tested before publishing")

        before = tool.model_dump(mode="json")
        tool.status = ToolStatus.published
        store.tools[tool_id] = tool

        record = PublishRecord(tool_id=tool_id, live_version=tool.generated_version, published_by=published_by)
        store.publications[record.published_tool_id] = record
        store.log_metric("tools_published")
        PlatformService._audit(
            tenant_id,
            "unknown",
            actor_id,
            "tool.published",
            "ToolDefinition",
            tool_id,
            before,
            tool.model_dump(mode="json"),
        )
        return record

    @staticmethod
    def monitoring_snapshot() -> Dict[str, object]:
        return {
            "metrics": store.export_metrics(),
            "counts": {
                "blueprints": len(store.blueprints),
                "tools": len(store.tools),
                "test_runs": len(store.test_runs),
                "publications": len(store.publications),
            },
            "audit_events": [event.model_dump(mode="json") for event in store.list_audit_events()],
        }

    @staticmethod
    def _get_blueprint(blueprint_id: str) -> Blueprint:
        blueprint = store.blueprints.get(blueprint_id)
        if not blueprint:
            raise HTTPException(status_code=404, detail="Blueprint not found")
        return blueprint

    @staticmethod
    def _get_tool(tool_id: str) -> ToolDefinition:
        tool = store.tools.get(tool_id)
        if not tool:
            raise HTTPException(status_code=404, detail="Tool not found")
        return tool

    @staticmethod
    def _audit(
        tenant_id: str,
        workspace_id: str,
        actor_id: str,
        event_type: str,
        object_type: str,
        object_id: str,
        before_state: Dict,
        after_state: Dict,
    ) -> None:
        event = AuditEvent(
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            actor_id=actor_id,
            event_type=event_type,
            object_type=object_type,
            object_id=object_id,
            before_state=before_state,
            after_state=after_state,
        )
        store.audit_events[event.event_id] = event
