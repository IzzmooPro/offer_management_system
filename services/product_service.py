"""Ürün servis katmanı."""
from typing import List, Optional
from database.db_manager import get_db
from models.product import Product


class ProductService:
    """Ürün CRUD işlemleri."""

    def get_by_code(self, code: str) -> Optional[Product]:
        """Ürün kodu ile ara (büyük/küçük harf duyarsız). Yoksa None döner."""
        db = get_db()
        row = db.fetchone(
            "SELECT * FROM products WHERE UPPER(product_code) = UPPER(?)", (code,))
        return Product.from_row(row) if row else None

    def get_all(self) -> List[Product]:
        db = get_db()
        rows = db.fetchall("SELECT * FROM products ORDER BY product_name")
        return [Product.from_row(r) for r in rows]

    def search(self, keyword: str) -> List[Product]:
        """Kod, ad veya açıklamaya göre ara (büyük/küçük harf duyarsız)."""
        db = get_db()
        kw = f"%{keyword}%"
        rows = db.fetchall(
            """SELECT * FROM products
               WHERE product_code LIKE ? OR product_name LIKE ? OR description LIKE ?
               ORDER BY product_name""",
            (kw, kw, kw))
        return [Product.from_row(r) for r in rows]

    def get_by_id(self, product_id: int) -> Optional[Product]:
        db = get_db()
        row = db.fetchone("SELECT * FROM products WHERE id = ?", (product_id,))
        return Product.from_row(row) if row else None

    def add(self, product: Product) -> int:
        db = get_db()
        cursor = db.execute(
            """INSERT INTO products (product_code, product_name, description, price, currency, stock, unit)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (product.product_code, product.product_name, product.description,
             product.price, product.currency, product.stock, product.unit))
        return cursor.lastrowid

    def update(self, product: Product):
        db = get_db()
        db.execute(
            """UPDATE products SET product_code=?, product_name=?, description=?,
               price=?, currency=?, stock=?, unit=? WHERE id=?""",
            (product.product_code, product.product_name, product.description,
             product.price, product.currency, product.stock, product.unit, product.id))

    def delete(self, product_id: int):
        db = get_db()
        db.execute("DELETE FROM products WHERE id=?", (product_id,))

    def count(self) -> int:
        db = get_db()
        row = db.fetchone("SELECT COUNT(*) as cnt FROM products")
        return row["cnt"] if row else 0
