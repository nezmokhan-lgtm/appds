"""
Alarab Road Trading W.L.L. — Logistics & Business Platform
Complete Phase-1+ operational foundation.
"""
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List

from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, Request, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from jose import jwt, JWTError
import bcrypt
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, DateTime,
    ForeignKey, Text, Boolean, func
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship

load_dotenv()

SECRET = os.getenv("APP_SECRET", "DEV_ONLY_CHANGE_THIS_SECRET_IMMEDIATELY")

# Database URL — Railway Postgres or local SQLite fallback
_raw_db = (os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL") or "").strip()
if not _raw_db or "://" not in _raw_db:
    DATABASE_URL = "sqlite:////tmp/alarab.db"
else:
    # SQLAlchemy prefers postgresql:// (Railway sometimes gives postgres://)
    if _raw_db.startswith("postgres://"):
        _raw_db = "postgresql://" + _raw_db[len("postgres://"):]
    DATABASE_URL = _raw_db

engine_args = {"connect_args": {"check_same_thread": False}} if DATABASE_URL.startswith("sqlite") else {"pool_pre_ping": True}
engine = create_engine(DATABASE_URL, **engine_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except Exception:
        return False

app = FastAPI(
    title="Alarab Logistics Platform",
    description="Unified Logistics & Business Management for Alarab Road Trading W.L.L.",
    version="1.0.0"
)
app.mount("/static", StaticFiles(directory=str(Path(__file__).parent / "static")), name="static")

# ─────────────────────────────────────────────
# MODELS
# ─────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(150), default="")
    role = Column(String(40), nullable=False, default="Operations")
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    email = Column(String(255), default="")
    phone = Column(String(80), default="")
    address = Column(String(300), default="")
    city = Column(String(100), default="")
    country = Column(String(80), default="Saudi Arabia")
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    shipments = relationship("Shipment", back_populates="customer_rel")
    invoices = relationship("Invoice", back_populates="customer_rel")

class Driver(Base):
    __tablename__ = "drivers"
    id = Column(Integer, primary_key=True)
    full_name = Column(String(150), nullable=False)
    phone = Column(String(80), default="")
    license_no = Column(String(80), default="")
    status = Column(String(40), default="Available")  # Available / On Trip / Off Duty
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    shipments = relationship("Shipment", back_populates="driver_rel")

class Vehicle(Base):
    __tablename__ = "vehicles"
    id = Column(Integer, primary_key=True)
    registration = Column(String(80), unique=True, nullable=False, index=True)
    vehicle_type = Column(String(100), default="Truck")
    make_model = Column(String(120), default="")
    capacity_tonnes = Column(Float, default=0)
    status = Column(String(50), default="Available")  # Available / In Use / Maintenance
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    shipments = relationship("Shipment", back_populates="vehicle_rel")

class Shipment(Base):
    __tablename__ = "shipments"
    id = Column(Integer, primary_key=True)
    reference = Column(String(40), unique=True, nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    customer_name = Column(String(200), nullable=False)  # denormalized for simplicity
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=True)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=True)
    pickup = Column(String(255), default="")
    delivery = Column(String(255), default="")
    cargo = Column(String(255), default="")
    weight_tonnes = Column(Float, default=0)
    status = Column(String(50), default="Pending")  # Pending / Confirmed / In Transit / Delivered / Cancelled
    notes = Column(Text, default="")
    scheduled_date = Column(String(20), default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    customer_rel = relationship("Customer", back_populates="shipments")
    vehicle_rel = relationship("Vehicle", back_populates="shipments")
    driver_rel = relationship("Driver", back_populates="shipments")

class Invoice(Base):
    __tablename__ = "invoices"
    id = Column(Integer, primary_key=True)
    number = Column(String(40), unique=True, nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    customer_name = Column(String(200), nullable=False)
    shipment_id = Column(Integer, ForeignKey("shipments.id"), nullable=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="SAR")
    status = Column(String(30), default="Draft")  # Draft / Sent / Paid / Overdue / Cancelled
    due_date = Column(String(20), default="")
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    customer_rel = relationship("Customer", back_populates="invoices")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True)
    user_email = Column(String(255), nullable=False)
    action = Column(String(80), nullable=False)
    entity = Column(String(80), nullable=False)
    entity_id = Column(Integer, nullable=True)
    detail = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# ─────────────────────────────────────────────
# SCHEMAS
# ─────────────────────────────────────────────

class CustomerIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    email: str = ""
    phone: str = ""
    address: str = ""
    city: str = ""
    country: str = "Saudi Arabia"
    notes: str = ""

class DriverIn(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=150)
    phone: str = ""
    license_no: str = ""
    status: str = "Available"
    notes: str = ""

class VehicleIn(BaseModel):
    registration: str = Field(..., min_length=1, max_length=80)
    vehicle_type: str = "Truck"
    make_model: str = ""
    capacity_tonnes: float = 0
    status: str = "Available"
    notes: str = ""

class ShipmentIn(BaseModel):
    customer: str = Field(..., min_length=1)
    customer_id: Optional[int] = None
    pickup: str = ""
    delivery: str = ""
    cargo: str = ""
    weight_tonnes: float = 0
    vehicle_id: Optional[int] = None
    driver_id: Optional[int] = None
    scheduled_date: str = ""
    notes: str = ""
    status: str = "Pending"

class ShipmentStatusIn(BaseModel):
    status: str

class InvoiceIn(BaseModel):
    customer: str = Field(..., min_length=1)
    customer_id: Optional[int] = None
    shipment_id: Optional[int] = None
    amount: float = Field(..., gt=0)
    currency: str = "SAR"
    due_date: str = ""
    notes: str = ""
    status: str = "Draft"

class InvoiceStatusIn(BaseModel):
    status: str

class UserIn(BaseModel):
    email: str
    password: str = Field(..., min_length=8)
    full_name: str = ""
    role: str = "Operations"

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    active: Optional[bool] = None
    password: Optional[str] = None

# ─────────────────────────────────────────────
# AUTH & HELPERS
# ─────────────────────────────────────────────

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def make_token(user: User) -> str:
    payload = {
        "sub": user.email,
        "role": user.role,
        "uid": user.id,
        "exp": datetime.utcnow() + timedelta(hours=12)
    }
    return jwt.encode(payload, SECRET, algorithm="HS256")

def current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get("alarab_session")
    if not token:
        raise HTTPException(status_code=401, detail="Sign in required")
    try:
        payload = jwt.decode(token, SECRET, algorithms=["HS256"])
        user = db.query(User).filter_by(email=payload.get("sub"), active=True).first()
        if not user:
            raise HTTPException(status_code=401, detail="Account unavailable")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Session expired or invalid")

def require_roles(*roles):
    def checker(user: User = Depends(current_user)):
        if user.role not in roles and user.role not in ("Admin", "MD"):
            raise HTTPException(status_code=403, detail="You do not have permission for this action")
        return user
    return checker

def audit(db: Session, user: User, action: str, entity: str, entity_id: int = None, detail: str = ""):
    db.add(AuditLog(
        user_email=user.email,
        action=action,
        entity=entity,
        entity_id=entity_id,
        detail=detail
    ))
    db.commit()

def next_invoice_number(db: Session) -> str:
    year = datetime.utcnow().year
    prefix = f"INV-{year}-"
    last = db.query(Invoice).filter(Invoice.number.like(f"{prefix}%")).order_by(Invoice.id.desc()).first()
    seq = int(last.number.split("-")[-1]) + 1 if last else 1
    return f"{prefix}{seq:04d}"

_ship_seq = 0
def next_shipment_ref() -> str:
    global _ship_seq
    _ship_seq += 1
    ts = datetime.utcnow()
    return f"SHP-{ts:%Y%m%d}-{ts.strftime('%H%M%S')}-{_ship_seq:03d}"

# ─────────────────────────────────────────────
# SEED DATA
# ─────────────────────────────────────────────

def seed():
    db = SessionLocal()
    try:
        if not db.query(User).filter_by(email="admin@alarab.local").first():
            db.add(User(
                email="admin@alarab.local",
                password_hash=hash_password("ChangeMe123!"),
                full_name="Platform Administrator",
                role="Admin"
            ))
            db.add(User(
                email="ops@alarab.local",
                password_hash=hash_password("OpsDemo123!"),
                full_name="Operations Lead",
                role="Operations"
            ))
            db.add(User(
                email="finance@alarab.local",
                password_hash=hash_password("FinanceDemo123!"),
                full_name="Finance Manager",
                role="Finance Manager"
            ))

        if db.query(Customer).count() == 0:
            customers = [
                Customer(name="Al-Rashid Trading Co.", email="ops@alrashid.sa", phone="+966 11 234 5678", city="Riyadh", country="Saudi Arabia"),
                Customer(name="Gulf Petrochemicals", email="logistics@gulfpetro.bh", phone="+973 17 123 456", city="Manama", country="Bahrain"),
                Customer(name="Najd Construction", email="procurement@najd.sa", phone="+966 13 456 7890", city="Dammam", country="Saudi Arabia"),
                Customer(name="Eastern Logistics Hub", email="bookings@elh.sa", phone="+966 13 987 6543", city="Khobar", country="Saudi Arabia"),
            ]
            db.add_all(customers)
            db.flush()

            drivers = [
                Driver(full_name="Ahmed Al-Harbi", phone="+966 50 111 2233", license_no="SA-DRV-88421", status="Available"),
                Driver(full_name="Khalid Al-Qahtani", phone="+966 55 444 5566", license_no="SA-DRV-11902", status="On Trip"),
                Driver(full_name="Faisal Al-Dosari", phone="+966 54 777 8899", license_no="SA-DRV-33017", status="Available"),
            ]
            db.add_all(drivers)
            db.flush()

            vehicles = [
                Vehicle(registration="RYD-4521", vehicle_type="Trailer", make_model="Volvo FH16", capacity_tonnes=40, status="Available"),
                Vehicle(registration="DMM-8830", vehicle_type="Flatbed", make_model="Mercedes Actros", capacity_tonnes=30, status="In Use"),
                Vehicle(registration="JED-1102", vehicle_type="Reefer", make_model="Scania R450", capacity_tonnes=25, status="Available"),
                Vehicle(registration="KHB-7744", vehicle_type="Tank", make_model="MAN TGX", capacity_tonnes=35, status="Maintenance"),
            ]
            db.add_all(vehicles)
            db.flush()

            c1, c2, c3 = customers[0], customers[1], customers[2]
            v1, v2 = vehicles[0], vehicles[1]
            d1, d2 = drivers[0], drivers[1]

            shipments = [
                Shipment(reference=next_shipment_ref(), customer_id=c1.id, customer_name=c1.name,
                         vehicle_id=v2.id, driver_id=d2.id, pickup="Riyadh Industrial City",
                         delivery="Dammam Port", cargo="Steel coils", weight_tonnes=28,
                         status="In Transit", scheduled_date="2026-11-05"),
                Shipment(reference=next_shipment_ref(), customer_id=c2.id, customer_name=c2.name,
                         pickup="Jubail", delivery="Manama Free Zone", cargo="Chemical drums",
                         weight_tonnes=18, status="Confirmed", scheduled_date="2026-11-07"),
                Shipment(reference=next_shipment_ref(), customer_id=c3.id, customer_name=c3.name,
                         pickup="Jeddah", delivery="Riyadh", cargo="Construction materials",
                         weight_tonnes=22, status="Pending", scheduled_date="2026-11-08"),
                Shipment(reference=next_shipment_ref(), customer_id=c1.id, customer_name=c1.name,
                         vehicle_id=v1.id, driver_id=d1.id, pickup="Yanbu", delivery="Riyadh",
                         cargo="Industrial equipment", weight_tonnes=15, status="Delivered",
                         scheduled_date="2026-11-01"),
            ]
            db.add_all(shipments)
            db.flush()

            invs = [
                Invoice(number="INV-2026-0001", customer_id=c1.id, customer_name=c1.name,
                        shipment_id=shipments[3].id, amount=18500, currency="SAR", status="Paid",
                        due_date="2026-11-15"),
                Invoice(number="INV-2026-0002", customer_id=c2.id, customer_name=c2.name,
                        shipment_id=shipments[1].id, amount=12400, currency="BHD", status="Sent",
                        due_date="2026-11-20"),
                Invoice(number="INV-2026-0003", customer_id=c3.id, customer_name=c3.name,
                        amount=9800, currency="SAR", status="Draft", due_date="2026-11-25"),
            ]
            db.add_all(invs)

        db.commit()
    finally:
        db.close()

seed()

# ─────────────────────────────────────────────
# AUTH ROUTES
# ─────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def home():
    return (Path(__file__).parent / "static" / "index.html").read_text(encoding="utf-8")

@app.post("/login")
def login(email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=email.lower().strip(), active=True).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    response = RedirectResponse("/", status_code=303)
    response.set_cookie(
        "alarab_session", make_token(user),
        httponly=True, secure=False, samesite="lax",
        max_age=12 * 60 * 60, path="/"
    )
    return response

@app.post("/logout")
def logout():
    response = RedirectResponse("/", status_code=303)
    response.delete_cookie("alarab_session", path="/")
    return response

@app.get("/api/me")
def me(user: User = Depends(current_user)):
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role
    }

# ─────────────────────────────────────────────
# DASHBOARD / SUMMARY
# ─────────────────────────────────────────────

@app.get("/api/summary")
def summary(user: User = Depends(current_user), db: Session = Depends(get_db)):
    total_shipments = db.query(Shipment).count()
    active = db.query(Shipment).filter(Shipment.status.in_(["Pending", "Confirmed", "In Transit"])).count()
    delivered = db.query(Shipment).filter(Shipment.status == "Delivered").count()
    revenue = db.query(func.coalesce(func.sum(Invoice.amount), 0)).filter(Invoice.status == "Paid").scalar() or 0
    pending_invoices = db.query(Invoice).filter(Invoice.status.in_(["Draft", "Sent", "Overdue"])).count()
    available_vehicles = db.query(Vehicle).filter(Vehicle.status == "Available").count()
    available_drivers = db.query(Driver).filter(Driver.status == "Available").count()

    recent = db.query(AuditLog).order_by(AuditLog.id.desc()).limit(8).all()
    recent_activity = [{
        "user": r.user_email,
        "action": r.action,
        "entity": r.entity,
        "detail": r.detail,
        "at": r.created_at.isoformat() if r.created_at else ""
    } for r in recent]

    return {
        "customers": db.query(Customer).count(),
        "vehicles": db.query(Vehicle).count(),
        "drivers": db.query(Driver).count(),
        "shipments": total_shipments,
        "active_shipments": active,
        "delivered_shipments": delivered,
        "invoices": db.query(Invoice).count(),
        "pending_invoices": pending_invoices,
        "paid_revenue": round(float(revenue), 2),
        "available_vehicles": available_vehicles,
        "available_drivers": available_drivers,
        "recent_activity": recent_activity
    }

# ─────────────────────────────────────────────
# CUSTOMERS
# ─────────────────────────────────────────────

@app.get("/api/customers")
def list_customers(
    q: str = Query(""),
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Customer)
    if q.strip():
        like = f"%{q.strip()}%"
        query = query.filter(
            (Customer.name.ilike(like)) |
            (Customer.email.ilike(like)) |
            (Customer.phone.ilike(like)) |
            (Customer.city.ilike(like))
        )
    rows = query.order_by(Customer.id.desc()).all()
    return [{
        "id": x.id, "name": x.name, "email": x.email, "phone": x.phone,
        "address": x.address, "city": x.city, "country": x.country, "notes": x.notes,
        "created_at": x.created_at.isoformat() if x.created_at else ""
    } for x in rows]

@app.post("/api/customers")
def create_customer(
    data: CustomerIn,
    user: User = Depends(require_roles("Admin", "MD", "Operations", "Sales Manager")),
    db: Session = Depends(get_db)
):
    obj = Customer(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    audit(db, user, "CREATE", "Customer", obj.id, obj.name)
    return {"id": obj.id, "name": obj.name}

@app.put("/api/customers/{cid}")
def update_customer(
    cid: int,
    data: CustomerIn,
    user: User = Depends(require_roles("Admin", "MD", "Operations", "Sales Manager")),
    db: Session = Depends(get_db)
):
    obj = db.query(Customer).get(cid)
    if not obj:
        raise HTTPException(404, "Customer not found")
    for k, v in data.model_dump().items():
        setattr(obj, k, v)
    db.commit()
    audit(db, user, "UPDATE", "Customer", obj.id, obj.name)
    return {"id": obj.id, "name": obj.name}

# ─────────────────────────────────────────────
# DRIVERS
# ─────────────────────────────────────────────

@app.get("/api/drivers")
def list_drivers(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.query(Driver).order_by(Driver.id.desc()).all()
    return [{
        "id": x.id, "full_name": x.full_name, "phone": x.phone,
        "license_no": x.license_no, "status": x.status, "notes": x.notes
    } for x in rows]

@app.post("/api/drivers")
def create_driver(
    data: DriverIn,
    user: User = Depends(require_roles("Admin", "MD", "Operations", "Transport Manager")),
    db: Session = Depends(get_db)
):
    obj = Driver(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    audit(db, user, "CREATE", "Driver", obj.id, obj.full_name)
    return {"id": obj.id, "full_name": obj.full_name}

@app.put("/api/drivers/{did}")
def update_driver(
    did: int,
    data: DriverIn,
    user: User = Depends(require_roles("Admin", "MD", "Operations", "Transport Manager")),
    db: Session = Depends(get_db)
):
    obj = db.query(Driver).get(did)
    if not obj:
        raise HTTPException(404, "Driver not found")
    for k, v in data.model_dump().items():
        setattr(obj, k, v)
    db.commit()
    audit(db, user, "UPDATE", "Driver", obj.id, obj.full_name)
    return {"id": obj.id}

# ─────────────────────────────────────────────
# VEHICLES
# ─────────────────────────────────────────────

@app.get("/api/vehicles")
def list_vehicles(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.query(Vehicle).order_by(Vehicle.id.desc()).all()
    return [{
        "id": x.id, "registration": x.registration, "vehicle_type": x.vehicle_type,
        "make_model": x.make_model, "capacity_tonnes": x.capacity_tonnes,
        "status": x.status, "notes": x.notes
    } for x in rows]

@app.post("/api/vehicles")
def create_vehicle(
    data: VehicleIn,
    user: User = Depends(require_roles("Admin", "MD", "Operations", "Transport Manager")),
    db: Session = Depends(get_db)
):
    if db.query(Vehicle).filter_by(registration=data.registration.strip()).first():
        raise HTTPException(409, "Vehicle registration already exists")
    obj = Vehicle(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    audit(db, user, "CREATE", "Vehicle", obj.id, obj.registration)
    return {"id": obj.id, "registration": obj.registration}

@app.put("/api/vehicles/{vid}")
def update_vehicle(
    vid: int,
    data: VehicleIn,
    user: User = Depends(require_roles("Admin", "MD", "Operations", "Transport Manager")),
    db: Session = Depends(get_db)
):
    obj = db.query(Vehicle).get(vid)
    if not obj:
        raise HTTPException(404, "Vehicle not found")
    for k, v in data.model_dump().items():
        setattr(obj, k, v)
    db.commit()
    audit(db, user, "UPDATE", "Vehicle", obj.id, obj.registration)
    return {"id": obj.id}

# ─────────────────────────────────────────────
# SHIPMENTS
# ─────────────────────────────────────────────

@app.get("/api/shipments")
def list_shipments(
    status: str = Query(""),
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Shipment)
    if status.strip():
        query = query.filter(Shipment.status == status.strip())
    rows = query.order_by(Shipment.id.desc()).all()
    return [{
        "id": x.id,
        "reference": x.reference,
        "customer": x.customer_name,
        "customer_id": x.customer_id,
        "pickup": x.pickup,
        "delivery": x.delivery,
        "cargo": x.cargo,
        "weight_tonnes": x.weight_tonnes,
        "status": x.status,
        "vehicle_id": x.vehicle_id,
        "driver_id": x.driver_id,
        "vehicle": x.vehicle_rel.registration if x.vehicle_rel else "",
        "driver": x.driver_rel.full_name if x.driver_rel else "",
        "scheduled_date": x.scheduled_date,
        "notes": x.notes,
        "created_at": x.created_at.isoformat() if x.created_at else ""
    } for x in rows]

@app.post("/api/shipments")
def create_shipment(
    data: ShipmentIn,
    user: User = Depends(require_roles("Admin", "MD", "Operations")),
    db: Session = Depends(get_db)
):
    ref = next_shipment_ref()
    obj = Shipment(
        reference=ref,
        customer_id=data.customer_id,
        customer_name=data.customer.strip(),
        pickup=data.pickup,
        delivery=data.delivery,
        cargo=data.cargo,
        weight_tonnes=data.weight_tonnes,
        vehicle_id=data.vehicle_id,
        driver_id=data.driver_id,
        scheduled_date=data.scheduled_date,
        notes=data.notes,
        status=data.status or "Pending"
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)

    # Update vehicle/driver status if assigned
    if obj.vehicle_id:
        v = db.query(Vehicle).get(obj.vehicle_id)
        if v and v.status == "Available":
            v.status = "In Use"
    if obj.driver_id:
        d = db.query(Driver).get(obj.driver_id)
        if d and d.status == "Available":
            d.status = "On Trip"
    db.commit()

    audit(db, user, "CREATE", "Shipment", obj.id, ref)
    return {"id": obj.id, "reference": ref}

@app.put("/api/shipments/{sid}/status")
def update_shipment_status(
    sid: int,
    data: ShipmentStatusIn,
    user: User = Depends(require_roles("Admin", "MD", "Operations", "Transport Manager")),
    db: Session = Depends(get_db)
):
    allowed = {"Pending", "Confirmed", "In Transit", "Delivered", "Cancelled"}
    if data.status not in allowed:
        raise HTTPException(400, f"Status must be one of: {', '.join(sorted(allowed))}")
    obj = db.query(Shipment).get(sid)
    if not obj:
        raise HTTPException(404, "Shipment not found")
    old = obj.status
    obj.status = data.status
    obj.updated_at = datetime.utcnow()

    # Free resources when delivered or cancelled
    if data.status in ("Delivered", "Cancelled"):
        if obj.vehicle_id:
            v = db.query(Vehicle).get(obj.vehicle_id)
            if v:
                v.status = "Available"
        if obj.driver_id:
            d = db.query(Driver).get(obj.driver_id)
            if d:
                d.status = "Available"

    db.commit()
    audit(db, user, "STATUS", "Shipment", obj.id, f"{old} → {data.status}")
    return {"id": obj.id, "status": obj.status}

@app.put("/api/shipments/{sid}")
def update_shipment(
    sid: int,
    data: ShipmentIn,
    user: User = Depends(require_roles("Admin", "MD", "Operations")),
    db: Session = Depends(get_db)
):
    obj = db.query(Shipment).get(sid)
    if not obj:
        raise HTTPException(404, "Shipment not found")
    obj.customer_name = data.customer.strip()
    obj.customer_id = data.customer_id
    obj.pickup = data.pickup
    obj.delivery = data.delivery
    obj.cargo = data.cargo
    obj.weight_tonnes = data.weight_tonnes
    obj.vehicle_id = data.vehicle_id
    obj.driver_id = data.driver_id
    obj.scheduled_date = data.scheduled_date
    obj.notes = data.notes
    if data.status:
        obj.status = data.status
    obj.updated_at = datetime.utcnow()
    db.commit()
    audit(db, user, "UPDATE", "Shipment", obj.id, obj.reference)
    return {"id": obj.id}

# ─────────────────────────────────────────────
# INVOICES
# ─────────────────────────────────────────────

@app.get("/api/invoices")
def list_invoices(
    status: str = Query(""),
    user: User = Depends(current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Invoice)
    if status.strip():
        query = query.filter(Invoice.status == status.strip())
    rows = query.order_by(Invoice.id.desc()).all()
    return [{
        "id": x.id,
        "number": x.number,
        "customer": x.customer_name,
        "customer_id": x.customer_id,
        "shipment_id": x.shipment_id,
        "amount": x.amount,
        "currency": x.currency,
        "status": x.status,
        "due_date": x.due_date,
        "notes": x.notes,
        "created_at": x.created_at.isoformat() if x.created_at else ""
    } for x in rows]

@app.post("/api/invoices")
def create_invoice(
    data: InvoiceIn,
    user: User = Depends(require_roles("Admin", "MD", "Finance Manager", "Accountant")),
    db: Session = Depends(get_db)
):
    number = next_invoice_number(db)
    obj = Invoice(
        number=number,
        customer_id=data.customer_id,
        customer_name=data.customer.strip(),
        shipment_id=data.shipment_id,
        amount=data.amount,
        currency=data.currency.upper()[:3],
        due_date=data.due_date,
        notes=data.notes,
        status=data.status or "Draft"
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    audit(db, user, "CREATE", "Invoice", obj.id, number)
    return {"id": obj.id, "number": number}

@app.put("/api/invoices/{iid}/status")
def update_invoice_status(
    iid: int,
    data: InvoiceStatusIn,
    user: User = Depends(require_roles("Admin", "MD", "Finance Manager", "Accountant")),
    db: Session = Depends(get_db)
):
    allowed = {"Draft", "Sent", "Paid", "Overdue", "Cancelled"}
    if data.status not in allowed:
        raise HTTPException(400, f"Status must be one of: {', '.join(sorted(allowed))}")
    obj = db.query(Invoice).get(iid)
    if not obj:
        raise HTTPException(404, "Invoice not found")
    old = obj.status
    obj.status = data.status
    obj.updated_at = datetime.utcnow()
    db.commit()
    audit(db, user, "STATUS", "Invoice", obj.id, f"{old} → {data.status}")
    return {"id": obj.id, "status": obj.status}

# ─────────────────────────────────────────────
# USERS (Admin only)
# ─────────────────────────────────────────────

@app.get("/api/users")
def list_users(user: User = Depends(require_roles("Admin", "MD")), db: Session = Depends(get_db)):
    rows = db.query(User).order_by(User.id).all()
    return [{
        "id": x.id, "email": x.email, "full_name": x.full_name,
        "role": x.role, "active": x.active,
        "created_at": x.created_at.isoformat() if x.created_at else ""
    } for x in rows]

@app.post("/api/users")
def create_user(
    data: UserIn,
    user: User = Depends(require_roles("Admin")),
    db: Session = Depends(get_db)
):
    email = data.email.lower().strip()
    if db.query(User).filter_by(email=email).first():
        raise HTTPException(409, "Email already registered")
    obj = User(
        email=email,
        password_hash=hash_password(data.password),
        full_name=data.full_name,
        role=data.role
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    audit(db, user, "CREATE", "User", obj.id, email)
    return {"id": obj.id, "email": obj.email}

@app.put("/api/users/{uid}")
def update_user(
    uid: int,
    data: UserUpdate,
    user: User = Depends(require_roles("Admin")),
    db: Session = Depends(get_db)
):
    obj = db.query(User).get(uid)
    if not obj:
        raise HTTPException(404, "User not found")
    if data.full_name is not None:
        obj.full_name = data.full_name
    if data.role is not None:
        obj.role = data.role
    if data.active is not None:
        obj.active = data.active
    if data.password:
        obj.password_hash = hash_password(data.password)
    db.commit()
    audit(db, user, "UPDATE", "User", obj.id, obj.email)
    return {"id": obj.id}

# ─────────────────────────────────────────────
# AUDIT
# ─────────────────────────────────────────────

@app.get("/api/audit")
def audit_logs(
    user: User = Depends(require_roles("Admin", "MD")),
    db: Session = Depends(get_db)
):
    rows = db.query(AuditLog).order_by(AuditLog.id.desc()).limit(150).all()
    return [{
        "id": x.id,
        "user": x.user_email,
        "action": x.action,
        "entity": x.entity,
        "entity_id": x.entity_id,
        "detail": x.detail,
        "created_at": x.created_at.isoformat() if x.created_at else ""
    } for x in rows]
