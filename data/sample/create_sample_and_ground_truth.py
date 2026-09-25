"""Generates the realistic sample ticket log DOCX file and ground-truth benchmark JSON."""

import json
from pathlib import Path
import re
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

SAMPLE_DIR = Path(__file__).resolve().parent

# Define representative sample texts with known ground truth entities
SAMPLE_DOCUMENTS = [
    {
        "id": "ticket_01_billing_dispute",
        "text": (
            "Ticket ID: TKT-1023 | Priority: High | Department: Customer Support\n"
            "Customer Name: John Doe\n"
            "Email: john.doe@gmail.com\n"
            "Phone: +91 9876543210\n"
            "Company: Acme Corporation\n"
            "Address: 123 Main Street, Suite 400, Seattle, WA 98101\n"
            "DOB: 12/05/1990\n"
            "SSN: 123-45-6789\n"
            "Credit Card: 4111 1111 1111 1111\n"
            "Client IP: 192.168.1.10\n"
            "Details: Customer John Doe reported unauthorized transaction on invoice INV-2026-1001 for Order ID ORD-123456. "
            "Ticket created on 14/03/2026. Non-PII test IP 999.300.1.2 and invalid card 4111 1111 1111 1112 were ignored."
        ),
        "ground_truth": [
            {"type": "PERSON", "text": "John Doe", "start": 84, "end": 92},
            {"type": "EMAIL", "text": "john.doe@gmail.com", "start": 100, "end": 118},
            {"type": "PHONE", "text": "+91 9876543210", "start": 126, "end": 140},
            {"type": "COMPANY", "text": "Acme Corporation", "start": 150, "end": 166},
            {"type": "ADDRESS", "text": "123 Main Street, Suite 400, Seattle, WA 98101", "start": 176, "end": 222},
            {"type": "DOB", "text": "12/05/1990", "start": 228, "end": 238},
            {"type": "SSN", "text": "123-45-6789", "start": 244, "end": 255},
            {"type": "CREDIT_CARD", "text": "4111 1111 1111 1111", "start": 269, "end": 288},
            {"type": "IP_ADDRESS", "text": "192.168.1.10", "start": 300, "end": 312},
            {"type": "PERSON", "text": "John Doe", "start": 331, "end": 339},
        ],
    },
    {
        "id": "ticket_02_account_escalation",
        "text": (
            "Ticket ID: TKT-1024 | Status: Escalated | Queue: Enterprise Billing\n"
            "Client: Rashmi Patil\n"
            "Work Email: rashmi.patil@example.com\n"
            "Contact Number: 9876543210\n"
            "Organization: Global Technologies Ltd.\n"
            "Mailing Address: 42 Park Avenue, Mumbai, Maharashtra 400001\n"
            "Date of Birth: 1985-08-22\n"
            "National ID / SSN: 456-78-1234\n"
            "Active Card: 5555 4444 3333 2222\n"
            "Session IP Address: 10.0.4.15\n"
            "Notes: Employee EMP12345 verified Rashmi Patil credentials on 2026-05-12. Everything verified."
        ),
        "ground_truth": [
            {"type": "PERSON", "text": "Rashmi Patil", "start": 77, "end": 89},
            {"type": "EMAIL", "text": "rashmi.patil@example.com", "start": 102, "end": 126},
            {"type": "PHONE", "text": "9876543210", "start": 143, "end": 153},
            {"type": "COMPANY", "text": "Global Technologies Ltd.", "start": 168, "end": 192},
            {"type": "ADDRESS", "text": "42 Park Avenue, Mumbai, Maharashtra 400001", "start": 210, "end": 252},
            {"type": "DOB", "text": "1985-08-22", "start": 268, "end": 278},
            {"type": "SSN", "text": "456-78-1234", "start": 298, "end": 309},
            {"type": "CREDIT_CARD", "text": "5555 4444 3333 2222", "start": 323, "end": 342},
            {"type": "IP_ADDRESS", "text": "10.0.4.15", "start": 363, "end": 372},
            {"type": "PERSON", "text": "Rashmi Patil", "start": 405, "end": 417},
        ],
    },
    {
        "id": "ticket_03_technical_access",
        "text": (
            "Ticket ID: TKT-1025 | Tier: L2 Infrastructure Support\n"
            "Requester: Alex Mercer\n"
            "Direct Email: alex.mercer@cloudcorp.net\n"
            "Direct Line: +1 (555) 019-2831\n"
            "Employer: Microsoft Corporation\n"
            "Office Address: 15 Maple Street, Apt 4B, Seattle, WA 98101\n"
            "User Born on: 15/08/2002\n"
            "Taxpayer SSN: 219-45-7890\n"
            "Corporate Card: 3782 8224 6310 005\n"
            "Assigned Gateway: 172.16.254.1\n"
            "Comments: Alex Mercer requested firewall port opening for server cluster. Next review on 01/09/2026."
        ),
        "ground_truth": [
            {"type": "PERSON", "text": "Alex Mercer", "start": 65, "end": 76},
            {"type": "EMAIL", "text": "alex.mercer@cloudcorp.net", "start": 91, "end": 116},
            {"type": "PHONE", "text": "+1 (555) 019-2831", "start": 130, "end": 147},
            {"type": "COMPANY", "text": "Microsoft Corporation", "start": 158, "end": 179},
            {"type": "ADDRESS", "text": "15 Maple Street, Apt 4B, Seattle, WA 98101", "start": 196, "end": 238},
            {"type": "DOB", "text": "15/08/2002", "start": 253, "end": 263},
            {"type": "SSN", "text": "219-45-7890", "start": 278, "end": 289},
            {"type": "CREDIT_CARD", "text": "3782 8224 6310 005", "start": 306, "end": 324},
            {"type": "IP_ADDRESS", "text": "172.16.254.1", "start": 343, "end": 355},
            {"type": "PERSON", "text": "Alex Mercer", "start": 366, "end": 377},
        ],
    },
]


