from fastapi import APIRouter

from app.core.pipeline import dashboard_payload

router = APIRouter()


@router.get("/sessions/{sid}/dashboard")
def dashboard(sid: str):
    return dashboard_payload(sid)
