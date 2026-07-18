"""Synthetic DOCX generator for evaluation.

Generates realistic test documents with known PII entities embedded.
Each document type simulates a different real-world scenario.
"""

import json
import sys
from pathlib import Path

from docx import Document
from docx.shared import Pt

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

OUTPUT_DIR = Path(__file__).parent


# ---------------------------------------------------------------------------
# Document templates with known PII ground truth
# ---------------------------------------------------------------------------

DOCUMENTS = {
    "resume": {
        "filename": "resume_001.docx",
        "content": (
            "RESUME\n\n"
            "Name: Rahul Sharma\n"
            "Email: rahul.sharma@gmail.com\n"
            "Phone: +91 98765 43210\n"
            "Date of Birth: 15 March 1990\n"
            "Address: 42 MG Road, Mumbai 400001\n\n"
            "EXPERIENCE\n\n"
            "Software Engineer at Infosys Limited (June 2015 - Present)\n"
            "Developed enterprise applications using Python and Java.\n"
            "Worked at Tata Consultancy Services Pvt. Ltd. (Jan 2013 - May 2015).\n\n"
            "EDUCATION\n\n"
            "B.Tech from Indian Institute of Technology, Mumbai (2009 - 2013)\n\n"
            "REFERENCES\n\n"
            "Contact Person: Priya Verma, HR Manager at Wipro Ltd\n"
            "Email: priya.verma@wipro.com\n"
            "Phone: +91 87654 32109\n"
        ),
        "ground_truth": [
            {"text": "Rahul Sharma", "type": "person"},
            {"text": "rahul.sharma@gmail.com", "type": "email"},
            {"text": "+91 98765 43210", "type": "phone"},
            {"text": "15 March 1990", "type": "date"},
            {"text": "42 MG Road, Mumbai 400001", "type": "address"},
            {"text": "Infosys Limited", "type": "company"},
            {"text": "Tata Consultancy Services Pvt. Ltd.", "type": "company"},
            {"text": "Indian Institute of Technology", "type": "company"},
            {"text": "Priya Verma", "type": "person"},
            {"text": "Wipro Ltd", "type": "company"},
            {"text": "priya.verma@wipro.com", "type": "email"},
            {"text": "+91 87654 32109", "type": "phone"},
        ],
    },
    "bank_statement": {
        "filename": "bank_statement_002.docx",
        "content": (
            "HDFC BANK LIMITED\n"
            "Account Statement\n\n"
            "Account Holder: Vikram Singh\n"
            "Account Number: 50100123456789\n"
            "IFSC: HDFC0001234\n\n"
            "Registered Address: 15 Park Street, Kolkata 700016\n"
            "Date of Birth: 22 July 1985\n"
            "Email: vikram.singh@hdfcbank.com\n"
            "Phone: +91 99887 76655\n\n"
            "TRANSACTION DETAILS\n\n"
            "Date: 01 January 2024 - Amount: Rs. 50000\n"
            "Date: 15 February 2024 - Amount: Rs. 75000\n"
            "Contact Person for queries: Ananya Desai\n"
            "Support Email: support@hdfcbank.com\n"
            "Helpline: 022 2409 4400\n\n"
            "This statement is generated on 18 March 2024.\n"
            "HDFC Bank Limited, Registered Office: HDFC Bank House,\n"
            "Near BKC, Mumbai 400051\n"
        ),
        "ground_truth": [
            {"text": "HDFC BANK LIMITED", "type": "company"},
            {"text": "HDFC Bank Limited", "type": "company"},
            {"text": "Vikram Singh", "type": "person"},
            {"text": "50100123456789", "type": "national_id"},
            {"text": "15 Park Street, Kolkata 700016", "type": "address"},
            {"text": "22 July 1985", "type": "date"},
            {"text": "vikram.singh@hdfcbank.com", "type": "email"},
            {"text": "+91 99887 76655", "type": "phone"},
            {"text": "01 January 2024", "type": "date"},
            {"text": "15 February 2024", "type": "date"},
            {"text": "18 March 2024", "type": "date"},
            {"text": "Ananya Desai", "type": "person"},
            {"text": "support@hdfcbank.com", "type": "email"},
            {"text": "022 2409 4400", "type": "phone"},
            {"text": "HDFC Bank House", "type": "address"},
        ],
    },
    "legal_agreement": {
        "filename": "legal_agreement_003.docx",
        "content": (
            "NON-DISCLOSURE AGREEMENT\n\n"
            "This Agreement is entered into on 01 April 2024\n"
            "between KSH International Limited (\"Company\")\n"
            "and Rajesh Kumar (\"Employee\").\n\n"
            "1. DEFINITIONS\n\n"
            "\"Confidential Information\" means any information disclosed\n"
            "by the Company to the Employee.\n\n"
            "2. OBLIGATIONS\n\n"
            "The Employee shall not disclose any Confidential Information.\n"
            "The Employee's address: 78 Civil Lines, Delhi 110001\n"
            "The Employee's email: rajesh.kumar@kshintl.com\n"
            "The Employee's phone: +91 98765 12345\n\n"
            "3. TERM\n\n"
            "This Agreement shall be effective from 01 April 2024\n"
            "to 31 March 2025.\n\n"
            "4. GOVERNING LAW\n\n"
            "This Agreement shall be governed by the laws of India.\n"
            "Disputes shall be resolved in Mumbai courts.\n\n"
            "Signed by:\n"
            "For KSH International Limited:\n"
            "Name: Sunil Mehta, Director\n"
            "Email: sunil.mehta@kshintl.com\n"
            "Phone: +91 22 2654 3210\n\n"
            "Employee:\n"
            "Name: Rajesh Kumar\n"
            "Date of Birth: 10 October 1988\n"
            "PAN: ABCPK1234R\n"
        ),
        "ground_truth": [
            {"text": "01 April 2024", "type": "date"},
            {"text": "31 March 2025", "type": "date"},
            {"text": "KSH International Limited", "type": "company"},
            {"text": "Rajesh Kumar", "type": "person"},
            {"text": "78 Civil Lines, Delhi 110001", "type": "address"},
            {"text": "rajesh.kumar@kshintl.com", "type": "email"},
            {"text": "+91 98765 12345", "type": "phone"},
            {"text": "01 April 2024", "type": "date"},
            {"text": "31 March 2025", "type": "date"},
            {"text": "Sunil Mehta", "type": "person"},
            {"text": "sunil.mehta@kshintl.com", "type": "email"},
            {"text": "+91 22 2654 3210", "type": "phone"},
            {"text": "10 October 1988", "type": "date"},
        ],
    },
    "invoice": {
        "filename": "invoice_004.docx",
        "content": (
            "TAX INVOICE\n\n"
            "Invoice Number: INV-2024-001\n"
            "Date: 15 March 2024\n\n"
            "From:\n"
            "Larsen & Toubro Ltd\n"
            "Office: L&T House, N.M. Marg, Ballard Estate\n"
            "Mumbai 400001\n"
            "GSTIN: 27AABCL1234F1Z5\n"
            "Email: billing@larsentoubro.com\n"
            "Phone: 022 6752 5678\n\n"
            "To:\n"
            "Mahindra & Mahindra Limited\n"
            "Gateway Building, Apollo Bunder\n"
            "Mumbai 400005\n"
            "Contact Person: Amit Patel\n"
            "Email: amit.patel@mahindra.com\n"
            "Phone: +91 98765 87654\n\n"
            "ITEMS:\n"
            "1. Engineering Consultancy - Rs. 500000\n"
            "2. Project Management - Rs. 250000\n"
            "3. Technical Support - Rs. 100000\n\n"
            "Total: Rs. 850000\n\n"
            "Payment due within 30 days of invoice date.\n"
            "For queries contact: accounts@larsentoubro.com\n"
        ),
        "ground_truth": [
            {"text": "15 March 2024", "type": "date"},
            {"text": "Larsen & Toubro Ltd", "type": "company"},
            {"text": "L&T House, N.M. Marg, Ballard Estate Mumbai 400001", "type": "address"},
            {"text": "billing@larsentoubro.com", "type": "email"},
            {"text": "022 6752 5678", "type": "phone"},
            {"text": "Mahindra & Mahindra Limited", "type": "company"},
            {"text": "Gateway Building, Apollo Bunder Mumbai 400005", "type": "address"},
            {"text": "Amit Patel", "type": "person"},
            {"text": "amit.patel@mahindra.com", "type": "email"},
            {"text": "+91 98765 87654", "type": "phone"},
            {"text": "accounts@larsentoubro.com", "type": "email"},
        ],
    },
    "meeting_minutes": {
        "filename": "meeting_minutes_005.docx",
        "content": (
            "BOARD MEETING MINUTES\n\n"
            "Company: ITC Limited\n"
            "Date of Meeting: 20 March 2024\n"
            "Time: 10:00 AM\n"
            "Venue: ITC Green Centre, Gurugram\n\n"
            "Attendees:\n"
            "1. Chairman: Ravi Shankar Prasad\n"
            "2. Director: Meera Nair\n"
            "3. CFO: Arun Kumar\n"
            "4. Company Secretary: Deepa Joshi\n\n"
            "AGENDA:\n\n"
            "1. Approval of previous meeting minutes (15 January 2024)\n"
            "2. Financial review for Q3 FY2024\n"
            "3. New product launch discussion\n"
            "4. Any other matter\n\n"
            "DISCUSSION:\n\n"
            "The Chairman welcomed all attendees.\n"
            "The CFO presented the financial results.\n"
            "Revenue for Q3: Rs. 16500 Crore\n"
            "Net Profit: Rs. 1850 Crore\n\n"
            "DECISIONS:\n\n"
            "1. Previous minutes approved.\n"
            "2. New product to be launched by 01 June 2024.\n"
            "3. Budget allocation: Rs. 500 Crore for marketing.\n\n"
            "Next meeting: 15 April 2024\n"
            "Contact for minutes: deepa.joshi@itc.in\n"
            "Phone: +91 124 456 7890\n"
        ),
        "ground_truth": [
            {"text": "ITC Limited", "type": "company"},
            {"text": "20 March 2024", "type": "date"},
            {"text": "Ravi Shankar Prasad", "type": "person"},
            {"text": "Meera Nair", "type": "person"},
            {"text": "Arun Kumar", "type": "person"},
            {"text": "Deepa Joshi", "type": "person"},
            {"text": "15 January 2024", "type": "date"},
            {"text": "01 June 2024", "type": "date"},
            {"text": "15 April 2024", "type": "date"},
            {"text": "deepa.joshi@itc.in", "type": "email"},
            {"text": "+91 124 456 7890", "type": "phone"},
        ],
    },
}


def generate_documents(output_dir: Path) -> list[dict]:
    """Generate all synthetic DOCX documents with ground truth."""
    output_dir.mkdir(parents=True, exist_ok=True)
    metadata = {}

    for doc_id, doc_info in DOCUMENTS.items():
        doc = Document()
        style = doc.styles["Normal"]
        style.font.size = Pt(11)

        for line in doc_info["content"].split("\n"):
            doc.add_paragraph(line)

        filepath = output_dir / doc_info["filename"]
        doc.save(str(filepath))

        metadata[doc_id] = {
            "filename": doc_info["filename"],
            "ground_truth": doc_info["ground_truth"],
        }

        print(f"Generated: {filepath.name}")

    return metadata


def save_ground_truth(metadata: dict, output_dir: Path) -> None:
    """Save ground truth labels as JSON."""
    gt_path = output_dir / "ground_truth.json"
    with open(gt_path, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"Ground truth saved: {gt_path}")


if __name__ == "__main__":
    print("Generating synthetic DOCX documents...")
    metadata = generate_documents(OUTPUT_DIR)
    save_ground_truth(metadata, OUTPUT_DIR)
    print(f"\nGenerated {len(metadata)} documents with ground truth labels.")
