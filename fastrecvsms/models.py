from enum import Enum
from typing import Optional

from pydantic import BaseModel


class OrderStatus(str, Enum):
    PENDING = "PENDING"
    RECEIVED = "RECEIVED"
    CANCELED = "CANCELED"
    TIMEOUT = "TIMEOUT"
    FINISHED = "FINISHED"
    BANNED = "BANNED"


class Balance(BaseModel):
    amount: float
    currency: str = "USD"
    provider: str


class ServiceInfo(BaseModel):
    name: str
    quantity: int
    price: float
    country: str = "any"


class Order(BaseModel):
    id: int
    phone: str
    country: str
    service: str
    price: float
    status: OrderStatus
    sms_code: Optional[str] = None
    sms_text: Optional[str] = None
    provider: str
    created_at: Optional[str] = None
