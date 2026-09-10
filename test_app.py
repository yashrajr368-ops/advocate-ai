import os
import io
import unittest
from app import app, db
from models import User, Case, AIReport, Document, Appointment, CaseTimeline

class AIAvocateTestSuite(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        self.client = app.test_client()

    def test_01_home_page(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Adv. Mukesh Singh Rathod", res.data)
        self.assertIn(b"Ask AI Legal Assistant", res.data)
        self.assertIn(b"Book Consultation", res.data)
        print("[PASS] Home page loaded with lead counsel Advocate Mukesh Singh Rathod and all triage sections.")

    def test_02_ai_chatbot_legal_query(self):
        res = self.client.post("/ask", json={
            "question": "What is the procedure for Section 138 cheque bounce in India?"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("answer", data)
        self.assertIn("Case Type", data["answer"])
        self.assertIn("Applicable Laws", data["answer"])
        print("[PASS] AI Chatbot legal query returned structured response.")

    def test_03_ai_chatbot_guardrail_refusal(self):
        res = self.client.post("/ask", json={
            "question": "How do I make chocolate cake?"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("Notice from AI Advocate", data["answer"])
        print("[PASS] AI Chatbot non-legal query was politely declined by guardrail.")

    def test_04_client_login_and_dashboard(self):
        res = self.client.post("/login", data={
            "email": "client@example.com",
            "password": "password123"
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Client Dashboard", res.data)
        self.assertIn(b"Total Cases", res.data)
        self.assertIn(b"Pending Cases", res.data)
        print("[PASS] Client logged in and accessed client dashboard.")

    def test_05_add_case_with_ai_analysis(self):
        # Login client
        self.client.post("/login", data={"email": "client@example.com", "password": "password123"})
        
        # Add new case
        res = self.client.post("/add_case", data={
            "client_name": "Sunil Mehra",
            "email": "client@example.com",
            "phone": "+91 97222 33445",
            "category": "Cyber Crime",
            "title": "Phishing email stole Rs 75,000 via fake lottery claim",
            "priority": "High",
            "description": "Client clicked an email purporting to be from RBI lottery asking for 75,000 processing fee. Sent via UPI to scammer."
        }, follow_redirects=True)
        
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Gemini AI Legal Intelligence", res.data)
        self.assertIn(b"Case Summary", res.data)
        self.assertIn(b"Relevant IPC / BNS Sections", res.data)
        print("[PASS] New case submitted and automatic AI legal analysis generated successfully.")

    def test_06_document_upload_and_download(self):
        # Login client
        self.client.post("/login", data={"email": "client@example.com", "password": "password123"})
        
        with app.app_context():
            c = Case.query.filter_by(email="client@example.com").first()
            case_id = c.id
        
        # Upload a dummy file
        fake_file = (io.BytesIO(b"Fake PDF evidentiary document content"), "sample_evidence.pdf")
        res = self.client.post("/upload_document", data={
            "case_id": str(case_id),
            "document": fake_file
        }, content_type="multipart/form-data", follow_redirects=True)
        
        self.assertEqual(res.status_code, 200)
        
        with app.app_context():
            doc = Document.query.filter_by(case_id=case_id).first()
            self.assertIsNotNone(doc)
            self.assertEqual(doc.original_filename, "sample_evidence.pdf")
            saved_name = doc.filename
        
        # Test download
        down_res = self.client.get(f"/uploads/{saved_name}")
        self.assertEqual(down_res.status_code, 200)
        self.assertEqual(down_res.data, b"Fake PDF evidentiary document content")
        print("[PASS] Document uploaded, database linked, and downloaded successfully.")

    def test_07_advocate_dashboard_and_case_update(self):
        # Login advocate
        res = self.client.post("/login", data={
            "email": "advocate@example.com",
            "password": "password123"
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Adv. Mukesh Singh Rathod Chambers", res.data)
        self.assertIn(b"Total Cases", res.data)
        self.assertIn(b"Total Clients", res.data)

        # Update case status & advocate notes
        with app.app_context():
            c = Case.query.first()
            case_id = c.id

        update_res = self.client.post(f"/update_case/{case_id}", data={
            "status": "In Progress",
            "advocate_notes": "Statutory notice drafted and dispatched under registered post."
        }, follow_redirects=True)

        self.assertEqual(update_res.status_code, 200)
        self.assertIn(b"Case status and advocate strategy notes saved successfully", update_res.data)
        
        with app.app_context():
            updated_c = db.session.get(Case, case_id)
            self.assertEqual(updated_c.status, "In Progress")
            self.assertIn("Statutory notice drafted", updated_c.advocate_notes)
        print("[PASS] Advocate dashboard accessed and case status updated successfully.")

    def test_08_printable_case_report(self):
        self.client.post("/login", data={"email": "advocate@example.com", "password": "password123"})
        with app.app_context():
            c = Case.query.first()
            case_id = c.id

        res = self.client.get(f"/case/{case_id}/report")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"CHAMBERS OF ADVOCATE MUKESH SINGH RATHOD", res.data)
        self.assertIn(b"MEMORANDUM OF CASE", res.data)
        self.assertIn(b"Applicable Indian Statutes", res.data)
        print("[PASS] Printable / PDF Case Report view rendered with court formatting.")

    def test_09_appointment_booking(self):
        res = self.client.post("/book_appointment", data={
            "client_name": "Meera Verma",
            "email": "meera@example.com",
            "phone": "+91 98888 77777",
            "category": "Property Disputes",
            "appointment_date": "2026-09-15",
            "appointment_time": "02:00 PM - 03:00 PM",
            "notes": "Title verification for commercial shop purchase."
        }, follow_redirects=True)

        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Appointment confirmed", res.data)
        
        with app.app_context():
            app_rec = Appointment.query.filter_by(email="meera@example.com").first()
            self.assertIsNotNone(app_rec)
            self.assertEqual(app_rec.appointment_time, "02:00 PM - 03:00 PM")
        print("[PASS] Appointment booking and simulated confirmation email completed.")

    def test_10_admin_dashboard(self):
        self.client.post("/login", data={"email": "admin@example.com", "password": "password123"})
        res = self.client.get("/admin_dashboard")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Root Administration", res.data)
        self.assertIn(b"User Management", res.data)
        self.assertIn(b"Cases Administration", res.data)
        print("[PASS] Admin dashboard loaded with system analytics and user controls.")

if __name__ == "__main__":
    unittest.main()
