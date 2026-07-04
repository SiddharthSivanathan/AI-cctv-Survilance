export interface Camera {
  id: string;
  organization_id: string;
  store_id: string;
  name: string;
  camera_type: string;
  description: string | null;
  rtsp_url: string;
  username: string | null;
  has_credentials: boolean;
  manufacturer: string | null;
  model: string | null;
  resolution: string | null;
  fps: number | null;
  codec: string | null;
  thumbnail_url: string | null;
  sample_fps: number;
  status: string;
  enabled: boolean;
  last_seen_at: string | null;
  last_error: string | null;
  created_at: string;
  updated_at: string;
}

export interface CreateCameraInput {
  store_id: string;
  name: string;
  camera_type?: string;
  description?: string;
  rtsp_url: string;
  username?: string;
  password?: string;
  manufacturer?: string;
  model?: string;
  sample_fps?: number;
}

export type UpdateCameraInput = Partial<
  Omit<CreateCameraInput, 'store_id'> & { store_id: string; enabled: boolean }
>;

export interface ConnectionTestResult {
  status: string;
  message: string | null;
  resolution: string | null;
  fps: number | null;
  codec: string | null;
  thumbnail_url: string | null;
}
