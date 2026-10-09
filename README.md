# Automated Textile Thread/Needle Insertion & Hole Detection System

An industrial-grade automated control application designed for high-density physical textile/design boards containing 5,000 to 10,000+ holes. The system pairs OpenCV computer vision for hole identification and Excel-style indexing with a real-time CNC 3D kinematics simulator, live camera inspection, homography coordinate calibration, and an Angular dashboard.

---

## 1. System Architecture

```
Angular Frontend (Operator Dashboard)
        │
        ├── REST API (HTTP) ───► FastAPI Backend
        │                              │
        └── WebSocket (Realtime) ──────┼──► Computer Vision (OpenCV)
                                       ├──► 3D Machine Controller / Simulator
                                       ├──► Inspection Camera Service
                                       └──► SQLAlchemy DB (SQLite / PostgreSQL)
```

### Coordinate Systems:
1. **Image Frame (`px`)**: Pixel coordinates $(x_{img}, y_{img})$ from high-resolution board camera.
2. **Board Frame (`mm`)**: Physical board layout dimensions $(x_{board}, y_{board})$ offset from fiducials.
3. **Machine Frame (`mm`)**: 3D CNC travel $(x_{mach}, y_{mach}, z_{mach})$ with safe travel Z and insertion stroke Z.

---

## 2. Core Features & Acceptance Criteria

- **High-Density Hole Visualization**: Custom HTML5 Canvas rendering 10,000+ holes at 60 FPS with level-of-detail label culling, smooth pan & zoom, and sub-millisecond hover search.
- **Excel-Style Hole Labeling**: Unlimited row scaling (`A1..A20`, `Z1..Z20`, `AA1..AA50`, `AB1`, etc.) with row clustering and left-to-right sorting.
- **Planar Homography Calibration**: 4-point perspective transformation calculating transformation matrix $H$ with sub-millimeter reprojection error validation.
- **CNC Machine Simulator**: Virtual 3D stepper motion, homing (G28), downstroke needle actuation, safety interlocks, and telemetry broadcasting.
- **Live Camera & Verification**: Real-time MJPEG live stream with HUD crosshairs, fiber/texture differential verification, and retry capability.
- **Database & Job State Persistence**: Complete job sequence history with attempt tracking and disconnection recovery.

---

## 3. Directory Structure

```
textile-thread-machine/
├── backend/
│   ├── app/
│   │   ├── api/             # REST Endpoints (boards, holes, jobs, machine, camera, calibration)
│   │   ├── camera/          # Camera abstraction & OpenCV MJPEG streamer
│   │   ├── database/        # SQLAlchemy Models & SQLite/Postgres sessions
│   │   ├── machine/         # Machine Controller Abstraction, Simulator & Real Hardware Adapter
│   │   ├── services/        # Business Logic & Job Execution Worker
│   │   ├── vision/          # OpenCV Detection Pipeline, Homography & Verification
│   │   ├── websocket/       # Connection Manager & Event Broadcaster
│   │   └── tests/           # Comprehensive Unit & Integration Test Suite
│   ├── requirements.txt
│   └── pytest.ini
├── frontend/
│   ├── src/app/
│   │   ├── core/            # Models & API / WebSocket Services
│   │   └── features/
│   │       ├── dashboard/   # Master Industrial Control Dashboard
│   │       ├── hole-map/    # High-Performance HTML5 Canvas Renderer
│   │       └── calibration/ # Planar Homography Calibration Modal
├── sample-data/             # Synthetic boards with 300, 1,000, and 5,000 holes
└── README.md
```

---

## 4. Quick Start & Execution

### Prerequisites:
- Python 3.11 or 3.12
- Node.js LTS (v20+ or v24+)
- Angular CLI (`npm install -g @angular/cli`)

### Running the Backend:
```powershell
cd backend
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
- API Base: `http://127.0.0.1:8000`
- Swagger Docs: `http://127.0.0.1:8000/docs`

### Running the Frontend:
```powershell
cd frontend
ng serve
```
- Dashboard: `http://localhost:4200`

### Running Automated Tests:
```powershell
cd backend
.\venv\Scripts\pytest
```

---

## 5. Machine Simulation Workflow Demo

1. Open `http://localhost:4200`.
2. Click **Upload** and choose `sample-data/sample_board_300.png` or `sample_board_1000.png`.
3. Click **Detect Holes** to run OpenCV detection (identifies all actual holes and assigns `A1`, `A2`, `B1`, etc.).
4. Search `A102` in the search bar to auto-zoom and inspect physical coordinates.
5. Click **Select All** or click individual holes to construct an insertion sequence.
6. Click **START JOB** to trigger simulated CNC movement, needle insertion stroke, live camera inspection, and real-time color updating.
7. If any hole fails verification, click **RETRY HOLE** to immediately re-execute that hole.
