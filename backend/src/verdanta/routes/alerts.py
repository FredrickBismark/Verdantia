from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from verdanta.core.database import get_db
from verdanta.models.garden import Garden
from verdanta.schemas.alert import AlertCreate, AlertResponse
from verdanta.services.alert_service import AlertService

router = APIRouter()
svc = AlertService()


@router.get("/gardens/{garden_id}/alerts", response_model=dict)
async def list_alerts(
    garden_id: int,
    dismissed: bool | None = False,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List alerts for a garden."""
    garden = await db.get(Garden, garden_id)
    if not garden:
        raise HTTPException(status_code=404, detail="Garden not found")
    alerts = await svc.get_active_alerts(
        garden_id, db, dismissed=dismissed, skip=skip, limit=limit
    )
    return {
        "data": [AlertResponse.model_validate(a) for a in alerts],
        "count": len(alerts),
    }


@router.post("/gardens/{garden_id}/alerts/check", response_model=dict)
async def trigger_alert_check(
    garden_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Manually trigger alert generation for a garden."""
    garden = await db.get(Garden, garden_id)
    if not garden:
        raise HTTPException(status_code=404, detail="Garden not found")
    created = await svc.run_all_checks(garden, db)
    await db.commit()
    return {
        "data": [AlertResponse.model_validate(a) for a in created],
        "count": len(created),
    }


@router.post("/gardens/{garden_id}/alerts", response_model=dict)
async def create_alert(
    garden_id: int,
    alert_in: AlertCreate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create a manual alert for a garden."""
    from verdanta.models.alert import Alert

    garden = await db.get(Garden, garden_id)
    if not garden:
        raise HTTPException(status_code=404, detail="Garden not found")

    alert = Alert(
        garden_id=garden_id,
        **alert_in.model_dump(),
    )
    db.add(alert)
    await db.flush()
    await db.refresh(alert)
    await db.commit()
    return {"data": AlertResponse.model_validate(alert)}


@router.post("/alerts/{alert_id}/acknowledge", response_model=dict)
async def acknowledge_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Mark an alert as acknowledged."""
    alert = await svc.acknowledge_alert(alert_id, db)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    await db.commit()
    return {"data": AlertResponse.model_validate(alert)}


@router.post("/alerts/{alert_id}/dismiss", response_model=dict)
async def dismiss_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Dismiss an alert."""
    alert = await svc.dismiss_alert(alert_id, db)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    await db.commit()
    return {"data": AlertResponse.model_validate(alert)}


@router.delete("/alerts/{alert_id}", status_code=204)
async def delete_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete an alert."""
    from verdanta.models.alert import Alert

    alert = await db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    await db.delete(alert)
    await db.commit()
