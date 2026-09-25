# PII Redaction Tool

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![spaCy](https://img.shields.io/badge/spaCy-3.7%2B-09A3D5.svg)](https://spacy.io/)
[![Render](https://img.shields.io/badge/Render-Live%20Demo-brightgreen.svg)](https://pii-redaction-tool-jfdr.onrender.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests Passing](https://img.shields.io/badge/Tests-32%20Passed-brightgreen.svg)]()

An enterprise-ready, format-preserving Personally Identifiable Information (PII) detection, redaction, and benchmark evaluation system. Built specifically for IT customer support tickets, service desk logs, and corporate documents, it combines deterministic rule-based algorithms with NLP Named Entity Recognition (NER) to securely detect sensitive personal data and replace it with realistic synthetic equivalents while maintaining original document layout and zero data leakage.

---

## 🌐 Live Demo

The application is deployed and publicly accessible on Render:

👉 **Live Web Application:** [https://pii-redaction-tool-jfdr.onrender.com](https://pii-redaction-tool-jfdr.onrender.com)  

---

## Table of Contents

- [Live Demo](#-live-demo)
- [Key Features](#key-features)
- [Supported PII Categories](#supported-pii-categories)
- [Tech Stack](#tech-stack)
- [Project Architecture](#project-architecture)
- [Installation Instructions (Windows)](#installation-instructions-windows)
  - [Prerequisites](#prerequisites)
  - [1. Clone / Open Project](#1-clone--open-project)
  - [2. Virtual Environment Setup](#2-virtual-environment-setup)
  - [3. Install Dependencies](#3-install-dependencies)
  - [4. Download spaCy Language Model](#4-download-spacy-language-model)
- [Running the Application Locally](#running-the-application-locally)
  - [Start Web Service](#start-web-service)
  - [Run via Command-Line Interface (CLI)](#run-via-command-line-interface-cli)
- [Web Interface Usage](#web-interface-usage)
- [Document Upload and Redaction Workflow](#document-upload-and-redaction-workflow)
- [Available API Endpoints](#available-api-endpoints)
- [Example Usage](#example-usage)
  - [CLI Batch Processing](#cli-batch-processing)
  - [cURL REST API Examples](#curl-rest-api-examples)
- [Automated Testing](#automated-testing)
- [Benchmark Evaluation & Ground Truth](#benchmark-evaluation--ground-truth)
- [Security and Privacy Considerations](#security-and-privacy-considerations)
- [Deployment Instructions (Render)](#deployment-instructions-render)
- [Environment Variables](#environment-variables)
- [Limitations](#limitations)
- [Future Improvements](#future-improvements)
- [License](#license)

---

## Key Features

- **Hybrid Detection Engine:** Blends high-precision deterministic regular expressions, Luhn checksum validation, and contextual window inspection with spaCy statistical NER (`en_core_web_sm`).
- **Deterministic Priority & Overlap Resolution:** Resolves overlapping entity boundaries through a prioritized hierarchy (e.g., structured credit cards and SSNs take precedence over broad NER spans).
- **Realistic Synthetic Substitution:** Replaces detected sensitive items with synthetic equivalents generated via Faker and curated pools, ensuring the document remains readable for downstream analysis.
- **Cross-Document Consistency:** Repeated mentions of the same raw PII entity (e.g., "John Doe") deterministically map to the identical synthetic replacement across the entire document session.
- **Anti-Collision Guarantee:** Synthetic replacement generation guarantees that the substituted value never equals or leaks any part of the original sensitive value.
- **Format-Preserving DOCX & TXT Engine:** Operates in-place on Word documents (`.docx`), preserving paragraphs, headings, bullet lists, tables, nested cells, and run-level styles (bold, italics, fonts), alongside plain text files (`.txt`).
- **False-Positive Prevention:** Whitelists operational ticketing identifiers (`TKT-1023`, `ORD-123456`, `INV-2026-1001`, `EMP12345`), infrastructure IP masks (`255.255.255.0`, `127.0.0.1`), software versions (`v1.2.3`), and non-DOB operational timestamps.
- **Self-Contained Evaluation Benchmark:** Evaluates real Precision, Recall, Accuracy, and F1-scores against ground-truth support ticket annotations with one click or CLI argument.
- **Dual Mode:** Operates as both an interactive FastAPI web application with Jinja2 dashboard and a batch command-line utility.

---

## Supported PII Categories

The system detects and redacts 9 distinct PII categories:

| Category | Description | Primary Detection Method | Example Formats |
| :--- | :--- | :--- | :--- |
| **`PERSON`** | Customer, client, requester, or agent names | spaCy NER (`PERSON`) + role-prefix cleaning | `John Doe`, `Rashmi Patil`, `Alex Mercer` |
| **`EMAIL`** | Standard and RFC-compliant email addresses | Deterministic RFC 5322 Regex | `john.doe@example.com`, `user.name@domain.co.in` |
| **`PHONE`** | International & domestic telephone numbers | Multi-pattern Regex with country code detection | `+91 9876543210`, `9876543210`, `+1 (555) 019-2831` |
| **`COMPANY`** | Legal corporate and organizational entities | Capitalized suffix Regex + spaCy NER (`ORG`) | `Acme Corporation`, `Global Technologies Ltd.`, `Microsoft Corporation` |
| **`ADDRESS`** | Physical street, postal, and office addresses | Street suffix patterns + Postal code + NER (`GPE`/`LOC`) | `123 Main Street, Suite 400, Seattle, WA 98101` |
| **`SSN`** | US Social Security Numbers | Standard area/group-code validated Regex | `123-45-6789`, `456-78-1234` |
| **`CREDIT_CARD`** | Payment card numbers across major card networks | Regex + Luhn mod-10 algorithm + Contextual check | `4111 1111 1111 1111`, `3782 8224 6310 005` |
| **`DOB`** | Date of Birth timestamps | Context-window inspection (e.g. "dob", "born on") | `12/05/1990`, `1985-08-22`, `15/08/2002` |
| **`IP_ADDRESS`** | Sensitive client/host IPv4 addresses | Strict 0-255 octet Regex + Subnet/version filtering | `192.168.1.10`, `172.16.254.1`, `10.0.4.15` |

---

## Tech Stack

- **Backend Web Framework:** [FastAPI](https://fastapi.tiangolo.com/) (Asynchronous ASGI framework)
- **ASGI Server:** [Uvicorn](https://www.uvicorn.org/)
- **Templating Engine:** [Jinja2](https://jinja.palletsprojects.com/)
- **Document Processing:** [python-docx](https://python-docx.readthedocs.io/) (OpenXML Word document manipulation)
- **Natural Language Processing:** [spaCy](https://spacy.io/) with `en_core_web_sm`
- **Synthetic Data Generation:** [Faker](https://faker.readthedocs.io/)
- **Evaluation & Metrics:** [scikit-learn](https://scikit-learn.org/) & built-in precision/recall/F1 scoring
- **Testing Framework:** [pytest](https://docs.pytest.org/) & Starlette `TestClient`

---

## Project Architecture

```
pii-redaction-tool/
├── data/
│   └── sample/
│       ├── create_sample_and_ground_truth.py   # Script to generate sample datasets
│       ├── ground_truth.json                   # Ground-truth benchmark dataset (30 entities)
│       └── sample_ticket_document.docx         # Sample input ticket document with tables
├── output/                                     # Destination directory for redacted documents
├── src/
│   ├── __init__.py
│   ├── config.py                               # Global configuration, constants, entity priority
│   ├── document_handler.py                     # DOCX/TXT file parsing, formatting preservation
│   ├── evaluator.py                            # Precision, Recall, F1 & Accuracy calculation
│   ├── ner_detector.py                         # spaCy NER pipeline wrapper & false-positive filters
│   ├── pii_detector.py                         # Hybrid detection pipeline & conflict resolution
│   ├── pii_patterns.py                         # Regex definitions, Luhn validator, identifier rules
│   ├── redactor.py                             # Offset-based text replacement engine
│   └── replacement_generator.py                # Consistent synthetic PII generator
├── static/
│   └── style.css                               # CSS styling for dashboard UI
├── templates/
│   └── index.html                              # Jinja2 template for web dashboard
├── tests/
│   ├── __init__.py
│   ├── conftest.py                             # Pytest fixtures
│   ├── test_api.py                             # FastAPI endpoint integration tests
│   ├── test_document_handler.py                # DOCX/TXT redaction & format tests
│   ├── test_evaluator.py                       # Evaluation metrics unit tests
│   ├── test_false_positives.py                 # Ticket ID & non-PII suppression tests
│   ├── test_pii_detector.py                    # Category detection unit tests
│   └── test_redactor.py                        # Consistency & anti-collision tests
├── uploads/                                    # Temporary upload staging (cleaned up automatically)
├── evaluation_report.md                        # Benchmark evaluation results
├── main.py                                     # Application entry point (FastAPI + CLI)
├── requirements.txt                            # Project Python dependencies
└── README.md                                   # Comprehensive project documentation
```

---

## Installation Instructions (Windows)

### Prerequisites

- **Python 3.10, 3.11, or 3.12** installed on your system.
- PowerShell or Windows Command Prompt.

### 1. Clone / Open Project

Navigate to the project root directory in PowerShell:

```powershell
cd C:\Users\User\.gemini\antigravity\scratch\pii-redaction-tool
```

### 2. Virtual Environment Setup

Create and activate an isolated Python virtual environment:

```powershell
# Create virtual environment named .venv
python -m venv .venv

# Activate the virtual environment
.\.venv\Scripts\Activate.ps1
```

> **Note for PowerShell execution policy:** If script execution is restricted, run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` before activating.

### 3. Install Dependencies

Install all required packages from `requirements.txt`:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Download spaCy Language Model

Download the English model used by the NER pipeline:

```powershell
python -m spacy download en_core_web_sm
```

---

## Running the Application Locally

### Start Web Service

To start the FastAPI web server on `http://127.0.0.1:8000`:

```powershell
# Using the main CLI runner
python main.py

# Or explicitly specifying host and port
python main.py --serve --host 127.0.0.1 --port 8000

# Or directly with Uvicorn
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Once started, open your web browser to:
👉 **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

### Run via Command-Line Interface (CLI)

The application provides a built-in CLI for batch operations without running the web service:

#### Redact a Single Document
```powershell
# Redact a DOCX file
python main.py --file data/sample/sample_ticket_document.docx --output output/redacted_ticket.docx

# Redact a plain text file
python main.py --file sample.txt --output output/redacted_sample.txt
```

#### Run Benchmark Evaluation in Terminal
```powershell
python main.py --evaluate
```

---

## Web Interface Usage

The interactive web dashboard provides a clean single-page experience:

1. **Category Badges:** Displays all 9 supported PII types supported by the active detector.
2. **Drag & Drop Upload:** Drag `.docx` or `.txt` files directly onto the drop zone, or click to open the file picker.
3. **Submit Redaction:** Click **"Redact Document"**. A live spinner indicates real-time entity detection and synthetic substitution.
4. **Redaction Summary:** Upon completion, the panel displays:
   - **Total PII Redacted:** Aggregate count of sensitive entities removed.
   - **Processing Time:** Execution time in seconds.
   - **Entity Breakdown:** Count of detected entities categorized by type (e.g., `PERSON: 9`, `EMAIL: 6`, `PHONE: 6`).
   - **Download Button:** Direct download link for the sanitized document (`redacted_<filename>`).
5. **Interactive Benchmark Runner:** Click **"Run Benchmark"** under the Benchmark section to evaluate system performance against ground truth annotations and render a live markdown table.

---

## Document Upload and Redaction Workflow

```
[Uploaded Document (.docx / .txt)]
               │
               ▼
   [Validation & File Sanitization]
   - Verify .docx or .txt extension
   - Reject empty files (0 bytes -> HTTP 400)
   - Enforce 15 MB file size boundary
   - Sanitize filename against path traversal
               │
               ▼
       [Text Extraction]
   - Paragraphs, Headings, Lists
   - Tables (Rows, Cells, Nested Paragraphs)
               │
               ▼
    [Hybrid PII Detection Pipeline]
   - Deterministic Regexes (Email, Phone, SSN, Credit Card, IP, Address, Legal Company)
   - spaCy NER (Person, Organization, Address/Location)
   - Filter false positives (Ticket IDs, Order numbers, Subnet masks)
               │
               ▼
     [Deterministic Conflict Resolver]
   - Resolve overlapping character intervals using priority & confidence
               │
               ▼
      [Synthetic Replacement Engine]
   - Lookup existing session cache (consistent replacement)
   - Generate realistic synthetic value with anti-collision checks
               │
               ▼
     [Document Reconstruction]
   - Replace spans in-place, preserving Word run-level formatting
   - Save clean file to output/
   - Immediately delete raw uploaded temporary file (Zero Data Retention)
               │
               ▼
   [HTTP Response / Download Ready]
```

---

## Available API Endpoints

| Method | Endpoint | Description | Sample Response / Status |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | Web dashboard HTML view | `200 OK` (HTML) |
| `GET` | `/health` or `/api/health` | Service health status & spaCy availability | `200 OK` (JSON: `{"status": "healthy", ...}`) |
| `POST` | `/upload` or `/api/redact` | Upload document (`multipart/form-data`) | `200 OK` (JSON with summary & download URL) |
| `GET` | `/download/{filename}` or `/api/download/{filename}` | Download sanitized document | `200 OK` (Binary file stream) |
| `GET` | `/evaluate` or `/api/evaluate` | Run evaluation benchmark against ground truth | `200 OK` (JSON with precision/recall/F1 metrics) |

---

## Example Usage

### CLI Batch Processing

```powershell
# Redact document
python main.py -f data/sample/sample_ticket_document.docx -o output/my_redacted_doc.docx
```

**Output:**
```
Processing document: sample_ticket_document.docx...
Redaction complete in 0.184s.
Saved to: output\my_redacted_doc.docx
Total PII items detected: 47
Breakdown by category:
  PERSON: 9
  EMAIL: 6
  PHONE: 6
  COMPANY: 7
  ADDRESS: 3
  DOB: 4
  SSN: 3
  CREDIT_CARD: 3
  IP_ADDRESS: 6
```

### cURL REST API Examples

#### 1. Check Health
```bash
curl -X GET http://127.0.0.1:8000/api/health
```

#### 2. Redact a Document
```bash
curl -X POST http://127.0.0.1:8000/api/redact \
  -F "file=@data/sample/sample_ticket_document.docx"
```

**Response:**
```json
{
  "status": "success",
  "file_id": "redacted_sample_ticket_document.docx",
  "original_filename": "sample_ticket_document.docx",
  "output_filename": "redacted_sample_ticket_document.docx",
  "download_url": "/download/redacted_sample_ticket_document.docx",
  "total_detected": 47,
  "breakdown": {
    "PERSON": 9,
    "EMAIL": 6,
    "PHONE": 6,
    "COMPANY": 7,
    "ADDRESS": 3,
    "DOB": 4,
    "SSN": 3,
    "CREDIT_CARD": 3,
    "IP_ADDRESS": 6
  },
  "processing_time_sec": 0.184
}
```

#### 3. Download Redacted Document
```bash
curl -O -J http://127.0.0.1:8000/api/download/redacted_sample_ticket_document.docx
```

#### 4. Run Benchmark Evaluation
```bash
curl -X GET http://127.0.0.1:8000/api/evaluate
```

---

## Automated Testing

The project includes an automated test suite implemented with `pytest`:

```powershell
# Run the complete test suite
pytest tests/

# Run with verbose output
pytest -v tests/
```

### Test Coverage Highlights

- **`test_api.py`:** Tests all FastAPI endpoints, HTML rendering, DOCX/TXT upload, file downloads, empty file rejection, invalid formats, corrupted DOCX handling, and 404 responses.
- **`test_document_handler.py`:** Validates DOCX paragraphs and tables, style preservation, zero PII leakage, and plain text processing.
- **`test_false_positives.py`:** Validates suppression of ticket IDs (`TKT-1023`, `ORD-123456`, `INV-2026-1001`), employee IDs (`EMP12345`), standard calendar dates, subnet masks (`255.255.255.0`), loopback IPs (`127.0.0.1`), software versions (`1.2.3.4`), and invalid credit card numbers.
- **`test_pii_detector.py`:** Unit tests for all individual entity detectors (`PERSON`, `EMAIL`, `PHONE`, `COMPANY`, `ADDRESS`, `SSN`, `CREDIT_CARD`, `DOB`, `IP_ADDRESS`) and multi-span conflict resolution.
- **`test_redactor.py`:** Asserts cross-sentence replacement consistency and synthetic anti-collision guarantees.
- **`test_evaluator.py`:** Verifies precision, recall, F1, and accuracy computations.

---

## Benchmark Evaluation & Ground Truth

The project includes a curated ground-truth dataset in [data/sample/ground_truth.json](data/sample/ground_truth.json) with 30 annotated PII entities spanning 3 diverse IT support ticket scenarios.

### Performance Results

| PII Category | Gold Count | Predicted | TP | FP | FN | Accuracy | Precision | Recall | F1-Score |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`PERSON`** | 6 | 6 | 6 | 0 | 0 | 1.000 | 1.000 | 1.000 | 1.000 |
| **`EMAIL`** | 3 | 3 | 3 | 0 | 0 | 1.000 | 1.000 | 1.000 | 1.000 |
| **`PHONE`** | 3 | 3 | 3 | 0 | 0 | 1.000 | 1.000 | 1.000 | 1.000 |
| **`COMPANY`** | 3 | 3 | 3 | 0 | 0 | 1.000 | 1.000 | 1.000 | 1.000 |
| **`ADDRESS`** | 3 | 3 | 3 | 0 | 0 | 1.000 | 1.000 | 1.000 | 1.000 |
| **`SSN`** | 3 | 3 | 3 | 0 | 0 | 1.000 | 1.000 | 1.000 | 1.000 |
| **`CREDIT_CARD`** | 3 | 3 | 3 | 0 | 0 | 1.000 | 1.000 | 1.000 | 1.000 |
| **`DOB`** | 3 | 3 | 3 | 0 | 0 | 1.000 | 1.000 | 1.000 | 1.000 |
| **`IP_ADDRESS`** | 3 | 3 | 3 | 0 | 0 | 1.000 | 1.000 | 1.000 | 1.000 |
| **OVERALL (Micro)** | **30** | **30** | **30** | **0** | **0** | **1.000** | **1.000** | **1.000** | **1.000** |

*See [evaluation_report.md](evaluation_report.md) for full benchmark documentation.*

---

## Security and Privacy Considerations

- **Safe Logging (Zero PII Logging):** Application logs only record execution duration, file size, entity counts, and non-sensitive filenames. Raw PII text values are never printed to logs or standard out.
- **API Leakage Protection:** REST API responses return detection counts and breakdown statistics. Unredacted text and entity span values are never exposed in JSON responses.
- **Zero Temporary Data Retention:** Files uploaded to the `uploads/` staging folder are automatically deleted in a `finally` block immediately after processing finishes.
- **Path Traversal Mitigation:** All uploaded filenames and download requests are sanitized using `Path(filename).name` to eliminate directory traversal attacks (`../`).
- **Input Validation & DoS Protection:** Maximum file size is strictly capped at 15 MB (`MAX_FILE_SIZE_BYTES`). Empty uploads (0 bytes) and unsupported file formats are rejected with HTTP 400.
- **No External Cloud Dependencies:** The detection, NER, and redaction pipelines run entirely offline on the local CPU without transmitting sensitive documents to external third-party APIs.
- **No Hardcoded Secrets:** Zero API keys, passwords, or authentication secrets exist in the repository.

---

## Deployment Instructions (Render)

To deploy the PII Redaction Tool as a Web Service on [Render](https://render.com/):

1. **Create New Web Service:**
   - Link your Git repository on Render.
   - Select **Python** as the runtime environment.

2. **Configure Build & Start Commands:**
   - **Build Command:**
     ```bash
     pip install --upgrade pip && pip install -r requirements.txt && python -m spacy download en_core_web_sm
     ```
   - **Start Command:**
     ```bash
     uvicorn main:app --host 0.0.0.0 --port $PORT
     ```

3. **Instance Type:**
   - Standard Free or Starter tier (requires ~512 MB to 1 GB RAM for spaCy `en_core_web_sm`).

4. **Verify Deployment:**
   - Once deployed, visit `https://<your-service>.onrender.com/health` to confirm the service reports `"status": "healthy"`.

---

## Environment Variables

The application is completely self-contained and does not require third-party API keys or cloud credentials. The only environment variable used in production deployment is:

| Variable | Required | Default | Description |
| :--- | :---: | :---: | :--- |
| `PORT` | Optional | `8000` | Port on which Uvicorn binds (automatically supplied by platforms like Render/Heroku). |

---

## Limitations

- **File Format Scope:** Currently supports `.docx` and `.txt` files. PDF, scans, and image-based documents (OCR) are not currently supported.
- **Language Scope:** The spaCy `en_core_web_sm` pipeline and regex heuristics are tailored for English-language documents and international PII conventions.
- **Unusual Name Spelling:** Unconventional or single-word names lacking context words ("Customer", "Requester") may not be recognized if not capitalized or detected by spaCy NER.
- **Handwritten / Highly Malformed Text:** Documents containing optical character recognition errors or non-standard ASCII characters may decrease detection accuracy.

---

## Future Improvements

- [ ] **PDF & OCR Support:** Ingest native PDFs and scanned images via Tesseract OCR or `pymupdf`.
- [ ] **Multilingual NER:** Expand entity recognition to multilingual models (`xx_ent_wiki_sm` or transformer-based models) for Spanish, German, French, and Hindi.
- [ ] **Custom PII Rules UI:** Allow administrators to define custom regexes and project-specific keyword dictionaries from the dashboard.
- [ ] **Role-Based Access Control (RBAC):** Add user authentication (OAuth2 / JWT) and audit logging for enterprise multi-tenant deployments.
- [ ] **Streaming Redaction:** Enable streaming processing for large batch documents (> 50 MB) using asynchronous chunked generators.

---

