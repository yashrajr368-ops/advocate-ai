import os
import re
import json
import logging
from dotenv import load_dotenv

# Try importing Google Generative AI
try:
    import certifi
    os.environ["GRPC_DEFAULT_SSL_ROOTS_FILE_PATH"] = certifi.where()
except Exception:
    pass

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

load_dotenv()

logger = logging.getLogger(__name__)

# Primary & Fallback model candidates
API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
MODELS_TO_TRY = ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-2.0-flash", "gemini-pro"]

gemini_model = None

if GENAI_AVAILABLE and API_KEY and not API_KEY.startswith("AQ."):
    try:
        genai.configure(api_key=API_KEY, transport="rest")
        for m_name in MODELS_TO_TRY:
            try:
                gemini_model = genai.GenerativeModel(m_name)
                logger.info(f"Gemini model initialized successfully with {m_name}")
                break
            except Exception:
                continue
    except Exception as e:
        logger.warning(f"Could not configure Gemini API: {e}")
        gemini_model = None


# ==========================================================
# Domain-Specific Legal Intelligence Fallback Knowledge Base
# ==========================================================
LEGAL_KNOWLEDGE_BASE = {
    "criminal": {
        "laws": "Bharatiya Nyaya Sanhita (BNS) 2023, Indian Penal Code (IPC) 1860, Bharatiya Nagarik Suraksha Sanhita (BNSS) 2023, Code of Criminal Procedure (CrPC) 1973, Bharatiya Sakshya Adhiniyam (BSA) 2023",
        "sections": "BNS Section 318 / IPC Section 420 (Cheating & Dishonestly Inducing Delivery), BNS Section 303 / IPC Section 379 (Theft), BNS Section 351 / IPC Section 506 (Criminal Intimidation), BNS Section 115 / IPC Section 323 (Voluntarily Causing Hurt)",
        "documents": "Copy of First Information Report (FIR) or Non-Cognizable Report (NCR), Medical Examination Report / MLC (if injury occurred), CCTV Footage / Photographs, Bank account statements (for financial cheating), Communication logs / WhatsApp chats / Emails",
        "evidence": "Witness statements recorded under Section 180 BNSS / 161 CrPC, digital forensics certificate under Section 63 BSA / 65B Indian Evidence Act, Call Detail Records (CDR), forensic audit reports",
        "next_steps": "1. Immediately file a complaint at the nearest police station or cyber crime portal.\n2. In case of police inaction, submit an application to the Superintendent of Police under Section 173(4) BNSS / 154(3) CrPC.\n3. Approach the Judicial Magistrate under Section 175(3) BNSS / 156(3) CrPC seeking directions for FIR registration.\n4. Consult your advocate for anticipatory bail (Section 482 BNSS) or regular bail (Section 480 BNSS) if apprehending arrest.",
        "advocate_notes": "Verify jurisdiction and determine whether cognizable or non-cognizable offense. Assess requirement of Section 41A CrPC / Section 35 BNSS notice before any arrest. Prepare Section 63 BSA certificate for digital corroboration.",
        "risk_level": "High",
        "court": "Chief Judicial Magistrate (CJM) Court / Court of Sessions",
        "timeline": "6 to 18 Months"
    },
    "cyber": {
        "laws": "Information Technology Act 2000 (as amended 2008), Bharatiya Nyaya Sanhita 2023, Bharatiya Sakshya Adhiniyam 2023",
        "sections": "IT Act Section 66C (Identity Theft), IT Act Section 66D (Cheating by Personation using Computer Resource), IT Act Section 67 (Publishing Obscene Information), BNS Section 318 / IPC Section 420 (Cyber Fraud)",
        "documents": "Screenshots of phishing links/messages/emails with full MIME headers, Bank transaction transaction IDs / UTR numbers, Mobile IMEI and SIM provider details, Complaint acknowledgment from National Cyber Crime Reporting Portal (cybercrime.gov.in)",
        "evidence": "Hash-verified digital forensic dumps, Certificate under Section 63 BSA (formerly 65B Evidence Act), Server IP logs, payment gateway ledger statements",
        "next_steps": "1. Immediately call the National Cyber Crime Helpline '1930' to freeze illicit bank transactions.\n2. Lodge an official complaint on https://cybercrime.gov.in within 24 hours.\n3. Request bank to put hold/lien on beneficiary account numbers.\n4. File an official complaint with the Cyber Crime Police Station having territorial jurisdiction.",
        "advocate_notes": "Expedite freezing order with bank nodal officers. Prepare petition under Section 457 CrPC / Section 503 BNSS for release of seized/frozen legitimate funds.",
        "risk_level": "High",
        "court": "Adjudicating Officer under IT Act / Special Cyber Crime Court / Magistrate Court",
        "timeline": "3 to 9 Months"
    },
    "property": {
        "laws": "Transfer of Property Act 1882, Specific Relief Act 1963 (amended 2018), Registration Act 1908, Civil Procedure Code (CPC) 1908, Real Estate (Regulation and Development) Act (RERA) 2016",
        "sections": "Specific Relief Act Section 5 & 6 (Recovery of Possession of Immovable Property), Specific Relief Act Section 34 (Declaratory Decrees), CPC Order 39 Rules 1 & 2 (Temporary Injunction), Transfer of Property Act Section 54 (Sale) & Section 106 (Lease Termination)",
        "documents": "Original Registered Sale Deed / Gift Deed / Will, Latest Non-Encumbrance Certificate (30 years search), Property Tax Receipts and Khata / Mutation extracts, Approved municipal building plan and layout map, Legal notices and postal delivery receipts",
        "evidence": "Chain of title deeds dating back minimum 30 years, Revenue survey maps and revenue patta entries, Demarcation and spot inspection reports by Court Commissioner, Eyewitness affidavits regarding continuous physical possession",
        "next_steps": "1. Issue a formal Legal Notice to the adverse party demanding cessation of trespass or execution of registered deed within 15 days.\n2. File a Civil Suit for Declaration of Title, Permanent Injunction, and Possession.\n3. Simultaneously file an application under CPC Order 39 Rules 1 & 2 seeking ad-interim temporary injunction to maintain status quo.\n4. Apply for appointment of an Advocate Commissioner for local spot inspection.",
        "advocate_notes": "Scrutinize limitation period (12 years for adverse possession suits, 3 years for specific performance of contract). Check court fee valuation under the relevant State Court Fees and Suits Valuation Act.",
        "risk_level": "Medium",
        "court": "Court of Civil Judge (Senior Division) / District Court",
        "timeline": "12 to 36 Months"
    },
    "family": {
        "laws": "Hindu Marriage Act 1955 / Special Marriage Act 1954, Protection of Women from Domestic Violence Act (PWDVA) 2005, Hindu Adoption and Maintenance Act 1956, Bharatiya Nagarik Suraksha Sanhita (BNSS) 2023 / CrPC 1973",
        "sections": "Hindu Marriage Act Section 13(1) (Contested Divorce on Cruelty/Desertion), Section 13B (Mutual Consent Divorce), Section 9 (Restitution of Conjugal Rights), Section 24 & 25 (Maintenance pendente lite & Permanent Alimony), BNSS Section 144 / CrPC Section 125 (Order for Maintenance)",
        "documents": "Original Marriage Certificate and Wedding Photographs / Invitation Card, Proof of Residence and Identity of both spouses, Children birth certificates (if custody involved), Detailed Income Tax Returns (ITR) and bank statements of both spouses, Affidavit of Disclosure of Assets and Liabilities (as mandated in Rajnesh v. Neha)",
        "evidence": "Recorded audio/video messages, email/text conversations establishing matrimonial cruelty or abandonment, medical treatment records, joint ownership financial documents",
        "next_steps": "1. Consider participating in mandatory pre-litigation mediation and counseling session.\n2. If settlement fails, file petition for dissolution of marriage under relevant personal law or Section 13B for mutual consent.\n3. File interim application for maintenance under Section 24 HMA or Section 144 BNSS / 125 CrPC.\n4. Address child custody and visitation rights through Guardians and Wards Act application.",
        "advocate_notes": "Attempt mutual settlement through comprehensive Memorandum of Understanding (MoU) to resolve alimony, custody, and return of Stridhan. Comply strictly with Rajnesh v. Neha asset disclosure guidelines.",
        "risk_level": "Medium",
        "court": "Principal Judge, Family Court",
        "timeline": "6 to 18 Months"
    },
    "corporate": {
        "laws": "Indian Contract Act 1872, Companies Act 2013, Arbitration and Conciliation Act 1996 (amended 2019/2021), Commercial Courts Act 2015, Insolvency and Bankruptcy Code (IBC) 2016",
        "sections": "Contract Act Section 73 & 74 (Compensation for Breach of Contract & Liquidated Damages), Arbitration Act Section 9 (Interim Relief) & Section 11 (Appointment of Arbitrators), Commercial Courts Act Section 12A (Mandatory Pre-Institution Mediation), IBC Section 9 (Operational Creditor Application)",
        "documents": "Executed Master Service Agreement (MSA), Non-Disclosure Agreement (NDA), and Statement of Work (SOW), Purchase Orders (PO), Invoices, and Delivery Challans with stamped acceptance, Written correspondence demanding payment, Formal Demand Notice under Section 8 IBC or Arbitration Notice under Section 21",
        "evidence": "Reconciled ledger accounts, bank transaction records, email confirmation of debt acknowledgment, minutes of board resolutions authorizing litigation",
        "next_steps": "1. Issue a statutory legal notice or Section 21 Arbitration Notice demanding dispute resolution within 30 days.\n2. Initiate mandatory Pre-Institution Mediation under Section 12A of the Commercial Courts Act 2015.\n3. File a Commercial Suit or invoke Section 9 of the Arbitration Act for urgent interim protection of assets.\n4. In case of unpaid operational debt, consider filing an application before NCLT under Section 9 of IBC if claim threshold exceeds ₹1 Crore.",
        "advocate_notes": "Check for exclusive jurisdiction and dispute resolution arbitration clauses. Verify stamp duty compliance of contracts in light of NN Global Mercantile ruling.",
        "risk_level": "Medium",
        "court": "Dedicated Commercial Court / District Court / National Company Law Tribunal (NCLT)",
        "timeline": "6 to 24 Months"
    },
    "cheque": {
        "laws": "Negotiable Instruments Act (NI Act) 1881, Code of Criminal Procedure 1973 / BNSS 2023, Civil Procedure Code 1908",
        "sections": "NI Act Section 138 (Dishonour of Cheque for Insufficiency of Funds), Section 141 (Offences by Companies & Directors), Section 142 (Cognizance of Offences), Section 143A (Power to Direct Interim Compensation up to 20%), CPC Order 37 (Summary Suit)",
        "documents": "Original dishonoured cheque and bank Return Memo indicating reason ('Funds Insufficient', 'Account Closed', etc.), Copy of statutory Legal Demand Notice dispatched within 30 days of memo, Postal speed post receipts and tracking consignment delivery reports, Invoices, promissory notes, or agreements proving legally enforceable debt",
        "evidence": "Statutory presumption of debt under Section 118 and Section 139 NI Act in favor of complainant, audited ledger balance showing unpaid liability",
        "next_steps": "1. Issue statutory 15-day Legal Demand Notice within 30 days of receiving the cheque return memo.\n2. If amount remains unpaid after 15 days from notice delivery, file Criminal Complaint under Section 138 within 30 days before Judicial Magistrate.\n3. File Application under Section 143A NI Act requesting 20% interim compensation deposit from the accused.\n4. Simultaneously file a Summary Suit under CPC Order 37 for civil recovery.",
        "advocate_notes": "Adhere strictly to statutory timeline: Memo + 30 days = Notice; Notice + 15 days cure period; Cure + 30 days = Filing deadline. Check director vicarious liability under Section 141.",
        "risk_level": "Low",
        "court": "Court of Metropolitan Magistrate / Judicial Magistrate First Class (JMFC)",
        "timeline": "6 to 12 Months"
    },
    "consumer": {
        "laws": "Consumer Protection Act 2019, Central Consumer Protection Authority (CCPA) Regulations 2020",
        "sections": "Consumer Protection Act Section 2(7) (Definition of Consumer), Section 2(11) (Deficiency in Service), Section 2(47) (Unfair Trade Practice), Section 35 (Manner of Making Complaint), Section 39 (Findings and Reliefs by District Commission)",
        "documents": "Tax invoice / purchase bill, warranty card, product packaging photographs, Service complaint emails, ticket numbers, and customer support chat logs, Proof of payment (credit card slip, UPI confirmation, bank statement), Pre-litigation legal notice served to manufacturer/service provider",
        "evidence": "Third-party technical expert test report (if manufacturing defect), comparison of advertised claims vs actual delivered product/service",
        "next_steps": "1. Send a registered legal demand notice granting 15 days to replace product, refund amount, or provide compensation.\n2. Lodge a grievance on the National Consumer Helpline (consumerhelpline.gov.in).\n3. File an e-Daakhil consumer complaint online before the District Consumer Disputes Redressal Commission.\n4. Claim full refund with interest and compensation for mental agony and litigation costs.",
        "advocate_notes": "Check pecuniary jurisdiction: District Commission (up to ₹50 Lakhs), State Commission (₹50 Lakhs to ₹2 Crores), National Commission (above ₹2 Crores). No stamp duty required; minimal fee.",
        "risk_level": "Low",
        "court": "District Consumer Disputes Redressal Commission (DCDRC)",
        "timeline": "4 to 10 Months"
    },
    "general": {
        "laws": "Constitution of India, Code of Civil Procedure 1908, Bharatiya Nagarik Suraksha Sanhita 2023, Bharatiya Nyaya Sanhita 2023",
        "sections": "Article 226 (Writ Jurisdiction of High Court), CPC Section 9 (Courts to try all civil suits unless barred), BNS General Principles of Liability",
        "documents": "Government-issued Photo ID Proof (Aadhaar / Passport / PAN), Chronological statement of facts with all dated supporting receipts, Written notices and formal replies exchanged between parties",
        "evidence": "Documentary records, notarized witness statements, sworn declarations",
        "next_steps": "1. Schedule an in-depth consultation with a specialized legal counsel.\n2. Consolidate all physical and electronic evidence into a chronologically indexed dossier.\n3. Send a formal legal notice setting forth the claims and establishing cause of action.\n4. Institute appropriate civil, criminal, or constitutional proceedings.",
        "advocate_notes": "Examine threshold issues of locus standi, cause of action, territorial and pecuniary jurisdiction, and limitation period.",
        "risk_level": "Medium",
        "court": "District & Sessions Court / Judicial Magistrate First Class (JMFC)",
        "timeline": "6 to 18 Months"
    }
}


