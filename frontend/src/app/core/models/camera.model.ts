export interface CameraStatus {
  is_connected: boolean;
  device_index: number;
  synthetic_mode: boolean;
  resolution: string;
  fps: number;
  active_hole?: string;
  active_state?: string;
}

export interface VerificationResult {
  success: boolean;
  confidence: number;
  reason: 'THREAD_DETECTED' | 'THREAD_NOT_DETECTED' | 'WRONG_POSITION' | 'LOW_CONFIDENCE' | 'CAMERA_ERROR';
  details?: string;
}
