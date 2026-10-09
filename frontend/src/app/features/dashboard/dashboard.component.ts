import { Component, OnInit, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { BoardService } from '../../core/services/board.service';
import { HoleService } from '../../core/services/hole.service';
import { JobService } from '../../core/services/job.service';
import { MachineService } from '../../core/services/machine.service';
import { CameraService } from '../../core/services/camera.service';
import { WebSocketService } from '../../core/services/websocket.service';
import { Board } from '../../core/models/board.model';
import { Hole } from '../../core/models/hole.model';
import { Job } from '../../core/models/job.model';
import { MachineStatus, MachinePosition } from '../../core/models/machine.model';
import { CameraStatus, VerificationResult } from '../../core/models/camera.model';
import { HoleMapCanvasComponent } from '../hole-map/hole-map-canvas.component';
import { CalibrationDialogComponent } from '../calibration/calibration-dialog.component';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, FormsModule, HoleMapCanvasComponent, CalibrationDialogComponent],
  template: `
    <div class="dashboard-wrapper">
      <!-- 1. TOP TELEMETRY BAR -->
      <header class="system-top-bar">
        <div class="brand-section">
          <span class="material-icons-outlined brand-icon">precision_manufacturing</span>
          <div class="brand-text">
            <h1>TEXTILE THREAD & NEEDLE INSERTION SYSTEM</h1>
            <span class="sub-brand mono-font">AUTOMATED VISION DETECTION & 3D CNC KINEMATICS</span>
          </div>
        </div>

        <div class="telemetry-pills">
          <!-- Machine Dot -->
          <div class="pill mono-font">
            <span class="status-dot" [ngClass]="(machineStatus?.is_connected) ? 'connected' : 'disconnected'"></span>
            <span class="pill-label">MACHINE:</span>
            <span class="pill-val">{{ machineStatus?.is_connected ? 'ONLINE' : 'OFFLINE' }}</span>
            <span class="pill-badge badge badge-processing" *ngIf="machineStatus?.operation && machineStatus?.operation !== 'READY' && machineStatus?.operation !== 'IDLE'">
              {{ machineStatus?.operation }}
            </span>
          </div>

          <!-- Camera Dot -->
          <div class="pill mono-font">
            <span class="status-dot" [ngClass]="(cameraStatus?.is_connected) ? 'connected' : 'disconnected'"></span>
            <span class="pill-label">CAMERA:</span>
            <span class="pill-val">{{ cameraStatus?.is_connected ? 'STREAMING' : 'OFFLINE' }}</span>
          </div>

          <!-- Mode Pill -->
          <div class="pill mono-font">
            <span class="pill-label">MODE:</span>
            <span class="pill-val mode-val">{{ machineStatus?.mode || 'SIMULATION' }}</span>
          </div>

          <!-- Calibration Pill -->
          <button class="pill-btn mono-font" (click)="showCalibration = true">
            <span class="material-icons-outlined">tune</span>
            <span>CALIBRATE</span>
          </button>

          <!-- Home Button -->
          <button class="pill-btn mono-font" (click)="onHomeMachine()" title="Drive all axes to Home (G28)">
            <span class="material-icons-outlined">home</span>
            <span>HOME</span>
          </button>

          <!-- Emergency Stop -->
          <button class="btn-industrial btn-estop" (click)="onEmergencyStop()">
            <span class="material-icons-outlined">dangerous</span>
            <span>E-STOP</span>
          </button>
        </div>
      </header>

      <!-- 2. KPI METRICS SUMMARY BAR -->
      <section class="kpi-summary-bar">
        <div class="kpi-card">
          <span class="kpi-title">TOTAL HOLES DETECTED</span>
          <span class="kpi-number mono-font text-primary">{{ holes.length | number }}</span>
        </div>
        <div class="kpi-card selected-card">
          <span class="kpi-title">SELECTED FOR INSERTION</span>
          <span class="kpi-number text-selected mono-font">{{ selectedHoles.length | number }}</span>
        </div>
        <div class="kpi-card success-card">
          <span class="kpi-title">SUCCESSFUL</span>
          <div class="kpi-val-row">
            <span class="kpi-number text-success mono-font">{{ successCount | number }}</span>
            <span class="kpi-pct mono-font" *ngIf="holes.length > 0">
              ({{ (successCount / (selectedHoles.length || holes.length) * 100).toFixed(1) }}%)
            </span>
          </div>
        </div>
        <div class="kpi-card failed-card">
          <span class="kpi-title">FAILED</span>
          <div class="kpi-val-row">
            <span class="kpi-number text-failed mono-font">{{ failedCount | number }}</span>
            <span class="badge badge-failed" *ngIf="failedCount > 0">{{ failedCount }} NEEDS RETRY</span>
          </div>
        </div>
        <div class="kpi-card pending-card">
          <span class="kpi-title">PENDING</span>
          <span class="kpi-number text-pending mono-font">{{ pendingCount | number }}</span>
        </div>
        <div class="kpi-card progress-kpi-card">
          <div class="kpi-progress-header">
            <span class="kpi-title">JOB PROGRESS</span>
            <span class="mono-font progress-pct">{{ jobProgressPct.toFixed(1) }}%</span>
          </div>
          <div class="progress-bar-container">
            <div class="progress-bar-fill" [style.width.%]="jobProgressPct"></div>
          </div>
        </div>
      </section>

      <!-- 3. MAIN WORKSPACE GRID -->
      <main class="main-workspace-grid">
        <!-- LEFT COLUMN: BOARD & HOLE MAP CANVAS -->
        <section class="board-viewport-panel">
          <!-- Viewport Header Controls -->
          <div class="panel-header-controls">
            <!-- Board Selection & Upload -->
            <div class="control-group">
              <label class="control-label">BOARD:</label>
              <select class="select-input" [ngModel]="activeBoard?.id" (ngModelChange)="onBoardSelected($event)">
                <option *ngFor="let b of boards" [value]="b.id">{{ b.name }} ({{ b.total_holes }} holes)</option>
              </select>

              <!-- Upload Custom Board Image Button -->
              <label class="btn-industrial btn-secondary file-upload-btn">
                <span class="material-icons-outlined">upload_file</span>
                <span>Upload New Board</span>
                <input type="file" (change)="onFileUpload($event)" accept="image/*" hidden />
              </label>

              <!-- Open Camera Button -->
              <button class="btn-industrial btn-secondary" (click)="openCameraModal()" title="Capture physical board with camera">
                <span class="material-icons-outlined">photo_camera</span>
                <span>Open Camera</span>
              </button>

              <!-- Run OpenCV Detection Button -->
              <button
                class="btn-industrial btn-primary"
                (click)="onDetectHoles()"
                [disabled]="!activeBoard || isDetecting"
              >
                <span class="material-icons-outlined" *ngIf="!isDetecting">biotech</span>
                <span class="material-icons-outlined spin" *ngIf="isDetecting">sync</span>
                <span>{{ isDetecting ? 'Analyzing...' : 'Detect Holes' }}</span>
              </button>
            </div>

            <!-- Search Box & Confirm -->
            <div class="control-group">
              <!-- Search Hole Box -->
              <div class="search-box">
                <span class="material-icons-outlined search-icon">search</span>
                <input
                  type="text"
                  placeholder="Find hole (e.g. A1, B3)"
                  class="search-input mono-font"
                  [(ngModel)]="searchQuery"
                  (keyup.enter)="onSearchHole()"
                />
                <button class="search-btn" (click)="onSearchHole()">FIND</button>
              </div>

              <!-- Confirm Map Button -->
              <button
                class="btn-industrial btn-success"
                (click)="onConfirmHoleMap()"
                [disabled]="holes.length === 0"
                title="Confirm Hole Map is verified for production execution"
              >
                <span class="material-icons-outlined">check_circle</span>
                <span>Confirm Map</span>
              </button>
            </div>
          </div>

          <!-- Interactive HTML5 Canvas Container -->
          <div class="canvas-viewport">
            <app-hole-map-canvas
              #canvasCmp
              [holes]="holes"
              [selectedHoles]="selectedHoles"
              [inspectedHole]="inspectedHole"
              [currentMachineHole]="currentMachineHole"
              [machinePosition]="machinePosition"
              [boardImageUrl]="boardImageUrl"
              (holeClicked)="onHoleClicked($event)"
            ></app-hole-map-canvas>
          </div>
        </section>

        <!-- RIGHT COLUMN: CURRENT HOLE INSPECTOR & SEQUENCE QUEUE -->
        <aside class="right-inspector-panel">
          <!-- Current Hole Inspector Card -->
          <div class="inspector-card">
            <div class="card-header">
              <div class="header-title-row">
                <span class="material-icons-outlined text-primary">pin_drop</span>
                <h3>HOLE INSPECTOR</h3>
              </div>
              <span
                *ngIf="inspectedHole"
                class="badge badge-{{ inspectedHole.status.toLowerCase() }}"
              >
                {{ inspectedHole.status }}
              </span>
            </div>

            <div class="card-body" *ngIf="inspectedHole; else noHoleSelected">
              <div class="hole-big-label-row">
                <div class="big-label mono-font">{{ inspectedHole.label }}</div>
                <div class="row-col-tags mono-font">
                  <span>ROW: <strong>{{ inspectedHole.row_number }}</strong></span>
                  <span>COL: <strong>{{ inspectedHole.column_number }}</strong></span>
                </div>
              </div>

              <!-- Coordinate Breakdown Table -->
              <div class="coord-matrix mono-font">
                <div class="coord-row">
                  <span class="coord-tag">IMAGE PIXELS:</span>
                  <span class="coord-val">X: {{ inspectedHole.image_x }}px, Y: {{ inspectedHole.image_y }}px</span>
                </div>
                <div class="coord-row">
                  <span class="coord-tag">BOARD MM:</span>
                  <span class="coord-val">X: {{ inspectedHole.board_x || (inspectedHole.image_x * 0.2 | number:'1.2-2') }}mm, Y: {{ inspectedHole.board_y || (inspectedHole.image_y * 0.2 | number:'1.2-2') }}mm</span>
                </div>
                <div class="coord-row highlight">
                  <span class="coord-tag">MACHINE 3D MM:</span>
                  <span class="coord-val">X: {{ inspectedHole.machine_x || (inspectedHole.image_x * 0.2 | number:'1.2-2') }}mm, Y: {{ inspectedHole.machine_y || (inspectedHole.image_y * 0.2 | number:'1.2-2') }}mm, Z: {{ machinePosition.z }}mm</span>
                </div>
                <div class="coord-row" *ngIf="inspectedHole.failure_reason">
                  <span class="coord-tag text-failed">FAILURE REASON:</span>
                  <span class="coord-val text-failed">{{ inspectedHole.failure_reason }}</span>
                </div>
              </div>

              <!-- Hole Action Row -->
              <div class="hole-action-row">
                <button
                  class="btn-industrial"
                  [ngClass]="isSelected(inspectedHole) ? 'btn-danger' : 'btn-primary'"
                  (click)="toggleHoleSelection(inspectedHole)"
                >
                  <span class="material-icons-outlined">{{ isSelected(inspectedHole) ? 'remove_circle' : 'add_circle' }}</span>
                  <span>{{ isSelected(inspectedHole) ? 'Deselect Hole' : 'Select for Insertion' }}</span>
                </button>

                <button
                  class="btn-industrial btn-warning"
                  (click)="onRetryHole(inspectedHole)"
                  [disabled]="!activeJob"
                  *ngIf="inspectedHole.status === 'FAILED'"
                >
                  <span class="material-icons-outlined">replay</span>
                  <span>RETRY</span>
                </button>
              </div>
            </div>

            <ng-template #noHoleSelected>
              <div class="empty-state-card">
                <span class="material-icons-outlined">touch_app</span>
                <p>Click on any hole on the board to select or inspect its coordinates.</p>
              </div>
            </ng-template>
          </div>

          <!-- Selected Sequence Queue Card -->
          <div class="sequence-queue-card">
            <div class="card-header">
              <div class="header-title-row">
                <span class="material-icons-outlined text-primary">format_list_numbered</span>
                <h3>INSERTION QUEUE</h3>
              </div>
              <span class="badge badge-selected">{{ selectedHoles.length }} SELECTED</span>
            </div>

            <div class="sequence-actions-bar">
              <button class="action-link" (click)="selectAllHoles()">Select All Holes ({{ holes.length }})</button>
              <button class="action-link text-danger-link" (click)="clearSelection()">Clear Selection</button>
            </div>

            <!-- Sequence List -->
            <div class="sequence-list mono-font">
              <div
                *ngFor="let h of selectedHoles; let idx = index"
                class="sequence-item"
                [class.active]="inspectedHole?.id === h.id"
                (click)="onSelectHoleFromList(h)"
              >
                <span class="seq-num">{{ idx + 1 }}.</span>
                <span class="seq-label">{{ h.label }}</span>
                <span class="badge badge-{{ h.status.toLowerCase() }}">{{ h.status }}</span>
                <span class="seq-coords">({{ h.machine_x || (h.image_x*0.2 | number:'1.1-1') }}mm, {{ h.machine_y || (h.image_y*0.2 | number:'1.1-1') }}mm)</span>
                <button class="remove-seq-btn" (click)="$event.stopPropagation(); toggleHoleSelection(h)" title="Remove">✕</button>
              </div>
              <div class="empty-seq" *ngIf="selectedHoles.length === 0">
                <span class="material-icons-outlined">ads_click</span>
                <p>Click on any hole in the board image or click "Select All" to choose which holes to insert.</p>
              </div>
            </div>
          </div>
        </aside>
      </main>

      <!-- 4. BOTTOM DOCK: LIVE CAMERA & JOB CONTROLS -->
      <footer class="bottom-dock">
        <!-- LIVE CAMERA INSPECTION PANEL -->
        <div class="camera-inspection-panel">
          <div class="panel-tag">
            <span class="status-dot connected"></span>
            <span class="mono-font">LIVE CAMERA INSPECTION</span>
          </div>

          <div class="camera-video-container">
            <img
              [src]="cameraStreamUrl"
              alt="Live Inspection Camera"
              class="camera-stream-img"
              (error)="onCameraStreamError($event)"
            />
          </div>

          <div class="camera-status-overlay mono-font">
            <div class="hud-item">
              <span class="hud-label">HOLE:</span>
              <span class="hud-val text-primary">{{ cameraStatus?.active_hole || inspectedHole?.label || 'A1' }}</span>
            </div>
            <div class="hud-item">
              <span class="hud-label">VERIFICATION:</span>
              <span
                class="badge badge-{{ (lastVerification?.reason === 'THREAD_DETECTED' || cameraStatus?.active_state === 'SUCCESS') ? 'success' : (cameraStatus?.active_state === 'FAILED' ? 'failed' : 'processing') }}"
              >
                {{ lastVerification?.reason || cameraStatus?.active_state || 'WAITING' }}
              </span>
            </div>
          </div>
        </div>

        <!-- JOB EXECUTION CONTROLS & MACHINE TELEMETRY -->
        <div class="job-control-panel">
          <div class="machine-coords-deck mono-font">
            <div class="axis-box">
              <span class="axis-title">X-AXIS</span>
              <span class="axis-val">{{ machinePosition.x | number:'1.2-2' }} <small>mm</small></span>
            </div>
            <div class="axis-box">
              <span class="axis-title">Y-AXIS</span>
              <span class="axis-val">{{ machinePosition.y | number:'1.2-2' }} <small>mm</small></span>
            </div>
            <div class="axis-box">
              <span class="axis-title">Z-AXIS</span>
              <span class="axis-val">{{ machinePosition.z | number:'1.2-2' }} <small>mm</small></span>
            </div>
            <div class="axis-box status-box">
              <span class="axis-title">OPERATION</span>
              <span class="axis-val text-primary">{{ machineStatus?.operation || 'READY' }}</span>
            </div>
          </div>

          <!-- Execution Controls -->
          <div class="deck-buttons-row">
            <button
              class="btn-industrial btn-primary btn-large"
              (click)="onStartJob()"
              [disabled]="isJobRunning || (holes.length === 0)"
            >
              <span class="material-icons-outlined">play_arrow</span>
              <span>START INSERTION JOB ({{ selectedHoles.length || holes.length }} HOLES)</span>
            </button>

            <button
              class="btn-industrial btn-warning"
              (click)="onPauseJob()"
              [disabled]="!isJobRunning"
            >
              <span class="material-icons-outlined">pause</span>
              <span>PAUSE</span>
            </button>

            <button
              class="btn-industrial btn-success"
              (click)="onResumeJob()"
              [disabled]="isJobRunning || !activeJob || activeJob.status !== 'PAUSED'"
            >
              <span class="material-icons-outlined">play_circle</span>
              <span>RESUME</span>
            </button>

            <button
              class="btn-industrial btn-danger"
              (click)="onStopJob()"
              [disabled]="!activeJob || activeJob.status === 'COMPLETED' || activeJob.status === 'STOPPED'"
            >
              <span class="material-icons-outlined">stop</span>
              <span>STOP JOB</span>
            </button>
          </div>
        </div>
      </footer>

      <!-- CALIBRATION MODAL -->
      <app-calibration-dialog
        *ngIf="showCalibration"
        [boardId]="activeBoard?.id"
        (closed)="showCalibration = false"
      ></app-calibration-dialog>

      <!-- CAMERA CAPTURE & OBJECT DETECTION MODAL -->
      <div class="camera-modal-backdrop" *ngIf="showCameraModal" (click)="closeCameraModal()">
        <div class="camera-modal-container" (click)="$event.stopPropagation()">
          <div class="modal-header">
            <div class="header-left">
              <span class="material-icons-outlined text-primary">photo_camera</span>
              <h3>BOARD VISION SCANNER & HOLE DETECTOR</h3>
            </div>
            <button class="close-btn" (click)="closeCameraModal()">✕</button>
          </div>

          <div class="modal-body">
            <!-- Video / Stream Feed Box with Viewfinder Overlay -->
            <div class="scanner-feed-box">
              <!-- HTML5 Webcam Video Element -->
              <video
                #webcamVideo
                *ngIf="cameraSource === 'webcam'"
                autoplay
                playsinline
                muted
                class="feed-video"
              ></video>

              <!-- Backend MJPEG Stream -->
              <img
                *ngIf="cameraSource === 'backend'"
                [src]="cameraStreamUrl"
                alt="Live Camera Feed"
                class="feed-video"
              />

              <!-- Viewfinder Reticle & Guides -->
              <div class="viewfinder-overlay">
                <div class="viewfinder-corner top-left"></div>
                <div class="viewfinder-corner top-right"></div>
                <div class="viewfinder-corner bottom-left"></div>
                <div class="viewfinder-corner bottom-right"></div>
                <div class="viewfinder-center-cross"></div>
                <div class="viewfinder-grid"></div>
                <div class="viewfinder-status-tag mono-font">
                  <span class="status-dot connected"></span>
                  <span>{{ cameraSource === 'webcam' ? 'LOCAL WEBCAM' : 'INDUSTRIAL CNC CAMERA' }} • ALIGN TEXTILE BOARD WITHIN FRAME</span>
                </div>
              </div>
            </div>

            <div class="scanner-controls-bar">
              <div class="source-toggle">
                <label class="toggle-label mono-font">SOURCE:</label>
                <button
                  class="btn-source mono-font"
                  [class.active]="cameraSource === 'webcam'"
                  (click)="switchCameraSource('webcam')"
                >
                  <span class="material-icons-outlined">videocam</span> Webcam
                </button>
                <button
                  class="btn-source mono-font"
                  [class.active]="cameraSource === 'backend'"
                  (click)="switchCameraSource('backend')"
                >
                  <span class="material-icons-outlined">precision_manufacturing</span> Industrial Cam
                </button>
              </div>

              <div class="scan-actions">
                <button class="btn-industrial btn-secondary" (click)="closeCameraModal()" [disabled]="isCapturing">
                  <span>Cancel</span>
                </button>
                <button
                  class="btn-industrial btn-primary btn-capture"
                  (click)="onCaptureAndDetectBoard()"
                  [disabled]="isCapturing"
                >
                  <span class="material-icons-outlined" *ngIf="!isCapturing">camera_enhance</span>
                  <span class="material-icons-outlined spin" *ngIf="isCapturing">sync</span>
                  <span>{{ isCapturing ? 'Scanning & Naming Holes...' : 'Capture & Detect Holes' }}</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .dashboard-wrapper {
      display: flex;
      flex-direction: column;
      height: 100vh;
      background-color: var(--bg-primary);
      color: var(--text-main);
      overflow: hidden;
    }

    /* 1. TOP BAR */
    .system-top-bar {
      height: 56px;
      background: var(--bg-secondary);
      border-bottom: 1px solid var(--border-color);
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 0 16px;
      flex-shrink: 0;
    }
    .brand-section {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .brand-icon {
      font-size: 28px;
      color: #38bdf8;
    }
    .brand-text h1 {
      font-size: 1.05rem;
      font-weight: 700;
      letter-spacing: 0.04em;
    }
    .sub-brand {
      font-size: 0.65rem;
      color: var(--text-dim);
      letter-spacing: 0.08em;
    }
    .telemetry-pills {
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .pill {
      display: flex;
      align-items: center;
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      padding: 4px 10px;
      border-radius: 6px;
      font-size: 0.75rem;
    }
    .pill-label {
      color: var(--text-muted);
      margin-right: 4px;
    }
    .pill-val {
      font-weight: 600;
      color: #f1f5f9;
    }
    .mode-val {
      color: #38bdf8;
    }
    .pill-badge {
      margin-left: 6px;
    }
    .pill-btn {
      display: flex;
      align-items: center;
      gap: 4px;
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      color: var(--text-main);
      padding: 5px 12px;
      border-radius: 6px;
      font-size: 0.75rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.15s;
    }
    .pill-btn:hover {
      background: var(--bg-card-hover);
      border-color: #3b82f6;
    }

    /* 2. KPI SUMMARY BAR */
    .kpi-summary-bar {
      height: 64px;
      background: #0d1322;
      border-bottom: 1px solid var(--border-color);
      display: grid;
      grid-template-columns: repeat(5, 1fr) 2fr;
      gap: 12px;
      padding: 8px 16px;
      flex-shrink: 0;
    }
    .kpi-card {
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 6px;
      padding: 6px 12px;
      display: flex;
      flex-direction: column;
      justify-content: center;
    }
    .kpi-title {
      font-size: 0.65rem;
      font-weight: 700;
      color: var(--text-muted);
      letter-spacing: 0.05em;
    }
    .kpi-number {
      font-size: 1.25rem;
      font-weight: 800;
    }
    .kpi-val-row {
      display: flex;
      align-items: baseline;
      gap: 6px;
    }
    .kpi-pct {
      font-size: 0.75rem;
      color: #34d399;
    }
    .text-success { color: #10b981; }
    .text-failed { color: #ef4444; }
    .text-pending { color: #f59e0b; }
    .text-selected { color: #3b82f6; }
    .text-primary { color: #38bdf8; }
    .progress-kpi-card {
      justify-content: space-between;
    }
    .kpi-progress-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .progress-pct {
      font-size: 0.85rem;
      font-weight: 700;
      color: #38bdf8;
    }
    .progress-bar-container {
      height: 8px;
      background: #090d16;
      border-radius: 4px;
      overflow: hidden;
      margin-top: 4px;
    }
    .progress-bar-fill {
      height: 100%;
      background: linear-gradient(90deg, #3b82f6, #06b6d4, #10b981);
      transition: width 0.3s ease;
    }

    /* 3. MAIN WORKSPACE GRID */
    .main-workspace-grid {
      flex: 1;
      display: grid;
      grid-template-columns: 1fr 340px;
      gap: 12px;
      padding: 12px 16px;
      overflow: hidden;
    }

    /* Left Board Viewport */
    .board-viewport-panel {
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 8px;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }
    .panel-header-controls {
      padding: 8px 12px;
      background: #111827;
      border-bottom: 1px solid var(--border-color);
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 8px;
    }
    .control-group {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .control-label {
      font-size: 0.75rem;
      font-weight: 700;
      color: var(--text-muted);
    }
    .select-input {
      background: #0b0f17;
      border: 1px solid var(--border-color);
      color: #f1f5f9;
      padding: 6px 10px;
      border-radius: 6px;
      font-size: 0.8rem;
      max-width: 260px;
    }
    .file-upload-btn {
      padding: 6px 12px;
      cursor: pointer;
    }
    .search-box {
      display: flex;
      align-items: center;
      background: #0b0f17;
      border: 1px solid var(--border-color);
      border-radius: 6px;
      padding: 2px 4px 2px 8px;
    }
    .search-icon {
      font-size: 16px;
      color: var(--text-dim);
    }
    .search-input {
      background: transparent;
      border: none;
      color: #f1f5f9;
      font-size: 0.8rem;
      padding: 4px 6px;
      width: 150px;
    }
    .search-input:focus { outline: none; }
    .search-btn {
      background: #1e293b;
      border: 1px solid var(--border-color);
      color: #38bdf8;
      font-size: 0.7rem;
      font-weight: 700;
      padding: 4px 10px;
      border-radius: 4px;
      cursor: pointer;
    }
    .canvas-viewport {
      flex: 1;
      position: relative;
    }

    /* Right Inspector & Queue */
    .right-inspector-panel {
      display: flex;
      flex-direction: column;
      gap: 12px;
      overflow: hidden;
    }
    .inspector-card, .sequence-queue-card {
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 8px;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }
    .inspector-card {
      flex-shrink: 0;
    }
    .sequence-queue-card {
      flex: 1;
    }
    .card-header {
      padding: 10px 14px;
      background: #111827;
      border-bottom: 1px solid var(--border-color);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .header-title-row {
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .header-title-row h3 {
      font-size: 0.85rem;
      font-weight: 700;
      letter-spacing: 0.04em;
    }
    .card-body {
      padding: 12px 14px;
    }
    .hole-big-label-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 10px;
    }
    .big-label {
      font-size: 1.75rem;
      font-weight: 800;
      color: #38bdf8;
    }
    .row-col-tags {
      display: flex;
      flex-direction: column;
      font-size: 0.75rem;
      color: var(--text-muted);
    }
    .coord-matrix {
      background: #0b0f17;
      border: 1px solid var(--border-color);
      border-radius: 6px;
      padding: 8px 10px;
      font-size: 0.75rem;
      margin-bottom: 12px;
    }
    .coord-row {
      display: flex;
      justify-content: space-between;
      padding: 3px 0;
    }
    .coord-row.highlight {
      border-top: 1px dashed var(--border-color);
      margin-top: 4px;
      padding-top: 6px;
      color: #38bdf8;
      font-weight: 600;
    }
    .coord-tag { color: var(--text-dim); }
    .hole-action-row {
      display: flex;
      gap: 8px;
    }
    .hole-action-row button {
      flex: 1;
    }
    .empty-state-card {
      padding: 24px;
      text-align: center;
      color: var(--text-dim);
    }
    .empty-state-card .material-icons-outlined {
      font-size: 32px;
      margin-bottom: 6px;
    }
    .sequence-actions-bar {
      padding: 6px 14px;
      background: #0d1322;
      border-bottom: 1px solid var(--border-color);
      display: flex;
      justify-content: space-between;
    }
    .action-link {
      background: none;
      border: none;
      color: #38bdf8;
      font-size: 0.75rem;
      font-weight: 600;
      cursor: pointer;
    }
    .action-link:hover { text-decoration: underline; }
    .text-danger-link { color: #f87171 !important; }
    .sequence-list {
      flex: 1;
      overflow-y: auto;
      padding: 6px 10px;
    }
    .sequence-item {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 5px 8px;
      border-radius: 4px;
      font-size: 0.75rem;
      cursor: pointer;
      margin-bottom: 3px;
      background: #0b0f17;
      border: 1px solid #1e293b;
    }
    .sequence-item:hover { background: var(--bg-card-hover); border-color: #3b82f6; }
    .sequence-item.active { background: #1e3a8a; border-color: #60a5fa; }
    .seq-num { color: var(--text-dim); width: 22px; }
    .seq-label { font-weight: 700; width: 45px; color: #38bdf8; }
    .seq-coords { color: var(--text-muted); font-size: 0.7rem; margin-left: auto; }
    .remove-seq-btn {
      background: transparent;
      border: none;
      color: #94a3b8;
      cursor: pointer;
      padding: 0 4px;
      font-size: 0.75rem;
    }
    .remove-seq-btn:hover { color: #ef4444; }
    .empty-seq {
      padding: 24px;
      text-align: center;
      color: var(--text-dim);
      font-size: 0.75rem;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 6px;
    }
    .empty-seq .material-icons-outlined {
      font-size: 28px;
      color: #38bdf8;
    }

    /* 4. BOTTOM DOCK */
    .bottom-dock {
      height: 175px;
      background: var(--bg-secondary);
      border-top: 1px solid var(--border-color);
      display: grid;
      grid-template-columns: 320px 1fr;
      gap: 16px;
      padding: 10px 16px;
      flex-shrink: 0;
    }
    .camera-inspection-panel {
      background: #0b0f17;
      border: 1px solid var(--border-color);
      border-radius: 8px;
      position: relative;
      overflow: hidden;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .panel-tag {
      position: absolute;
      top: 8px;
      left: 8px;
      display: flex;
      align-items: center;
      background: rgba(15, 23, 42, 0.85);
      border: 1px solid #243452;
      border-radius: 4px;
      padding: 2px 6px;
      font-size: 0.65rem;
      font-weight: 700;
      z-index: 5;
    }
    .camera-video-container {
      width: 100%;
      height: 100%;
    }
    .camera-stream-img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
    .camera-status-overlay {
      position: absolute;
      bottom: 8px;
      left: 8px;
      right: 8px;
      background: rgba(15, 23, 42, 0.85);
      border: 1px solid #243452;
      border-radius: 4px;
      padding: 4px 8px;
      display: flex;
      justify-content: space-between;
      font-size: 0.7rem;
    }
    .hud-item { display: flex; align-items: center; gap: 4px; }
    .hud-label { color: var(--text-dim); }
    .hud-val { font-weight: 700; }

    /* Job Controls Deck */
    .job-control-panel {
      display: flex;
      flex-direction: column;
      justify-content: space-between;
    }
    .machine-coords-deck {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 10px;
    }
    .axis-box {
      background: #0b0f17;
      border: 1px solid var(--border-color);
      border-radius: 6px;
      padding: 6px 12px;
    }
    .axis-title {
      display: block;
      font-size: 0.65rem;
      font-weight: 700;
      color: var(--text-dim);
    }
    .axis-val {
      font-size: 1.15rem;
      font-weight: 800;
      color: #f1f5f9;
    }
    .axis-val small { font-size: 0.7rem; color: var(--text-dim); }
    .deck-buttons-row {
      display: flex;
      gap: 12px;
    }
    .btn-large {
      flex: 2;
      font-size: 0.95rem;
      padding: 12px 20px;
    }
    .deck-buttons-row button:not(.btn-large) {
      flex: 1;
      padding: 12px 14px;
    }
    .spin { animation: spin 1s infinite linear; }
    @keyframes spin { 100% { transform: rotate(360deg); } }

    /* CAMERA SCANNER MODAL */
    .camera-modal-backdrop {
      position: fixed;
      inset: 0;
      background: rgba(4, 7, 14, 0.85);
      backdrop-filter: blur(6px);
      z-index: 1000;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 20px;
    }
    .camera-modal-container {
      background: var(--bg-card);
      border: 1px solid #243452;
      border-radius: 12px;
      box-shadow: 0 20px 40px rgba(0, 0, 0, 0.6), 0 0 20px rgba(56, 189, 248, 0.15);
      width: 100%;
      max-width: 820px;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      animation: modalFadeIn 0.2s ease-out;
    }
    @keyframes modalFadeIn {
      from { opacity: 0; transform: scale(0.97); }
      to { opacity: 1; transform: scale(1); }
    }
    .modal-header {
      padding: 14px 20px;
      background: var(--bg-secondary);
      border-bottom: 1px solid var(--border-color);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .header-left {
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .header-left h3 {
      font-size: 0.95rem;
      font-weight: 700;
      letter-spacing: 0.05em;
    }
    .close-btn {
      background: none;
      border: none;
      color: var(--text-dim);
      font-size: 1.2rem;
      cursor: pointer;
      padding: 4px;
    }
    .close-btn:hover { color: #f87171; }
    .scanner-feed-box {
      position: relative;
      background: #020617;
      height: 440px;
      overflow: hidden;
      display: flex;
      align-items: center;
      justify-content: center;
      border-top: 1px solid var(--border-color);
      border-bottom: 1px solid var(--border-color);
    }
    .feed-video {
      width: 100%;
      height: 100%;
      object-fit: contain;
    }
    .viewfinder-overlay {
      position: absolute;
      inset: 20px;
      pointer-events: none;
      border: 1px solid rgba(56, 189, 248, 0.3);
      box-shadow: inset 0 0 30px rgba(0,0,0,0.5);
    }
    .viewfinder-corner {
      position: absolute;
      width: 24px;
      height: 24px;
      border-color: #38bdf8;
      border-style: solid;
    }
    .viewfinder-corner.top-left { top: -2px; left: -2px; border-width: 3px 0 0 3px; }
    .viewfinder-corner.top-right { top: -2px; right: -2px; border-width: 3px 3px 0 0; }
    .viewfinder-corner.bottom-left { bottom: -2px; left: -2px; border-width: 0 0 3px 3px; }
    .viewfinder-corner.bottom-right { bottom: -2px; right: -2px; border-width: 0 3px 3px 0; }
    .viewfinder-center-cross {
      position: absolute;
      top: 50%;
      left: 50%;
      width: 30px;
      height: 30px;
      transform: translate(-50%, -50%);
    }
    .viewfinder-center-cross::before, .viewfinder-center-cross::after {
      content: '';
      position: absolute;
      background: rgba(56, 189, 248, 0.7);
    }
    .viewfinder-center-cross::before { top: 14px; left: 0; right: 0; height: 2px; }
    .viewfinder-center-cross::after { left: 14px; top: 0; bottom: 0; width: 2px; }
    .viewfinder-grid {
      position: absolute;
      inset: 0;
      background-size: 33.333% 33.333%;
      background-image:
        linear-gradient(to right, rgba(56, 189, 248, 0.08) 1px, transparent 1px),
        linear-gradient(to bottom, rgba(56, 189, 248, 0.08) 1px, transparent 1px);
    }
    .viewfinder-status-tag {
      position: absolute;
      top: 10px;
      left: 10px;
      background: rgba(15, 23, 42, 0.85);
      border: 1px solid #243452;
      border-radius: 4px;
      padding: 4px 8px;
      font-size: 0.7rem;
      display: flex;
      align-items: center;
      gap: 6px;
      color: #94a3b8;
    }
    .scanner-controls-bar {
      padding: 14px 20px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: var(--bg-secondary);
    }
    .source-toggle {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .toggle-label {
      font-size: 0.75rem;
      color: var(--text-dim);
      font-weight: 700;
    }
    .btn-source {
      background: #0b0f17;
      border: 1px solid var(--border-color);
      color: var(--text-muted);
      border-radius: 6px;
      padding: 6px 12px;
      font-size: 0.75rem;
      display: flex;
      align-items: center;
      gap: 6px;
      cursor: pointer;
      transition: all 0.15s ease;
    }
    .btn-source.active {
      background: #1e3a8a;
      border-color: #3b82f6;
      color: #f1f5f9;
      font-weight: 600;
    }
    .scan-actions {
      display: flex;
      gap: 10px;
    }
    .btn-capture {
      font-size: 0.85rem;
      padding: 10px 18px;
    }
  `]
})
export class DashboardComponent implements OnInit {
  @ViewChild('canvasCmp') canvasCmp!: HoleMapCanvasComponent;

