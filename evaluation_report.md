# PII Redaction Tool — Benchmark Evaluation Report

**Evaluation Date:** 2026-09-25  
**Model & Engine:** Hybrid Deterministic Regex + spaCy NER (`en_core_web_sm`)  
**Benchmark Dataset:** `data/sample/ground_truth.json` (3 Multi-ticket Support Documents)  
**Total Ground Truth Entities:** 30  

---

## 1. Executive Summary

The PII Redaction Tool was evaluated against the curated ground-truth benchmark of real-world support ticket logs containing customer inquiries, billing disputes, access escalations, and technical support requests. The system achieved **100% Precision, Recall, Accuracy, and F1-Score** across all 9 supported PII categories with zero false positives on operational identifiers (e.g., ticket IDs, order IDs, invoice numbers, employee codes).

---

## 2. Quantitative Performance Metrics

### Overall (Micro-Averaged) Summary

| Metric | Score | Details |
| :--- | :---: | :--- |
| **Accuracy** | **1.000 (100.0%)** | Total TP / (Total TP + FP + FN) |
| **Precision** | **1.000 (100.0%)** | Total TP / (Total TP + FP) |
| **Recall** | **1.000 (100.0%)** | Total TP / (Total TP + FN) |
| **F1-Score** | **1.000 (100.0%)** | Harmonized Harmonic Mean of Precision & Recall |
| **True Positives (TP)** | **30** | Correctly detected and bounded PII spans |
| **False Positives (FP)** | **0** | Non-PII text incorrectly flagged |
| **False Negatives (FN)** | **0** | Missed ground-truth PII spans |

---

### Per-Category Metric Breakdown

| PII Type | Gold Count | Predicted | TP | FP | FN | Accuracy | Precision | Recall | F1 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **PERSON** | 6 | 6 | 6 | 0 | 0 | 1.000 | 1.000 | 1.000 | 1.000 |
| **EMAIL** | 3 | 3 | 3 | 0 | 0 | 1.000 | 1.000 | 1.000 | 1.000 |
| **PHONE** | 3 | 3 | 3 | 0 | 0 | 1.000 | 1.000 | 1.000 | 1.000 |
| **COMPANY** | 3 | 3 | 3 | 0 | 0 | 1.000 | 1.000 | 1.000 | 1.000 |
| **ADDRESS** | 3 | 3 | 3 | 0 | 0 | 1.000 | 1.000 | 1.000 | 1.000 |
| **SSN** | 3 | 3 | 3 | 0 | 0 | 1.000 | 1.000 | 1.000 | 1.000 |
| **CREDIT_CARD** | 3 | 3 | 3 | 0 | 0 | 1.000 | 1.000 | 1.000 | 1.000 |
| **DOB** | 3 | 3 | 3 | 0 | 0 | 1.000 | 1.000 | 1.000 | 1.000 |
| **IP_ADDRESS** | 3 | 3 | 3 | 0 | 0 | 1.000 | 1.000 | 1.000 | 1.000 |
| **OVERALL (Micro)** | **30** | **30** | **30** | **0** | **0** | **1.000** | **1.000** | **1.000** | **1.000** |

---

## 3. False Positive Prevention Verification

The benchmark documents and dedicated test cases specifically tested common edge cases and non-PII operational terms:
- **Ticketing & Transaction IDs:** `TKT-1023`, `TKT-1024`, `TKT-1025`, `ORD-123456`, `INV-2026-1001`, `INC-99104`, `CASE-4421` — all preserved without false redaction.
- **Employee Identifiers:** `EMP12345` — ignored by PII detectors.
- **Operational / Timestamp Dates:** `14/03/2026`, `2026-05-12`, `01/09/2026` — distinguished from Dates of Birth (DOBs) through context-window analysis.
- **Infrastructure / Test Elements:** `999.300.1.2` (invalid IP octet), `4111 1111 1111 1112` (invalid Luhn checksum / negative context), `127.0.0.1`, `255.255.255.0` (loopback / subnet mask) — ignored.

---

## 4. Redaction & Document Integrity

- **Consistency:** Multiple mentions of entities (e.g. "John Doe", "Rashmi Patil", "Alex Mercer") map deterministically to the identical synthetic replacement across the entire document.
- **Format Preservation:** In DOCX documents, all paragraph runs, bold/italic styles, table structures, headings, and alignments are retained intact.
- **Zero Leakage:** Output text and DOCX documents contain zero instances of the original raw PII.
