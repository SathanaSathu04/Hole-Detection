import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, tap } from 'rxjs';
import { ApiService } from './api.service';
import { WebSocketService } from './websocket.service';
import { MachinePosition, MachineStatus, Calibration, CalibrationPoint } from '../models/machine.model';

@Injectable({
  providedIn: 'root'
})
export class MachineService {
  private positionSubject = new BehaviorSubject<MachinePosition>({ x: 0, y: 0, z: 25.0 });
  public position$ = this.positionSubject.asObservable();

  private statusSubject = new BehaviorSubject<MachineStatus>({
    is_connected: true,
    is_homed: true,
    is_busy: false,
    is_paused: false,
    is_emergency_stopped: false,
    operation: 'READY',
    position: { x: 0, y: 0, z: 25.0 },
    mode: 'SIMULATION'
  });
  public status$ = this.statusSubject.asObservable();

  private calibrationSubject = new BehaviorSubject<Calibration | null>(null);
  public calibration$ = this.calibrationSubject.asObservable();

  constructor(
    private api: ApiService,
    private ws: WebSocketService
  ) {
    this.refreshStatus();
    this.listenToWebSocketUpdates();
  }

  private listenToWebSocketUpdates(): void {
    this.ws.onEvents([
      'MACHINE_CONNECTED', 'MACHINE_DISCONNECTED', 'MACHINE_READY',
      'MACHINE_MOVING', 'MACHINE_POSITION', 'MACHINE_ERROR', 'INITIAL_STATE'
    ]).subscribe({
      next: (event) => {
        if (event.event === 'MACHINE_POSITION' || event.data?.position) {
          const pos = event.data?.position || event['position'];
          if (pos) {
            this.positionSubject.next(pos);
            const current = this.statusSubject.value;
            this.statusSubject.next({ ...current, position: pos, operation: event.data?.operation || current.operation });
          }
        }
        if (event.event === 'MACHINE_READY') {
          const current = this.statusSubject.value;
          this.statusSubject.next({ ...current, is_busy: false, is_emergency_stopped: false, operation: 'READY' });
        }
        if (event.event === 'MACHINE_ERROR') {
          const current = this.statusSubject.value;
          this.statusSubject.next({ ...current, is_emergency_stopped: true, operation: 'STOPPED' });
        }
        if (event.event === 'INITIAL_STATE' && event.data?.machine) {
          this.statusSubject.next(event.data.machine);
          if (event.data.machine.position) {
            this.positionSubject.next(event.data.machine.position);
          }
        }
      }
    });
  }

  public refreshStatus(): void {
    this.api.get<MachineStatus>('machine/status').subscribe({
      next: (status) => {
        this.statusSubject.next(status);
        if (status.position) {
          this.positionSubject.next(status.position);
        }
      },
      error: (err) => console.warn('Machine status check failed:', err)
    });
  }

  public connect(mode: 'SIMULATION' | 'REAL' = 'SIMULATION', port = 'COM3', baudrate = 115200): Observable<any> {
    return this.api.post('machine/connect', { mode, port, baudrate }).pipe(
      tap(() => this.refreshStatus())
    );
  }

  public disconnect(): Observable<any> {
    return this.api.post('machine/disconnect', {}).pipe(
      tap(() => this.refreshStatus())
    );
  }

  public home(): Observable<any> {
    return this.api.post('machine/home', {}).pipe(
      tap(() => this.refreshStatus())
    );
  }

  public stop(): Observable<any> {
    return this.api.post('machine/stop', {}).pipe(
      tap(() => this.refreshStatus())
    );
  }

  public move(x: number, y: number, z?: number, speed?: number): Observable<any> {
    return this.api.post('machine/move', { x, y, z, speed });
  }

  public calibrate(boardId: string | undefined, points: CalibrationPoint[]): Observable<Calibration> {
    return this.api.post<Calibration>('calibration', {
      board_id: boardId,
      name: 'Board Homography Calibration',
      reference_points: points
    }).pipe(
      tap((calib) => this.calibrationSubject.next(calib))
    );
  }
}
