"""Uygulama geneli sabitler — tek kaynak, tüm modüller buradan import eder."""

SYM_MAP = {"TL": "₺", "EUR": "€", "USD": "$"}

STATUS_ORDER = ["Beklemede", "Onaylandı", "İptal"]

STATUS_CONFIG = {
    "Beklemede": {"bg": "#fff8e1", "fg": "#b45309", "dot": "#f59e0b"},
    "Onaylandı": {"bg": "#ecfdf5", "fg": "#065f46", "dot": "#10b981"},
    "İptal":     {"bg": "#fef2f2", "fg": "#991b1b", "dot": "#ef4444"},
}
