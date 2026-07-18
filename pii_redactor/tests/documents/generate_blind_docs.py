"""Generate blind validation documents.

These are unseen documents to test generalization of the PII detectors.
They contain PII that is NOT present in the synthetic training documents.
"""

import json
import sys
from pathlib import Path

from docx import Document
from docx.shared import Pt

OUTPUT_DIR = Path(__file__).parent


BLIND_DOCUMENTS = {
    "employment_contract": {
        "filename": "blind_employment_001.docx",
        "content": (
            "EMPLOYMENT CONTRACT\n\n"
            "This contract is made between:\n"
            "Employer: Bharat Heavy Electricals Limited (BHEL)\n"
            "Registered Office: BHEL House, Siri Fort, New Delhi 110016\n\n"
            "Employee: Sanjay Kulkarni\n"
            "Date of Birth: 25 December 1987\n"
            "Address: 15 Aundh Road, Pune 411007\n"
            "Email: sanjay.kulkarni@bhel.com\n"
            "Phone: +91 98234 56789\n\n"
            "1. POSITION\n\n"
            "The Employee is appointed as Senior Engineer.\n"
            "Start Date: 01 July 2024\n\n"
            "2. COMPENSATION\n\n"
            "Annual Salary: Rs. 1200000\n"
            "Medical Insurance: Provided\n\n"
            "3. CONFIDENTIALITY\n\n"
            "The Employee agrees to maintain confidentiality.\n"
            "This contract is governed by Indian law.\n\n"
            "Signed on 20 June 2024\n\n"
            "For BHEL:\n"
            "Director: Priya Raghavan\n"
            "Email: priya.raghavan@bhel.com\n"
        ),
        "ground_truth": [
            {"text": "Bharat Heavy Electricals Limited", "type": "company"},
            {"text": "BHEL", "type": "company"},
            {"text": "BHEL House, Siri Fort, New Delhi 110016", "type": "address"},
            {"text": "Sanjay Kulkarni", "type": "person"},
            {"text": "25 December 1987", "type": "date"},
            {"text": "15 Aundh Road, Pune 411007", "type": "address"},
            {"text": "sanjay.kulkarni@bhel.com", "type": "email"},
            {"text": "+91 98234 56789", "type": "phone"},
            {"text": "01 July 2024", "type": "date"},
            {"text": "20 June 2024", "type": "date"},
            {"text": "Priya Raghavan", "type": "person"},
            {"text": "priya.raghavan@bhel.com", "type": "email"},
        ],
    },
    "medical_report": {
        "filename": "blind_medical_002.docx",
        "content": (
            "MEDICAL REPORT\n\n"
            "Patient: Meena Iyer\n"
            "Date of Birth: 03 August 1992\n"
            "Patient ID: MED-2024-5678\n"
            "Phone: 022 2345 6789\n"
            "Email: meena.iyer@email.com\n\n"
            "Hospital: Apollo Hospitals Enterprise Ltd\n"
            "Address: 21 Greams Road, Chennai 600006\n\n"
            "Date of Visit: 10 March 2024\n"
            "Doctor: Dr. Venkatesh Rao\n"
            "Specialization: Cardiology\n\n"
            "FINDINGS:\n"
            "Blood Pressure: 120/80 mmHg\n"
            "Heart Rate: 72 bpm\n"
            "Cholesterol: 190 mg/dL\n\n"
            "RECOMMENDATION:\n"
            "Follow-up appointment on 10 April 2024.\n"
            "Regular exercise recommended.\n\n"
            "Dr. Venkatesh Rao\n"
            "Apollo Hospitals Enterprise Ltd\n"
            "Email: dr.venkatesh@apollohospitals.com\n"
            "Phone: +91 44 2829 3333\n"
        ),
        "ground_truth": [
            {"text": "Meena Iyer", "type": "person"},
            {"text": "03 August 1992", "type": "date"},
            {"text": "meena.iyer@email.com", "type": "email"},
            {"text": "022 2345 6789", "type": "phone"},
            {"text": "Apollo Hospitals Enterprise Ltd", "type": "company"},
            {"text": "21 Greams Road, Chennai 600006", "type": "address"},
            {"text": "10 March 2024", "type": "date"},
            {"text": "10 April 2024", "type": "date"},
            {"text": "Venkatesh Rao", "type": "person"},
            {"text": "dr.venkatesh@apollohospitals.com", "type": "email"},
            {"text": "+91 44 2829 3333", "type": "phone"},
        ],
    },
    "vendor_agreement": {
        "filename": "blind_vendor_003.docx",
        "content": (
            "VENDOR SERVICE AGREEMENT\n\n"
            "Date: 15 May 2024\n\n"
            "Party A: Zomato Limited\n"
            "Address: Tower C, DLF Cyber City, Gurugram 122002\n"
            "Contact: Nisha Aggarwal\n"
            "Email: nisha.aggarwal@zomato.com\n"
            "Phone: +91 98111 22233\n\n"
            "Party B: FreshCart Solutions Pvt. Ltd.\n"
            "Address: 42 Koramangala, Bengaluru 560034\n"
            "Contact: Kiran Bhat\n"
            "Email: kiran.bhat@freshcart.in\n"
            "Phone: 080 2555 6677\n\n"
            "SCOPE:\n"
            "Party B will supply fresh produce to Party A.\n"
            "Contract Duration: 01 June 2024 to 31 May 2025.\n\n"
            "PAYMENT TERMS:\n"
            "Net 30 days from invoice date.\n"
            "GSTIN: 07ZZZZ1234F1Z5\n\n"
            "For Zomato Limited:\n"
            "Name: Aditya Malhotra, VP Operations\n"
            "Date: 15 May 2024\n\n"
            "For FreshCart Solutions:\n"
            "Name: Kiran Bhat, Managing Director\n"
            "Date: 15 May 2024\n"
        ),
        "ground_truth": [
            {"text": "15 May 2024", "type": "date"},
            {"text": "Zomato Limited", "type": "company"},
            {"text": "Tower C, DLF Cyber City, Gurugram 122002", "type": "address"},
            {"text": "Nisha Aggarwal", "type": "person"},
            {"text": "nisha.aggarwal@zomato.com", "type": "email"},
            {"text": "+91 98111 22233", "type": "phone"},
            {"text": "FreshCart Solutions Pvt. Ltd.", "type": "company"},
            {"text": "42 Koramangala, Bengaluru 560034", "type": "address"},
            {"text": "Kiran Bhat", "type": "person"},
            {"text": "kiran.bhat@freshcart.in", "type": "email"},
            {"text": "080 2555 6677", "type": "phone"},
            {"text": "01 June 2024", "type": "date"},
            {"text": "31 May 2025", "type": "date"},
            {"text": "Aditya Malhotra", "type": "person"},
        ],
    },
    "tax_notice": {
        "filename": "blind_tax_004.docx",
        "content": (
            "INCOME TAX ASSESSMENT ORDER\n\n"
            "PAN: BCRPS1234M\n"
            "Assessment Year: 2024-25\n"
            "Name: Suresh Pillai\n"
            "Address: 8 Marine Drive, Kochi 682031\n"
            "Date of Birth: 17 November 1979\n"
            "Email: suresh.pillai@gmail.com\n"
            "Phone: +91 94444 55566\n\n"
            "INCOME DETAILS:\n"
            "Salary Income: Rs. 1500000\n"
            "Interest Income: Rs. 45000\n"
            "Total Income: Rs. 1545000\n\n"
            "TAX COMPUTED:\n"
            "Tax on Total Income: Rs. 195000\n"
            "Less: TDS: Rs. 180000\n"
            "Tax Payable: Rs. 15000\n\n"
            "Date of Order: 25 March 2024\n"
            "Assessing Officer: Kavitha Nair\n"
            "Circle: Circle-3(1), Kochi\n\n"
            "This order is passed under Section 143(3).\n"
            "Contact: kavitha.nair@incometax.gov.in\n"
        ),
        "ground_truth": [
            {"text": "Suresh Pillai", "type": "person"},
            {"text": "8 Marine Drive, Kochi 682031", "type": "address"},
            {"text": "17 November 1979", "type": "date"},
            {"text": "suresh.pillai@gmail.com", "type": "email"},
            {"text": "+91 94444 55566", "type": "phone"},
            {"text": "25 March 2024", "type": "date"},
            {"text": "Kavitha Nair", "type": "person"},
            {"text": "kavitha.nair@incometax.gov.in", "type": "email"},
        ],
    },
    "partnership_deed": {
        "filename": "blind_partnership_005.docx",
        "content": (
            "PARTNERSHIP DEED\n\n"
            "This Partnership Deed is entered into on 01 September 2024\n"
            "between the following Partners:\n\n"
            "Partner 1: Arun Sharma\n"
            "Address: 23 Nehru Nagar, Jaipur 302001\n"
            "Email: arun.sharma@gmail.com\n"
            "Phone: +91 99887 11223\n"
            "Date of Birth: 05 February 1983\n\n"
            "Partner 2: Deepika Chopra\n"
            "Address: 67 Civil Lines, Lucknow 226001\n"
            "Email: deepika.chopra@yahoo.com\n"
            "Phone: 0522 234 5678\n"
            "Date of Birth: 12 September 1986\n\n"
            "FIRM NAME: Sharma & Chopra Consultants\n"
            "DATE OF FORMATION: 01 September 2024\n"
            "ADDRESS OF FIRM: 23 Nehru Nagar, Jaipur 302001\n\n"
            "1. PROFIT SHARING RATIO\n\n"
            "Partner 1: 60%\n"
            "Partner 2: 40%\n\n"
            "2. DURATION\n\n"
            "The partnership shall continue for 5 years.\n"
            "End Date: 31 August 2029.\n\n"
            "Signed by:\n"
            "Arun Sharma (Date: 01 September 2024)\n"
            "Deepika Chopra (Date: 01 September 2024)\n"
        ),
        "ground_truth": [
            {"text": "01 September 2024", "type": "date"},
            {"text": "Arun Sharma", "type": "person"},
            {"text": "23 Nehru Nagar, Jaipur 302001", "type": "address"},
            {"text": "arun.sharma@gmail.com", "type": "email"},
            {"text": "+91 99887 11223", "type": "phone"},
            {"text": "05 February 1983", "type": "date"},
            {"text": "Deepika Chopra", "type": "person"},
            {"text": "67 Civil Lines, Lucknow 226001", "type": "address"},
            {"text": "deepika.chopra@yahoo.com", "type": "email"},
            {"text": "0522 234 5678", "type": "phone"},
            {"text": "12 September 1986", "type": "date"},
            {"text": "31 August 2029", "type": "date"},
        ],
    },
}


def generate_blind_documents(output_dir: Path) -> None:
    """Generate all blind validation documents."""
    output_dir.mkdir(parents=True, exist_ok=True)
    metadata = {}

    for doc_id, doc_info in BLIND_DOCUMENTS.items():
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

    gt_path = output_dir / "blind_ground_truth.json"
    with open(gt_path, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"\nBlind ground truth saved: {gt_path}")
    print(f"Generated {len(metadata)} blind validation documents.")


if __name__ == "__main__":
    print("Generating blind validation documents...")
    generate_blind_documents(OUTPUT_DIR)
