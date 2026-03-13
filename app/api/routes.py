from __future__ import annotations

from typing import Dict

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.models import Blueprint
from app.services.platform_service import PlatformService

router = APIRouter(prefix="/api/v1", tags=["platform"])


class ActorContext(BaseModel):
    tenant_id: str = Field(default="tenant-demo")
    actor_id: str = Field(default="system")


class CreateBlueprintRequest(BaseModel):
    actor: ActorContext = Field(default_factory=ActorContext)
    blueprint: Blueprint


class ApproveBlueprintRequest(BaseModel):
    actor: ActorContext = Field(default_factory=ActorContext)
    reviewer_id: str


class GenerateToolRequest(BaseModel):
    actor: ActorContext = Field(default_factory=ActorContext)


class RunTestsRequest(BaseModel):
    actor: ActorContext = Field(default_factory=ActorContext)
    pass_threshold: float = 0.8


class PublishRequest(BaseModel):
    actor: ActorContext = Field(default_factory=ActorContext)
    published_by: str


@router.post("/blueprints")
def create_blueprint(payload: CreateBlueprintRequest) -> Blueprint:
    return PlatformService.create_blueprint(
        tenant_id=payload.actor.tenant_id,
        actor_id=payload.actor.actor_id,
        blueprint=payload.blueprint,
    )


@router.post("/blueprints/{blueprint_id}/approve")
def approve_blueprint(blueprint_id: str, payload: ApproveBlueprintRequest) -> Blueprint:
    return PlatformService.approve_blueprint(
        tenant_id=payload.actor.tenant_id,
        actor_id=payload.actor.actor_id,
        blueprint_id=blueprint_id,
        reviewer_id=payload.reviewer_id,
    )


@router.post("/blueprints/{blueprint_id}/generate")
def generate_tool(blueprint_id: str, payload: GenerateToolRequest):
    return PlatformService.generate_tool(
        tenant_id=payload.actor.tenant_id,
        actor_id=payload.actor.actor_id,
        blueprint_id=blueprint_id,
    )


@router.post("/tools/{tool_id}/test")
def run_tests(tool_id: str, payload: RunTestsRequest) -> Dict[str, object]:
    return PlatformService.run_tests(
        tenant_id=payload.actor.tenant_id,
        actor_id=payload.actor.actor_id,
        tool_id=tool_id,
        pass_threshold=payload.pass_threshold,
    )


@router.post("/tools/{tool_id}/publish")
def publish_tool(tool_id: str, payload: PublishRequest):
    return PlatformService.publish_tool(
        tenant_id=payload.actor.tenant_id,
        actor_id=payload.actor.actor_id,
        tool_id=tool_id,
        published_by=payload.published_by,
    )


@router.get("/monitoring/snapshot")
def monitoring_snapshot():
    return PlatformService.monitoring_snapshot()
