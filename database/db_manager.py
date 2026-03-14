"""Veritabanı yönetimi — SQLite, migration desteği."""
import sqlite3, logging
from pathlib import Path
from app_paths import DB_PATH, SCHEMA_PATH

logger = logging.getLogger("db_manager")


class DB:
    def __init__(self):
        self.db_path  = DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()
        self._migrate()

    def _get_conn(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        return conn

    def _init_schema(self):
        schema = SCHEMA_PATH.read_text(encoding="utf-8")
        with self._get_conn() as conn:
            conn.executescript(schema)
        logger.debug("Şema başlatıldı.")

    def _migrate(self):
        """Eksik sütunları mevcut DB'ye ekler — güvenli ALTER TABLE."""
        migrations = [
            ("offers", "company_name",       "TEXT DEFAULT ''"),
            ("offers", "customer_address",   "TEXT DEFAULT ''"),
            ("offers", "contact_person",     "TEXT DEFAULT ''"),
            ("offers", "validity",           "TEXT DEFAULT ''"),
            ("offers", "validity_note",      "TEXT DEFAULT ''"),
            ("offers", "payment_term",       "TEXT DEFAULT ''"),
            ("offers", "status",             "TEXT DEFAULT 'Beklemede'"),
        ]
        with self._get_conn() as conn:
            for table, col, coltype in migrations:
                try:
                    conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {coltype}")
                    logger.info("Migration: %s.%s eklendi", table, col)
                except sqlite3.OperationalError:
                    pass  # Sütun zaten var

            # Mevcut tekliflerde company_name boşsa → customers tablosundan doldur
            conn.execute("""
                UPDATE offers
                SET company_name = (
                    SELECT c.company_name FROM customers c
                    WHERE c.id = offers.customer_id
                )
                WHERE (company_name IS NULL OR company_name = '')
                  AND customer_id IS NOT NULL
            """)

    def execute(self, sql: str, params=()):
        with self._get_conn() as conn:
            cursor = conn.execute(sql, params)
            conn.commit()
            return cursor

    def fetchone(self, sql: str, params=()):
        with self._get_conn() as conn:
            return conn.execute(sql, params).fetchone()

    def fetchall(self, sql: str, params=()):
        with self._get_conn() as conn:
            return conn.execute(sql, params).fetchall()

    def transaction(self):
        """Atomik işlemler için context manager.
        
        Kullanım:
            with db.transaction() as conn:
                conn.execute("INSERT ...")
                conn.execute("INSERT ...")
            # Hata olursa otomatik ROLLBACK
        """
        return self._get_conn()

    def close(self):
        """Bağlantıyı kapat (uygulama kapanırken)."""
        logger.debug("Veritabanı bağlantısı kapatıldı.")
        global _instance
        _instance = None


_instance = None

def get_db() -> DB:
    global _instance
    if _instance is None:
        _instance = DB()
    return _instance
