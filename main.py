from fastapi import FastAPI
from fastapi.responses import HTMLResponse,FileResponse
from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Boolean,
    DateTime
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from datetime import datetime
from uuid import uuid4
from difflib import SequenceMatcher
import time


# ============================================================
# DATABASE
# ============================================================

DATABASE_URL = "sqlite:///./govbridge.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# ============================================================
# DATABASE MODELS
# ============================================================

class Consent(Base):

    __tablename__ = "consents"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    citizen_id = Column(
        String,
        index=True
    )

    purpose = Column(String)

    identity = Column(
        Boolean,
        default=False
    )

    address = Column(
        Boolean,
        default=False
    )

    tax_status = Column(
        Boolean,
        default=False
    )

    granted = Column(
        Boolean,
        default=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )


class AuditLog(Base):

    __tablename__ = "audit_logs"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    citizen_id = Column(String)

    service = Column(String)

    action = Column(String)

    status = Column(String)

    response_time = Column(String)

    timestamp = Column(
        DateTime,
        default=datetime.utcnow
    )


class Application(Base):

    __tablename__ = "applications"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    application_id = Column(
        String,
        unique=True,
        index=True
    )

    citizen_id = Column(String)

    service = Column(String)

    status = Column(String)

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )


# Create database tables
Base.metadata.create_all(bind=engine)


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="GovBridge",
    description="""
    Government Digital Interoperability Platform.

    This is a hackathon prototype that demonstrates
    interoperability between multiple simulated
    government digital services.
    """,
    version="1.0.0"
)


# ============================================================
# REQUEST MODELS
# ============================================================

class ConsentRequest(BaseModel):

    citizen_id: str

    purpose: str

    identity: bool = True

    address: bool = True

    tax_status: bool = True


class CitizenRequest(BaseModel):

    citizen_id: str

    name: str

    dob: str

    aadhaar: str

    pan: str


class ApplicationRequest(BaseModel):

    citizen_id: str

    name: str

    dob: str

    aadhaar: str

    pan: str


# ============================================================
# HOME
# ============================================================

@app.get("/", response_class=HTMLResponse)
def home():
    return FileResponse("index.html")



# ============================================================
# MOCK AADHAAR SERVICE
# ============================================================

def verify_aadhaar(
    aadhaar,
    name,
    dob
):

    start = time.time()

    # Simulated Aadhaar database

    if aadhaar.endswith("1234"):

        result = {

            "service": "AADHAAR",

            "status": "VERIFIED",

            "full_name": name,

            "dob": dob,

            "address":
                "Hyderabad, Telangana"
        }

    else:

        result = {

            "service": "AADHAAR",

            "status": "NOT_FOUND"
        }

    response_time = round(
        (time.time() - start) * 1000,
        2
    )

    result["response_time"] = (
        f"{response_time} ms"
    )

    return result


# ============================================================
# MOCK PAN SERVICE
# ============================================================

def verify_pan(
    pan,
    name
):

    start = time.time()

    # Simulated PAN database

    if len(pan) == 10:

        result = {

            "service": "PAN",

            "status": "VERIFIED",

            "pan": pan,

            "holder_name":
                name.upper(),

            "pan_status":
                "ACTIVE"
        }

    else:

        result = {

            "service": "PAN",

            "status": "INVALID"
        }

    response_time = round(
        (time.time() - start) * 1000,
        2
    )

    result["response_time"] = (
        f"{response_time} ms"
    )

    return result


# ============================================================
# MOCK GST SERVICE
# ============================================================

def verify_gst(name):

    start = time.time()

    # Simulated GST database

    result = {

        "service": "GST",

        "status": "VERIFIED",

        "legal_name": name,

        "registration_status":
            "ACTIVE"
    }

    response_time = round(
        (time.time() - start) * 1000,
        2
    )

    result["response_time"] = (
        f"{response_time} ms"
    )

    return result


# ============================================================
# MOCK ADDRESS SERVICE
# ============================================================

def verify_address(address):

    start = time.time()

    if address:

        result = {

            "service": "ADDRESS",

            "status": "VERIFIED",

            "address": address
        }

    else:

        result = {

            "service": "ADDRESS",

            "status": "FAILED"
        }

    response_time = round(
        (time.time() - start) * 1000,
        2
    )

    result["response_time"] = (
        f"{response_time} ms"
    )

    return result


