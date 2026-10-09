import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, tap } from 'rxjs';
import { ApiService } from './api.service';
import { WebSocketService } from './websocket.service';
import { Hole, HoleDetectionConfig, HoleStatus } from '../models/hole.model';

@Injectable({
  providedIn: 'root'
})
export class HoleService {
  private holesSubject = new BehaviorSubject<Hole[]>([]);
  public holes$ = this.holesSubject.asObservable();

  private selectedHolesSubject = new BehaviorSubject<Hole[]>([]);
  public selectedHoles$ = this.selectedHolesSubject.asObservable();

  private inspectedHoleSubject = new BehaviorSubject<Hole | null>(null);
  public inspectedHole$ = this.inspectedHoleSubject.asObservable();

  private isDetectingSubject = new BehaviorSubject<boolean>(false);
  public isDetecting$ = this.isDetectingSubject.asObservable();

  constructor(
    private api: ApiService,
    private ws: WebSocketService
  ) {
    this.listenToWebSocketUpdates();
  }

  private listenToWebSocketUpdates(): void {
    this.ws.onEvents(['HOLE_PROCESSING', 'HOLE_SUCCESS', 'HOLE_FAILED', 'HOLE_RETRY']).subscribe({
      next: (event) => {
        const holeId = event.data?.hole_id;
        const status = event.data?.status || (event.event === 'HOLE_PROCESSING' ? 'PROCESSING' : (event.event === 'HOLE_SUCCESS' ? 'SUCCESS' : 'FAILED'));
        const reason = event.data?.reason;
        const attempt = event.data?.attempt;

        const currentHoles = this.holesSubject.value;
        const target = currentHoles.find(h => h.id === holeId || h.label === event.data?.label);
        if (target) {
          target.status = status as HoleStatus;
          if (reason) target.failure_reason = reason;
          if (attempt !== undefined) target.attempt_count = attempt;

          // If this is the inspected hole, update inspector
          if (this.inspectedHoleSubject.value?.id === target.id) {
            this.inspectedHoleSubject.next({ ...target });
          }

          // Trigger update to subscribers
          this.holesSubject.next([...currentHoles]);
        }
      }
    });
  }

  public loadHoles(boardId: string): Observable<Hole[]> {
    return this.api.get<Hole[]>(`boards/${boardId}/holes`).pipe(
      tap((holes) => {
        this.holesSubject.next(holes);
        if (holes.length > 0 && !this.inspectedHoleSubject.value) {
          this.inspectedHoleSubject.next(holes[0]);
        }
      })
    );
  }

  public detectHoles(boardId: string, config?: Partial<HoleDetectionConfig>): Observable<any> {
    this.isDetectingSubject.next(true);
    return this.api.post<any>(`boards/${boardId}/holes/detect`, config || {}).pipe(
      tap(() => {
        this.isDetectingSubject.next(false);
        this.loadHoles(boardId).subscribe();
      })
    );
  }

  public searchHole(boardId: string, label: string): Observable<Hole> {
    return this.api.get<Hole>(`boards/${boardId}/holes/search`, { label }).pipe(
      tap((hole) => {
        if (hole) {
          this.setInspectedHole(hole);
        }
      })
    );
  }

  public setInspectedHole(hole: Hole | null): void {
    this.inspectedHoleSubject.next(hole);
  }

  public toggleHoleSelection(hole: Hole): void {
    const current = [...this.selectedHolesSubject.value];
    const index = current.findIndex(h => h.id === hole.id);
    if (index >= 0) {
      current.splice(index, 1);
      hole.status = 'PENDING';
    } else {
      current.push(hole);
      hole.status = 'SELECTED';
    }
    this.selectedHolesSubject.next(current);
    this.holesSubject.next([...this.holesSubject.value]);
  }

  public selectAllHoles(): void {
    const all = this.holesSubject.value;
    all.forEach(h => h.status = 'SELECTED');
    this.selectedHolesSubject.next([...all]);
    this.holesSubject.next([...all]);
  }

  public clearSelection(): void {
    const all = this.holesSubject.value;
    all.forEach(h => {
      if (h.status === 'SELECTED') {
        h.status = 'PENDING';
      }
    });
    this.selectedHolesSubject.next([]);
    this.holesSubject.next([...all]);
  }

  public reorderSelection(newOrder: Hole[]): void {
    this.selectedHolesSubject.next(newOrder);
  }

  public addManualHole(boardId: string, imageX: number, imageY: number, label?: string): Observable<Hole> {
    return this.api.post<Hole>(`boards/${boardId}/holes/manual`, { image_x: imageX, image_y: imageY, label }).pipe(
      tap((newHole) => {
        const current = this.holesSubject.value;
        this.holesSubject.next([...current, newHole]);
        this.setInspectedHole(newHole);
      })
    );
  }

  public deleteHole(boardId: string, holeId: string): Observable<any> {
    return this.api.delete(`boards/${boardId}/holes/${holeId}`).pipe(
      tap(() => {
        const current = this.holesSubject.value.filter(h => h.id !== holeId);
        this.holesSubject.next(current);
        const selected = this.selectedHolesSubject.value.filter(h => h.id !== holeId);
        this.selectedHolesSubject.next(selected);
        if (this.inspectedHoleSubject.value?.id === holeId) {
          this.inspectedHoleSubject.next(current[0] || null);
        }
      })
    );
  }
}
