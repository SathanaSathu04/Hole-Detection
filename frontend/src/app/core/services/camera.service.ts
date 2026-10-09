import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, tap } from 'rxjs';
import { ApiService } from './api.service';
import { WebSocketService } from './websocket.service';
import { CameraStatus, VerificationResult } from '../models/camera.model';

@Injectable({
  providedIn: 'root'
})
export class CameraService {
  private statusSubject = new BehaviorSubject<CameraStatus>({
    is_connected: true,
    device_index: 0,
    synthetic_mode: true,
    resolution: '640x480',
    fps: 30,
    active_hole: 'A1',
    active_state: 'IDLE'
  });
  public status$ = this.statusSubject.asObservable();

  private verificationSubject = new BehaviorSubject<VerificationResult | null>(null);
  public verification$ = this.verificationSubject.asObservable();

  constructor(
    private api: ApiService,
    private ws: WebSocketService
  ) {
    this.refreshStatus();
    this.listenToWebSocketUpdates();
  }

  private listenToWebSocketUpdates(): void {
    this.ws.onEvents(['CAMERA_CONNECTED', 'CAMERA_DISCONNECTED', 'CAMERA_VERIFICATION', 'INITIAL_STATE']).subscribe({
      next: (event) => {
        if (event.event === 'CAMERA_CONNECTED') {
          const current = this.statusSubject.value;
          this.statusSubject.next({ ...current, is_connected: true });
        }
        if (event.event === 'CAMERA_DISCONNECTED') {
          const current = this.statusSubject.value;
          this.statusSubject.next({ ...current, is_connected: false });
        }
        if (event.event === 'CAMERA_VERIFICATION') {
          if (event.data) {
            this.verificationSubject.next(event.data);
          }
        }
        if (event.event === 'INITIAL_STATE' && event.data?.camera) {
          this.statusSubject.next(event.data.camera);
        }
      }
    });
  }

  public refreshStatus(): void {
    this.api.get<CameraStatus>('camera/status').subscribe({
      next: (status) => this.statusSubject.next(status),
      error: (err) => console.warn('Camera status check failed:', err)
    });
  }

  public connect(deviceIndex = 0): Observable<any> {
    return this.api.post('camera/connect', { device_index: deviceIndex }).pipe(
      tap(() => this.refreshStatus())
    );
  }

  public disconnect(): Observable<any> {
    return this.api.post('camera/disconnect', {}).pipe(
      tap(() => this.refreshStatus())
    );
  }

  public captureBoard(name?: string): Observable<any> {
    return this.api.post('camera/capture-board', { name });
  }

  public getStreamUrl(): string {
    return this.api.getApiUrl('camera/stream');
  }

  public getSnapshotUrl(): string {
    return this.api.getApiUrl('camera/frame') + `?t=${Date.now()}`;
  }
}