# ============================================================
# IDENTITY MATCHING
# ============================================================

def calculate_similarity(
    name1,
    name2
):

    if not name1 or not name2:

        return 0

    score = SequenceMatcher(
        None,
        name1.lower(),
        name2.lower()
    ).ratio()

    return round(
        score * 100,
        2
    )


# ============================================================
# CONSENT API
# ============================================================

@app.post("/api/consent")
def grant_consent(
    request: ConsentRequest,
    db: Session = Depends(get_db)
):

    consent = Consent(

        citizen_id=
            request.citizen_id,

        purpose=
            request.purpose,

        identity=
            request.identity,

        address=
            request.address,

        tax_status=
            request.tax_status,

        granted=True
    )

    db.add(consent)

    db.commit()

    db.refresh(consent)

    return {

        "success": True,

        "message":
            "Citizen consent granted",

        "consent_id":
            consent.id,

        "citizen_id":
            request.citizen_id,

        "purpose":
            request.purpose,

        "permissions": {

            "identity":
                request.identity,

            "address":
                request.address,

            "tax_status":
                request.tax_status
        }
    }


# ============================================================
# VERIFY CITIZEN
# ============================================================

@app.post("/api/verify")
def verify_citizen(
    request: CitizenRequest,
    db: Session = Depends(get_db)
):

    # --------------------------------------------------------
    # STEP 1: CHECK CONSENT
    # --------------------------------------------------------

    consent = db.query(
        Consent
    ).filter(
        Consent.citizen_id ==
            request.citizen_id,

        Consent.granted == True
    ).first()

    if not consent:

        return {

            "success": False,

            "status":
                "CONSENT_REQUIRED",

            "message":
                "Citizen consent is required before accessing government services."
        }


    # --------------------------------------------------------
    # STEP 2: AADHAAR
    # --------------------------------------------------------

    aadhaar = verify_aadhaar(

        request.aadhaar,

        request.name,

        request.dob
    )

    db.add(
        AuditLog(

            citizen_id=
                request.citizen_id,

            service=
                "AADHAAR",

            action=
                "IDENTITY_VERIFICATION",

            status=
                aadhaar["status"],

            response_time=
                aadhaar["response_time"]
        )
    )


    # --------------------------------------------------------
    # STEP 3: PAN
    # --------------------------------------------------------

    pan = verify_pan(

        request.pan,

        request.name
    )

    db.add(
        AuditLog(

            citizen_id=
                request.citizen_id,

            service=
                "PAN",

            action=
                "PAN_VERIFICATION",

            status=
                pan["status"],

            response_time=
                pan["response_time"]
        )
    )


    # --------------------------------------------------------
    # STEP 4: GST
    # --------------------------------------------------------

    gst = verify_gst(

        request.name
    )

    db.add(
        AuditLog(

            citizen_id=
                request.citizen_id,

            service=
                "GST",

            action=
                "TAX_VERIFICATION",

            status=
                gst["status"],

            response_time=
                gst["response_time"]
        )
    )


    # --------------------------------------------------------
    # STEP 5: ADDRESS
    # --------------------------------------------------------

    address = verify_address(

        aadhaar.get(
            "address"
        )
    )

    db.add(
        AuditLog(

            citizen_id=
                request.citizen_id,

            service=
                "ADDRESS",

            action=
                "ADDRESS_VERIFICATION",

            status=
                address["status"],

            response_time=
                address["response_time"]
        )
    )


    # --------------------------------------------------------
    # STEP 6: IDENTITY MATCHING
    # --------------------------------------------------------

    aadhaar_name = aadhaar.get(
        "full_name",
        ""
    )

    pan_name = pan.get(
        "holder_name",
        ""
    )

    gst_name = gst.get(
        "legal_name",
        ""
    )


    aadhaar_pan_score = (
        calculate_similarity(

            aadhaar_name,

            pan_name
        )
    )


    aadhaar_gst_score = (
        calculate_similarity(

            aadhaar_name,

            gst_name
        )
    )


    overall_score = round(

        (
            aadhaar_pan_score
            +
            aadhaar_gst_score
        ) / 2,

        2
    )


    # --------------------------------------------------------
    # STEP 7: OVERALL VERIFICATION
    # --------------------------------------------------------

    if (

        aadhaar["status"] ==
            "VERIFIED"

        and

        pan["status"] ==
            "VERIFIED"

        and

        gst["status"] ==
            "VERIFIED"

        and

        address["status"] ==
            "VERIFIED"

        and

        overall_score >= 80

    ):

        overall_status = "VERIFIED"

    else:

        overall_status ="MANUAL_VERIFICATION"


    db.commit()


    # --------------------------------------------------------
    # STEP 8: UNIFIED CITIZEN PROFILE
    # --------------------------------------------------------

    unified_profile = {

        "name":
            aadhaar.get(
                "full_name"
            ),

        "date_of_birth":
            aadhaar.get(
                "dob"
            ),

        "address":
            aadhaar.get(
                "address"
            ),

        "pan":
            pan.get(
                "pan"
            ),

        "pan_status":
            pan.get(
                "pan_status"
            ),

        "gst_status":
            gst.get(
                "registration_status"
            ),

        "identity_verified":
            overall_status ==
            "VERIFIED"
    }


    # --------------------------------------------------------
    # FINAL RESPONSE
    # --------------------------------------------------------

    return {

        "success": True,

        "citizen_id":
            request.citizen_id,

        "overall_status":
            overall_status,

        "identity_match": {

            "aadhaar_pan":
                aadhaar_pan_score,

            "aadhaar_gst":
                aadhaar_gst_score,

            "overall_confidence":
                overall_score
        },

        "unified_profile":
            unified_profile,

        "government_services": {

            "aadhaar":
                aadhaar,

            "pan":
                pan,

            "gst":
                gst,

            "address":
                address
        }
    }