def detect_category_key(text):
    text_lower = text.lower()
    if any(k in text_lower or k in text for k in ["cheque", "dishonour", "bounce", "138", "promissory", "memo", "चेक", "बाउंस", "अनादर"]):
        return "cheque"
    if any(k in text_lower or k in text for k in ["cyber", "hack", "phishing", "online fraud", "otp", "crypto", "social media", "impersonat", "साइबर", "हैक", "ओटीपी", "ऑनलाइन फ्रॉड", "यूपीआई"]):
        return "cyber"
    if any(k in text_lower or k in text for k in ["crime", "police", "fir", "arrest", "theft", "murder", "assault", "bail", "bns", "ipc", "अपराध", "पुलिस", "एफआईआर", "जमानत", "चोरी", "मारपीट", "धोखाधड़ी"]):
        return "criminal"
    if any(k in text_lower or k in text for k in ["property", "land", "flat", "plot", "tenant", "rent", "trespass", "possession", "mutation", "khata", "builder", "संपत्ति", "जमीन", "प्लाट", "मकान", "किराया", "कब्जा", "बंटवारा", "नामांतरण"]):
        return "property"
    if any(k in text_lower or k in text for k in ["divorce", "marriage", "wife", "husband", "maintenance", "custody", "alimony", "dowry", "498a", "matrimonial", "तलाक", "शादी", "विवाह", "पत्नी", "पति", "दहेज", "भरण-पोषण"]):
        return "family"
    if any(k in text_lower or k in text for k in ["company", "contract", "partnership", "business", "shareholder", "corporate", "agreement", "arbitration", "vendor", "nclt", "कंपनी", "करार", "अनुबंध", "व्यापार"]):
        return "corporate"
    if any(k in text_lower or k in text for k in ["consumer", "defective", "warranty", "deficiency", "refund", "unfair", "shopping", "ecommerce", "उपभोक्ता", "वारंटी", "दोषपूर्ण", "रिफंड"]):
        return "consumer"
    return "general"