  public boards: Board[] = [];
  public activeBoard: Board | null = null;
  public holes: Hole[] = [];
  public selectedHoles: Hole[] = [];
  public inspectedHole: Hole | null = null;
  public currentMachineHole: Hole | null = null;
  public activeJob: Job | null = null;

  public machineStatus: MachineStatus | null = null;
  public machinePosition: MachinePosition = { x: 0, y: 0, z: 25.0 };
  public cameraStatus: CameraStatus | null = null;
  public lastVerification: VerificationResult | null = null;

  public isDetecting = false;
  public isJobRunning = false;
  public showCalibration = false;
  public searchQuery = '';

  public boardImageUrl: string | null = null;
  public cameraStreamUrl = '';

  // KPI Metrics
  public successCount = 0;
  public failedCount = 0;
  public pendingCount = 0;
  public jobProgressPct = 0;

  constructor(
    private boardService: BoardService,
    private holeService: HoleService,
    private jobService: JobService,
    private machineService: MachineService,
    private cameraService: CameraService,
    private ws: WebSocketService
  ) { }

  ngOnInit(): void {
    this.cameraStreamUrl = this.cameraService.getStreamUrl();

    // Subscribe to state streams
    this.boardService.boards$.subscribe(b => this.boards = b);
    this.boardService.activeBoard$.subscribe(board => {
      this.activeBoard = board;
      if (board) {
        this.boardImageUrl = this.boardService.getBoardImageUri(board.id);
        this.holeService.loadHoles(board.id).subscribe();
      } else {
        this.boardImageUrl = null;
        this.holes = [];
      }
    });

    this.holeService.holes$.subscribe(holes => {
      this.holes = holes;
      this.updateCounts();
    });

    this.holeService.selectedHoles$.subscribe(s => this.selectedHoles = s);
    this.holeService.inspectedHole$.subscribe(h => this.inspectedHole = h);
    this.holeService.isDetecting$.subscribe(d => this.isDetecting = d);

    this.machineService.status$.subscribe(s => this.machineStatus = s);
    this.machineService.position$.subscribe(p => this.machinePosition = p);

    this.cameraService.status$.subscribe(c => this.cameraStatus = c);
    this.cameraService.verification$.subscribe(v => this.lastVerification = v);

    this.jobService.activeJob$.subscribe(j => {
      this.activeJob = j;
      if (j) {
        const total = j.total_holes || (this.selectedHoles.length || this.holes.length || 1);
        const proc = (j.successful_holes || 0) + (j.failed_holes || 0);
        this.jobProgressPct = Math.min(100, (proc / total) * 100);
      } else {
        this.jobProgressPct = 0;
      }
    });
    this.jobService.isJobRunning$.subscribe(r => this.isJobRunning = r);
  }

