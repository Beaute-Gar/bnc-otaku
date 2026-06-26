from fastapi import APIRouter, Request
from backend.database import session_factory
from backend.models.adtracking import AdEvent

router = APIRouter(prefix="/api/ad", tags=["Publicité"])


@router.post("/view")
def track_ad_view(request: Request):
    ip = request.client.host if request.client else "unknown"
    with session_factory() as db:
        db.add(AdEvent(event_type="ad_view", page="/certificate", ip_address=ip))
        db.commit()
    return {"ok": True}


@router.get("/events")
def get_ad_events():
    with session_factory() as db:
        total = db.query(AdEvent).filter(AdEvent.event_type == "ad_view").count()
    return {"total_views": total}
