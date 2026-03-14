from verdanta.services.sensor_service import (
    _sensor_registry,
    parse_mqtt_topic,
    register_sensor,
)


def test_parse_mqtt_topic_valid() -> None:
    result = parse_mqtt_topic("verdanta/sensors/1/temp-001")
    assert result == (1, "temp-001")


def test_parse_mqtt_topic_nested_sensor_id() -> None:
    result = parse_mqtt_topic("verdanta/sensors/2/greenhouse/shelf-a")
    assert result == (2, "greenhouse/shelf-a")


def test_parse_mqtt_topic_invalid_prefix() -> None:
    result = parse_mqtt_topic("other/prefix/1/temp-001")
    assert result is None


def test_parse_mqtt_topic_missing_sensor_id() -> None:
    result = parse_mqtt_topic("verdanta/sensors/1")
    assert result is None


def test_parse_mqtt_topic_non_numeric_garden() -> None:
    result = parse_mqtt_topic("verdanta/sensors/abc/temp-001")
    assert result is None


def test_register_sensor_new() -> None:
    # Clear registry
    _sensor_registry.clear()

    register_sensor(
        garden_id=1,
        sensor_id="test-sensor",
        sensor_type="temperature",
        location="Bed A",
        source="manual",
    )
    key = (1, "test-sensor")
    assert key in _sensor_registry
    assert _sensor_registry[key]["sensor_type"] == "temperature"
    assert _sensor_registry[key]["location"] == "Bed A"
    assert _sensor_registry[key]["source"] == "manual"


def test_register_sensor_update() -> None:
    _sensor_registry.clear()

    register_sensor(1, "test-sensor", "temperature", "Bed A")
    first_seen = _sensor_registry[(1, "test-sensor")]["first_seen"]

    register_sensor(1, "test-sensor", "temperature_v2", "Bed B")
    entry = _sensor_registry[(1, "test-sensor")]
    assert entry["sensor_type"] == "temperature_v2"
    assert entry["location"] == "Bed B"
    assert entry["first_seen"] == first_seen  # unchanged

    _sensor_registry.clear()
