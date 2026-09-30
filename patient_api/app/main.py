from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from . import crud
from .database import init_db
from .schemas import PatientCreate, PatientUpdate, mask_id_card

app = FastAPI(title="门诊系统 - 患者管理模块", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    init_db()


def _ok(data=None, message: str = "ok"):
    return {"code": 0, "message": message, "data": data}


@app.get("/api/patients")
def list_patients(
    keyword: Optional[str] = Query(None, description="姓名/手机号/身份证后四位"),
    gender: Optional[str] = Query(None, description="male/female"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    if gender is not None and gender not in ("male", "female"):
        raise HTTPException(status_code=422, detail={"code": 1, "message": "gender must be 'male' or 'female'"})
    items, total = crud.list_patients(keyword, gender, page, page_size)
    return _ok({
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    })


@app.post("/api/patients", status_code=201)
def create_patient(payload: PatientCreate):
    if crud.phone_exists(payload.phone):
        raise HTTPException(status_code=409, detail={"code": 1, "message": "phone already exists"})
    if payload.id_card:
        _, _, digest = mask_id_card(payload.id_card)
        if crud.id_card_exists(digest):
            raise HTTPException(status_code=409, detail={"code": 1, "message": "id_card already exists"})
    return _ok(crud.create_patient(payload), "created")


@app.get("/api/patients/{patient_id}")
def get_patient(patient_id: int):
    patient = crud.get_patient(patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail={"code": 1, "message": "patient not found"})
    return _ok(patient)


@app.put("/api/patients/{patient_id}")
def update_patient(patient_id: int, payload: PatientUpdate):
    if crud.get_patient(patient_id) is None:
        raise HTTPException(status_code=404, detail={"code": 1, "message": "patient not found"})
    if payload.phone is not None and crud.phone_exists(payload.phone, patient_id):
        raise HTTPException(status_code=409, detail={"code": 1, "message": "phone already exists"})
    if payload.id_card:
        _, _, digest = mask_id_card(payload.id_card)
        if crud.id_card_exists(digest, patient_id):
            raise HTTPException(status_code=409, detail={"code": 1, "message": "id_card already exists"})
    return _ok(crud.update_patient(patient_id, payload), "updated")


@app.delete("/api/patients/{patient_id}")
def delete_patient(patient_id: int):
    if not crud.delete_patient(patient_id):
        raise HTTPException(status_code=404, detail={"code": 1, "message": "patient not found"})
    return _ok(message="deleted")
