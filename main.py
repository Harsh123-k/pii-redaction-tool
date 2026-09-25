"""Main entry point for the PII Redaction Tool.

Provides both:
1. A FastAPI web service with Jinja2 dashboard for interactive document redaction & evaluation.
2. A command-line interface (CLI) for batch file redaction and benchmark evaluation.
"""

import argparse
import logging
from pathlib import Path
import sys
from typing import Optional

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

from src.config import (
    ALLOWED_EXTENSIONS,
    BASE_DIR,
    MAX_FILE_SIZE_BYTES,
    OUTPUT_DIR,
    SAMPLE_DIR,
    SUPPORTED_PII_TYPES,
    UPLOAD_DIR,
)
from src.document_handler import DocumentHandler
from src.evaluator import PIIEvaluator

# Configure application logging (safe logging: no PII values logged)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("pii_redaction_tool")

# Initialize FastAPI application
app = FastAPI(
    title="PII Redaction Tool",
    description="Automated PII detection, redaction, and evaluation system for support ticket documents.",
    version="1.0.0",
)

# Static files and templates
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Global processing instances
handler = DocumentHandler()
evaluator = PIIEvaluator()


@app.get("/", response_class=HTMLResponse)
async def index_view(request: Request):
    """Render the main upload dashboard."""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "supported_types": SUPPORTED_PII_TYPES,
            "max_file_size_mb": MAX_FILE_SIZE_BYTES // (1024 * 1024),
        },
    )


@app.get("/health")
@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "pii-redaction-tool",
        "version": "1.0.0",
        "spacy_available": handler.detector.ner_detector.is_available(),
    }


@app.post("/upload")
@app.post("/api/redact")
async def upload_document(file: UploadFile = File(...)):
    """Upload and redact a document (.docx or .txt)."""
    raw_filename = file.filename or "uploaded_document"
    filename = Path(raw_filename).name  # Prevent path traversal
    ext = Path(filename).suffix.lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. Allowed extensions: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Read uploaded content and enforce file size boundary
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty.",
        )
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds maximum allowed size of {MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB.",
        )

    temp_input_path = UPLOAD_DIR / filename
    with open(temp_input_path, "wb") as f:
        f.write(content)

    output_filename = f"redacted_{filename}"
    output_path = OUTPUT_DIR / output_filename

    try:
        result = handler.process_document(temp_input_path, output_path)
    except Exception as e:
        logger.error("Processing failed for '%s': %s", filename, e, exc_info=True)
        raise HTTPException(status_code=400, detail=f"Processing failed: {str(e)}")
    finally:
        # Zero data retention: ensure temporary unredacted file is removed
        try:
            if temp_input_path.exists():
                temp_input_path.unlink()
        except Exception as cleanup_err:
            logger.warning("Could not delete temporary file '%s': %s", temp_input_path, cleanup_err)

    return {
        "status": "success",
        "file_id": output_filename,
        "original_filename": filename,
        "output_filename": output_filename,
        "download_url": f"/download/{output_filename}",
        "total_detected": result["total_detected"],
        "breakdown": result["breakdown"],
        "processing_time_sec": result["processing_time_sec"],
    }


@app.get("/download/{filename}")
@app.get("/api/download/{filename}")
async def download_file(filename: str):
    """Download a redacted document from output directory."""
    safe_filename = Path(filename).name  # Prevent path traversal
    file_path = OUTPUT_DIR / safe_filename
    if not file_path.exists() or not file_path.is_file():
        alt_path = OUTPUT_DIR / f"redacted_{safe_filename}"
        if alt_path.exists() and alt_path.is_file():
            file_path = alt_path
        else:
            raise HTTPException(status_code=404, detail="Requested file was not found.")
    return FileResponse(
        path=str(file_path),
        filename=file_path.name,
        media_type="application/octet-stream",
    )


@app.get("/evaluate")
@app.get("/api/evaluate")
async def evaluate_benchmark():
    """Execute evaluation benchmark against the ground-truth annotations."""
    gt_file = SAMPLE_DIR / "ground_truth.json"
    if not gt_file.exists():
        raise HTTPException(status_code=404, detail="Ground truth benchmark file not found.")

    res = evaluator.evaluate_benchmark_file(gt_file)
    markdown_table = PIIEvaluator.format_markdown_table(res)

    return {
        "status": "success",
        "overall": res["overall"],
        "per_type": res["per_type"],
        "markdown_table": markdown_table,
    }


def run_cli():
    """Handle CLI execution."""
    parser = argparse.ArgumentParser(
        description="PII Redaction Tool - Secure automated PII redaction and evaluation."
    )
    parser.add_argument(
        "--file",
        "-f",
        type=str,
        help="Path to an input DOCX or TXT file to redact.",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Custom destination path for the redacted document.",
    )
    parser.add_argument(
        "--evaluate",
        "-e",
        action="store_true",
        help="Run benchmark evaluation against ground truth dataset.",
    )
    parser.add_argument(
        "--serve",
        "-s",
        action="store_true",
        help="Launch the FastAPI web server.",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Server host address (default: 127.0.0.1).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Server port (default: 8000).",
    )

    args = parser.parse_args()

    if args.evaluate:
        gt_file = SAMPLE_DIR / "ground_truth.json"
        print("\nRunning benchmark evaluation against ground-truth dataset...\n")
        res = evaluator.evaluate_benchmark_file(gt_file)
        print(PIIEvaluator.format_markdown_table(res))
        print("\nOverall Summary:")
        for k, v in res["overall"].items():
            print(f"  {k.capitalize()}: {v}")
        return

    if args.file:
        input_p = Path(args.file)
        if not input_p.exists():
            print(f"Error: Specified file does not exist: {input_p}", file=sys.stderr)
            sys.exit(1)

        out_p = Path(args.output) if args.output else None
        print(f"Processing document: {input_p.name}...")
        res = handler.process_document(input_p, out_p)
        print(f"Redaction complete in {res['processing_time_sec']}s.")
        print(f"Saved to: {res['output_path']}")
        print(f"Total PII items detected: {res['total_detected']}")
        print("Breakdown by category:")
        for t, count in res["breakdown"].items():
            print(f"  {t}: {count}")
        return

    # Default action or --serve flag: start web server
    print(f"Starting PII Redaction Tool web application on http://{args.host}:{args.port}")
    uvicorn.run("main:app", host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    run_cli()
