import { Component, EventEmitter, Input, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MachineService } from '../../core/services/machine.service';
import { Calibration, CalibrationPoint } from '../../core/models/machine.model';

@Component({
  selector: 'app-calibration-dialog',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="modal-backdrop" (click)="close()">
      <div class="modal-card" (click)="$event.stopPropagation()">
        <div class="modal-header">
          <div class="header-left">
            <span class="material-icons-outlined text-primary">tune</span>
            <h3>Planar Coordinate Calibration & Homography</h3>
          </div>
          <button class="icon-close" (click)="close()">
            <span class="material-icons-outlined">close</span>
          </button>
        </div>

        <div class="modal-body">
          <p class="section-desc">
            Map image pixel coordinates <code>(X, Y)</code> to physical CNC machine coordinates <code>(X, Y mm)</code> using 4-point planar perspective transformation.
          </p>

          <table class="calibration-table mono-font">
            <thead>
              <tr>
                <th>Pt</th>
                <th>Image X (px)</th>
                <th>Image Y (px)</th>
                <th>Machine X (mm)</th>
                <th>Machine Y (mm)</th>
              </tr>
            </thead>
            <tbody>
              <tr *ngFor="let pt of points; let i = index">
                <td>#{{ i + 1 }}</td>
                <td><input type="number" [(ngModel)]="pt.image_x" class="input-cell" /></td>
                <td><input type="number" [(ngModel)]="pt.image_y" class="input-cell" /></td>
                <td><input type="number" [(ngModel)]="pt.machine_x" class="input-cell" /></td>
                <td><input type="number" [(ngModel)]="pt.machine_y" class="input-cell" /></td>
              </tr>
            </tbody>
          </table>

          <div class="calibration-result" *ngIf="lastResult">
            <div class="result-badge" [class.success]="lastResult.is_valid" [class.danger]="!lastResult.is_valid">
              <span class="material-icons-outlined">{{ lastResult.is_valid ? 'check_circle' : 'error' }}</span>
              <span>{{ lastResult.message || (lastResult.is_valid ? 'Calibration Valid' : 'Calibration Error') }}</span>
            </div>
            <div class="error-metric mono-font" *ngIf="lastResult.reprojection_error !== undefined">
              Mean Reprojection Error: <strong>{{ lastResult.reprojection_error.toFixed(4) }} mm</strong>
            </div>
          </div>
        </div>

        <div class="modal-footer">
          <button class="btn-industrial btn-secondary" (click)="loadPreset()">
            Reset Defaults
          </button>
          <button class="btn-industrial btn-primary" (click)="calculate()" [disabled]="isCalculating">
            <span class="material-icons-outlined" *ngIf="!isCalculating">calculate</span>
            <span class="material-icons-outlined spin" *ngIf="isCalculating">sync</span>
            Compute Homography
          </button>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .modal-backdrop {
      position: fixed;
      top: 0;
      left: 0;
      width: 100vw;
      height: 100vh;
      background: rgba(0, 0, 0, 0.75);
      backdrop-filter: blur(4px);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 100;
    }
    .modal-card {
      background: #131b2e;
      border: 1px solid #243452;
      border-radius: 12px;
      width: 650px;
      max-width: 90vw;
      box-shadow: 0 10px 40px rgba(0, 0, 0, 0.8);
    }
    .modal-header {
      padding: 16px 20px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid #243452;
    }
    .header-left {
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .text-primary { color: #38bdf8; }
    .icon-close {
      background: transparent;
      border: none;
      color: #94a3b8;
      cursor: pointer;
    }
    .icon-close:hover { color: #ffffff; }
    .modal-body {
      padding: 20px;
    }
    .section-desc {
      font-size: 0.85rem;
      color: #94a3b8;
      margin-bottom: 16px;
    }
    .section-desc code {
      background: #182238;
      padding: 2px 6px;
      border-radius: 4px;
      color: #38bdf8;
    }
    .calibration-table {
      width: 100%;
      border-collapse: collapse;
      margin-bottom: 16px;
    }
    .calibration-table th {
      text-align: left;
      font-size: 0.75rem;
      color: #94a3b8;
      padding: 8px 6px;
      border-bottom: 1px solid #243452;
    }
    .calibration-table td {
      padding: 6px;
    }
    .input-cell {
      width: 100%;
      background: #0b0f17;
      border: 1px solid #243452;
      border-radius: 4px;
      color: #f1f5f9;
      padding: 6px 8px;
      font-size: 0.85rem;
    }
    .input-cell:focus {
      outline: none;
      border-color: #3b82f6;
    }
    .calibration-result {
      background: #0b0f17;
      border: 1px solid #243452;
      border-radius: 8px;
      padding: 12px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .result-badge {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 0.85rem;
      font-weight: 600;
    }
    .result-badge.success { color: #10b981; }
    .result-badge.danger { color: #ef4444; }
    .error-metric {
      font-size: 0.8rem;
      color: #94a3b8;
    }
    .modal-footer {
      padding: 16px 20px;
      border-top: 1px solid #243452;
      display: flex;
      justify-content: space-between;
    }
    .spin {
      animation: spin 1s infinite linear;
    }
    @keyframes spin {
      100% { transform: rotate(360deg); }
    }
  `]
})
export class CalibrationDialogComponent {
  @Input() boardId?: string;
  @Output() closed = new EventEmitter<void>();

  public points: CalibrationPoint[] = [
    { image_x: 100, image_y: 100, machine_x: 20.0, machine_y: 20.0 },
    { image_x: 700, image_y: 100, machine_x: 140.0, machine_y: 20.0 },
    { image_x: 700, image_y: 500, machine_x: 140.0, machine_y: 100.0 },
    { image_x: 100, image_y: 500, machine_x: 20.0, machine_y: 100.0 }
  ];

  public isCalculating = false;
  public lastResult: Calibration | null = null;

  constructor(private machineService: MachineService) {}

  public loadPreset(): void {
    this.points = [
      { image_x: 100, image_y: 100, machine_x: 20.0, machine_y: 20.0 },
      { image_x: 700, image_y: 100, machine_x: 140.0, machine_y: 20.0 },
      { image_x: 700, image_y: 500, machine_x: 140.0, machine_y: 100.0 },
      { image_x: 100, image_y: 500, machine_x: 20.0, machine_y: 100.0 }
    ];
    this.lastResult = null;
  }

  public calculate(): void {
    this.isCalculating = true;
    this.machineService.calibrate(this.boardId, this.points).subscribe({
      next: (res) => {
        this.lastResult = res;
        this.isCalculating = false;
      },
      error: (err) => {
        this.isCalculating = false;
        alert(err.error?.detail || 'Calibration calculation failed');
      }
    });
  }

  public close(): void {
    this.closed.emit();
  }
}