def analyze_case_legal(category, title, description, priority="Medium"):
    """
    Analyzes a legal case using Gemini AI.
    Falls back gracefully to the comprehensive Indian Legal Knowledge Base.
    Returns a dictionary of structured legal intelligence fields.
    """
    prompt = f"""
You are an expert Senior Indian Legal Counsel and AI Legal Analyst.
Analyze the following legal case according to Indian Law, including modern statutory reforms (Bharatiya Nyaya Sanhita 2023 - BNS, Bharatiya Nagarik Suraksha Sanhita 2023 - BNSS, Bharatiya Sakshya Adhiniyam 2023 - BSA, Indian Penal Code, Civil Procedure Code, and relevant Special Acts).

Case Category: {category}
Case Title: {title}
Priority Level: {priority}
Case Description:
{description}

Provide a comprehensive, professional legal analysis formatted EXACTLY with these markdown sections:

### 1. Case Summary
(Concise 2-3 paragraph summary of facts, issues, and primary grievance)

### 2. Possible Indian Laws
(Specific statutes, acts, regulations, and constitutional provisions)

### 3. Possible IPC/BNS Sections
(Specific sections under BNS 2023 and corresponding IPC sections where applicable)

### 4. Required Documents
(Checklist of primary documents required to initiate or defend legal action)

### 5. Evidence Required
(Critical physical, electronic, forensic, and documentary evidence needed)

### 6. Next Steps
(Step-by-step actionable roadmap for the client and counsel)

### 7. Advocate Notes
(Strategic litigation points, limitation issues, jurisdiction, bail/injunction remedies)

### 8. Risk Level
(Must be strictly one of: Low, Medium, High, or Critical)

### 9. Court Suggestion
(Recommended forum or judicial hierarchy, e.g., District Court, High Court, NCLT, JMFC, Consumer Forum)

### 10. Estimated Timeline
(Realistic judicial timeframe, e.g., 3-6 Months, 6-12 Months, 1-2 Years)
"""

    # Attempt Gemini API call
    if gemini_model:
        try:
            response = gemini_model.generate_content(prompt)
            if response and hasattr(response, "text") and response.text:
                raw_text = response.text.strip()
                parsed = parse_ai_case_response(raw_text)
                parsed["raw_response"] = raw_text
                return parsed
        except Exception as e:
            logger.warning(f"Gemini generation call failed, using fallback engine: {e}")

    # Fallback to rich built-in legal intelligence
    cat_key = detect_category_key(f"{category} {title} {description}")
    fallback_data = LEGAL_KNOWLEDGE_BASE.get(cat_key, LEGAL_KNOWLEDGE_BASE["general"])

    summary = (
        f"The client has reported a {category.lower()} dispute concerning '{title}'. "
        f"Based on the preliminary facts provided: {description[:300]}... "
        f"This matter involves immediate questions of statutory compliance, protection of legal rights, "
        f"and determination of civil/criminal liability under Indian jurisprudence."
    )

    risk = "High" if priority in ["High", "Urgent"] else fallback_data.get("risk_level", "Medium")

    return {
        "case_summary": summary,
        "possible_laws": fallback_data["laws"],
        "possible_sections": fallback_data["sections"],
        "required_documents": fallback_data["documents"],
        "evidence_required": fallback_data["evidence"],
        "next_steps": fallback_data["next_steps"],
        "advocate_notes": fallback_data["advocate_notes"],
        "risk_level": risk,
        "court_suggestion": fallback_data["court"],
        "timeline_estimate": fallback_data["timeline"],
        "raw_response": f"Generated via AI Advocate Intelligence Engine for {category}."
    }


