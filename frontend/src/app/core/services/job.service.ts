import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, tap } from 'rxjs';
import { ApiService } from './api.service';
import { WebSocketService } from './websocket.service';
import { Job } from '../models/job.model';

@Injectable({
  providedIn: 'root'
})
export class JobService {
  private activeJobSubject = new BehaviorSubject<Job | null>(null);
  public activeJob$ = this.activeJobSubject.asObservable();

  private isJobRunningSubject = new BehaviorSubject<boolean>(false);
  public isJobRunning$ = this.isJobRunningSubject.asObservable();

  private recentJobsSubject = new BehaviorSubject<Job[]>([]);
  public recentJobs$ = this.recentJobsSubject.asObservable();

  constructor(
    private api: ApiService,
    private ws: WebSocketService
  ) {
    this.listenToWebSocketUpdates();
  }

  private listenToWebSocketUpdates(): void {
    this.ws.onEvents([
      'JOB_CREATED', 'JOB_STARTED', 'JOB_PAUSED', 'JOB_RESUMED', 'JOB_STOPPED', 'JOB_COMPLETED',
      'HOLE_SUCCESS', 'HOLE_FAILED'
    ]).subscribe({
      next: (event) => {
        const currentJob = this.activeJobSubject.value;
        if (!currentJob) return;

        if (event.event === 'JOB_STARTED') {
          currentJob.status = 'RUNNING';
          this.isJobRunningSubject.next(true);
        } else if (event.event === 'JOB_PAUSED') {
          currentJob.status = 'PAUSED';
          this.isJobRunningSubject.next(false);
        } else if (event.event === 'JOB_RESUMED') {
          currentJob.status = 'RUNNING';
          this.isJobRunningSubject.next(true);
        } else if (event.event === 'JOB_STOPPED') {
          currentJob.status = 'STOPPED';
          this.isJobRunningSubject.next(false);
        } else if (event.event === 'JOB_COMPLETED') {
          currentJob.status = 'COMPLETED';
          this.isJobRunningSubject.next(false);
        } else if (event.event === 'HOLE_SUCCESS') {
          currentJob.successful_holes = (currentJob.successful_holes || 0) + 1;
          currentJob.processed_holes = (currentJob.processed_holes || 0) + 1;
        } else if (event.event === 'HOLE_FAILED') {
          currentJob.failed_holes = (currentJob.failed_holes || 0) + 1;
          currentJob.processed_holes = (currentJob.processed_holes || 0) + 1;
        }

        this.activeJobSubject.next({ ...currentJob });
      }
    });
  }

  public createJob(boardId: string, holeIds: string[], name?: string): Observable<Job> {
    return this.api.post<Job>('jobs', { board_id: boardId, hole_ids: holeIds, name }).pipe(
      tap((job) => {
        this.activeJobSubject.next(job);
        this.loadJobDetail(job.id).subscribe();
      })
    );
  }

  public loadJobDetail(jobId: string): Observable<Job> {
    return this.api.get<Job>(`jobs/${jobId}`).pipe(
      tap((job) => {
        this.activeJobSubject.next(job);
        this.isJobRunningSubject.next(job.status === 'RUNNING');
      })
    );
  }

  public startJob(jobId: string): Observable<any> {
    return this.api.post(`jobs/${jobId}/start`, {}).pipe(
      tap(() => {
        const current = this.activeJobSubject.value;
        if (current) {
          current.status = 'RUNNING';
          this.activeJobSubject.next({ ...current });
          this.isJobRunningSubject.next(true);
        }
      })
    );
  }

  public pauseJob(jobId: string): Observable<any> {
    return this.api.post(`jobs/${jobId}/pause`, {}).pipe(
      tap(() => {
        const current = this.activeJobSubject.value;
        if (current) {
          current.status = 'PAUSED';
          this.activeJobSubject.next({ ...current });
          this.isJobRunningSubject.next(false);
        }
      })
    );
  }

  public resumeJob(jobId: string): Observable<any> {
    return this.api.post(`jobs/${jobId}/resume`, {}).pipe(
      tap(() => {
        const current = this.activeJobSubject.value;
        if (current) {
          current.status = 'RUNNING';
          this.activeJobSubject.next({ ...current });
          this.isJobRunningSubject.next(true);
        }
      })
    );
  }

  public stopJob(jobId: string): Observable<any> {
    return this.api.post(`jobs/${jobId}/stop`, {}).pipe(
      tap(() => {
        const current = this.activeJobSubject.value;
        if (current) {
          current.status = 'STOPPED';
          this.activeJobSubject.next({ ...current });
          this.isJobRunningSubject.next(false);
        }
      })
    );
  }

  public retryHole(jobId: string, holeId: string): Observable<any> {
    return this.api.post(`jobs/${jobId}/retry/${holeId}`, {});
  }
}
