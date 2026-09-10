from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

# ==========================================
# User Table
# ==========================================
class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(30), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    user_type = db.Column(db.String(30), nullable=False, default="Client")  # Client, Advocate, Admin
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    cases = db.relationship("Case", backref="client", lazy=True, cascade="all, delete-orphan")
    documents = db.relationship("Document", backref="uploader", lazy=True, cascade="all, delete-orphan")
    appointments_as_client = db.relationship("Appointment", foreign_keys="Appointment.client_id", backref="client_user", lazy=True)
    appointments_as_advocate = db.relationship("Appointment", foreign_keys="Appointment.advocate_id", backref="advocate_user", lazy=True)

    def is_advocate(self):
        return self.user_type in ["Advocate", "Admin"]

    def is_admin(self):
        return self.user_type == "Admin"

    def __repr__(self):
        return f"<User {self.full_name} ({self.user_type})>"


# ==========================================
# Case Table
# ==========================================
class Case(db.Model):
    __tablename__ = "cases"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    client_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(30), nullable=False)

    # Details
    category = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(20), default="Medium")  # Low, Medium, High, Urgent
    status = db.Column(db.String(50), default="Pending")    # Pending, In Progress, Under Review, Hearing Scheduled, Completed, Closed

    # Advocate Notes
    advocate_notes = db.Column(db.Text, default="")

    # Quick AI summary / Document filename compatibility
    ai_summary = db.Column(db.Text, default="")
    document_name = db.Column(db.String(255), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    ai_reports = db.relationship("AIReport", backref="case", lazy=True, cascade="all, delete-orphan", order_by="desc(AIReport.id)")
    documents = db.relationship("Document", backref="case", lazy=True, cascade="all, delete-orphan", order_by="desc(Document.id)")
    timeline = db.relationship("CaseTimeline", backref="case", lazy=True, cascade="all, delete-orphan", order_by="desc(CaseTimeline.id)")

    @property
    def latest_ai_report(self):
        return self.ai_reports[0] if self.ai_reports else None

    def __repr__(self):
        return f"<Case #{self.id}: {self.title}>"


# ==========================================
# AI Report Table
# ==========================================
class AIReport(db.Model):
    __tablename__ = "ai_reports"

    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey("cases.id"), nullable=False, index=True)

    case_summary = db.Column(db.Text, nullable=False)
    possible_laws = db.Column(db.Text, default="")
    possible_sections = db.Column(db.Text, default="")
    required_documents = db.Column(db.Text, default="")
    evidence_required = db.Column(db.Text, default="")
    next_steps = db.Column(db.Text, default="")
    advocate_notes = db.Column(db.Text, default="")
    risk_level = db.Column(db.String(30), default="Medium")  # Low, Medium, High, Critical
    court_suggestion = db.Column(db.String(200), default="District & Sessions Court / JMFC")
    timeline_estimate = db.Column(db.String(100), default="3-6 Months")
    raw_response = db.Column(db.Text, default="")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<AIReport for Case #{self.case_id} ({self.risk_level})>"


# ==========================================
# Document Table
# ==========================================
class Document(db.Model):
    __tablename__ = "documents"

    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey("cases.id"), nullable=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50), default="Unknown")
    file_size = db.Column(db.String(50), default="0 KB")

    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Document {self.original_filename}>"


# ==========================================
# Appointment Table
# ==========================================
class Appointment(db.Model):
    __tablename__ = "appointments"

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    advocate_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    client_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(30), nullable=False)
    category = db.Column(db.String(100), default="General Legal Consultation")
    appointment_date = db.Column(db.String(50), nullable=False)
    appointment_time = db.Column(db.String(50), nullable=False)
    notes = db.Column(db.Text, default="")
    status = db.Column(db.String(30), default="Pending")  # Pending, Confirmed, Completed, Cancelled

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Appointment #{self.id} for {self.client_name}>"


# ==========================================
# Case Timeline Table
# ==========================================
class CaseTimeline(db.Model):
    __tablename__ = "case_timeline"

    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey("cases.id"), nullable=False, index=True)

    action = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    performed_by = db.Column(db.String(120), default="System")
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<CaseTimeline {self.action} on Case #{self.case_id}>"
