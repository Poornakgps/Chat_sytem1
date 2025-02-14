from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class BuyerChat:
    chat_id: int
    message: str
    file_name: Optional[str]
    timestamp: datetime
    is_bargain: bool = False
    bargain_amount: Optional[float] = None
    payment_status: str = "pending"
    
    @classmethod
    def from_db_row(cls, row):
        return cls(
            chat_id=row[0],
            message=row[1],
            file_name=row[2],
            timestamp=datetime.fromisoformat(row[3]),
            is_bargain=bool(row[4]),
            bargain_amount=row[5],
            payment_status=row[6]
        )

@dataclass
class SellerChat:
    chat_id: int
    message: str
    file_name: Optional[str]
    timestamp: datetime
    order_status: Optional[str] = None
    bargain_status: Optional[str] = None
    payment_status: Optional[str] = None
    payment_qr_code: Optional[str] = None
    tracking_number: Optional[str] = None
    
    @classmethod
    def from_db_row(cls, row):
        return cls(
            chat_id=row[0],
            message=row[1],
            file_name=row[2],
            timestamp=datetime.fromisoformat(row[3]),
            order_status=row[4],
            bargain_status=row[5],
            payment_status=row[6],
            payment_qr_code=row[7],
            tracking_number=row[8]
        )

@dataclass
class ChatMessage:
    message: str
    file_name: Optional[str]
    timestamp: datetime
    sender: str
    type: Optional[str] = None
    amount: Optional[float] = None
    tracking: Optional[str] = None
    
    def to_dict(self):
        return {
            'message': self.message,
            'file_name': self.file_name,
            'timestamp': self.timestamp.isoformat(),
            'sender': self.sender,
            **({"type": self.type} if self.type else {}),
            **({"amount": self.amount} if self.amount else {}),
            **({"tracking": self.tracking} if self.tracking else {})
        }
