export interface Garden {
  id: number;
  name: string;
  location: string | null;
  description: string | null;
  hardiness_zone: string | null;
  latitude: number | null;
  longitude: number | null;
  created_at: string;
  updated_at: string;
}

export interface Plant {
  id: number;
  name: string;
  species: string | null;
  variety: string | null;
  description: string | null;
  care_notes: string | null;
  sun_requirement: string | null;
  water_requirement: string | null;
  soil_type: string | null;
  garden_id: number | null;
  created_at: string;
  updated_at: string;
}

export interface Task {
  id: number;
  title: string;
  description: string | null;
  task_type: string;
  status: string;
  due_date: string | null;
  completed_at: string | null;
  plant_id: number | null;
  created_at: string;
  updated_at: string;
}

export interface SensorReading {
  id: number;
  sensor_id: string;
  metric: string;
  value: number;
  unit: string;
  recorded_at: string;
  garden_id: number | null;
}
