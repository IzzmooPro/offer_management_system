"""Teklif kalemi modeli."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class OfferItem:
    """Teklif kalemi veri modeli."""
    id: Optional[int] = None
    offer_id: Optional[int] = None
    product_id: Optional[int] = None
    product_code: str = ""
    product_name: str = ""
    description: str = ""
    quantity: float = 1.0
    unit: str = "Adet"
    delivery_time: str = "2-3 Hafta"
    unit_price: float = 0.0
    total_price: float = 0.0

    @classmethod
    def from_row(cls, row):
        """Veritabanı satırından OfferItem nesnesi oluşturur."""
        if row is None:
            return None
        return cls(
            id=row["id"],
            offer_id=row["offer_id"],
            product_id=row["product_id"],
            product_code=row["product_code"] or "",
            product_name=row["product_name"] or "",
            description=row["description"] or "",
            quantity=row["quantity"],
            unit=row["unit"] or "Adet",
            delivery_time=row["delivery_time"] or "2-3 Hafta",
            unit_price=row["unit_price"],
            total_price=row["total_price"],
        )
