"""fixes: nullable garden_id on llm_interactions, query indexes, restrict FK on plantings.species_id

Revision ID: a1b2c3d4e5f6
Revises: 24c5b35436f6
Create Date: 2026-03-13 00:00:00.000000

Changes:
- llm_interactions.garden_id: NOT NULL -> NULL  (curation interactions are not garden-scoped)
- Add indexes for common query patterns on weather_records, calendar_events,
  sensor_readings, llm_interactions, and plantings
- plantings.species_id FK: add ondelete RESTRICT to prevent silent cascade deletes
  of plantings when a plant species is removed
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "24c5b35436f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. Make llm_interactions.garden_id nullable ───────────────────────────
    # SQLite requires batch mode for column alterations.
    with op.batch_alter_table("llm_interactions", schema=None) as batch_op:
        batch_op.alter_column(
            "garden_id",
            existing_type=sa.Integer(),
            nullable=True,
        )

    # ── 2. Add plantings.species_id FK with RESTRICT ──────────────────────────
    # Recreate the plantings table via batch to update the FK constraint.
    with op.batch_alter_table("plantings", schema=None) as batch_op:
        batch_op.drop_constraint("fk_plantings_species_id", type_="foreignkey")
        batch_op.create_foreign_key(
            "fk_plantings_species_id",
            "plant_species",
            ["species_id"],
            ["id"],
            ondelete="RESTRICT",
        )

    # ── 3. Indexes ────────────────────────────────────────────────────────────

    # weather_records — primary query pattern: by garden + type, and by garden + time
    op.create_index(
        "ix_weather_records_garden_type",
        "weather_records",
        ["garden_id", "record_type"],
    )
    op.create_index(
        "ix_weather_records_garden_timestamp",
        "weather_records",
        ["garden_id", "timestamp"],
    )
    op.create_index(
        "ix_weather_records_garden_fetched",
        "weather_records",
        ["garden_id", "fetched_at"],
    )

    # calendar_events — primary query pattern: by garden + date
    op.create_index(
        "ix_calendar_events_garden_date",
        "calendar_events",
        ["garden_id", "scheduled_date"],
    )
    op.create_index(
        "ix_calendar_events_garden_completed",
        "calendar_events",
        ["garden_id", "completed"],
    )

    # sensor_readings — by garden + sensor + time
    op.create_index(
        "ix_sensor_readings_garden_sensor_time",
        "sensor_readings",
        ["garden_id", "sensor_id", "timestamp"],
    )

    # llm_interactions — by garden + time for history queries
    op.create_index(
        "ix_llm_interactions_garden_time",
        "llm_interactions",
        ["garden_id", "timestamp"],
    )

    # plantings — by garden for listing
    op.create_index(
        "ix_plantings_garden_id",
        "plantings",
        ["garden_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_plantings_garden_id", table_name="plantings")
    op.drop_index("ix_llm_interactions_garden_time", table_name="llm_interactions")
    op.drop_index(
        "ix_sensor_readings_garden_sensor_time", table_name="sensor_readings"
    )
    op.drop_index("ix_calendar_events_garden_completed", table_name="calendar_events")
    op.drop_index("ix_calendar_events_garden_date", table_name="calendar_events")
    op.drop_index("ix_weather_records_garden_fetched", table_name="weather_records")
    op.drop_index(
        "ix_weather_records_garden_timestamp", table_name="weather_records"
    )
    op.drop_index("ix_weather_records_garden_type", table_name="weather_records")

    with op.batch_alter_table("plantings", schema=None) as batch_op:
        batch_op.drop_constraint("fk_plantings_species_id", type_="foreignkey")
        batch_op.create_foreign_key(
            "fk_plantings_species_id",
            "plant_species",
            ["species_id"],
            ["id"],
        )

    with op.batch_alter_table("llm_interactions", schema=None) as batch_op:
        batch_op.alter_column(
            "garden_id",
            existing_type=sa.Integer(),
            nullable=False,
        )
