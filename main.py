import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import User, Medicine, Doctor, Prescription, Consultation, Order, OrderItem, IdResponse, MessageResponse, Paginated

app = FastAPI(title="Raksha API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Helpers
class MongoJSONEncoder(BaseModel):
    class Config:
        json_encoders = {ObjectId: str}

def to_public(doc: dict):
    if not doc:
        return doc
    doc["id"] = str(doc.pop("_id"))
    return doc


@app.get("/", response_model=MessageResponse)
async def read_root():
    return {"message": "Raksha FastAPI backend is running"}

@app.get("/api/hello", response_model=MessageResponse)
async def hello():
    return {"message": "Hello from Raksha backend API!"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": "❌ Not Set",
        "database_name": "❌ Not Set",
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response


# ------------------------------
# Public API: Medicines
# ------------------------------
@app.get("/api/medicines", response_model=Paginated)
def list_medicines(q: Optional[str] = None, category: Optional[str] = None, limit: int = 50, skip: int = 0):
    filt = {}
    if q:
        filt["name"] = {"$regex": q, "$options": "i"}
    if category:
        filt["category"] = category
    total = db.medicine.count_documents(filt) if db else 0
    items = []
    if db:
        cursor = db.medicine.find(filt).skip(skip).limit(limit)
        items = [to_public(x) for x in cursor]
    return {"total": total, "items": items}


@app.get("/api/medicines/{id}")
def get_medicine(id: str):
    if not db:
        raise HTTPException(500, "Database not configured")
    doc = db.medicine.find_one({"_id": ObjectId(id)})
    if not doc:
        raise HTTPException(404, "Medicine not found")
    return to_public(doc)


# ------------------------------
# Doctors
# ------------------------------
@app.get("/api/doctors", response_model=Paginated)
def list_doctors(q: Optional[str] = None, specialty: Optional[str] = None, limit: int = 50, skip: int = 0):
    filt = {}
    if q:
        filt["name"] = {"$regex": q, "$options": "i"}
    if specialty:
        filt["specialty"] = specialty
    total = db.doctor.count_documents(filt) if db else 0
    items = []
    if db:
        cursor = db.doctor.find(filt).skip(skip).limit(limit)
        items = [to_public(x) for x in cursor]
    return {"total": total, "items": items}


@app.get("/api/doctors/{id}")
def get_doctor(id: str):
    if not db:
        raise HTTPException(500, "Database not configured")
    doc = db.doctor.find_one({"_id": ObjectId(id)})
    if not doc:
        raise HTTPException(404, "Doctor not found")
    return to_public(doc)


# ------------------------------
# Prescriptions
# ------------------------------
@app.get("/api/prescriptions", response_model=Paginated)
def list_prescriptions(user_id: str, limit: int = 50, skip: int = 0):
    if not db:
        return {"total": 0, "items": []}
    filt = {"user_id": user_id}
    total = db.prescription.count_documents(filt)
    cursor = db.prescription.find(filt).skip(skip).limit(limit)
    items = [to_public(x) for x in cursor]
    return {"total": total, "items": items}


@app.post("/api/prescriptions", response_model=IdResponse)
def create_prescription(payload: Prescription):
    new_id = create_document("prescription", payload)
    return {"id": new_id}


# ------------------------------
# Consultations
# ------------------------------
@app.get("/api/consultations", response_model=Paginated)
def list_consultations(user_id: Optional[str] = None, doctor_id: Optional[str] = None, limit: int = 50, skip: int = 0):
    if not db:
        return {"total": 0, "items": []}
    filt = {}
    if user_id:
        filt["user_id"] = user_id
    if doctor_id:
        filt["doctor_id"] = doctor_id
    total = db.consultation.count_documents(filt)
    cursor = db.consultation.find(filt).skip(skip).limit(limit)
    items = [to_public(x) for x in cursor]
    return {"total": total, "items": items}


@app.post("/api/consultations", response_model=IdResponse)
def create_consultation(payload: Consultation):
    new_id = create_document("consultation", payload)
    return {"id": new_id}


# ------------------------------
# Orders
# ------------------------------
@app.get("/api/orders", response_model=Paginated)
def list_orders(user_id: str, limit: int = 50, skip: int = 0):
    if not db:
        return {"total": 0, "items": []}
    filt = {"user_id": user_id}
    total = db.order.count_documents(filt)
    cursor = db.order.find(filt).skip(skip).limit(limit)
    items = [to_public(x) for x in cursor]
    return {"total": total, "items": items}


@app.post("/api/orders", response_model=IdResponse)
def create_order(payload: Order):
    new_id = create_document("order", payload)
    return {"id": new_id}


# ------------------------------
# Optional seed endpoint for demo (uses mock data if provided from frontend later)
# ------------------------------
@app.post("/api/seed", response_model=MessageResponse)
def seed_basic():
    if not db:
        raise HTTPException(500, "Database not configured")
    # Idempotent simple seed
    if db.medicine.count_documents({}) == 0:
        db.medicine.insert_many([
            {"name": "Paracetamol", "brand": "Acme Pharma", "category": "Pain Relief", "price": 2.99, "stock": 120, "requires_rx": False},
            {"name": "Amoxicillin", "brand": "Acme Pharma", "category": "Antibiotics", "price": 5.49, "stock": 80, "requires_rx": True}
        ])
    if db.doctor.count_documents({}) == 0:
        db.doctor.insert_many([
            {"name": "Dr. A. Mehta", "specialty": "Cardiologist", "experience_years": 12, "rating": 4.8, "fee": 25.0, "languages": ["en", "hi"]},
            {"name": "Dr. S. Rao", "specialty": "Dermatologist", "experience_years": 8, "rating": 4.6, "fee": 20.0, "languages": ["en"]}
        ])
    return {"message": "Seeded demo data (if collections were empty)"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
