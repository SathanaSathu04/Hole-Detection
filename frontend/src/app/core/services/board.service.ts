import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, tap } from 'rxjs';
import { ApiService } from './api.service';
import { Board } from '../models/board.model';

@Injectable({
  providedIn: 'root'
})
export class BoardService {
  private boardsSubject = new BehaviorSubject<Board[]>([]);
  public boards$ = this.boardsSubject.asObservable();

  private activeBoardSubject = new BehaviorSubject<Board | null>(null);
  public activeBoard$ = this.activeBoardSubject.asObservable();

  constructor(private api: ApiService) {
    this.refreshBoards();
  }

  public refreshBoards(): void {
    this.api.get<Board[]>('boards').subscribe({
      next: (boards) => {
        this.boardsSubject.next(boards);
        if (boards.length > 0 && !this.activeBoardSubject.value) {
          this.setActiveBoard(boards[0]);
        }
      },
      error: (err) => console.error('Failed to load boards:', err)
    });
  }

  public setActiveBoard(board: Board | null): void {
    this.activeBoardSubject.next(board);
  }

  public uploadBoard(file: File, name?: string): Observable<Board> {
    const formData = new FormData();
    formData.append('file', file);
    if (name) {
      formData.append('name', name);
    }
    return this.api.postFormData<Board>('boards/upload', formData).pipe(
      tap((newBoard) => {
        this.refreshBoards();
        this.setActiveBoard(newBoard);
      })
    );
  }

  public getBoardImageUri(boardId: string): string {
    return this.api.getApiUrl(`boards/${boardId}/image`);
  }

  public deleteBoard(boardId: string): Observable<any> {
    return this.api.delete(`boards/${boardId}`).pipe(
      tap(() => {
        if (this.activeBoardSubject.value?.id === boardId) {
          this.activeBoardSubject.next(null);
        }
        this.refreshBoards();
      })
    );
  }
}