def verify_and_compute_ground_truth():
    """Compute and verify exact character offsets for ground truth annotations."""
    for doc in SAMPLE_DOCUMENTS:
        text = doc["text"]
        for g in doc["ground_truth"]:
            target = g["text"]
            # Search for occurrence
            # In cases of multiple occurrences (e.g. repeated person name),
            # find all occurrences and select the one closest to original or by count
            occ = [m.start() for m in re.finditer(re.escape(target), text)]
            if not occ:
                raise ValueError(f"Could not find target '{target}' in {doc['id']}")
            
            # Find best matching occurrence
            best_start = min(occ, key=lambda s: abs(s - g["start"]))
            g["start"] = best_start
            g["end"] = best_start + len(target)
            assert text[g["start"]:g["end"]] == target, f"Mismatch: '{text[g['start']:g['end']]}' != '{target}'"
    print("All ground-truth offsets successfully computed and verified!")



def create_docx_file():
    """Build a professional, realistic DOCX ticket log document containing paragraphs, lists, and tables."""
    doc = Document()

    # Document Title
    title = doc.add_heading("Customer Support & IT Service Ticket Log", level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Subtitle / Metadata
    p_meta = doc.add_paragraph()
    p_meta.add_run("Classification: Internal Confidential Document\n").bold = True
    p_meta.add_run("System: SupportTrack Enterprise Incident Management (v4.2.1)\n")
    p_meta.add_run("Generated Date: 2026-03-25 | Review Frequency: Quarterly\n")

    doc.add_heading("1. Executive Summary & Incident Notes", level=1)
    p_intro = doc.add_paragraph(
        "This ticket log records customer account modifications, billing disputes, and technical support "
        "requests collected across our global service portals. Each entry contains customer details, "
        "network access traces, and transaction records requiring compliance with privacy regulations."
    )

    doc.add_heading("2. Support Case Logs", level=1)

    for item in SAMPLE_DOCUMENTS:
        doc.add_heading(f"Case Record: {item['id'].upper()}", level=2)
        lines = item["text"].split("\n")
        for line in lines:
            p = doc.add_paragraph()
            if ":" in line:
                key, val = line.split(":", 1)
                p.add_run(f"{key}:").bold = True
                p.add_run(val)
            else:
                p.add_run(line)

    doc.add_heading("3. Structured Incident Summary Table", level=1)
    doc.add_paragraph(
        "The following table summarizes active accounts and verification details for cross-departmental auditing:"
    )

    # Add Table
    table = doc.add_table(rows=1, cols=6)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"

    hdr_cells = table.rows[0].cells
    headers = ["Ticket ID", "Customer Name", "Contact Email", "Phone Number", "Company", "Client IP"]
    for i, h in enumerate(headers):
        hdr_cells[i].text = h
        hdr_cells[i].paragraphs[0].runs[0].bold = True

    table_data = [
        ("TKT-1023", "John Doe", "john.doe@gmail.com", "+91 9876543210", "Acme Corporation", "192.168.1.10"),
        ("TKT-1024", "Rashmi Patil", "rashmi.patil@example.com", "9876543210", "Global Technologies Ltd.", "10.0.4.15"),
        ("TKT-1025", "Alex Mercer", "alex.mercer@cloudcorp.net", "+1 (555) 019-2831", "Microsoft Corporation", "172.16.254.1"),
    ]

    for row_data in table_data:
        row_cells = table.add_row().cells
        for i, val in enumerate(row_data):
            row_cells[i].text = val

    doc.add_heading("4. Non-PII Operational Identifiers & Reference Data", level=1)
    p_non_pii = doc.add_paragraph(
        "For compliance verification, ensure that standard system identifiers are not incorrectly redacted:\n"
        "- Hardware Asset Tags: EMP12345, EMP99882\n"
        "- Billing Invoices: INV-2026-1001, INV-2026-1002\n"
        "- E-Commerce Orders: ORD-123456, ORD-789012\n"
        "- Incident Codes: INC-404, TKT-9999\n"
        "- Broadcast & Netmask: 255.255.255.0, 127.0.0.1\n"
        "- System Release Date: 12 May 2024 (Non-DOB event)\n"
    )

    docx_path = SAMPLE_DIR / "sample_ticket_document.docx"
    doc.save(str(docx_path))
    print(f"Generated sample DOCX file at: {docx_path}")


def save_ground_truth_json():
    """Save the ground truth dataset to JSON."""
    gt_path = SAMPLE_DIR / "ground_truth.json"
    data = {
        "description": "Benchmark evaluation dataset for PII Redaction Tool containing support ticket logs.",
        "version": "1.0.0",
        "documents": SAMPLE_DOCUMENTS,
    }
    with open(gt_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"Generated ground truth JSON at: {gt_path}")


if __name__ == "__main__":
    verify_and_compute_ground_truth()
    create_docx_file()
    save_ground_truth_json()
