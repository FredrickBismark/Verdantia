import logging
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from verdanta.models.alert import Alert
from verdanta.models.garden import Garden
from verdanta.models.planting import CalendarEvent, Planting
from verdanta.models.weather import WeatherRecord

logger = logging.getLogger(__name__)


class AlertService:
    """Generates and manages proactive garden alerts."""

    async def check_frost_alerts(
        self, garden: Garden, db: AsyncSession
    ) -> list[Alert]:
        """Create alerts for upcoming frost risk from weather forecasts."""
        today = date.today()
        result = await db.execute(
            select(WeatherRecord).where(
                WeatherRecord.garden_id == garden.id,
                WeatherRecord.record_type == "forecast",
                WeatherRecord.frost_risk.is_(True),
                WeatherRecord.timestamp >= datetime.combine(today, datetime.min.time()),
                WeatherRecord.timestamp
                <= datetime.combine(today + timedelta(days=3), datetime.min.time()),
            )
        )
        frost_records = result.scalars().all()
        if not frost_records:
            return []

        created: list[Alert] = []
        for rec in frost_records:
            trigger = rec.timestamp.date() if isinstance(rec.timestamp, datetime) else today
            exists = await db.execute(
                select(Alert).where(
                    Alert.garden_id == garden.id,
                    Alert.alert_type == "frost",
                    Alert.trigger_date == trigger,
                    Alert.dismissed.is_(False),
                )
            )
            if exists.scalar_one_or_none():
                continue

            temp_str = f" (low: {rec.temp_min_c}°C)" if rec.temp_min_c is not None else ""
            alert = Alert(
                garden_id=garden.id,
                alert_type="frost",
                severity="high",
                title=f"Frost risk on {trigger.strftime('%b %d')}",
                description=f"Weather forecast indicates frost risk{temp_str}. "
                "Consider covering sensitive plants or moving containers indoors.",
                source="weather_service",
                trigger_date=trigger,
                triggered_at=datetime.now(UTC),
                metadata_json={"temp_min_c": rec.temp_min_c, "weather_record_id": rec.id},
            )
            db.add(alert)
            created.append(alert)

        return created

    async def check_weather_extreme_alerts(
        self, garden: Garden, db: AsyncSession
    ) -> list[Alert]:
        """Create alerts for extreme weather conditions."""
        today = date.today()
        result = await db.execute(
            select(WeatherRecord).where(
                WeatherRecord.garden_id == garden.id,
                WeatherRecord.record_type == "forecast",
                WeatherRecord.timestamp >= datetime.combine(today, datetime.min.time()),
                WeatherRecord.timestamp
                <= datetime.combine(today + timedelta(days=3), datetime.min.time()),
            )
        )
        forecasts = result.scalars().all()
        created: list[Alert] = []

        for rec in forecasts:
            trigger = rec.timestamp.date() if isinstance(rec.timestamp, datetime) else today

            # Heavy rain alert
            if rec.precipitation_mm is not None and rec.precipitation_mm > 25:
                exists = await db.execute(
                    select(Alert).where(
                        Alert.garden_id == garden.id,
                        Alert.alert_type == "extreme_weather",
                        Alert.trigger_date == trigger,
                        Alert.dismissed.is_(False),
                        Alert.title.contains("rain"),
                    )
                )
                if not exists.scalar_one_or_none():
                    alert = Alert(
                        garden_id=garden.id,
                        alert_type="extreme_weather",
                        severity="medium",
                        title=f"Heavy rain expected on {trigger.strftime('%b %d')}",
                        description=(
                            f"Forecast shows {rec.precipitation_mm}mm of rain. "
                            "Consider drainage and protecting delicate crops."
                        ),
                        source="weather_service",
                        trigger_date=trigger,
                        triggered_at=datetime.now(UTC),
                        metadata_json={"precipitation_mm": rec.precipitation_mm},
                    )
                    db.add(alert)
                    created.append(alert)

            # Extreme heat
            if rec.temp_max_c is not None and rec.temp_max_c > 38:
                exists = await db.execute(
                    select(Alert).where(
                        Alert.garden_id == garden.id,
                        Alert.alert_type == "extreme_weather",
                        Alert.trigger_date == trigger,
                        Alert.dismissed.is_(False),
                        Alert.title.contains("heat"),
                    )
                )
                if not exists.scalar_one_or_none():
                    alert = Alert(
                        garden_id=garden.id,
                        alert_type="extreme_weather",
                        severity="high",
                        title=f"Extreme heat on {trigger.strftime('%b %d')}",
                        description=(
                            f"Temperature forecast of {rec.temp_max_c}°C. "
                            "Increase watering and provide shade where possible."
                        ),
                        source="weather_service",
                        trigger_date=trigger,
                        triggered_at=datetime.now(UTC),
                        metadata_json={"temp_max_c": rec.temp_max_c},
                    )
                    db.add(alert)
                    created.append(alert)

        return created

    async def check_overdue_tasks(
        self, garden: Garden, db: AsyncSession
    ) -> list[Alert]:
        """Create alerts for overdue calendar tasks."""
        today = date.today()
        result = await db.execute(
            select(CalendarEvent).where(
                CalendarEvent.garden_id == garden.id,
                CalendarEvent.completed.is_(False),
                CalendarEvent.scheduled_date < today,
            )
        )
        overdue = result.scalars().all()
        created: list[Alert] = []

        for event in overdue:
            exists = await db.execute(
                select(Alert).where(
                    Alert.garden_id == garden.id,
                    Alert.alert_type == "watering",
                    Alert.dismissed.is_(False),
                    Alert.metadata_json.contains({"calendar_event_id": event.id}),
                )
            )
            if exists.scalar_one_or_none():
                continue

            days_overdue = (today - event.scheduled_date).days
            severity = "high" if days_overdue > 3 else "medium"
            alert = Alert(
                garden_id=garden.id,
                planting_id=event.planting_id,
                alert_type="watering",
                severity=severity,
                title=f"Overdue: {event.title}",
                description=(
                    f"Task \"{event.title}\" was scheduled for "
                    f"{event.scheduled_date.strftime('%b %d')} "
                    f"({days_overdue} day{'s' if days_overdue != 1 else ''} ago)."
                ),
                source="calendar",
                trigger_date=event.scheduled_date,
                triggered_at=datetime.now(UTC),
                metadata_json={"calendar_event_id": event.id},
            )
            db.add(alert)
            created.append(alert)

        return created

    async def check_harvest_windows(
        self, garden: Garden, db: AsyncSession
    ) -> list[Alert]:
        """Create alerts for plantings approaching harvest readiness."""
        today = date.today()
        result = await db.execute(
            select(Planting).where(
                Planting.garden_id == garden.id,
                Planting.status.in_(["growing", "active"]),
                Planting.date_seeded.isnot(None),
            )
        )
        plantings = result.scalars().all()
        created: list[Alert] = []

        for p in plantings:
            species = await db.get(type(p).species.property.entity.class_, p.species_id)
            if not species or not species.days_to_maturity_min:
                continue

            seed_date = p.date_seeded
            if seed_date is None:
                continue

            maturity_date = seed_date + timedelta(days=species.days_to_maturity_min)
            days_until = (maturity_date - today).days

            if 0 <= days_until <= 7 and not p.date_first_harvest:
                exists = await db.execute(
                    select(Alert).where(
                        Alert.garden_id == garden.id,
                        Alert.planting_id == p.id,
                        Alert.alert_type == "harvest",
                        Alert.dismissed.is_(False),
                    )
                )
                if exists.scalar_one_or_none():
                    continue

                alert = Alert(
                    garden_id=garden.id,
                    planting_id=p.id,
                    alert_type="harvest",
                    severity="low",
                    title=f"{species.common_name} approaching harvest",
                    description=(
                        f"Your {species.common_name} "
                        f"(planted {seed_date.strftime('%b %d')}) "
                        f"may be ready to harvest around "
                        f"{maturity_date.strftime('%b %d')}."
                    ),
                    source="calendar",
                    trigger_date=maturity_date,
                    triggered_at=datetime.now(UTC),
                    metadata_json={
                        "planting_id": p.id,
                        "species": species.common_name,
                        "days_to_maturity": species.days_to_maturity_min,
                    },
                )
                db.add(alert)
                created.append(alert)

        return created

    async def run_all_checks(
        self, garden: Garden, db: AsyncSession
    ) -> list[Alert]:
        """Run all alert checks for a garden and return newly created alerts."""
        all_alerts: list[Alert] = []
        all_alerts.extend(await self.check_frost_alerts(garden, db))
        all_alerts.extend(await self.check_weather_extreme_alerts(garden, db))
        all_alerts.extend(await self.check_overdue_tasks(garden, db))
        all_alerts.extend(await self.check_harvest_windows(garden, db))
        if all_alerts:
            await db.flush()
        return all_alerts

    async def get_active_alerts(
        self,
        garden_id: int,
        db: AsyncSession,
        *,
        dismissed: bool | None = False,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Alert]:
        """Get alerts for a garden with optional filters."""
        stmt = select(Alert).where(Alert.garden_id == garden_id)
        if dismissed is not None:
            stmt = stmt.where(Alert.dismissed == dismissed)
        stmt = stmt.order_by(
            Alert.severity.desc(), Alert.trigger_date.desc()
        ).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def acknowledge_alert(
        self, alert_id: int, db: AsyncSession
    ) -> Alert | None:
        alert = await db.get(Alert, alert_id)
        if not alert:
            return None
        alert.acknowledged = True
        alert.acknowledged_at = datetime.now(UTC)
        await db.flush()
        return alert

    async def dismiss_alert(
        self, alert_id: int, db: AsyncSession
    ) -> Alert | None:
        alert = await db.get(Alert, alert_id)
        if not alert:
            return None
        alert.dismissed = True
        alert.dismissed_at = datetime.now(UTC)
        await db.flush()
        return alert


async def check_all_gardens_alerts() -> None:
    """Background job: check alerts for all gardens."""
    from verdanta.core.database import async_session_factory

    async with async_session_factory() as db:
        result = await db.execute(select(Garden))
        gardens = result.scalars().all()
        svc = AlertService()
        for garden in gardens:
            try:
                created = await svc.run_all_checks(garden, db)
                if created:
                    logger.info(
                        "Created %d alerts for garden %s",
                        len(created),
                        garden.name,
                    )
            except Exception:
                logger.warning(
                    "Alert check failed for garden %d", garden.id, exc_info=True
                )
        await db.commit()
