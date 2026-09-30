import hashlib
import re
from typing import Optional
from pydantic import BaseModel, Field, field_validator


def mask_id_card(id_card: str) -> tuple[str, str, str]:
    """Return (masked, last4, sha256_hash) for a raw id card number."""
    id_card = id_card.strip()
    if len(id_card) == 18:
        masked = id_card[:6] + "********" + id_card[-4:]
    elif len(id_card) == 15:
        masked = id_card[:6] + "*****" + id_card[-4:]
    elif len(id_card) > 2:
        masked = id_card[0] + "*" * (len(id_card) - 2) + id_card[-1]
    else:
        masked = id_card
    last4 = id_card[-4:] if len(id_card) >= 4 else id_card
    digest = hashlib.sha256(id_card.encode("utf-8")).hexdigest()
    return masked, last4, digest


class PatientCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="患者姓名")
    gender: str = Field(..., description="性别: male/female")
    birth_date: Optional[str] = Field(None, description="出生日期 YYYY-MM-DD")
    phone: str = Field(..., description="手机号")
    id_card: Optional[str] = Field(None, description="身份证号(明文，仅用于脱敏存储)")
    address: Optional[str] = Field(None, max_length=200)

    @field_validator("gender")
    @classmethod
    def check_gender(cls, v: str) -> str:
        if v not in ("male", "female"):
            raise ValueError("gender must be 'male' or 'female'")
        return v

    @field_validator("phone")
    @classmethod
    def check_phone(cls, v: str) -> str:
        if not re.fullmatch(r"1\d{10}", v):
            raise ValueError("phone must be an 11-digit mobile number")
        return v


class PatientUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    gender: Optional[str] = None
    birth_date: Optional[str] = None
    phone: Optional[str] = None
    id_card: Optional[str] = None
    address: Optional[str] = Field(None, max_length=200)

    @field_validator("gender")
    @classmethod
    def check_gender(cls, v):
        if v is not None and v not in ("male", "female"):
            raise ValueError("gender must be 'male' or 'female'")
        return v

    @field_validator("phone")
    @classmethod
    def check_phone(cls, v):
        if v is not None and not re.fullmatch(r"1\d{10}", v):
            raise ValueError("phone must be an 11-digit mobile number")
        return v
