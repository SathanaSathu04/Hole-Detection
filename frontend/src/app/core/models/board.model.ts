export type BoardStatus = 'UPLOADED' | 'PROCESSING' | 'READY' | 'ERROR';

export interface Board {
  id: string;
  name: string;
  image_path: string;
  image_width?: number;
  image_height?: number;
  total_holes: number;
  status: BoardStatus;
  created_at: string;
  updated_at?: string;
}
