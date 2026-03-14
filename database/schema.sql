-- Ürünler tablosu
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_code TEXT NOT NULL UNIQUE,
    product_name TEXT NOT NULL,
    description TEXT,
    price REAL NOT NULL DEFAULT 0,
    currency TEXT NOT NULL DEFAULT 'EUR',
    stock REAL NOT NULL DEFAULT 0,
    unit TEXT NOT NULL DEFAULT 'Adet'
);

-- Müşteriler tablosu
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT NOT NULL,
    contact_person TEXT,
    address TEXT,
    phone TEXT,
    email TEXT
);

-- Teklifler tablosu
CREATE TABLE IF NOT EXISTS offers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    offer_no TEXT NOT NULL UNIQUE,
    customer_id INTEGER,
    company_name TEXT,
    customer_address TEXT,
    contact_person TEXT,
    date TEXT NOT NULL,
    currency TEXT NOT NULL DEFAULT 'EUR',
    total_amount REAL NOT NULL DEFAULT 0,
    validity TEXT DEFAULT '',
    validity_note TEXT DEFAULT '',
    payment_term TEXT DEFAULT '',
    status TEXT DEFAULT 'Beklemede',
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL
);

-- Teklif kalemleri tablosu
CREATE TABLE IF NOT EXISTS offer_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    offer_id INTEGER NOT NULL,
    product_id INTEGER,
    product_code TEXT,
    product_name TEXT,
    description TEXT,
    quantity REAL NOT NULL DEFAULT 1,
    unit TEXT DEFAULT 'Adet',
    delivery_time TEXT DEFAULT '2-3 Hafta',
    unit_price REAL NOT NULL DEFAULT 0,
    total_price REAL NOT NULL DEFAULT 0,
    FOREIGN KEY (offer_id) REFERENCES offers(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL
);

-- Teklif sayacı tablosu
CREATE TABLE IF NOT EXISTS offer_counter (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    year INTEGER NOT NULL,
    last_number INTEGER NOT NULL DEFAULT 0
);