# ============================================================
# BUSINESS LICENSE APPLICATION
# ============================================================

@app.post("/api/application")
def create_application(
    request: ApplicationRequest,
    db: Session = Depends(get_db)
):

    application_id = (

        "BL-"
        +
        str(uuid4())[
            :8
        ].upper()
    )


    application = Application(

        application_id=
            application_id,

        citizen_id=
            request.citizen_id,

        service=
            "BUSINESS_LICENSE",

        status=
            "SUBMITTED"
    )


    db.add(application)


    # Audit entry

    db.add(
        AuditLog(

            citizen_id=
                request.citizen_id,

            service=
                "BUSINESS_LICENSE",

            action=
                "APPLICATION_SUBMITTED",

            status=
                "SUCCESS",

            response_time=
                "0 ms"
        )
    )


    db.commit()


    return {

        "success": True,

        "message":
            "Business license application submitted",

        "application_id":
            application_id,

        "citizen_id":
            request.citizen_id,

        "service":
            "BUSINESS_LICENSE",

        "status":
            "SUBMITTED"
    }


# ============================================================
# AUDIT LOG API
# ============================================================

@app.get("/api/audit/{citizen_id}")
def get_audit_logs(

    citizen_id: str,

    db: Session = Depends(get_db)
):

    logs = db.query(
        AuditLog
    ).filter(
        AuditLog.citizen_id ==
            citizen_id
    ).order_by(
        AuditLog.timestamp
    ).all()


    return {

        "citizen_id":
            citizen_id,

        "total_transactions":
            len(logs),

        "logs": [

            {

                "service":
                    log.service,

                "action":
                    log.action,

                "status":
                    log.status,

                "response_time":
                    log.response_time,

                "timestamp":
                    log.timestamp
            }

            for log in logs
        ]
    }


# ============================================================
# APPLICATION STATUS
# ============================================================

@app.get(
    "/api/application/{application_id}"
)
def get_application(

    application_id: str,

    db: Session = Depends(get_db)
):

    application = db.query(
        Application
    ).filter(
        Application.application_id ==
            application_id
    ).first()


    if not application:

        return {

            "success": False,

            "message":
                "Application not found"
        }


    return {

        "success": True,

        "application": {

            "application_id":
                application.application_id,

            "citizen_id":
                application.citizen_id,

            "service":
                application.service,

            "status":
                application.status,

            "created_at":
                application.created_at
        }
    }

@app.get("/",response_class=HTMLResponse)
def home():
    with open("index.html","r") as file:
        return file.read()