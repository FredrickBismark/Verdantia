"""IoT sensor service with MQTT integration.

Connects to local Mosquitto broker, ingests sensor readings,
and provides sensor discovery and status tracking.
"""

import json
import logging
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from verdanta.core.config import settings
from verdanta.models.weather import SensorReading

logger = logging.getLogger(__name__)

# In-memory registry of sensors discovered via MQTT or manual entry.
# Keys are (garden_id, sensor_id) tuples.
_sensor_registry: dict[tuple[int, str], dict] = {}


def register_sensor(
    garden_id: int,
    sensor_id: str,
    sensor_type: str,
    location: str | None = None,
    source: str = "manual",
) -> None:
    """Register or update a sensor in the in-memory registry."""
    key = (garden_id, sensor_id)
    now = datetime.now(UTC)
    if key in _sensor_registry:
        _sensor_registry[key]["last_seen"] = now.isoformat()
        _sensor_registry[key]["sensor_type"] = sensor_type
        if location:
            _sensor_registry[key]["location"] = location
    else:
        _sensor_registry[key] = {
            "sensor_id": sensor_id,
            "garden_id": garden_id,
            "sensor_type": sensor_type,
            "location": location,
            "source": source,
            "first_seen": now.isoformat(),
            "last_seen": now.isoformat(),
            "connected": source == "mqtt",
        }


async def discover_sensors_from_db(
    garden_id: int,
    db: AsyncSession,
) -> list[dict]:
    """Discover sensors from existing readings in the database."""
    result = await db.execute(
        select(
            SensorReading.sensor_id,
            func.max(SensorReading.sensor_type).label("sensor_type"),
            func.max(SensorReading.location).label("location"),
            func.count(SensorReading.id).label("reading_count"),
            func.min(SensorReading.timestamp).label("first_reading"),
            func.max(SensorReading.timestamp).label("last_reading"),
        )
        .where(SensorReading.garden_id == garden_id)
        .group_by(SensorReading.sensor_id)
    )
    rows = result.all()

    sensors = []
    for row in rows:
        key = (garden_id, row.sensor_id)
        registry_entry = _sensor_registry.get(key, {})
        sensors.append({
            "sensor_id": row.sensor_id,
            "garden_id": garden_id,
            "sensor_type": row.sensor_type,
            "location": row.location,
            "reading_count": row.reading_count,
            "first_reading": row.first_reading.isoformat() if row.first_reading else None,
            "last_reading": row.last_reading.isoformat() if row.last_reading else None,
            "connected": registry_entry.get("connected", False),
            "source": registry_entry.get("source", "manual"),
        })

    # Also include registry-only sensors not yet in DB
    db_sensor_ids = {row.sensor_id for row in rows}
    for (gid, sid), entry in _sensor_registry.items():
        if gid == garden_id and sid not in db_sensor_ids:
            sensors.append({
                **entry,
                "reading_count": 0,
                "first_reading": None,
                "last_reading": None,
            })

    return sensors


async def get_sensor_status(
    garden_id: int,
    db: AsyncSession,
) -> list[dict]:
    """Get status information for all sensors in a garden."""
    sensors = await discover_sensors_from_db(garden_id, db)

    statuses = []
    now = datetime.now(UTC)
    for sensor in sensors:
        last_reading = sensor.get("last_reading")
        if last_reading and isinstance(last_reading, str):
            last_dt = datetime.fromisoformat(last_reading)
            if last_dt.tzinfo is None:
                last_dt = last_dt.replace(tzinfo=UTC)
            age_seconds = (now - last_dt).total_seconds()
            if age_seconds < 300:
                health = "active"
            elif age_seconds < 3600:
                health = "idle"
            else:
                health = "stale"
        else:
            health = "unknown"

        statuses.append({
            "sensor_id": sensor["sensor_id"],
            "garden_id": garden_id,
            "sensor_type": sensor["sensor_type"],
            "location": sensor.get("location"),
            "connected": sensor.get("connected", False),
            "health": health,
            "reading_count": sensor.get("reading_count", 0),
            "last_reading": last_reading,
        })

    return statuses


async def ingest_mqtt_reading(
    garden_id: int,
    payload: dict,
    db: AsyncSession,
) -> SensorReading:
    """Parse an MQTT payload and create a SensorReading."""
    sensor_id = payload["sensor_id"]
    sensor_type = payload.get("sensor_type", "unknown")
    value = float(payload["value"])
    unit = payload.get("unit", "")
    location = payload.get("location")
    timestamp_str = payload.get("timestamp")
    timestamp = (
        datetime.fromisoformat(timestamp_str) if timestamp_str else datetime.now(UTC)
    )

    register_sensor(
        garden_id=garden_id,
        sensor_id=sensor_id,
        sensor_type=sensor_type,
        location=location,
        source="mqtt",
    )

    reading = SensorReading(
        garden_id=garden_id,
        sensor_id=sensor_id,
        sensor_type=sensor_type,
        value=value,
        unit=unit,
        timestamp=timestamp,
        location=location,
    )
    db.add(reading)
    await db.flush()
    await db.refresh(reading)
    return reading


def parse_mqtt_topic(topic: str) -> tuple[int, str] | None:
    """Parse a topic like 'verdanta/sensors/{garden_id}/{sensor_id}' into (garden_id, sensor_id)."""
    prefix = settings.mqtt_topic_prefix
    if not topic.startswith(prefix):
        return None
    suffix = topic[len(prefix):].strip("/")
    parts = suffix.split("/", 1)
    if len(parts) < 2:
        return None
    try:
        garden_id = int(parts[0])
    except ValueError:
        return None
    sensor_id = parts[1]
    return (garden_id, sensor_id)


async def start_mqtt_listener() -> None:
    """Start the MQTT listener as a background task.

    Subscribes to the configured topic prefix and ingests readings.
    Requires aiomqtt and a running Mosquitto broker.
    """
    if not settings.mqtt_enabled:
        logger.info("MQTT is disabled — skipping sensor listener")
        return

    try:
        import aiomqtt
    except ImportError:
        logger.warning("aiomqtt not installed — MQTT sensor listener unavailable")
        return

    topic_filter = f"{settings.mqtt_topic_prefix}/#"
    logger.info(
        "Starting MQTT listener on %s:%d topic=%s",
        settings.mqtt_broker_host,
        settings.mqtt_broker_port,
        topic_filter,
    )

    from verdanta.core.database import async_session_factory

    try:
        async with aiomqtt.Client(
            hostname=settings.mqtt_broker_host,
            port=settings.mqtt_broker_port,
        ) as client:
            await client.subscribe(topic_filter)
            async for message in client.messages:
                try:
                    topic_str = str(message.topic)
                    parsed = parse_mqtt_topic(topic_str)
                    if not parsed:
                        logger.debug("Ignoring MQTT message on topic: %s", topic_str)
                        continue

                    garden_id, sensor_id = parsed
                    payload = json.loads(message.payload)
                    payload.setdefault("sensor_id", sensor_id)

                    async with async_session_factory() as db:
                        await ingest_mqtt_reading(garden_id, payload, db)
                        await db.commit()

                except Exception:
                    logger.warning("Failed to process MQTT message", exc_info=True)
    except Exception:
        logger.error("MQTT listener connection failed", exc_info=True)
