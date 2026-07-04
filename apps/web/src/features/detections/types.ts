export interface DetectionBox {
  class_id: number;
  class_name: string;
  confidence: number;
  bbox: [number, number, number, number]; // x1,y1,x2,y2 in the 640x640 sampled frame
  track_id: number | null;
}

export interface LatestDetections {
  camera_id: string;
  person_count: number;
  detections: DetectionBox[];
}

/** The AI sampler resizes frames to this square before inference. */
export const DETECTION_FRAME_SIZE = 640;
