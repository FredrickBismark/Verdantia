// ── Garden ──────────────────────────────────────────────────────────────────

export interface Garden {
  id: number;
  name: string;
  latitude: number;
  longitude: number;
  elevation_m: number | null;
  usda_zone: string | null;
  soil_type_default: string | null;
  timezone: string;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface GardenCreate {
  name: string;
  latitude: number;
  longitude: number;
  elevation_m?: number | null;
  usda_zone?: string | null;
  soil_type_default?: string | null;
  timezone?: string;
  notes?: string | null;
}

// ── Plant Species ───────────────────────────────────────────────────────────

export interface PlantSpecies {
  id: number;
  common_name: string;
  scientific_name: string | null;
  family: string | null;
  variety: string | null;
  growth_habit: string | null;
  days_to_maturity_min: number | null;
  days_to_maturity_max: number | null;
  optimal_soil_ph_min: number | null;
  optimal_soil_ph_max: number | null;
  sun_requirement: string | null;
  water_requirement: string | null;
  frost_tolerance: string | null;
  min_temp_c: number | null;
  max_temp_c: number | null;
  spacing_cm: number | null;
  depth_cm: number | null;
  companion_plants: Record<string, unknown> | null;
  antagonist_plants: Record<string, unknown> | null;
  custom_fields: Record<string, unknown> | null;
  curation_status: string;
  last_curated_at: string | null;
  curation_model: string | null;
  created_at: string;
  updated_at: string;
}

export interface DossierSection {
  id: number;
  species_id: number;
  section_type: string;
  title: string;
  content: string;
  confidence: 'high' | 'medium' | 'low' | 'contradicted';
  source_ids: number[] | null;
  display_order: number;
  is_localized: boolean;
  last_updated: string;
}

export interface PlantDataSource {
  id: number;
  species_id: number;
  source_type: string;
  source_name: string;
  source_url: string | null;
  raw_data: Record<string, unknown>;
  confidence_score: number | null;
  ingested_at: string;
  notes: string | null;
}

export interface PlantDetail extends PlantSpecies {
  dossier_sections: DossierSection[];
  data_sources: PlantDataSource[];
}

// ── Planting ────────────────────────────────────────────────────────────────

export interface Planting {
  id: number;
  garden_id: number;
  species_id: number;
  bed_or_location: string | null;
  quantity: number;
  date_seeded: string | null;
  date_transplanted: string | null;
  date_first_harvest: string | null;
  date_last_harvest: string | null;
  date_removed: string | null;
  status: string;
  notes: string | null;
  custom_fields: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

// ── Calendar ────────────────────────────────────────────────────────────────

export interface CalendarEvent {
  id: number;
  garden_id: number;
  planting_id: number | null;
  event_type: string;
  title: string;
  description: string | null;
  scheduled_date: string;
  scheduled_time: string | null;
  recurrence_rule: string | null;
  completed: boolean;
  completed_at: string | null;
  source: string;
  priority: string | null;
  weather_dependent: boolean;
  color: string | null;
  created_at: string;
}

// ── Weather ─────────────────────────────────────────────────────────────────

export interface WeatherRecord {
  id: number;
  garden_id: number;
  timestamp: string;
  record_type: string;
  source: string;
  temp_c: number | null;
  temp_min_c: number | null;
  temp_max_c: number | null;
  humidity_pct: number | null;
  precipitation_mm: number | null;
  wind_speed_kmh: number | null;
  soil_temp_c: number | null;
  soil_moisture_pct: number | null;
  uv_index: number | null;
  cloud_cover_pct: number | null;
  frost_risk: boolean | null;
}

export interface SensorReading {
  id: number;
  garden_id: number;
  sensor_id: string;
  sensor_type: string;
  value: number;
  unit: string;
  timestamp: string;
  location: string | null;
}

// ── Harvest ─────────────────────────────────────────────────────────────────

export interface HarvestLog {
  id: number;
  planting_id: number;
  harvest_date: string;
  quantity: number;
  unit: string;
  quality_rating: number | null;
  notes: string | null;
  created_at: string;
}

// ── Soil ────────────────────────────────────────────────────────────────────

export interface SoilTest {
  id: number;
  garden_id: number;
  location: string | null;
  test_date: string;
  ph: number | null;
  nitrogen_ppm: number | null;
  phosphorus_ppm: number | null;
  potassium_ppm: number | null;
  organic_matter_pct: number | null;
  texture: string | null;
  notes: string | null;
  raw_data: Record<string, unknown> | null;
  created_at: string;
}

// ── Advisor ─────────────────────────────────────────────────────────────────

export interface LLMInteraction {
  id: number;
  garden_id: number;
  planting_id: number | null;
  interaction_type: string;
  user_prompt: string;
  system_context: string;
  response: string;
  model_used: string;
  provider: string;
  timestamp: string;
  feedback: string | null;
  tokens_used: number | null;
}

export interface Alert {
  priority: string;
  category: string;
  description: string;
  timestamp: string;
}

// ── Settings ────────────────────────────────────────────────────────────────

export interface AppSetting {
  key: string;
  value: string;
}

export interface ProviderPreset {
  base_url: string;
  requires_api_key: boolean;
  models: Array<{
    id: string;
    name: string;
    vision: boolean;
  }>;
}

// ── API Response Wrappers ───────────────────────────────────────────────────

export interface ApiResponse<T> {
  data: T;
}

export interface ApiListResponse<T> {
  data: T[];
  count: number;
}
