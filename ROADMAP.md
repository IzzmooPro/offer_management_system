# 🗺️ Teklif Yönetim Sistemi — Yol Haritası

## ✅ Mevcut Durum (Masaüstü — PySide6, v1, Mart 2026)

### Tamamlanan Özellikler
- Dashboard: istatistik kartları, teklif tablosu, arama/filtre
- Teklif oluşturma: 3 adımlı wizard (Müşteri → Ürünler → Özet)
- Teklif yönetimi: düzenleme, durum güncelleme, silme, PDF oluşturma
- PDF çıktısı: logo, imzalar, Türkçe karakter (DejaVu font), geçerlilik süresi sağa hizalı
- Ürün ve müşteri CRUD
- Excel/CSV import (ürün ve müşteri)
- Excel/CSV export (teklifler)
- Açık/Koyu tema
- **Veri & Program ayrımı**: AppData veri klasörü, Documents yedek klasörü
- **Otomatik yedekleme**: kapanışta + teklif kaydında + zamanlı aralık
- **Manuel yedekleme**: kullanıcı seçtiği klasöre
- **Geri yükleme**: ZIP seç, onayla, geri yükle
- **Startup backup algılama**: boş veri klasörü → yedek öner
- **Otomatik güncelleme sistemi**: GitHub tabanlı, sessiz kontrol, Güncelle/Daha sonra
- **Güncelleme güvenliği**: veri klasörlerine dokunmaz
- Ayarlar: şirket bilgileri, yetkililer, logo/imza, PDF şablon metinleri
- Log rotasyonu (30 gün)
- F1 yardım penceresi (toggle açma/kapama)
- EXE derleme: `build_exe.bat`
- Dağıtım temizleme: `clear_for_distribution.py`
- Version: v1 (Hakkında ve başlık alanında gösterilir)
- Bağlantılar: siyah, altı çizgili (E-posta + GitHub)

### Bekleyen Küçük Özellikler
- [ ] Teklif kopyalama (duplicate/clone)
- [ ] Inter font desteği (assets/fonts/Inter-Regular.ttf konulunca aktif)
- [ ] PDF önizleme (pip install pymupdf gerektirir)
- [ ] Teklif tarihi düzenleme modunda değiştirilebilir olsun

---

## 🌐 Sonraki Büyük Hedef: Web Versiyonu

### Neden Web?
- Telefon, tablet, Mac, PC — her cihazdan tarayıcıyla erişim
- Tek merkezi veri (ofis PC veya VPS)
- PDF sunucuda oluşur, her cihazdan indirilebilir
- Birden fazla kullanıcı aynı anda, roller: Admin / Satış / Muhasebe
- Paraşüt gibi çalışır ama veri sende kalır, aylık abonelik yok

### Seçilen Stack
```
FastAPI          → Python backend (servisler aynen gelir)
HTMX             → dinamik HTML, az JS
TailwindCSS      → stil sistemi
Jinja2           → HTML şablonları
PostgreSQL       → çok kullanıcı için (SQLite de olur az kullanımda)
Tailscale VPN    → güvenli erişim
```

### Kurtarılacak Mevcut Kodlar (%60-70)
- ✅ database/     → aynen kullanılır
- ✅ models/       → aynen kullanılır
- ✅ services/     → aynen kullanılır
- ✅ pdf/          → aynen kullanılır
- ✅ constants.py  → aynen kullanılır
- ❌ ui/           → HTMX + Tailwind HTML sayfalarıyla değişir

---

## 💰 Maliyet

### Ofis PC → 0 TL/ay
- Tailscale (ücretsiz, 3 kullanıcıya kadar)
- DuckDNS (ücretsiz sabit domain)
- Python / FastAPI / PostgreSQL (ücretsiz, açık kaynak)

### VPS Sunucu → ~150-200 TL/ay
- Hetzner CX22 ~5€/ay, DigitalOcean ~6$/ay
- Özel domain: yıllık +100-300 TL ekstra

---

## 📌 Başlamak İçin

"Web versiyonuna başlayalım" demek yeterli.
HTMX + FastAPI stack'iyle, mevcut servisler üzerine inşa ederiz.