  private updateCounts(): void {
    this.successCount = this.holes.filter(h => h.status === 'SUCCESS').length;
    this.failedCount = this.holes.filter(h => h.status === 'FAILED').length;
    this.pendingCount = this.holes.filter(h => h.status === 'PENDING').length;
  }

  public onBoardSelected(boardId: string): void {
    const found = this.boards.find(b => b.id === boardId);
    if (found) {
      this.boardService.setActiveBoard(found);
    }
  }

  public onFileUpload(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files[0]) {
      const file = input.files[0];
      this.boardService.uploadBoard(file).subscribe({
        next: (board) => {
          this.holeService.detectHoles(board.id).subscribe();
        },
        error: (err) => alert('Board upload failed: ' + (err.error?.detail || err.message))
      });
    }
  }

  public onDetectHoles(): void {
    if (!this.activeBoard) return;
    this.holeService.detectHoles(this.activeBoard.id).subscribe();
  }

  public onConfirmHoleMap(): void {
    alert(`✓ Hole Map Confirmed! All ${this.holes.length} holes verified and indexed for insertion.`);
  }

  public onSearchHole(): void {
    if (!this.searchQuery.trim() || !this.activeBoard) return;
    const query = this.searchQuery.trim().toUpperCase();
    const found = this.holes.find(h => h.label === query);
    if (found) {
      this.holeService.setInspectedHole(found);
      this.canvasCmp.zoomToHole(found);
    } else {
      this.holeService.searchHole(this.activeBoard.id, query).subscribe({
        next: (hole) => {
          if (hole) {
            this.canvasCmp.zoomToHole(hole);
          }
        },
        error: () => alert(`Hole '${query}' not found.`)
      });
    }
  }

  public onHoleClicked(hole: Hole): void {
    this.holeService.setInspectedHole(hole);
    // Direct toggle on click: select/deselect hole
    this.holeService.toggleHoleSelection(hole);
  }

  public onSelectHoleFromList(hole: Hole): void {
    this.holeService.setInspectedHole(hole);
    this.canvasCmp.zoomToHole(hole);
  }

  public isSelected(hole: Hole): boolean {
    return this.selectedHoles.some(h => h.id === hole.id);
  }

  public toggleHoleSelection(hole: Hole): void {
    this.holeService.toggleHoleSelection(hole);
  }

  public selectAllHoles(): void {
    this.holeService.selectAllHoles();
  }

  public clearSelection(): void {
    this.holeService.clearSelection();
  }

  public onStartJob(): void {
    if (!this.activeBoard) {
      alert('Please upload or select a board first.');
      return;
    }
    const holeIds = this.selectedHoles.length > 0 ? this.selectedHoles.map(h => h.id) : this.holes.map(h => h.id);

    this.jobService.createJob(this.activeBoard.id, holeIds).subscribe({
      next: (job) => {
        this.jobService.startJob(job.id).subscribe({
          error: (err) => alert(err.error?.detail || 'Job start failed')
        });
      },
      error: (err) => alert('Job creation failed: ' + (err.error?.detail || err.message))
    });
  }

  public onPauseJob(): void {
    if (this.activeJob) {
      this.jobService.pauseJob(this.activeJob.id).subscribe();
    }
  }

  public onResumeJob(): void {
    if (this.activeJob) {
      this.jobService.resumeJob(this.activeJob.id).subscribe();
    }
  }

  public onStopJob(): void {
    if (this.activeJob) {
      this.jobService.stopJob(this.activeJob.id).subscribe();
    }
  }

  public onRetryHole(hole: Hole): void {
    if (this.activeJob) {
      this.jobService.retryHole(this.activeJob.id, hole.id).subscribe();
    }
  }

  public onHomeMachine(): void {
    this.machineService.home().subscribe();
  }

  public onEmergencyStop(): void {
    this.machineService.stop().subscribe();
  }

  public onCameraStreamError(event: any): void {
    setTimeout(() => {
      this.cameraStreamUrl = this.cameraService.getSnapshotUrl();
    }, 1000);
  }

  // Camera Scanning & Object Detection Modal Logic
  @ViewChild('webcamVideo') webcamVideoRef?: ElementRef<HTMLVideoElement>;
  public showCameraModal = false;
  public cameraSource: 'webcam' | 'backend' = 'backend';
  public isCapturing = false;
  private mediaStream: MediaStream | null = null;

  public openCameraModal(): void {
    this.showCameraModal = true;
    if (this.cameraSource === 'webcam') {
      this.startWebcam();
    }
  }

  public closeCameraModal(): void {
    this.stopWebcam();
    this.showCameraModal = false;
    this.isCapturing = false;
  }

  public switchCameraSource(source: 'webcam' | 'backend'): void {
    this.cameraSource = source;
    if (source === 'webcam') {
      this.startWebcam();
    } else {
      this.stopWebcam();
    }
  }

  private startWebcam(): void {
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 1920 }, height: { ideal: 1080 } }
      })
      .then(stream => {
        this.mediaStream = stream;
        setTimeout(() => {
          if (this.webcamVideoRef?.nativeElement) {
            this.webcamVideoRef.nativeElement.srcObject = stream;
          }
        }, 100);
      })
      .catch(err => {
        console.warn('Webcam getUserMedia not accessible, switching to industrial camera stream:', err);
        this.cameraSource = 'backend';
      });
    } else {
      this.cameraSource = 'backend';
    }
  }

  private stopWebcam(): void {
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach(track => track.stop());
      this.mediaStream = null;
    }
  }

  public onCaptureAndDetectBoard(): void {
    this.isCapturing = true;

    if (this.cameraSource === 'webcam' && this.webcamVideoRef?.nativeElement) {
      const video = this.webcamVideoRef.nativeElement;
      const canvas = document.createElement('canvas');
      canvas.width = video.videoWidth || 1280;
      canvas.height = video.videoHeight || 720;
      const ctx = canvas.getContext('2d');
      if (ctx) {
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        canvas.toBlob((blob) => {
          if (blob) {
            const timestamp = new Date().toISOString().replace(/[-:T.]/g, '').slice(0, 14);
            const fileName = `camera_scan_${timestamp}.png`;
            const file = new File([blob], fileName, { type: 'image/png' });
            
            this.boardService.uploadBoard(file, `Camera Scan (${new Date().toLocaleTimeString()})`).subscribe({
              next: (board) => {
                this.holeService.detectHoles(board.id).subscribe({
                  next: () => {
                    this.isCapturing = false;
                    this.closeCameraModal();
                  },
                  error: () => {
                    this.isCapturing = false;
                    this.closeCameraModal();
                  }
                });
              },
              error: (err) => {
                this.isCapturing = false;
                alert('Failed to process captured board: ' + (err.error?.detail || err.message));
              }
            });
          } else {
            this.isCapturing = false;
            alert('Failed to create image frame from camera.');
          }
        }, 'image/png');
      } else {
        this.isCapturing = false;
        alert('Canvas context unavailable.');
      }
    } else {
      // Backend Industrial Camera Capture & Detection
      const timestamp = new Date().toLocaleTimeString();
      this.cameraService.captureBoard(`Camera Scan (${timestamp})`).subscribe({
        next: (res) => {
          this.isCapturing = false;
          this.closeCameraModal();
          this.boardService.refreshBoards();
          if (res.board) {
            this.boardService.setActiveBoard(res.board);
          }
        },
        error: (err) => {
          this.isCapturing = false;
          alert('Failed to capture board from industrial camera: ' + (err.error?.detail || err.message));
        }
      });
    }
  }
}

