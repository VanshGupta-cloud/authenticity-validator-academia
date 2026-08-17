import uuid
from datetime import datetime
from src.database import SessionLocal, Base, engine
from src import models
from src.security import hash_password
from src.certificate_crypto import build_canonical_payload, hash_certificate, sign_hash

def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Check if institution exists
    inst = db.query(models.Institution).first()
    if not inst:
        inst = models.Institution(
            id=str(uuid.uuid4()),
            name="Global Institute of Technology",
            code="GIT",
            email="admin@git.edu",
            password_hash=hash_password("admin123"),
            is_verified=True,
            created_at=datetime.utcnow()
        )
        db.add(inst)
        db.commit()
        db.refresh(inst)

    # Check if issuer user exists
    issuer = db.query(models.User).filter(models.User.email == "issuer@git.edu").first()
    if not issuer:
        issuer = models.User(
            id=str(uuid.uuid4()),
            institution_id=inst.id,
            full_name="Dr. Robert Sterling",
            email="issuer@git.edu",
            password_hash=hash_password("issuer123"),
            role="ISSUER",
            created_at=datetime.utcnow()
        )
        db.add(issuer)

    # Check if student exists
    student = db.query(models.User).filter(models.User.email == "student@git.edu").first()
    if not student:
        student = models.User(
            id=str(uuid.uuid4()),
            institution_id=inst.id,
            full_name="Elena R. Vance",
            email="student@git.edu",
            password_hash=hash_password("student123"),
            role="STUDENT",
            created_at=datetime.utcnow()
        )
        db.add(student)

    db.commit()

    # Seed demo certificates matching template screenshots
    demo_certs = [
        {
            "cert_num": "AVFA-GIT-2024-001",
            "name": "Elena R. Vance",
            "roll": "CS-2024-001",
            "course": "Master of Science in Computer Science",
            "date": "2024-10-24",
            "cgpa": "9.82 / 10.0",
            "marks": "98.2%",
            "status": "ISSUED",
            "rev_reason": None,
        },
        {
            "cert_num": "CERT-2024-0042",
            "name": "Eleanor Vance",
            "roll": "CS-2024-015",
            "course": "B.Sc Computer Science",
            "date": "2024-10-24",
            "cgpa": "3.85 / 4.0",
            "marks": "92.5%",
            "status": "ISSUED",
            "rev_reason": None,
        },
        {
            "cert_num": "CERT-2024-0039",
            "name": "Julian Drake",
            "roll": "HA-2024-088",
            "course": "M.A. History",
            "date": "2024-10-22",
            "cgpa": "3.92 / 4.0",
            "marks": "94.0%",
            "status": "ISSUED",
            "rev_reason": None,
        },
        {
            "cert_num": "CERT-2024-0034",
            "name": "Marcus Thorne",
            "roll": "BBA-2024-102",
            "course": "BBA Business Admin",
            "date": "2024-10-18",
            "cgpa": "2.40 / 4.0",
            "marks": "65.0%",
            "status": "REVOKED",
            "rev_reason": "Administrative credential audit failed - incomplete prerequisite credits",
        },
        {
            "cert_num": "CERT-2024-0028",
            "name": "Sarah Jenkins",
            "roll": "PH-2024-003",
            "course": "Ph.D Physics",
            "date": "2024-09-30",
            "cgpa": "4.00 / 4.0",
            "marks": "99.0%",
            "status": "ISSUED",
            "rev_reason": None,
        },
        {
            "cert_num": "CERT-2024-0115",
            "name": "Jane Doe",
            "roll": "CS-2024-009",
            "course": "Master of Science in Computer Science",
            "date": "2024-05-15",
            "cgpa": "3.95 / 4.0",
            "marks": "96.5%",
            "status": "ISSUED",
            "rev_reason": None,
        }
    ]

    for item in demo_certs:
        existing = db.query(models.Certificate).filter(models.Certificate.certificate_number == item["cert_num"]).first()
        if not existing:
            payload = build_canonical_payload(
                student_name=item["name"],
                student_roll_no=item["roll"],
                degree_name=item["course"],
                issue_date=item["date"],
                institution_id=inst.id
            )
            h = hash_certificate(payload)
            sig = sign_hash(h)
            
            c = models.Certificate(
                id=str(uuid.uuid4()),
                certificate_number=item["cert_num"],
                institution_id=inst.id,
                issuer_id=issuer.id if issuer else None,
                student_name=item["name"],
                student_roll_no=item["roll"],
                course_name=item["course"],
                issue_date=item["date"],
                cgpa=item["cgpa"],
                marks=item["marks"],
                sha256_hash=h,
                digital_signature=sig,
                status=item["status"],
                revocation_reason=item["rev_reason"],
                revoked_at=datetime.utcnow() if item["status"] == "REVOKED" else None,
                qr_code_url=f"/verify?hash={h}",
                pdf_url=f"/api/v1/certificates/download/{item['cert_num']}",
                created_at=datetime.utcnow()
            )
            db.add(c)

    db.commit()
    db.close()
    print("Database schema and demo seed data initialized successfully!")

if __name__ == "__main__":
    init_db()
