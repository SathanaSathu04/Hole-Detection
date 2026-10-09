import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)


def create_system_manual_pdf(filename="Textile_Thread_Insertion_System_Manual.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    # Custom styles
    primary_color = colors.HexColor("#0f172a")
    accent_blue = colors.HexColor("#2563eb")
    accent_cyan = colors.HexColor("#0284c7")
    accent_green = colors.HexColor("#059669")
    text_dark = colors.HexColor("#1e293b")
    text_muted = colors.HexColor("#475569")
    bg_light = colors.HexColor("#f8fafc")
    border_color = colors.HexColor("#cbd5e1")

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=primary_color,
        spaceAfter=6
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=accent_cyan,
        spaceAfter=15
    )

    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=primary_color,
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=accent_blue,
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=text_dark,
        spaceAfter=4
    )

    code_style = ParagraphStyle(
        'Code_Custom',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#0f172a"),
        backColor=colors.HexColor("#f1f5f9"),
        borderColor=border_color,
        borderWidth=0.5,
        borderPadding=4,
        spaceAfter=4
    )

    table_cell = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10.5,
        textColor=text_dark
    )

    table_header = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10.5,
        textColor=colors.white
    )

    story = []

    # Title & Header Banner
    story.append(Paragraph("Automated Textile Thread/Needle Insertion System", title_style))
    story.append(Paragraph("Complete Technical Manual: System Prerequisites, Installation & Operator Functionalities", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=accent_blue, spaceBefore=0, spaceAfter=10))

    # SECTION 1: System Requirements & Software to Install
    story.append(Paragraph("1. System Requirements & Software to Install", h1_style))
    story.append(Paragraph("Before starting the application on Windows, verify that the following prerequisites are installed:", body_style))

    req_data = [
        [Paragraph("Software / Tool", table_header), Paragraph("Required Version", table_header), Paragraph("Verification Command", table_header), Paragraph("Purpose", table_header)],
        [Paragraph("<strong>Python</strong>", table_cell), Paragraph("3.11 or 3.12 (64-bit)", table_cell), Paragraph("<code>python --version</code>", table_cell), Paragraph("FastAPI, OpenCV CV Pipeline, Kinematics Simulator", table_cell)],
        [Paragraph("<strong>Node.js</strong>", table_cell), Paragraph("LTS (v20+ or v24+)", table_cell), Paragraph("<code>node --version</code>", table_cell), Paragraph("JavaScript runtime for Angular toolchain", table_cell)],
        [Paragraph("<strong>npm</strong>", table_cell), Paragraph("v10+ or v11+", table_cell), Paragraph("<code>npm --version</code>", table_cell), Paragraph("Frontend package manager", table_cell)],
        [Paragraph("<strong>Angular CLI</strong>", table_cell), Paragraph("v19+ or v22+", table_cell), Paragraph("<code>ng version</code>", table_cell), Paragraph("Angular development server and compiler", table_cell)],
        [Paragraph("<strong>Git</strong>", table_cell), Paragraph("v2.40+", table_cell), Paragraph("<code>git --version</code>", table_cell), Paragraph("Source control management", table_cell)],
    ]
    req_table = Table(req_data, colWidths=[90, 110, 130, 200])
    req_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary_color),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, border_color),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, bg_light]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(req_table)
    story.append(Spacer(1, 8))

    # SECTION 2: Step-by-Step Installation Commands
    story.append(Paragraph("2. Installation & Running Commands", h1_style))
    story.append(Paragraph("<strong>Backend Installation (PowerShell / Command Prompt):</strong>", body_style))
    backend_cmd = "cd C:\\Users\\sathu\\Desktop\\App\\backend\npython -m venv venv\n.\\venv\\Scripts\\Activate.ps1\npython -m pip install --upgrade pip\npip install fastapi uvicorn opencv-python numpy scipy pyserial websockets sqlalchemy alembic python-multipart pydantic httpx pytest\nuvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
    story.append(Paragraph(backend_cmd.replace('\n', '<br/>'), code_style))

    story.append(Paragraph("<strong>Frontend Installation (PowerShell / Command Prompt):</strong>", body_style))
    frontend_cmd = "cd C:\\Users\\sathu\\Desktop\\App\\frontend\nnpm install\nnpm install @angular/material @angular/cdk zone.js\nnpm start"
    story.append(Paragraph(frontend_cmd.replace('\n', '<br/>'), code_style))
    story.append(Spacer(1, 8))

    # SECTION 3: All Functionalities Breakdown
    story.append(Paragraph("3. Detailed Functional Guide", h1_style))

    funcs = [
        ("Upload Board Image",
         "Allows the operator to upload any high-resolution physical textile board photo (.png, .jpg, .bmp). The image is safely stored in backend/storage/boards/ with unique IDs and pixel dimensions indexed in the database."),
        
        ("Detect Holes (OpenCV Computer Vision)",
         "Runs an advanced computer vision pipeline (Grayscale -> Gaussian blur -> Adaptive thresholding -> Morphological filtering -> Circularity filtering -> Sub-pixel centroid moments). Detects every actual physical hole without making rigid rectangular grid assumptions."),
        
        ("Confirm Hole Map",
         "Locks and verifies the detected hole map for production. Prevents accidental modifications and ensures coordinate accuracy before triggering physical or simulated CNC needle movements."),
        
        ("Excel-Style Hole Labeling (A1..ZZ20)",
         "Automatically numbers detected holes into rows and columns using scalable Excel naming (A1..A20, B1..B20, Z1..Z20, AA1..AA50, AB1, etc.). Supports 5,000 to 10,000+ holes with zero label collisions."),
        
        ("Manual Hole Selection & Deselection",
         "The operator can click directly on any hole on the canvas board image to select or deselect it. Selected holes turn Electric Blue and are added to the execution sequence queue."),
        
        ("Select All & Clear Selection",
         "Allows the operator to queue all detected holes with a single click ('Select All Holes') or clear the entire queue ('Clear Selection') to start fresh."),
        
        ("Start Job",
         "Initiates sequential CNC execution. The virtual machine head moves smoothly across X, Y at Safe Z height (25mm), lowers the needle downstroke (5mm), actuates thread insertion, and captures a live camera frame for optical verification."),
        
        ("Pause Job & Resume Job",
         "Provides real-time machine execution control. Pausing freezes all stepper motion and holds position. Resuming continues seamlessly from the exact current hole without skipping or repeating."),
        
        ("Stop Job",
         "Safely aborts the active insertion job, returns the toolhead to Safe Z height, and marks the job as STOPPED."),
        
        ("Live Camera Inspection & Fiber Verification",
         "Streams live video from a connected USB camera (or high-definition synthetic inspection feed). Upon needle actuation, OpenCV analyzes fiber density, texture variance, and edge deviation to verify thread presence, returning THREAD_DETECTED or THREAD_NOT_DETECTED."),
        
        ("Hole Retry Workflow (Green / Red Status)",
         "Holes that pass verification turn Emerald Green (SUCCESS). If a hole fails, it turns Crimson Red (FAILED). The operator can select the failed hole and click RETRY to re-position and re-insert immediately."),
        
        ("HOME Button (G28 Reference Homing)",
         "Drives the CNC axes to the physical limit switches at (0, 0, 25mm). Establishes the real-world hardware coordinate origin so all subsequent millimeter coordinates are mathematically accurate."),
        
        ("CALIBRATE Button (Planar Homography)",
         "Calculates a 3x3 perspective transformation matrix mapping camera pixels (px) to physical CNC millimeters (mm) using 4 corner reference points, validating sub-millimeter reprojection accuracy."),
        
        ("Hole Search & 3D Coordinates Inspector",
         "Allows searching by label (e.g. A1, B3) to instantly pan, zoom, and display all 3 coordinate systems: Image Pixels (X, Y px), Board Layout (X, Y mm), and Machine CNC (X, Y, Z mm).")
    ]

    for title, desc in funcs:
        story.append(Paragraph(f"• <strong>{title}</strong>", h2_style))
        story.append(Paragraph(desc, body_style))

    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1, color=border_color, spaceBefore=4, spaceAfter=8))

    # SECTION 4: Quick Reference Table
    story.append(Paragraph("4. Operator Control Quick Reference", h1_style))
    ref_data = [
        [Paragraph("Control / Action", table_header), Paragraph("Description", table_header), Paragraph("Visual Indicator", table_header)],
        [Paragraph("<strong>Click Hole</strong>", table_cell), Paragraph("Select/deselect hole for insertion", table_cell), Paragraph("Turns <strong>Electric Blue</strong>", table_cell)],
        [Paragraph("<strong>Detect Holes</strong>", table_cell), Paragraph("OpenCV hole detection & Excel labeling", table_cell), Paragraph("Renders Amber dots + <code>A1..N20</code>", table_cell)],
        [Paragraph("<strong>START JOB</strong>", table_cell), Paragraph("Starts 3D movement & thread insertion", table_cell), Paragraph("Current hole pulses <strong>Cyan</strong>", table_cell)],
        [Paragraph("<strong>Success Result</strong>", table_cell), Paragraph("Thread confirmed by camera check", table_cell), Paragraph("Turns <strong>Emerald Green</strong>", table_cell)],
        [Paragraph("<strong>Failure Result</strong>", table_cell), Paragraph("Thread missing or low confidence", table_cell), Paragraph("Turns <strong>Crimson Red</strong>", table_cell)],
        [Paragraph("<strong>RETRY</strong>", table_cell), Paragraph("Re-runs insertion on failed hole", table_cell), Paragraph("Re-executes needle stroke", table_cell)],
        [Paragraph("<strong>HOME</strong>", table_cell), Paragraph("Re-zeros machine to (0,0,25mm)", table_cell), Paragraph("Position resets to <code>0.00, 0.00</code>", table_cell)],
        [Paragraph("<strong>E-STOP</strong>", table_cell), Paragraph("Emergency software halt", table_cell), Paragraph("Machine status = <code>STOPPED</code>", table_cell)],
    ]
    ref_table = Table(ref_data, colWidths=[120, 240, 170])
    ref_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary_color),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, border_color),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, bg_light]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(ref_table)

    doc.build(story)
    print(f"Generated PDF documentation successfully: {filename}")
    return filename


if __name__ == "__main__":
    out_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Textile_Thread_Insertion_System_Manual.pdf")
    create_system_manual_pdf(out_file)
