from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator


class ApprovalStatus(str, Enum):
    draft = "draft"
    pending_review = "pending_review"
    approved = "approved"
    rejected = "rejected"


class ToolStatus(str, Enum):
    draft = "draft"
    tested = "tested"
    published = "published"
    archived = "archived"


class GateDecision(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class WorkflowTransition(BaseModel):
    from_state: str
    to_state: str
    action: str


class TargetUser(BaseModel):
    role: str
    objective: str


class InputSpec(BaseModel):
    input_name: str
    type: str
    source: str


class OutputSpec(BaseModel):
    output_name: str
    format: str


class EntityField(BaseModel):
    name: str
    type: str
    required: bool = True


class DataEntity(BaseModel):
    entity_name: str
    fields: List[EntityField]


class ScreenDefinition(BaseModel):
    screen_name: str
    purpose: str
    visible_to: List[str]


class WorkflowDefinition(BaseModel):
    states: List[str]
    transitions: List[WorkflowTransition]
    actions: List[str]

    @model_validator(mode="after")
    def validate_transition_states(self) -> "WorkflowDefinition":
        states = set(self.states)
        for transition in self.transitions:
            if transition.from_state not in states or transition.to_state not in states:
                raise ValueError("All transitions must reference defined workflow states")
        return self


class AgentDefinition(BaseModel):
    agent_name: str
    purpose: str
    trigger: str
    tools: List[str]


class ReviewGate(BaseModel):
    gate_name: str
    required_for: str
    decision: GateDecision = GateDecision.pending


class BlueprintContent(BaseModel):
    product_name: str
    sector: str
    pack_version: str
    use_case_template: str
    workspace_type: str
    problem_statement: str
    target_users: List[TargetUser]
    inputs: List[InputSpec]
    outputs: List[OutputSpec]
    data_entities: List[DataEntity]
    screens: List[ScreenDefinition]
    workflow: WorkflowDefinition
    agents: List[AgentDefinition]
    review_gates: List[ReviewGate]
    alerts: Dict[str, Any]
    permissions: Dict[str, Any]
    kpis: List[str]
    test_scenarios: List[str]
    publishing_profile: Dict[str, Any]
    claims_boundary: str
    risk_notes: List[str]


class Blueprint(BaseModel):
    blueprint_id: str = Field(default_factory=lambda: str(uuid4()))
    workspace_id: str
    pack_id: str
    template_id: str
    version: int = 1
    schema_version: str = "1.0"
    approval_status: ApprovalStatus = ApprovalStatus.draft
    content_json: BlueprintContent
    reviewer_id: Optional[str] = None
    approved_at: Optional[datetime] = None
    provenance: Dict[str, Any] = Field(default_factory=dict)


class ToolDefinition(BaseModel):
    tool_id: str = Field(default_factory=lambda: str(uuid4()))
    blueprint_id: str
    generated_version: int = 1
    status: ToolStatus = ToolStatus.draft
    ui_config: Dict[str, Any]
    workflow_config: Dict[str, Any]
    agent_config: Dict[str, Any]
    permission_config: Dict[str, Any]
    audit_tags: Dict[str, Any]


class TestScenario(BaseModel):
    scenario_id: str = Field(default_factory=lambda: str(uuid4()))
    blueprint_id: str
    name: str
    input_fixture: Dict[str, Any]
    expected_result: Dict[str, Any]
    severity: str
    status: str = "pending"


class TestRun(BaseModel):
    run_id: str = Field(default_factory=lambda: str(uuid4()))
    scenario_id: str
    tool_id: str
    outcome: str
    logs: List[str]
    reviewer_notes: Optional[str] = None
    executed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PublishRecord(BaseModel):
    published_tool_id: str = Field(default_factory=lambda: str(uuid4()))
    tool_id: str
    live_version: int
    published_by: str
    published_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    rollback_target: Optional[int] = None


class AuditEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    tenant_id: str
    workspace_id: str
    actor_id: str
    event_type: str
    object_type: str
    object_id: str
    before_state: Dict[str, Any]
    after_state: Dict[str, Any]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
