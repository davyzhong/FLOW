from pydantic import BaseModel

from flow_api.api.schemas.intake import ErrorDetail
from flow_api.dashboard.models import DashboardOverview


class DashboardOverviewResponse(DashboardOverview):
    """Public read-only Finance BP dashboard response."""


class DashboardErrorResponse(BaseModel):
    detail: ErrorDetail


__all__ = ["DashboardErrorResponse", "DashboardOverviewResponse"]
