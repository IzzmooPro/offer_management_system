# Teklif Yönetim Sistemi  —  Version: v1.0

Profesyonel teklif, ürün ve müşteri yönetimi için Windows masaüstü uygulaması.

---

## Gereksinimler

- Windows 10 veya üzeri
- Python 3.12 veya üzeri
- pip (Python paket yöneticisi)

---

## Kurulum

```bat
pip install -r requirements.txt
python main.py
```

---

## Yüklenen Kütüphaneler

| Kütüphane   | Sürüm Gereksinimi | Açıklama                          |
|-------------|-------------------|-----------------------------------|
| PySide6     | >= 6.8.0          | Qt6 tabanlı GUI framework         |
| reportlab   | >= 4.0.0          | PDF oluşturma kütüphanesi         |
| Pillow      | >= 10.0.0         | Logo / imza resim işleme          |
| openpyxl    | >= 3.1.0          | Excel import/export için          |
| pyinstaller | >= 6.0.0          | EXE derleme (isteğe bağlı)        |

---

## Özellikler

- 📦 Ürün / Stok Yönetimi (CRUD, Excel/CSV import)
- 👥 Müşteri Yönetimi (CRUD, Excel/CSV import)
- 📋 3 Adımlı Teklif Sihirbazı (Müşteri → Ürünler → Özet)
- 📄 Profesyonel PDF Teklif Çıktısı (logo, imzalar, Türkçe karakter)
- 🔢 Otomatik Teklif Numarası (PREFIX-000001)
- 💱 Çoklu Para Birimi (TL / EUR / USD)
- 📊 Dashboard (istatistik kartları, arama, filtre, durum takibi)
- 📤 Excel / CSV Export (teklif listesi)
- 🌙 Açık / Koyu Tema
- 💾 Otomatik Yedekleme (kapanışta + teklif kaydında + zamanlı)
- ♻️  Geri Yükleme & Startup Backup Algılama
- 🔄 Otomatik Güncelleme Sistemi (GitHub tabanlı, sessiz başlangıç kontrolü)
- ⚙️  Şirket Ayarları (bilgiler, yetkililer, logo & imza yükleme)
- ❓ F1 Yardım Penceresi (toggle açma/kapama)

---

## Veri Mimarisi

Program dosyaları ve kullanıcı verileri **ayrı klasörlerde** saklanır.
Güncelleme sistemi veri klasörlerine hiçbir zaman dokunmaz.

```
Program Dosyaları:
  Program Files\OfferManagementSystem\   (veya proje klasörü)

Kullanıcı Verisi:
  %LOCALAPPDATA%\OfferManagementSystem\data\
    ├── database.db        ← Tüm veriler (müşteri, teklif, ürün)
    ├── company.cfg        ← Şirket bilgileri ve PDF ayarları
    ├── logo.png           ← Şirket logosu
    ├── signature1.png     ← 1. yetkili imzası
    ├── signature2.png     ← 2. yetkili imzası
    ├── offers_pdf/        ← Oluşturulan PDF'ler
    ├── logs/              ← Uygulama logları (30 gün)
    └── backup_meta.json   ← Otomatik yedekleme ayarları

Yedekler:
  %USERPROFILE%\Documents\OfferManagementSystem\backups\
    └── backup_YYYY_MM_DD_HHMMSS.zip
```

---

## Klasör Yapısı (Kaynak Kod)

```
offer_management_system/
├── main.py                    ← Programı buradan başlatın
├── app_paths.py               ← Merkezi path yönetimi (AppData + EXE mod)
├── constants.py               ← SYM_MAP, STATUS_CONFIG, STATUS_ORDER
├── build_exe.bat              ← PyInstaller ile tek EXE derleme
├── clear_for_distribution.py  ← EXE öncesi test verisi temizleme
├── requirements.txt
├── database/
├── models/
├── services/
├── pdf/
├── assets/
│   └── fonts/
│       ├── DejaVuSans.ttf
│       └── DejaVuSans-Bold.ttf
└── ui/
    ├── updater.py             ← Otomatik güncelleme sistemi
    ├── backup_manager.py      ← Yedekleme/geri yükleme
    └── ...
```

---

## EXE Derleme

```bat
build_exe.bat
```

Çıktı: `dist\TeklifYonetim.exe` — tek dosya, kurulum gerektirmez.

**EXE dağıtmadan önce test verilerini temizlemek için:**
```bat
python clear_for_distribution.py
```
Bu script müşteri/teklif/ürün kayıtlarını siler; şirket bilgileri ve PDF ayarlarını korur.

---

## Otomatik Güncelleme

Program her açılışında GitHub'u arka planda kontrol eder.
- Güncelleme **yoksa** → hiçbir şey gösterilmez (sessiz)
- Güncelleme **varsa** → "Yeni bir sürüm bulundu." diyalogu açılır
  - **Güncelle** → İndirir, programı kapatır, yükler, yeniden açar
  - **Daha sonra** → Diyalogu kapatır, programa devam eder

> Güncelleme sistemi yalnızca program dosyalarını değiştirir.
> AppData veri klasörü ve Documents yedek klasörüne **kesinlikle dokunmaz**.

---

## Kısayollar

| Kısayol  | İşlev                        |
|----------|------------------------------|
| F1       | Yardım penceresi aç / kapat  |
| Ctrl+T   | Tema değiştir (açık/koyu)    |
| Ctrl+B   | Yedekle / Geri Yükle         |
| Ctrl+H   | Hakkında                     |

---

## Yedekleme

- **Otomatik**: Program kapanırken + teklif kaydedilince + belirli aralıklarla
- **Manuel**: Araçlar → Yedekle / Geri Yükle → "Klasör Seç ve Yedekle"
- **Varsayılan konum**: `Documents\OfferManagementSystem\backups\`
- **Format**: `backup_YYYY_MM_DD_HHMMSS.zip`
- İçerik: veritabanı + şirket ayarları + logo/imzalar
- En fazla 20 yedek tutulur, eskiler otomatik silinir

---

## Geliştirici

- GitHub: [IzzmooPro/offer_management_system](https://github.com/IzzmooPro/offer_management_system)
- E-posta: IzzmooPro@gmail.com
