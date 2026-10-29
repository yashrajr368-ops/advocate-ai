import os
from functools import wraps
from datetime import datetime
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    redirect,
    url_for,
    flash,
    send_from_directory,
    abort
)
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user
)

from models import db, User, Case, AIReport, Document, Appointment, CaseTimeline
import ai_service

# ==========================================
# Application Setup & Configuration
# ==========================================
load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "ai_advocate_super_secret_key_2026")
is_vercel = bool(os.getenv("VERCEL"))
if is_vercel:
    base_dir = "/tmp"
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(base_dir, 'database.db')}"
    UPLOAD_FOLDER = os.path.join(base_dir, "uploads")
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///database.db")
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Upload Configuration
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB max

ALLOWED_EXTENSIONS = {"pdf", "doc", "docx", "png", "jpg", "jpeg"}

try:
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
except Exception as e:
    print(f"Warning: could not create upload directory {UPLOAD_FOLDER}: {e}")

# Initialize Extensions
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = "Please sign in to access your legal portal."
login_manager.login_message_category = "info"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def format_file_size(size_in_bytes):
    if size_in_bytes < 1024:
        return f"{size_in_bytes} B"
    elif size_in_bytes < 1024 * 1024:
        return f"{size_in_bytes / 1024:.1f} KB"
    else:
        return f"{size_in_bytes / (1024 * 1024):.1f} MB"


# ==========================================
# Role-based Access Control Decorators
# ==========================================
def advocate_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("login"))
        if current_user.user_type not in ["Advocate", "Admin"]:
            flash("Access denied: Advocate privileges required.", "danger")
            return redirect(url_for("client_dashboard"))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("login"))
        if current_user.user_type != "Admin":
            flash("Access denied: Administrator privileges required.", "danger")
            return redirect(url_for("home"))
        return f(*args, **kwargs)
    return decorated_function


def client_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("login"))
        if current_user.user_type not in ["Client", "Admin"]:
            flash("Access denied: Client portal only.", "danger")
            return redirect(url_for("advocate_dashboard"))
        return f(*args, **kwargs)
    return decorated_function


# ==========================================
# Public Routes
# ==========================================
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/ai_chat")
def ai_chat():
    return render_template("ai_chat.html")


@app.route("/ask", methods=["POST"])
def ask():
    """
    AI Legal Chatbot API Endpoint.
    Strictly answers legal inquiries under Indian jurisprudence.
    """
    try:
        data = request.get_json(silent=True) or {}
        question = data.get("question", "").strip()

        if not question:
            return jsonify({"answer": "Please provide a legal grievance or statutory question."})

        answer = ai_service.chat_legal_assistant(question)
        return jsonify({"answer": answer})

    except Exception as e:
        app.logger.error(f"Error in /ask route: {e}")
        return jsonify({"answer": f"Error communicating with legal intelligence service: {str(e)}"})


@app.route("/contact", methods=["POST"])
def contact_submit():
    name = request.form.get("contact_name")
    email = request.form.get("contact_email")
    message = request.form.get("contact_message")

    app.logger.info(f"Contact form inquiry from {name} ({email}): {message}")
    flash("Thank you! Your legal inquiry has been received. Our coordinating desk will contact you within 24 hours.", "success")
    return redirect(url_for("home"))


