"""Ürün modeli."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Product:
    """Ürün veri modeli."""
    id: Optional[int] = None
    product_code: str = ""
    product_name: str = ""
    description: str = ""
    price: float = 0.0
    currency: str = "EUR"
    stock: float = 0.0
    unit: str = "Adet"

    @classmethod
    def from_row(cls, row):
        """Veritabanı satırından Product nesnesi oluşturur."""
        if row is None:
            return None
        return cls(
            id=row["id"],
            product_code=row["product_code"],
            product_name=row["product_name"],
            description=row["description"] or "",
            price=row["price"],
            currency=row["currency"],
            stock=row["stock"],
            unit=row["unit"],
        )
