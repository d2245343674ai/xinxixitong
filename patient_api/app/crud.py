import sqlite3
from typing import Any, Optional

from .database import get_connection
from .schemas import PatientCreate, PatientUpdate, mask_id_card

PATIENT_COLUMNS = [
    "id", "name", "gender", "birth_date", "phone",
    "id_card_masked", "address", "created_at", "updated_at",
]


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    d = {k: row[k] for k in PATIENT_COLUMNS}
    return d


def list_patients(
    keyword: Optional[str] = None,
    gender: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[dict[str, Any]], int]:
    conds: list[str] = []
    params: list[Any] = []
    if keyword:
        conds.append("(name LIKE ? OR phone LIKE ? OR id_card_last4 = ?)")
        like = f"%{keyword}%"
        params += [like, like, keyword]
    if gender:
        conds.append("gender = ?")
        params.append(gender)
    where = (" WHERE " + " AND ".join(conds)) if conds else ""

    conn = get_connection()
    try:
        total = conn.execute(f"SELECT COUNT(*) AS c FROM patients{where}", params).fetchone()["c"]
        offset = (page - 1) * page_size
        rows = conn.execute(
            f"SELECT {', '.join(PATIENT_COLUMNS)} FROM patients{where} "
            f"ORDER BY id DESC LIMIT ? OFFSET ?",
            params + [page_size, offset],
        ).fetchall()
        return [_row_to_dict(r) for r in rows], total
    finally:
        conn.close()


def get_patient(patient_id: int) -> Optional[dict[str, Any]]:
    conn = get_connection()
    try:
        row = conn.execute(
            f"SELECT {', '.join(PATIENT_COLUMNS)} FROM patients WHERE id = ?",
            (patient_id,),
        ).fetchone()
        return _row_to_dict(row) if row else None
    finally:
        conn.close()


def create_patient(data: PatientCreate) -> dict[str, Any]:
    masked, last4, digest = mask_id_card(data.id_card) if data.id_card else (None, None, None)
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO patients (name, gender, birth_date, phone, id_card_masked, id_card_last4, id_card_hash, address) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (data.name, data.gender, data.birth_date, data.phone, masked, last4, digest, data.address),
        )
        conn.commit()
        return get_patient(cur.lastrowid)
    finally:
        conn.close()


def update_patient(patient_id: int, data: PatientUpdate) -> Optional[dict[str, Any]]:
    fields: dict[str, Any] = data.model_dump(exclude_unset=True)
    if "id_card" in fields:
        raw = fields.pop("id_card")
        if raw:
            masked, last4, digest = mask_id_card(raw)
            fields["id_card_masked"] = masked
            fields["id_card_last4"] = last4
            fields["id_card_hash"] = digest
    if not fields:
        return get_patient(patient_id)

    set_clause = ", ".join(f"{k} = ?" for k in fields)
    set_clause += ", updated_at = datetime('now', 'localtime')"
    params = list(fields.values()) + [patient_id]

    conn = get_connection()
    try:
        cur = conn.execute(f"UPDATE patients SET {set_clause} WHERE id = ?", params)
        conn.commit()
        if cur.rowcount == 0:
            return None
        return get_patient(patient_id)
    finally:
        conn.close()


def delete_patient(patient_id: int) -> bool:
    conn = get_connection()
    try:
        cur = conn.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def phone_exists(phone: str, exclude_id: Optional[int] = None) -> bool:
    conn = get_connection()
    try:
        if exclude_id is None:
            row = conn.execute("SELECT 1 FROM patients WHERE phone = ?", (phone,)).fetchone()
        else:
            row = conn.execute(
                "SELECT 1 FROM patients WHERE phone = ? AND id != ?", (phone, exclude_id)
            ).fetchone()
        return row is not None
    finally:
        conn.close()


def id_card_exists(digest: str, exclude_id: Optional[int] = None) -> bool:
    conn = get_connection()
    try:
        if exclude_id is None:
            row = conn.execute(
                "SELECT 1 FROM patients WHERE id_card_hash = ?", (digest,)
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT 1 FROM patients WHERE id_card_hash = ? AND id != ?", (digest, exclude_id)
            ).fetchone()
        return row is not None
    finally:
        conn.close()
