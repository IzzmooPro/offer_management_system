"""Teklif modeli."""
from dataclasses import dataclass, field
from typing import Optional, List
from models.offer_item import OfferItem


@dataclass
class Offer:
    """Teklif veri modeli — DB şemasıyla senkronize."""
    id: Optional[int] = None
    offer_no: str = ""
    customer_id: Optional[int] = None
    company_name: str = ""
    customer_address: str = ""
    contact_person: str = ""
    date: str = ""
    currency: str = "EUR"
    total_amount: float = 0.0
    validity: str = ""
    validity_note: str = ""
    payment_term: str = ""
    status: str = "Beklemede"
    items: List[OfferItem] = field(default_factory=list)

    @classmethod
    def from_row(cls, row):
        """Veritabanı satırından Offer nesnesi oluşturur."""
        if row is None:
            return None
        return cls(
            id=row["id"],
            offer_no=row["offer_no"],
            customer_id=row.get("customer_id"),
            company_name=row.get("company_name") or "",
            customer_address=row.get("customer_address") or "",
            contact_person=row.get("contact_person") or "",
            date=row["date"],
            currency=row["currency"],
            total_amount=row["total_amount"],
            validity=row.get("validity") or "",
            validity_note=row.get("validity_note") or "",
            payment_term=row.get("payment_term") or "",
            status=row.get("status") or "Beklemede",
        )