def parse_ai_case_response(text):
    """
    Extracts structured fields from the AI response markdown text.
    """
    sections = {
        "case_summary": "",
        "possible_laws": "",
        "possible_sections": "",
        "required_documents": "",
        "evidence_required": "",
        "next_steps": "",
        "advocate_notes": "",
        "risk_level": "Medium",
        "court_suggestion": "District & Sessions Court / JMFC",
        "timeline_estimate": "6 to 12 Months"
    }

    def extract_section(patterns, default=""):
        for p in patterns:
            match = re.search(p, text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()
        return default

    sections["case_summary"] = extract_section([
        r"###\s*1\.\s*Case Summary\s*\n(.*?)(?=###|\Z)",
        r"\*\*1\.\s*Case Summary:\*\*\s*\n(.*?)(?=\*\*|\Z)",
        r"Case Summary:\s*\n(.*?)(?=\n[A-Z0-9#]|\Z)"
    ], "Legal case summary prepared for review.")

    sections["possible_laws"] = extract_section([
        r"###\s*2\.\s*Possible Indian Laws\s*\n(.*?)(?=###|\Z)",
        r"\*\*2\.\s*Possible Indian Laws:\*\*\s*\n(.*?)(?=\*\*|\Z)"
    ], "Relevant Indian Statutes and Enactments")

    sections["possible_sections"] = extract_section([
        r"###\s*3\.\s*Possible IPC/BNS Sections\s*\n(.*?)(?=###|\Z)",
        r"\*\*3\.\s*Possible IPC/BNS Sections:\*\*\s*\n(.*?)(?=\*\*|\Z)"
    ], "Applicable penal and procedural sections under review")

    sections["required_documents"] = extract_section([
        r"###\s*4\.\s*Required Documents\s*\n(.*?)(?=###|\Z)",
        r"\*\*4\.\s*Required Documents:\*\*\s*\n(.*?)(?=\*\*|\Z)"
    ], "Official Identity Proof, Relevant Notices, Transaction Receipts")

    sections["evidence_required"] = extract_section([
        r"###\s*5\.\s*Evidence Required\s*\n(.*?)(?=###|\Z)",
        r"\*\*5\.\s*Evidence Required:\*\*\s*\n(.*?)(?=\*\*|\Z)"
    ], "Documentary, electronic, and physical corroborative evidence")

    sections["next_steps"] = extract_section([
        r"###\s*6\.\s*Next Steps\s*\n(.*?)(?=###|\Z)",
        r"\*\*6\.\s*Next Steps:\*\*\s*\n(.*?)(?=\*\*|\Z)"
    ], "Consult advocate, compile documents, issue legal notice.")

    sections["advocate_notes"] = extract_section([
        r"###\s*7\.\s*Advocate Notes\s*\n(.*?)(?=###|\Z)",
        r"\*\*7\.\s*Advocate Notes:\*\*\s*\n(.*?)(?=\*\*|\Z)"
    ], "Review jurisdiction, limitation period, and cause of action.")

    risk_match = re.search(r"###\s*8\.\s*Risk Level\s*[:\n]*\s*(Low|Medium|High|Critical)", text, re.IGNORECASE)
    if risk_match:
        sections["risk_level"] = risk_match.group(1).capitalize()

    court_match = extract_section([
        r"###\s*9\.\s*Court Suggestion\s*[:\n]*\s*(.*?)(?=###|\n\n|\Z)"
    ], "District Court / Magistrate Court")
    if court_match:
        sections["court_suggestion"] = court_match.split("\n")[0].strip()

    timeline_match = extract_section([
        r"###\s*10\.\s*Estimated Timeline\s*[:\n]*\s*(.*?)(?=###|\n\n|\Z)"
    ], "6 to 12 Months")
    if timeline_match:
        sections["timeline_estimate"] = timeline_match.split("\n")[0].strip()

    return sections


def is_hindi_text(text):
    """
    Checks if query contains Devanagari characters or strong Hindi markers.
    """
    if re.search(r'[\u0900-\u097F]', text):
        return True
    hindi_markers = [
        "kya", "kaise", "kanoon", "dhara", "adalat", "mukadma", "zamanat", "zamin", 
        "shikayat", "vakil", "peshi", "muavza", "talaq", "dhokha", "batawara", "kiraya"
    ]
    t_lower = text.lower()
    return sum(1 for m in hindi_markers if m in t_lower) >= 2


def is_legal_question(query):
    """
    Checks whether the user question is related to legal topics in English or Hindi.
    """
    # Devanagari characters presence
    has_devanagari = bool(re.search(r'[\u0900-\u097F]', query))
    
    legal_keywords = [
        "law", "legal", "court", "judge", "police", "fir", "advocate", "lawyer",
        "case", "ipc", "bns", "crpc", "bnss", "cpc", "bsa", "rights", "divorce",
        "crime", "theft", "fraud", "property", "rent", "tenant", "bail", "arrest",
        "cheque", "notice", "contract", "agreement", "consumer", "complaint",
        "fine", "penalty", "injunction", "will", "probate", "custody", "alimony",
        "affidavit", "power of attorney", "trademark", "patent", "copyright",
        "statute", "section", "article", "tribunal", "mact", "rera", "nclt",
        "high court", "supreme court", "suit", "appeal", "petition", "litigation",
        # Hindi keywords (in Devanagari)
        "कानून", "धारा", "कोर्ट", "अदालत", "न्यायालय", "वकील", "मुकदमा", "अधिवक्ता",
        "पुलिस", "एफआईआर", "जमानत", "तलाक", "संपत्ति", "जमीन", "चेक", "नोटिस",
        "उपभोक्ता", "शिकायत", "धोखाधड़ी", "चोरी", "जुर्माना", "हर्जाना", "राठौड़",
        "शादी", "दहेज", "बंटवारा", "किराया", "मकान", "करार", "अनुबंध", "पेशी",
        "गवाह", "साक्ष्य", "जिरह", "दलील", "अधिकार", "न्याय", "कार्रवाई",
        # Romanized Hindi (Hinglish)
        "kanoon", "dhara", "adalat", "mukadma", "zamanat", "zamin", "vakil",
        "peshi", "dhokhadhadi", "kiraya", "makan", "talaq", "batawara"
    ]
    query_lower = query.lower()
    return any(kw in query_lower or kw in query for kw in legal_keywords)


def chat_legal_assistant(user_message):
    """
    Chatbot endpoint using Gemini API.
    Supports both Hindi and English.
    Strictly answers legal queries. Politeness refusal for non-legal queries.
    Enforces 5-point format.
    """
    user_message_clean = user_message.strip()
    is_hindi = is_hindi_text(user_message_clean)

    # Guardrail check
    if not is_legal_question(user_message_clean):
        # Quick check for generic greetings
        greetings_en = ["hi", "hello", "hey", "good morning", "good evening", "good afternoon"]
        greetings_hi = ["नमस्ते", "प्रणाम", "नमस्कार", "namaste", "ram ram", "pranam", "kese ho", "kaise ho"]

        user_lower = user_message_clean.lower()
        if user_lower in greetings_en:
            return (
                "⚖️ **Greetings from Adv. Mukesh Singh Rathod's AI Legal Desk!**\n\n"
                "I am your dedicated AI Legal Assistant. I can assist you in **both English and Hindi (हिंदी)** with:\n"
                "- Analyzing legal issues under Indian Law (BNS 2023, IPC, CrPC, CPC, Cyber Laws, Property, Family Law)\n"
                "- Identifying applicable statutory sections and judicial remedies\n"
                "- Document checklists and next procedural steps\n\n"
                "Please describe your legal situation or question to begin."
            )
        elif any(g in user_lower or g in user_message_clean for g in greetings_hi):
            return (
                "⚖️ **अधिवक्ता मुकेश सिंह राठौड़ के एआई विधिक डेस्क में आपका स्वागत है!**\n\n"
                "मैं आपका समर्पित एआई कानूनी सहायक हूँ। मैं **हिंदी और अंग्रेज़ी (English)** दोनों भाषाओं में आपकी सहायता कर सकता हूँ:\n"
                "- भारतीय कानूनों (BNS 2023, IPC, CrPC, BNSS, IT Act, पारिवारिक एवं संपत्ति कानून) के तहत केस विश्लेषण\n"
                "- आपके मामले में लागू कानूनी धाराएं एवं अदालती प्रक्रियाएं\n"
                "- आवश्यक दस्तावेजों की सूची एवं आगामी कानूनी कदम\n\n"
                "कृपया अपनी कानूनी समस्या या प्रश्न बताएं।"
            )

        if is_hindi:
            return (
                "⚖️ **विधिक सूचना / Notice from AI Advocate:**\n\n"
                "यह एआई केवल **भारतीय कानूनों, धाराओं, न्यायालयीन प्रक्रियाओं एवं विधिक समस्याओं** के समाधान हेतु प्रशिक्षित है।\n\n"
                "गैर-कानूनी विषयों (जैसे सामान्य ज्ञान, मनोरंजन, प्रोग्रामिंग, खाना पकाना आदि) पर उत्तर देना संभव नहीं है। "
                "कृपया किसी विधिक शिकायत, संपत्ति विवाद, चेक बाउंस, वैवाहिक मामले या कानून से संबंधित प्रश्न पूछें।"
            )
        return (
            "⚖️ **Notice from AI Advocate:**\n\n"
            "I am designed exclusively to assist with **legal queries, statutory provisions, court procedures, and legal documentation under Indian jurisprudence**.\n\n"
            "I cannot answer unrelated questions regarding general topics, entertainment, cooking, programming, or non-legal matters. "
            "Please ask a question relating to a legal grievance, contract, dispute, or statutory law."
        )

    lang_instruction = (
        "3. LANGUAGE REQUIREMENT: The user has asked in HINDI (or Hinglish). You MUST answer completely in polite, formal, accurate HINDI (हिंदी), with relevant BNS/IPC section numbers clearly explained. Format section headers as:\n"
        "### 1. मामले का प्रकार (Case Type)\n"
        "### 2. लागू कानून एवं धाराएं (Applicable Laws & Sections)\n"
        "### 3. आवश्यक दस्तावेज एवं साक्ष्य (Required Documents)\n"
        "### 4. आगामी कानूनी कदम (Next Steps)\n"
        "### 5. संक्षिप्त निष्कर्ष (Summary)\n"
        "Add statutory disclaimer in Hindi."
        if is_hindi else
        "3. LANGUAGE REQUIREMENT: Respond in clear, professional ENGLISH."
    )

    system_prompt = f"""
You are the AI Legal Assistant for the Chambers of Advocate Mukesh Singh Rathod, an expert in Indian Law and courtroom litigation.
A user has asked a legal question:
"{user_message_clean}"

Follow these STRICT rules:
1. Provide a professional, well-structured answer formatted EXACTLY as follows:
### 1. Case Type
(Identify the legal branch, e.g., Criminal Law, Cyber Law, Matrimonial, Property Dispute, Consumer Protection)

### 2. Applicable Laws & Sections
(Cite relevant Acts such as Bharatiya Nyaya Sanhita 2023, IPC, IT Act 2000, Contract Act, CPC, BNSS, etc., with specific sections)

### 3. Required Documents
(Bullet list of essential documents and evidence needed)

### 4. Next Steps
(Actionable immediate steps: police complaint, legal notice, mediation, filing in court)

### 5. Summary
(2-3 sentence executive takeaway for the client and their advocate)

2. Add a clear disclaimer that this is informational legal intelligence and does not constitute a formal advocate-client relationship.
{lang_instruction}
"""

    if gemini_model:
        try:
            response = gemini_model.generate_content(system_prompt)
            if response and hasattr(response, "text") and response.text:
                return response.text.strip()
        except Exception as e:
            logger.warning(f"Gemini chat failed, using fallback engine: {e}")

    # Fallback to structured knowledge engine response
    cat_key = detect_category_key(user_message_clean)
    fb = LEGAL_KNOWLEDGE_BASE.get(cat_key, LEGAL_KNOWLEDGE_BASE["general"])

    if is_hindi:
        formatted_response = f"""### 1. मामले का प्रकार (Case Type)
**{cat_key.capitalize()} विधिक विवाद एवं निवारण**

### 2. लागू कानून एवं धाराएं (Applicable Laws & Sections)
- **लागू कानून:** {fb['laws']}
- **प्रमुख धाराएं:** {fb['sections']}

### 3. आवश्यक दस्तावेज एवं साक्ष्य (Required Documents)
- {fb['documents'].replace(', ', '\n- ')}

### 4. आगामी कानूनी कदम (Next Steps)
{fb['next_steps']}

### 5. संक्षिप्त निष्कर्ष (Summary)
यह मामला {cat_key.capitalize()} विधि क्षेत्र के अंतर्गत आता है। अधिकारों की रक्षा हेतु सभी साक्ष्य सुरक्षित रखें एवं {fb['court']} के समक्ष विधिक नोटिस या वाद प्रस्तुत करने हेतु विधिक परामर्श लें।

*विधिक अस्वीकरण (Disclaimer): यह विधिक जानकारी केवल प्रारंभिक मार्गदर्शन हेतु है। अदालत में औपचारिक पैरवी हेतु वरिष्ठ अधिवक्ता मुकेश सिंह राठौड़ से प्रत्यक्ष संपर्क करें।*"""
    else:
        formatted_response = f"""### 1. Case Type
**{cat_key.capitalize()} Law & Dispute Resolution**

### 2. Applicable Laws & Sections
- **Governing Statutes:** {fb['laws']}
- **Key Sections:** {fb['sections']}

### 3. Required Documents
- {fb['documents'].replace(', ', '\n- ')}

### 4. Next Steps
{fb['next_steps']}

### 5. Summary
This matter falls squarely under {cat_key.capitalize()} jurisprudence. Immediate preservation of evidence and timely legal notice or petition filing before the {fb['court']} will safeguard your rights.

*Disclaimer: This response is generated by Chambers of Adv. Mukesh Singh Rathod for informational guidance based on Indian Law. Please consult a qualified advocate for formal courtroom representation.*"""

    return formatted_response
