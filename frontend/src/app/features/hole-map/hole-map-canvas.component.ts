import {
  Component,
  ElementRef,
  EventEmitter,
  Input,
  OnChanges,
  OnDestroy,
  OnInit,
  Output,
  SimpleChanges,
  ViewChild
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { Hole } from '../../core/models/hole.model';
import { MachinePosition } from '../../core/models/machine.model';

@Component({
  selector: 'app-hole-map-canvas',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="canvas-container" #container (window:resize)="onResize()">
      <!-- Canvas Element -->
      <canvas
        #canvas
        (mousedown)="onMouseDown($event)"
        (mousemove)="onMouseMove($event)"
        (mouseup)="onMouseUp($event)"
        (mouseleave)="onMouseLeave()"
        (wheel)="onWheel($event)"
        (click)="onClick($event)"
      ></canvas>

      <!-- Floating Controls Overlay -->
      <div class="canvas-floating-controls">
        <button class="ctrl-btn" (click)="zoomIn()" title="Zoom In">
          <span class="material-icons-outlined">add</span>
        </button>
        <button class="ctrl-btn" (click)="zoomOut()" title="Zoom Out">
          <span class="material-icons-outlined">remove</span>
        </button>
        <button class="ctrl-btn" (click)="resetView()" title="Fit View">
          <span class="material-icons-outlined">fit_screen</span>
        </button>
        <span class="zoom-badge mono-font">{{ (scale * 100).toFixed(0) }}%</span>
      </div>

      <!-- Hover Tooltip -->
      <div
        *ngIf="hoveredHole"
        class="hole-tooltip mono-font"
        [style.left.px]="tooltipX"
        [style.top.px]="tooltipY"
      >
        <div class="tooltip-header">
          <span class="tooltip-label">{{ hoveredHole.label }}</span>
          <span class="badge badge-{{ hoveredHole.status.toLowerCase() }}">
            {{ hoveredHole.status }}
          </span>
        </div>
        <div class="tooltip-row">
          <span>Row: {{ hoveredHole.row_number }}</span>
          <span>Col: {{ hoveredHole.column_number }}</span>
        </div>
        <div class="tooltip-row">
          <span>Image: ({{ hoveredHole.image_x }}, {{ hoveredHole.image_y }})</span>
        </div>
        <div class="tooltip-row" *ngIf="hoveredHole.machine_x !== undefined">
          <span>Machine: ({{ hoveredHole.machine_x }}mm, {{ hoveredHole.machine_y }}mm)</span>
        </div>
        <div class="tooltip-hint">Click to select/deselect hole</div>
      </div>
    </div>
  `,
  styles: [`
    :host {
      display: block;
      width: 100%;
      height: 100%;
      position: relative;
    }
    .canvas-container {
      width: 100%;
      height: 100%;
      position: relative;
      background-color: #070a10;
      overflow: hidden;
      cursor: crosshair;
      border-radius: 8px;
    }
    canvas {
      display: block;
      width: 100%;
      height: 100%;
    }
    .canvas-floating-controls {
      position: absolute;
      bottom: 16px;
      right: 16px;
      display: flex;
      align-items: center;
      gap: 6px;
      background: rgba(19, 27, 46, 0.9);
      backdrop-filter: blur(8px);
      border: 1px solid #243452;
      border-radius: 8px;
      padding: 4px 8px;
      z-index: 10;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
    }
    .ctrl-btn {
      background: #182238;
      border: 1px solid #243452;
      color: #94a3b8;
      width: 32px;
      height: 32px;
      border-radius: 6px;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      transition: all 0.15s;
    }
    .ctrl-btn:hover {
      background: #243452;
      color: #ffffff;
      border-color: #3b82f6;
    }
    .ctrl-btn .material-icons-outlined {
      font-size: 18px;
    }
    .zoom-badge {
      font-size: 0.75rem;
      color: #94a3b8;
      padding: 0 6px;
      min-width: 44px;
      text-align: center;
    }
    .hole-tooltip {
      position: absolute;
      pointer-events: none;
      background: rgba(15, 23, 42, 0.95);
      border: 1px solid #38bdf8;
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.6);
      border-radius: 6px;
      padding: 8px 12px;
      font-size: 0.75rem;
      z-index: 20;
      min-width: 180px;
      transform: translate(12px, 12px);
    }
    .tooltip-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 4px;
      padding-bottom: 4px;
      border-bottom: 1px solid #243452;
    }
    .tooltip-label {
      font-weight: 700;
      color: #38bdf8;
      font-size: 0.85rem;
    }
    .tooltip-row {
      display: flex;
      justify-content: space-between;
      color: #cbd5e1;
      margin-top: 2px;
    }
    .tooltip-hint {
      margin-top: 6px;
      font-size: 0.7rem;
      color: #38bdf8;
      text-align: center;
      font-style: italic;
    }
  `]
})
export class HoleMapCanvasComponent implements OnInit, OnChanges, OnDestroy {
  @ViewChild('canvas', { static: true }) canvasRef!: ElementRef<HTMLCanvasElement>;
  @ViewChild('container', { static: true }) containerRef!: ElementRef<HTMLDivElement>;

  @Input() holes: Hole[] = [];
  @Input() selectedHoles: Hole[] = [];
  @Input() inspectedHole: Hole | null = null;
  @Input() currentMachineHole: Hole | null = null;
  @Input() machinePosition: MachinePosition = { x: 0, y: 0, z: 25.0 };
  @Input() boardImageUrl: string | null = null;

  @Output() holeClicked = new EventEmitter<Hole>();

  private ctx!: CanvasRenderingContext2D;
  private boardImage: HTMLImageElement | null = null;
  private animationFrameId: number | null = null;

  // Viewport Transform (Pan & Zoom)
  public scale = 1.0;
  public panX = 0;
  public panY = 0;
  private isDragging = false;
  private startDragX = 0;
  private startDragY = 0;

  // Hover state
  public hoveredHole: Hole | null = null;
  public tooltipX = 0;
  public tooltipY = 0;

  // Animation pulse
  private pulsePhase = 0;

  ngOnInit(): void {
    this.ctx = this.canvasRef.nativeElement.getContext('2d')!;
    this.setupCanvasSize();
    this.startRenderLoop();
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['boardImageUrl'] && this.boardImageUrl) {
      this.loadBoardImage(this.boardImageUrl);
    }
    if (changes['holes'] && this.holes.length > 0 && !this.isDragging) {
      if (changes['holes'].isFirstChange() || changes['holes'].previousValue?.length === 0) {
        setTimeout(() => this.resetView(), 100);
      }
    }
  }

  ngOnDestroy(): void {
    if (this.animationFrameId) {
      cancelAnimationFrame(this.animationFrameId);
    }
  }

  private loadBoardImage(url: string): void {
    const img = new Image();
    img.crossOrigin = 'anonymous';
    img.onload = () => {
      this.boardImage = img;
      this.resetView();
    };
    img.src = url;
  }

  public onResize(): void {
    this.setupCanvasSize();
  }

  private setupCanvasSize(): void {
    const canvas = this.canvasRef.nativeElement;
    const container = this.containerRef.nativeElement;
    const dpr = window.devicePixelRatio || 1;

    const width = container.clientWidth || 800;
    const height = container.clientHeight || 600;

    canvas.width = width * dpr;
    canvas.height = height * dpr;
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;

    this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  public resetView(): void {
    const container = this.containerRef.nativeElement;
    const cw = container.clientWidth || 800;
    const ch = container.clientHeight || 600;

    if (this.boardImage && this.boardImage.width > 0) {
      const scaleX = (cw * 0.92) / this.boardImage.width;
      const scaleY = (ch * 0.92) / this.boardImage.height;
      this.scale = Math.min(scaleX, scaleY, 2.5);
      this.panX = (cw - this.boardImage.width * this.scale) / 2;
      this.panY = (ch - this.boardImage.height * this.scale) / 2;
    } else if (this.holes.length > 0) {
      const xs = this.holes.map(h => h.image_x);
      const ys = this.holes.map(h => h.image_y);
      const minX = Math.min(...xs);
      const maxX = Math.max(...xs);
      const minY = Math.min(...ys);
      const maxY = Math.max(...ys);
      const spanX = Math.max(maxX - minX, 100);
      const spanY = Math.max(maxY - minY, 100);

      const scaleX = (cw * 0.88) / spanX;
      const scaleY = (ch * 0.88) / spanY;
      this.scale = Math.min(scaleX, scaleY, 2.5);
      this.panX = (cw - (minX + maxX) * this.scale) / 2;
      this.panY = (ch - (minY + maxY) * this.scale) / 2;
    } else {
      this.scale = 1.0;
      this.panX = 0;
      this.panY = 0;
    }
  }

  public zoomIn(): void {
    this.zoomAroundPoint(this.containerRef.nativeElement.clientWidth / 2, this.containerRef.nativeElement.clientHeight / 2, 1.25);
  }

  public zoomOut(): void {
    this.zoomAroundPoint(this.containerRef.nativeElement.clientWidth / 2, this.containerRef.nativeElement.clientHeight / 2, 0.8);
  }

  public zoomToHole(hole: Hole): void {
    const container = this.containerRef.nativeElement;
    const cw = container.clientWidth || 800;
    const ch = container.clientHeight || 600;

    this.scale = 2.5;
    this.panX = cw / 2 - hole.image_x * this.scale;
    this.panY = ch / 2 - hole.image_y * this.scale;
  }

  private zoomAroundPoint(cursorX: number, cursorY: number, factor: number): void {
    const newScale = Math.min(Math.max(this.scale * factor, 0.15), 15.0);
    this.panX = cursorX - (cursorX - this.panX) * (newScale / this.scale);
    this.panY = cursorY - (cursorY - this.panY) * (newScale / this.scale);
    this.scale = newScale;
  }

  public onWheel(event: WheelEvent): void {
    event.preventDefault();
    const rect = this.canvasRef.nativeElement.getBoundingClientRect();
    const cursorX = event.clientX - rect.left;
    const cursorY = event.clientY - rect.top;
    const factor = event.deltaY < 0 ? 1.15 : 0.87;
    this.zoomAroundPoint(cursorX, cursorY, factor);
  }

  public onMouseDown(event: MouseEvent): void {
    this.isDragging = true;
    this.startDragX = event.clientX - this.panX;
    this.startDragY = event.clientY - this.panY;
  }

  public onMouseMove(event: MouseEvent): void {
    const rect = this.canvasRef.nativeElement.getBoundingClientRect();
    const cursorX = event.clientX - rect.left;
    const cursorY = event.clientY - rect.top;

    if (this.isDragging) {
      this.panX = event.clientX - this.startDragX;
      this.panY = event.clientY - this.startDragY;
      this.hoveredHole = null;
    } else {
      const imgX = (cursorX - this.panX) / this.scale;
      const imgY = (cursorY - this.panY) / this.scale;
      this.hoveredHole = this.findHoleAtImageCoords(imgX, imgY);
      if (this.hoveredHole) {
        this.tooltipX = Math.min(cursorX, rect.width - 200);
        this.tooltipY = Math.min(cursorY, rect.height - 140);
      }
    }
  }

  public onMouseUp(event: MouseEvent): void {
    this.isDragging = false;
  }

  public onMouseLeave(): void {
    this.isDragging = false;
    this.hoveredHole = null;
  }

  public onClick(event: MouseEvent): void {
    const rect = this.canvasRef.nativeElement.getBoundingClientRect();
    const cursorX = event.clientX - rect.left;
    const cursorY = event.clientY - rect.top;

    const imgX = (cursorX - this.panX) / this.scale;
    const imgY = (cursorY - this.panY) / this.scale;
    const hit = this.findHoleAtImageCoords(imgX, imgY);
    if (hit) {
      this.holeClicked.emit(hit);
    }
  }

  private findHoleAtImageCoords(x: number, y: number): Hole | null {
    const hitRadius = Math.max(14 / this.scale, 10);
    const hitRadiusSq = hitRadius * hitRadius;

    for (let i = 0; i < this.holes.length; i++) {
      const h = this.holes[i];
      const dx = h.image_x - x;
      const dy = h.image_y - y;
      if (dx * dx + dy * dy <= hitRadiusSq) {
        return h;
      }
    }
    return null;
  }

  private startRenderLoop(): void {
    const render = () => {
      this.pulsePhase += 0.06;
      this.draw();
      this.animationFrameId = requestAnimationFrame(render);
    };
    this.animationFrameId = requestAnimationFrame(render);
  }

  private draw(): void {
    const container = this.containerRef.nativeElement;
    const width = container.clientWidth || 800;
    const height = container.clientHeight || 600;

    this.ctx.save();
    this.ctx.clearRect(0, 0, width, height);

    // Background Canvas Grid
    this.drawBackgroundGrid(width, height);

    // Apply viewport transform (pan & zoom)
    this.ctx.translate(this.panX, this.panY);
    this.ctx.scale(this.scale, this.scale);

    // 1. Draw Board Image
    if (this.boardImage) {
      this.ctx.drawImage(this.boardImage, 0, 0);
    }

    // 2. Draw Detected Holes with Labels & Status
    this.drawHoles();

    // 3. Draw Machine Head Crosshair
    this.drawMachineCrosshair();

    this.ctx.restore();
  }

  private drawBackgroundGrid(width: number, height: number): void {
    this.ctx.fillStyle = '#090d16';
    this.ctx.fillRect(0, 0, width, height);

    this.ctx.strokeStyle = '#111827';
    this.ctx.lineWidth = 1;
    const gridSize = 40;
    const offsetX = this.panX % gridSize;
    const offsetY = this.panY % gridSize;

    this.ctx.beginPath();
    for (let x = offsetX; x < width; x += gridSize) {
      this.ctx.moveTo(x, 0);
      this.ctx.lineTo(x, height);
    }
    for (let y = offsetY; y < height; y += gridSize) {
      this.ctx.moveTo(0, y);
      this.ctx.lineTo(width, y);
    }
    this.ctx.stroke();
  }

  private drawHoles(): void {
    const count = this.holes.length;

    for (let i = 0; i < count; i++) {
      const hole = this.holes[i];
      const isSelected = hole.status === 'SELECTED' || this.selectedHoles.some(s => s.id === hole.id);
      const isInspected = this.inspectedHole?.id === hole.id;
      const isProcessing = hole.status === 'PROCESSING' || this.currentMachineHole?.id === hole.id;
      const isHovered = this.hoveredHole?.id === hole.id;

      const x = hole.image_x;
      const y = hole.image_y;
      const baseRadius = Math.max(hole.radius || 6, 5);

      // Color mapping
      let fillColor = '#f59e0b'; // PENDING (Amber)
      let strokeColor = '#d97706';

      if (isSelected) {
        fillColor = '#2563eb'; // SELECTED (Blue)
        strokeColor = '#60a5fa';
      }
      if (hole.status === 'PROCESSING' || isProcessing) {
        fillColor = '#06b6d4'; // PROCESSING (Cyan)
        strokeColor = '#22d3ee';
      } else if (hole.status === 'SUCCESS') {
        fillColor = '#10b981'; // SUCCESS (Green)
        strokeColor = '#34d399';
      } else if (hole.status === 'FAILED') {
        fillColor = '#ef4444'; // FAILED (Red)
        strokeColor = '#f87171';
      } else if (hole.status === 'SKIPPED') {
        fillColor = '#64748b'; // SKIPPED (Grey)
        strokeColor = '#94a3b8';
      }

      // 1. Processing Pulsing Aura
      if (isProcessing) {
        const pulseR = baseRadius + Math.sin(this.pulsePhase) * 5 + 6;
        this.ctx.beginPath();
        this.ctx.arc(x, y, pulseR, 0, Math.PI * 2);
        this.ctx.fillStyle = 'rgba(6, 182, 212, 0.3)';
        this.ctx.fill();
        this.ctx.strokeStyle = '#22d3ee';
        this.ctx.lineWidth = 2;
        this.ctx.stroke();
      }

      // 2. Main Hole Circle
      this.ctx.beginPath();
      this.ctx.arc(x, y, isHovered || isInspected ? baseRadius + 3 : baseRadius, 0, Math.PI * 2);
      this.ctx.fillStyle = fillColor;
      this.ctx.fill();
      this.ctx.strokeStyle = isInspected || isSelected ? '#ffffff' : strokeColor;
      this.ctx.lineWidth = isInspected ? 3 : (isSelected ? 2 : 1.2);
      this.ctx.stroke();

      // 3. Selection Highlight Ring
      if (isSelected || isInspected || isHovered) {
        this.ctx.beginPath();
        this.ctx.arc(x, y, baseRadius + 6, 0, Math.PI * 2);
        this.ctx.strokeStyle = isSelected ? '#38bdf8' : '#cbd5e1';
        this.ctx.lineWidth = 1.8;
        this.ctx.setLineDash([3, 3]);
        this.ctx.stroke();
        this.ctx.setLineDash([]);
      }

      // 4. Hole Label (Clearly visible with dark pill background)
      const fontSize = Math.max(9, Math.min(13, 11 / Math.sqrt(this.scale)));
      this.ctx.font = `bold ${fontSize}px 'JetBrains Mono', monospace`;
      this.ctx.textAlign = 'center';
      this.ctx.textBaseline = 'middle';

      const labelText = hole.label;
      const textWidth = this.ctx.measureText(labelText).width;
      const labelY = y - baseRadius - (fontSize * 0.75);

      // Draw label background badge for maximum readability
      this.ctx.fillStyle = isSelected ? 'rgba(37, 99, 235, 0.9)' : (isInspected ? 'rgba(15, 23, 42, 0.95)' : 'rgba(15, 23, 42, 0.85)');
      this.ctx.fillRect(x - textWidth / 2 - 3, labelY - fontSize / 2 - 1, textWidth + 6, fontSize + 3);

      this.ctx.strokeStyle = isSelected ? '#60a5fa' : '#334155';
      this.ctx.lineWidth = 0.8;
      this.ctx.strokeRect(x - textWidth / 2 - 3, labelY - fontSize / 2 - 1, textWidth + 6, fontSize + 3);

      this.ctx.fillStyle = isSelected ? '#ffffff' : (isInspected ? '#38bdf8' : '#e2e8f0');
      this.ctx.fillText(labelText, x, labelY);
    }
  }

  private drawMachineCrosshair(): void {
    if (this.machinePosition) {
      const imgX = this.machinePosition.x / 0.2;
      const imgY = this.machinePosition.y / 0.2;

      this.ctx.strokeStyle = '#e11d48';
      this.ctx.lineWidth = 2;
      const size = 18 / this.scale;

      this.ctx.beginPath();
      this.ctx.moveTo(imgX - size, imgY);
      this.ctx.lineTo(imgX + size, imgY);
      this.ctx.moveTo(imgX, imgY - size);
      this.ctx.lineTo(imgX, imgY + size);
      this.ctx.stroke();

      this.ctx.beginPath();
      this.ctx.arc(imgX, imgY, size * 0.5, 0, Math.PI * 2);
      this.ctx.stroke();
    }
  }
}