# ==========================================
# Authentication Routes
# ==========================================
@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        if current_user.user_type == "Advocate":
            return redirect(url_for("advocate_dashboard"))
        elif current_user.user_type == "Admin":
            return redirect(url_for("admin_dashboard"))
        return redirect(url_for("client_dashboard"))

    if request.method == "POST":
        fullname = request.form.get("fullname", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "").strip()
        user_type = request.form.get("user_type", "Client").capitalize()

        if user_type not in ["Client", "Advocate"]:
            user_type = "Client"

        if not fullname or not email or not password:
            flash("All required fields must be completed.", "warning")
            return redirect(url_for("register"))

        existing = User.query.filter_by(email=email).first()
        if existing:
            flash("An account with that email address is already registered. Please sign in.", "warning")
            return redirect(url_for("login"))

        hashed_password = generate_password_hash(password)
        new_user = User(
            full_name=fullname,
            email=email,
            phone=phone,
            password=hashed_password,
            user_type=user_type
        )
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        flash(f"Welcome, {new_user.full_name}! Your account has been registered successfully.", "success")

        if new_user.user_type == "Advocate":
            return redirect(url_for("advocate_dashboard"))
        return redirect(url_for("client_dashboard"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        if current_user.user_type == "Advocate":
            return redirect(url_for("advocate_dashboard"))
        elif current_user.user_type == "Admin":
            return redirect(url_for("admin_dashboard"))
        return redirect(url_for("client_dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash(f"Signed in as {user.full_name} ({user.user_type}).", "success")

            next_page = request.args.get("next")
            if next_page and not next_page.startswith("//"):
                return redirect(next_page)

            if user.user_type == "Advocate":
                return redirect(url_for("advocate_dashboard"))
            elif user.user_type == "Admin":
                return redirect(url_for("admin_dashboard"))
            else:
                return redirect(url_for("client_dashboard"))

        flash("Invalid email or password. Please verify your credentials.", "danger")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been signed out successfully.", "info")
    return redirect(url_for("home"))


@app.route("/profile", methods=["GET"])
@login_required
def profile():
    return render_template("profile.html")


@app.route("/update_profile", methods=["POST"])
@login_required
def update_profile():
    full_name = request.form.get("full_name", "").strip()
    phone = request.form.get("phone", "").strip()

    if full_name:
        current_user.full_name = full_name
    if phone:
        current_user.phone = phone

    db.session.commit()
    flash("Profile contact information updated successfully.", "success")
    return redirect(url_for("profile"))


@app.route("/change_password", methods=["POST"])
@login_required
def change_password():
    new_password = request.form.get("new_password", "").strip()
    confirm_password = request.form.get("confirm_password", "").strip()

    if len(new_password) < 6:
        flash("Password must be at least 6 characters.", "warning")
        return redirect(url_for("profile"))

    if new_password != confirm_password:
        flash("Passwords do not match.", "warning")
        return redirect(url_for("profile"))

    current_user.password = generate_password_hash(new_password)
    db.session.commit()
    flash("Password updated successfully.", "success")
    return redirect(url_for("profile"))


# ==========================================
# Client Dashboard & Case Submission
# ==========================================
@app.route("/client_dashboard")
@login_required
@client_required
def client_dashboard():
    user_id = current_user.id
    total_cases = Case.query.filter_by(user_id=user_id).count()
    pending_cases = Case.query.filter_by(user_id=user_id, status="Pending").count()
    in_progress_cases = Case.query.filter(Case.user_id == user_id, Case.status.in_(["In Progress", "Under Review", "Hearing Scheduled"])).count()
    completed_cases = Case.query.filter_by(user_id=user_id, status="Completed").count()
    documents_count = Document.query.filter_by(user_id=user_id).count()

    recent_cases = Case.query.filter_by(user_id=user_id).order_by(Case.id.desc()).limit(5).all()

    return render_template(
        "client_dashboard.html",
        total_cases=total_cases,
        pending_cases=pending_cases,
        in_progress_cases=in_progress_cases,
        completed_cases=completed_cases,
        documents_count=documents_count,
        recent_cases=recent_cases
    )


@app.route("/add_case", methods=["GET", "POST"])
@login_required
def add_case():
    if request.method == "POST":
        client_name = request.form.get("client_name") or current_user.full_name
        email = request.form.get("email") or current_user.email
        phone = request.form.get("phone") or current_user.phone
        category = request.form.get("category", "General Civil Dispute")
        title = request.form.get("title", "").strip()
        priority = request.form.get("priority", "Medium")
        description = request.form.get("description", "").strip()

        if not title or not description:
            flash("Please provide a title and case description.", "warning")
            return render_template("add_case.html")

        # 1. Automatically call Gemini AI Legal Intelligence
        ai_result = ai_service.analyze_case_legal(category, title, description, priority)

        # 2. Create Case record
        new_case = Case(
            user_id=current_user.id,
            client_name=client_name,
            email=email,
            phone=phone,
            category=category,
            title=title,
            priority=priority,
            description=description,
            status="Pending",
            ai_summary=ai_result.get("case_summary", "")
        )
        db.session.add(new_case)
        db.session.flush()  # Obtain new_case.id

        # 3. Create AI Report entry
        new_report = AIReport(
            case_id=new_case.id,
            case_summary=ai_result.get("case_summary", ""),
            possible_laws=ai_result.get("possible_laws", ""),
            possible_sections=ai_result.get("possible_sections", ""),
            required_documents=ai_result.get("required_documents", ""),
            evidence_required=ai_result.get("evidence_required", ""),
            next_steps=ai_result.get("next_steps", ""),
            advocate_notes=ai_result.get("advocate_notes", ""),
            risk_level=ai_result.get("risk_level", "Medium"),
            court_suggestion=ai_result.get("court_suggestion", "District Court"),
            timeline_estimate=ai_result.get("timeline_estimate", "6 to 12 Months"),
            raw_response=ai_result.get("raw_response", "")
        )
        db.session.add(new_report)

        # 4. Create initial Timeline item
        timeline_entry = CaseTimeline(
            case_id=new_case.id,
            action="Case Lodged & AI Analyzed",
            description=f"Matter filed under {category}. Gemini AI completed statutory analysis (Risk: {ai_result.get('risk_level')}).",
            performed_by=current_user.full_name
        )
        db.session.add(timeline_entry)

        db.session.commit()
        flash("Case filed successfully! Gemini AI has generated your preliminary legal brief.", "success")
        return redirect(url_for("view_case", case_id=new_case.id))

    return render_template("add_case.html")


@app.route("/my_cases")
@login_required
def my_cases():
    cases = Case.query.filter_by(user_id=current_user.id).order_by(Case.id.desc()).all()
    return render_template("my_cases.html", cases=cases)


@app.route("/view_case/<int:case_id>")
@login_required
def view_case(case_id):
    case = Case.query.get_or_404(case_id)

    # Access control: Client can view only their own cases; Advocates & Admins can view any case
    if current_user.user_type == "Client" and case.user_id != current_user.id:
        flash("Access denied: You cannot view cases filed by another client.", "danger")
        return redirect(url_for("client_dashboard"))

    return render_template("view_case.html", case=case)


# ==========================================
# Advocate Dashboard & Case Controls
# ==========================================
@app.route("/advocate_dashboard")
@login_required
@advocate_required
def advocate_dashboard():
    search = request.args.get("search", "").strip()
    status_filter = request.args.get("status", "").strip()

    query = Case.query

    if search:
        query = query.filter(
            (Case.client_name.ilike(f"%{search}%")) |
            (Case.title.ilike(f"%{search}%")) |
            (Case.category.ilike(f"%{search}%"))
        )

    if status_filter:
        query = query.filter_by(status=status_filter)

    cases = query.order_by(Case.id.desc()).all()

    # Aggregate Metrics
    total_cases = Case.query.count()
    pending_cases = Case.query.filter_by(status="Pending").count()
    in_progress_cases = Case.query.filter(Case.status.in_(["In Progress", "Under Review", "Hearing Scheduled"])).count()
    completed_cases = Case.query.filter_by(status="Completed").count()
    total_clients = User.query.filter_by(user_type="Client").count()
    uploaded_documents = Document.query.count()

    return render_template(
        "advocate_dashboard.html",
        cases=cases,
        search=search,
        status=status_filter,
        total_cases=total_cases,
        pending_cases=pending_cases,
        in_progress_cases=in_progress_cases,
        completed_cases=completed_cases,
        total_clients=total_clients,
        uploaded_documents=uploaded_documents
    )


@app.route("/update_case/<int:case_id>", methods=["POST"])
@login_required
@advocate_required
def update_case(case_id):
    case = Case.query.get_or_404(case_id)

    old_status = case.status
    new_status = request.form.get("status", case.status)
    advocate_notes = request.form.get("advocate_notes", "")

    case.status = new_status
    case.advocate_notes = advocate_notes

    # Add Case Timeline entry
    timeline_desc = f"Advocate {current_user.full_name} updated status to '{new_status}'."
    if advocate_notes:
        timeline_desc += " New notes recorded."

    timeline_entry = CaseTimeline(
        case_id=case.id,
        action="Status & Notes Updated",
        description=timeline_desc,
        performed_by=f"Adv. {current_user.full_name}"
    )
    db.session.add(timeline_entry)

    db.session.commit()
    flash("Case status and advocate strategy notes saved successfully.", "success")
    return redirect(url_for("view_case", case_id=case.id))


# ==========================================
# Document Management
# ==========================================
@app.route("/upload_document", methods=["GET", "POST"])
@login_required
def upload_document():
    if request.method == "POST":
        file = request.files.get("document")
        case_id = request.form.get("case_id")

        if not file or file.filename == "":
            flash("Please choose a file to upload.", "warning")
            return redirect(url_for("upload_document"))

        if not allowed_file(file.filename):
            flash("Invalid file format. Allowed: PDF, DOC, DOCX, PNG, JPG, JPEG.", "danger")
            return redirect(url_for("upload_document"))

        # Sanitize filename & create unique on-disk name
        original_name = secure_filename(file.filename)
        timestamp_str = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        saved_filename = f"{timestamp_str}_{original_name}"
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], saved_filename)

        file.save(file_path)
        file_size_bytes = os.path.getsize(file_path)
        formatted_size = format_file_size(file_size_bytes)
        file_ext = original_name.rsplit(".", 1)[1].upper() if "." in original_name else "FILE"

        target_case_id = int(case_id) if case_id else None

        new_doc = Document(
            case_id=target_case_id,
            user_id=current_user.id,
            filename=saved_filename,
            original_filename=original_name,
            file_type=file_ext,
            file_size=formatted_size
        )
        db.session.add(new_doc)

        if target_case_id:
            c = db.session.get(Case, target_case_id)
            if c:
                c.document_name = original_name
                # Record timeline
                t_entry = CaseTimeline(
                    case_id=c.id,
                    action="Document Uploaded",
                    description=f"Uploaded '{original_name}' ({formatted_size}) to case dossier.",
                    performed_by=current_user.full_name
                )
                db.session.add(t_entry)

        db.session.commit()
        flash(f"Document '{original_name}' uploaded successfully.", "success")

        if target_case_id:
            return redirect(url_for("view_case", case_id=target_case_id))
        return redirect(url_for("upload_document"))

    # GET: Load available cases for dropdown
    if current_user.user_type in ["Advocate", "Admin"]:
        cases = Case.query.order_by(Case.id.desc()).all()
        documents = Document.query.order_by(Document.id.desc()).all()
    else:
        cases = Case.query.filter_by(user_id=current_user.id).order_by(Case.id.desc()).all()
        documents = Document.query.filter_by(user_id=current_user.id).order_by(Document.id.desc()).all()

    return render_template("upload_document.html", cases=cases, documents=documents)


@app.route("/uploads/<path:filename>")
@login_required
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=True)


# ==========================================
# Appointment Booking
# ==========================================
@app.route("/appointment")
def appointment():
    if current_user.is_authenticated:
        if current_user.user_type in ["Advocate", "Admin"]:
            appointments = Appointment.query.order_by(Appointment.id.desc()).all()
        else:
            appointments = Appointment.query.filter_by(client_id=current_user.id).order_by(Appointment.id.desc()).all()
    else:
        appointments = []

    return render_template("appointment.html", appointments=appointments)


@app.route("/book_appointment", methods=["POST"])
def book_appointment():
    client_name = request.form.get("client_name")
    email = request.form.get("email")
    phone = request.form.get("phone")
    category = request.form.get("category", "General Legal Consultation")
    appointment_date = request.form.get("appointment_date")
    appointment_time = request.form.get("appointment_time")
    notes = request.form.get("notes", "")

    if not client_name or not email or not appointment_date or not appointment_time:
        flash("Please fill in all mandatory appointment booking details.", "warning")
        return redirect(url_for("appointment"))

    client_id = current_user.id if current_user.is_authenticated else None

    new_app = Appointment(
        client_id=client_id,
        client_name=client_name,
        email=email,
        phone=phone,
        category=category,
        appointment_date=appointment_date,
        appointment_time=appointment_time,
        notes=notes,
        status="Confirmed"
    )
    db.session.add(new_app)
    db.session.commit()

    # Simulate email confirmation notification
    app.logger.info(f"CONFIRMATION EMAIL SIMULATION: Sent to {email} for appointment on {appointment_date} at {appointment_time}.")

    flash(f"Appointment confirmed for {appointment_date} at {appointment_time}! A confirmation notification has been dispatched to {email}.", "success")
    return redirect(url_for("appointment"))


# ==========================================
# Printable Court Case Report
# ==========================================
@app.route("/case/<int:case_id>/report")
@login_required
def case_report(case_id):
    case = Case.query.get_or_404(case_id)
    if current_user.user_type == "Client" and case.user_id != current_user.id:
        flash("Unauthorized access to case report.", "danger")
        return redirect(url_for("client_dashboard"))
    return render_template("case_report.html", case=case)


# ==========================================
# Admin Management Routes
# ==========================================
@app.route("/admin_dashboard")
@login_required
@admin_required
def admin_dashboard():
    users = User.query.order_by(User.id.desc()).all()
    cases = Case.query.order_by(Case.id.desc()).all()
    appointments = Appointment.query.order_by(Appointment.id.desc()).all()

    advocates_count = User.query.filter_by(user_type="Advocate").count()
    clients_count = User.query.filter_by(user_type="Client").count()
    total_cases = len(cases)

    return render_template(
        "admin_dashboard.html",
        users=users,
        cases=cases,
        appointments=appointments,
        advocates_count=advocates_count,
        clients_count=clients_count,
        total_cases=total_cases
    )


@app.route("/admin/delete_case/<int:case_id>", methods=["POST"])
@login_required
@admin_required
def admin_delete_case(case_id):
    case = Case.query.get_or_404(case_id)
    db.session.delete(case)
    db.session.commit()
    flash(f"Case #{case_id} and all associated reports have been permanently removed.", "info")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/toggle_role/<int:user_id>", methods=["POST"])
@login_required
@admin_required
def admin_toggle_role(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You cannot modify your own administrative role.", "warning")
        return redirect(url_for("admin_dashboard"))

    if user.user_type == "Client":
        user.user_type = "Advocate"
    elif user.user_type == "Advocate":
        user.user_type = "Client"

    db.session.commit()
    flash(f"User {user.full_name} role changed to {user.user_type}.", "success")
    return redirect(url_for("admin_dashboard"))


# ==========================================
# Error Handlers
# ==========================================
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template("500.html"), 500


# ==========================================
# Database Seeder for Out-of-the-Box Demo
# ==========================================
def seed_demo_data():
    """
    Seeds initial demonstration accounts and sample cases if empty.
    """
    if User.query.count() == 0:
        print("[INFO] Seeding default demo accounts...")

        admin = User(
            full_name="Chief Legal Admin",
            email="admin@example.com",
            phone="+91 99999 00001",
            password=generate_password_hash("password123"),
            user_type="Admin"
        )

        advocate = User(
            full_name="Adv. Mukesh Singh Rathod (Senior Counsel)",
            email="advocate@example.com",
            phone="+91 98269 35975",
            password=generate_password_hash("password123"),
            user_type="Advocate"
        )

        client = User(
            full_name="Sunil Mehra",
            email="client@example.com",
            phone="+91 97222 33445",
            password=generate_password_hash("password123"),
            user_type="Client"
        )

        db.session.add_all([admin, advocate, client])
        db.session.commit()

    if Case.query.count() == 0:
        print("[INFO] Seeding sample cases & reports...")
        client = User.query.filter_by(user_type="Client").first()
        if not client:
            client = User(
                full_name="Sunil Mehra",
                email="client@example.com",
                phone="+91 97222 33445",
                password=generate_password_hash("password123"),
                user_type="Client"
            )
            db.session.add(client)
            db.session.commit()
        sample_cases_data = [
            {
                "user_id": client.id,
                "client_name": client.full_name,
                "email": client.email,
                "phone": client.phone,
                "category": "Cyber Crime",
                "title": "Unauthorized debit of ₹2,50,000 via spoofed banking APK application",
                "priority": "High",
                "status": "In Progress",
                "description": "On 15th August 2026, client received an SMS claiming electricity bill update with an APK download link. Upon installing, banking OTPs were forwarded and ₹2,50,000 was debited via IMPS to unknown beneficiary account in multiple tranches. Immediate cyber complaint 1930 was dialed within 2 hours.",
                "advocate_notes": "Section 1930 acknowledgment obtained. Filing Section 503 BNSS petition for defreezing recovered funds with Metropolitan Magistrate.",
                "risk_level": "High"
            },
            {
                "user_id": client.id,
                "client_name": client.full_name,
                "email": client.email,
                "phone": client.phone,
                "category": "Cheque Bounce",
                "title": "Dishonour of business supply cheque worth ₹5,00,000 for lack of funds",
                "priority": "Medium",
                "status": "Pending",
                "description": "Client supplied raw industrial textiles worth ₹5,00,000 against valid tax invoices to M/s Apex Enterprises. Cheque No. 445102 dated 10th July 2026 returned unpaid on 22nd July 2026 with bank return memo stating 'Funds Insufficient'. 15-day statutory legal demand notice issued via registered speed post on 3rd August 2026.",
                "advocate_notes": "Statutory notice served on 7th August. 15-day cure period expires on 22nd August. Preparing Section 138 NI Act complaint for JMFC filing.",
                "risk_level": "Medium"
            },
            {
                "user_id": client.id,
                "client_name": client.full_name,
                "email": client.email,
                "phone": client.phone,
                "category": "Property & Real Estate",
                "title": "Illegal boundary encroachment on registered agricultural land Plot No. 42",
                "priority": "Urgent",
                "status": "Hearing Scheduled",
                "description": "Ancestral agricultural land of 2.5 acres registered under registered sale deed 1994. Adjacent landholders attempted to erect an unauthorized boundary wall and cut mature timber trees without demarcation or permission. Police advised approaching Civil Court.",
                "advocate_notes": "Plaint drafted with CPC Order 39 Rules 1 & 2 ad-interim injunction application. Hearing listed for urgent status quo order on Thursday.",
                "risk_level": "High"
            }
        ]

        for sc in sample_cases_data:
            c = Case(
                user_id=sc["user_id"],
                client_name=sc["client_name"],
                email=sc["email"],
                phone=sc["phone"],
                category=sc["category"],
                title=sc["title"],
                priority=sc["priority"],
                status=sc["status"],
                description=sc["description"],
                advocate_notes=sc["advocate_notes"],
                ai_summary=f"Automated legal assessment for {sc['category']} matter involving {sc['title']}."
            )
            db.session.add(c)
            db.session.flush()

            # Generate AI report
            ai_data = ai_service.analyze_case_legal(sc["category"], sc["title"], sc["description"], sc["priority"])
            rep = AIReport(
                case_id=c.id,
                case_summary=ai_data["case_summary"],
                possible_laws=ai_data["laws" if "laws" in ai_data else "possible_laws"],
                possible_sections=ai_data["sections" if "sections" in ai_data else "possible_sections"],
                required_documents=ai_data["documents" if "documents" in ai_data else "required_documents"],
                evidence_required=ai_data["evidence" if "evidence" in ai_data else "evidence_required"],
                next_steps=ai_data["next_steps"],
                advocate_notes=ai_data["advocate_notes"],
                risk_level=sc["risk_level"],
                court_suggestion=ai_data.get("court_suggestion", "District Court"),
                timeline_estimate=ai_data.get("timeline_estimate", "6 to 12 Months"),
                raw_response="Demo pre-seeded legal dossier."
            )
            db.session.add(rep)

            # Timeline
            t = CaseTimeline(
                case_id=c.id,
                action="Case Registered & AI Analysis Generated",
                description=f"Matter filed under {sc['category']}. AI generated legal dossier and statutory citations.",
                performed_by="AI Advocate Engine"
            )
            db.session.add(t)

        # Sample Appointment
        sample_app = Appointment(
            client_id=client.id,
            client_name=client.full_name,
            email=client.email,
            phone=client.phone,
            category="Property & Real Estate",
            appointment_date="2026-09-12",
            appointment_time="11:30 AM - 12:30 PM",
            notes="Discussing boundary wall stay application before District Court.",
            status="Confirmed"
        )
        db.session.add(sample_app)

        db.session.commit()
        print("[OK] Demo accounts and seed cases generated successfully.")


# ==========================================
# Application Entry Point
# ==========================================
with app.app_context():
    db.create_all()
    seed_demo_data()

if __name__ == "__main__":
    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000
    )
