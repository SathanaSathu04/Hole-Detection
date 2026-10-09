export type JobStatus = 'DRAFT' | 'READY' | 'RUNNING' | 'PAUSED' | 'COMPLETED' | 'FAILED' | 'STOPPED';

export interface JobHole {
  id: string;
  hole_id: string;
  sequence: number;
  status: string;
  attempt_count: number;
  failure_reason?: string;
  target_machine_x?: number;
  target_machine_y?: number;
  label?: string;
  image_x?: number;
  image_y?: number;
}

export interface Job {
  id: string;
  board_id: string;
  name: string;
  status: JobStatus;
  total_holes: number;
  processed_holes: number;
  successful_holes: number;
  failed_holes: number;
  skipped_holes: number;
  current_hole_id?: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  job_holes?: JobHole[];
}
