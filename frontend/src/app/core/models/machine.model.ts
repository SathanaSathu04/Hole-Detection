export interface MachinePosition {
  x: number;
  y: number;
  z: number;
}

export interface MachineStatus {
  is_connected: boolean;
  is_homed: boolean;
  is_busy: boolean;
  is_paused: boolean;
  is_emergency_stopped: boolean;
  operation: string;
  current_hole?: string;
  position: MachinePosition;
  mode: 'SIMULATION' | 'REAL';
  port?: string;
  baudrate?: number;
}

export interface CalibrationPoint {
  image_x: number;
  image_y: number;
  machine_x: number;
  machine_y: number;
}

export interface Calibration {
  id: string;
  board_id?: string;
  name: string;
  is_valid: boolean;
  reprojection_error: number;
  reference_points: CalibrationPoint[];
  transformation_matrix: number[][];
  message?: string;
}
