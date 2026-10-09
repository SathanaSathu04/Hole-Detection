export type HoleStatus = 'PENDING' | 'SELECTED' | 'PROCESSING' | 'SUCCESS' | 'FAILED' | 'SKIPPED';

export interface Hole {
  id: string;
  board_id: string;
  label: string;
  row_number: number;
  column_number: number;
  image_x: number;
  image_y: number;
  radius: number;
  board_x?: number;
  board_y?: number;
  machine_x?: number;
  machine_y?: number;
  status: HoleStatus;
  failure_reason?: string;
  attempt_count: number;
}

export interface HoleDetectionConfig {
  min_radius: number;
  max_radius: number;
  min_circularity: number;
  min_distance: number;
  blur_ksize: number;
  contrast_alpha: number;
  brightness_beta: number;
  threshold_method: 'adaptive_gaussian' | 'otsu' | 'manual';
  manual_threshold_value: number;
  dark_holes: boolean;
  row_tolerance_px: number;
}
