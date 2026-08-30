from typing import Literal

from pydantic import BaseModel


class WorkspaceResponse(BaseModel):
    workspace_id: Literal["flow-v1"]
    name: Literal["FLOW"]
    primary_role: Literal["finance_bp"]
    industry: Literal["logistics_supply_chain"]
    timezone: str
    currency: Literal["CNY"]
