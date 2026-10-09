import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, Subject, filter, map } from 'rxjs';

export interface WebSocketEvent {
  event: string;
  timestamp: string;
  data?: any;
  [key: string]: any;
}

@Injectable({
  providedIn: 'root'
})
export class WebSocketService {
  private socket: WebSocket | null = null;
  private readonly wsUrl = 'ws://localhost:8000/ws';
  private reconnectInterval = 2500;
  private shouldReconnect = true;

  private isConnectedSubject = new BehaviorSubject<boolean>(false);
  public isConnected$ = this.isConnectedSubject.asObservable();

  private eventSubject = new Subject<WebSocketEvent>();
  public events$ = this.eventSubject.asObservable();

  constructor() {
    this.connect();
  }

  public connect(): void {
    if (this.socket && (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING)) {
      return;
    }

    try {
      this.socket = new WebSocket(this.wsUrl);

      this.socket.onopen = () => {
        console.log('[WebSocket] Connected to industrial backend server');
        this.isConnectedSubject.next(true);
      };

      this.socket.onmessage = (event) => {
        try {
          const parsed: WebSocketEvent = JSON.parse(event.data);
          this.eventSubject.next(parsed);
        } catch (e) {
          // Handle string frames (e.g. 'pong')
        }
      };

      this.socket.onclose = () => {
        this.isConnectedSubject.next(false);
        if (this.shouldReconnect) {
          setTimeout(() => this.connect(), this.reconnectInterval);
        }
      };

      this.socket.onerror = (error) => {
        console.warn('[WebSocket] Error:', error);
        this.isConnectedSubject.next(false);
      };
    } catch (e) {
      console.error('[WebSocket] Connection failed:', e);
      if (this.shouldReconnect) {
        setTimeout(() => this.connect(), this.reconnectInterval);
      }
    }
  }

  public onEvent(eventType: string): Observable<WebSocketEvent> {
    return this.events$.pipe(
      filter(e => e.event === eventType)
    );
  }

  public onEvents(eventTypes: string[]): Observable<WebSocketEvent> {
    return this.events$.pipe(
      filter(e => eventTypes.includes(e.event))
    );
  }

  public send(data: string | object): void {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      const msg = typeof data === 'string' ? data : JSON.stringify(data);
      this.socket.send(msg);
    }
  }

  public disconnect(): void {
    this.shouldReconnect = false;
    if (this.socket) {
      this.socket.close();
    }
  }
}
