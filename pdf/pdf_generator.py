"""
PDF teklif oluşturucu.
ReportLab ile profesyonel kurumsal teklif belgesi üretir.
Türkçe karakter desteği: Windows sistem fontlarından TTF yüklenir.
"""
import logging
import datetime
from pathlib import Path
from app_paths import (
    ASSETS_DIR,
    LOGO_PATH,
    SIG1_PATH,
    SIG2_PATH,
    CFG_PATH,
)
from constants import SYM_MAP
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, Image
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

logger = logging.getLogger("pdf_generator")

COLOR_DARK     = colors.HexColor("#1a1a2e")
COLOR_MID_GRAY = colors.HexColor("#cccccc")
COLOR_ROW_ALT  = colors.HexColor("#f5f7fa")

# ── Font kayıt sistemi ────────────────────────────────────────────────────────

# Font arama sırası:
# 1. Projeye gömülü DejaVu (her platformda çalışır — önerilen)
# 2. Windows sistem fontları
# 3. Linux sistem fontları
_ASSETS_FONTS = ASSETS_DIR / "fonts"

_FONT_SEARCH = [
    # Projeye gömülü (garantili Türkçe — önerilen)
    (str(_ASSETS_FONTS / "DejaVuSans.ttf"),      str(_ASSETS_FONTS / "DejaVuSans-Bold.ttf")),
    # Windows sistem fontları (yedek)
    ("C:/Windows/Fonts/arial.ttf",               "C:/Windows/Fonts/arialbd.ttf"),
    ("C:/Windows/Fonts/calibri.ttf",             "C:/Windows/Fonts/calibrib.ttf"),
    ("C:/Windows/Fonts/tahoma.ttf",              "C:/Windows/Fonts/tahomabd.ttf"),
    ("C:/Windows/Fonts/verdana.ttf",             "C:/Windows/Fonts/verdanab.ttf"),
]

_FONT_REGULAR  = "Helvetica"
_FONT_BOLD     = "Helvetica-Bold"
_FONTS_LOADED  = False
_STYLE_COUNTER = 0


def _load_fonts():
    """Türkçe destekli TTF fontunu sisteme göre yükler."""
    global _FONT_REGULAR, _FONT_BOLD, _FONTS_LOADED
    if _FONTS_LOADED:
        return

    for reg_path, bold_path in _FONT_SEARCH:
        if Path(reg_path).exists():
            try:
                pdfmetrics.registerFont(TTFont("TR_Regular", reg_path))
                pdfmetrics.registerFont(TTFont("TR_Bold",    bold_path))
                pdfmetrics.registerFontFamily(
                    "TR",
                    normal="TR_Regular",
                    bold="TR_Bold",
                )
                _FONT_REGULAR = "TR_Regular"
                _FONT_BOLD    = "TR_Bold"
                _FONTS_LOADED = True
                logger.info("Font yüklendi: %s", reg_path)
                return
            except Exception as e:
                logger.warning("Font yüklenemedi (%s): %s", reg_path, e)

    logger.warning("Türkçe font bulunamadı, Helvetica kullanılacak (karakterler bozuk çıkabilir)")
    _FONTS_LOADED = True


# ── Config okuma ─────────────────────────────────────────────────────────────

def _load_company() -> dict:
    defaults = {
        "name": "ŞİRKET ADI", "address": "Adres", "tel": "-",
        "fax": "-", "mail": "-", "web": "-",
        "sales_person1_name": "", "sales_person1_title": "", "sales_person1_email": "",
        "sales_person2_name": "", "sales_person2_title": "", "sales_person2_email": "",
        # PDF sabit metinler (ayarlardan değiştirilebilir, PDF sırasına göre)
        "pdf_giris_metni": "Firmamızdan talep etmiş olduğunuz malzemeler ile ilgili teklifimizi tetkiklerinize sunar, değerli siparişlerinizi bekleriz.",
        "pdf_iskonto":     "Firmanıza iskonto uygulanmış olup, fiyatlar NET tir.",
        "pdf_teslim_yeri": "Büromuz veya Kargo bedeli karşı taraf ödemeli şartiyla Kargo şirketi ile.",
        "pdf_kur_notu":    "•Verilen döviz fiyatlar Fatura tarihindeki T.C.M.B. Efektif Satış Kuru üzerinden TL.'sına çevrilecektir.",
        "pdf_kdv_notu":    "•Fiyatlarımıza K.D.V. dahil değildir.",
        "pdf_onay_metni":  "Yukarıda teklif edilen malzemeleri belirttiğiniz özellik ve şartlarda satın almayı kabul ediyoruz.",
        "pdf_teslim_notu": "NOT : Teklifimiz de belirtilen teslim süreleri teklifin yazıldığı andaki güncel stoklara göre verilmiştir. Sipariş anında stok durumuna göre teslim süreleri değişebilir.",
        "pdf_iptal_notu":  "Siparişlerin yazılı olarak maille veya fax yoluyla geçilmesine müteakip siparişlerin iptali ve ürünlerin iadesi kabul edilmemektedir.",
    }
    if CFG_PATH.exists():
        try:
            for line in CFG_PATH.read_text(encoding="utf-8").splitlines():
                if "=" in line:
                    k, _, v = line.partition("=")
                    defaults[k.strip()] = v.strip()
        except Exception as e:
            logger.warning("Config okunamadı: %s", e)
    return defaults


# ── Ana üretici ──────────────────────────────────────────────────────────────

def generate_pdf(offer_data: dict, output_path: str) -> str:
    _load_fonts()
    company  = _load_company()
    currency = offer_data.get("currency", "EUR")
    sym      = SYM_MAP.get(currency, currency)

    logger.info("PDF oluşturuluyor: %s → %s", offer_data.get("offer_no","?"), output_path)

    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=15*mm, rightMargin=15*mm,
        topMargin=8*mm,  bottomMargin=12*mm,
    )
    width = A4[0] - 30 * mm
    story = []

    story += _header(company, width)
    story += _customer_block(offer_data, width)
    story.append(Spacer(1, 5*mm))
    story += _intro_text(company)
    story.append(Spacer(1, 5*mm))
    story += _terms(width, offer_data, company)
    story.append(Spacer(1, 5*mm))
    story += _product_table(offer_data, width, sym)
    story.append(Spacer(1, 4*mm))
    story += _total_block(offer_data, width, sym)
    story += _validity_block(offer_data, width)
    story.append(Spacer(1, 5*mm))
    story += _signature_block(company, width)
    story.append(Spacer(1, 4*mm))
    story += _footer_notes(width, company)

    doc.build(story)
    logger.info("PDF tamamlandı: %s", output_path)
    return output_path


# ── Yardımcı: stil üretici ───────────────────────────────────────────────────

def _s(size=9, bold=False, align=TA_LEFT, color=colors.black) -> ParagraphStyle:
    global _STYLE_COUNTER
    _STYLE_COUNTER += 1
    return ParagraphStyle(
        name=f"s{_STYLE_COUNTER}",
        fontSize=size,
        fontName=_FONT_BOLD if bold else _FONT_REGULAR,
        alignment=align,
        leading=size + 5,
        textColor=color,
    )


# ── Bölümler ─────────────────────────────────────────────────────────────────

def _header(company, width):
    """Logo + şirket bilgileri."""
    logo_w = 64 * mm
    info_w = width - logo_w

    # Logo
    if LOGO_PATH.exists():
        try:
            logo_col = [Image(str(LOGO_PATH), width=64*mm, height=14*mm)]
        except Exception as e:
            logger.warning("Logo yüklenemedi: %s", e)
            logo_col = [Paragraph("", _s(9))]
    else:
        logo_col = [Paragraph("", _s(9))]

    # Şirket bilgileri (sağa hizalı)
    company_col = [
        Paragraph(company["name"],            _s(11, True,  TA_RIGHT, COLOR_DARK)),
        Paragraph(company["address"],         _s(8.5, False, TA_RIGHT)),
        Paragraph(f"Tel  : {company['tel']}", _s(8.5, False, TA_RIGHT)),
        Paragraph(f"Fax  : {company['fax']}", _s(8.5, False, TA_RIGHT)),
        Paragraph(f"Mail : {company['mail']}",_s(8.5, False, TA_RIGHT)),
        Paragraph(f"Web  : {company['web']}", _s(8.5, False, TA_RIGHT)),
    ]

    t = Table([[logo_col, company_col]], colWidths=[logo_w, info_w])
    t.setStyle(TableStyle([
        ("VALIGN",       (0,0), (-1,-1), "TOP"),
        ("ALIGN",        (0,0), (0,0),   "LEFT"),
        ("ALIGN",        (1,0), (1,0),   "RIGHT"),
        ("LEFTPADDING",  (0,0), (-1,-1), 0),
        ("RIGHTPADDING", (0,0), (-1,-1), 0),
        ("TOPPADDING",   (0,0), (-1,-1), 0),
        ("BOTTOMPADDING",(0,0), (-1,-1), 0),
    ]))

    return [
        t,
        Spacer(1, 3*mm),
        HRFlowable(width=width, thickness=1, color=COLOR_DARK),
        Spacer(1, 4*mm),
    ]


def _customer_block(offer_data, width):
    """Müşteri bilgileri bloğu (sol: firma/adres/kişi, sağ: tarih/teklif no)."""
    lb = _s(9, True)
    vb = _s(9)

    def row(label, value):
        return [Paragraph(f"<b>{label}</b>", lb),
                Paragraph(":", lb),
                Paragraph(str(value), vb)]

    half = width / 2
    left_data = [
        row("FİRMA ADI",    offer_data.get("company_name", "")),
        row("ADRES",        offer_data.get("customer_address", "")),
        row("İLGİLİ KİŞİ", offer_data.get("contact_person", "")),
    ]
    right_data = [
        row("TARİH",      offer_data.get("date", "")),
        row("TEKLİF NO",  offer_data.get("offer_no", "")),
        ["", "", ""],
    ]

    ts = TableStyle([
        ("VALIGN",        (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING",   (0,0), (-1,-1), 0),
        ("RIGHTPADDING",  (0,0), (-1,-1), 2),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3),
    ])
    lt = Table(left_data,  colWidths=[28*mm, 5*mm, half-33*mm]); lt.setStyle(ts)
    rt = Table(right_data, colWidths=[24*mm, 5*mm, half-29*mm]); rt.setStyle(ts)

    wrapper = Table([[lt, rt]], colWidths=[half, half])
    wrapper.setStyle(TableStyle([
        ("VALIGN",       (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING",  (0,0), (-1,-1), 0),
        ("RIGHTPADDING", (0,0), (-1,-1), 0),
    ]))
    return [wrapper]


def _intro_text(company: dict):
    giris = company.get("pdf_giris_metni", "")
    elements = []
    if giris:
        elements.append(Paragraph(giris, _s(9)))
        elements.append(Spacer(1, 2*mm))
    elements.append(Paragraph("<b>Saygılarımızla</b>", _s(9, True)))
    elements.append(Spacer(1, 1*mm))
    elements.append(Paragraph("<b>Teklifimiz EK'tedir</b>", _s(9, True)))
    return elements


def _terms(width, offer_data=None, company: dict = None):
    company  = company or {}
    lb = _s(9, True)
    vb = _s(9)
    rows = []
    iskonto     = company.get("pdf_iskonto", "")
    teslim_yeri = company.get("pdf_teslim_yeri", "")
    payment     = (offer_data or {}).get("payment_term", "")
    if iskonto:
        rows.append(("İskonto", iskonto))
    if teslim_yeri:
        rows.append(("Teslim Yeri", teslim_yeri))
    if payment:
        rows.append(("Ödeme", payment))
    if not rows:
        return []
    data = [[Paragraph(f"<b>{l}</b>", lb), Paragraph(":", lb), Paragraph(v, vb)]
            for l, v in rows]
    t = Table(data, colWidths=[22*mm, 5*mm, width-27*mm])
    t.setStyle(TableStyle([
        ("VALIGN",        (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING",   (0,0), (-1,-1), 0),
        ("RIGHTPADDING",  (0,0), (-1,-1), 2),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3),
    ]))
    return [t]


def _product_table(offer_data, width, sym):
    """Ürün tablosu — 9 kolon."""
    th = _s(8.5, True,  TA_CENTER, colors.white)
    tc = _s(8.5, False, TA_LEFT)
    tm = _s(8.5, False, TA_CENTER)
    tr = _s(8.5, False, TA_RIGHT)

    # Kolon genişlikleri  (Adet: 10→13mm, fark malzeme kodu sütunundan alınır)
    col_w = [8*mm, 22*mm, 38*mm, 25*mm, 13*mm, 16*mm, 8*mm, 22*mm, 22*mm]
    diff  = width - sum(col_w)
    col_w[1] += diff   # Ürün adı sütunu kalan alanı alır

    headers = [
        Paragraph("No",              th),
        Paragraph("Malzeme\nKodu",   th),
        Paragraph("Ürün Adı",        th),
        Paragraph("Açıklama",        th),
        Paragraph("Adet",            th),
        Paragraph("Teslim\nSüresi",  th),
        Paragraph("Br",              th),
        Paragraph("Net Fiyat",       th),
        Paragraph("Toplam",          th),
    ]

    data = [headers]
    for i, item in enumerate(offer_data.get("items", []), 1):
        data.append([
            Paragraph(str(i),                               tm),
            Paragraph(item.get("product_code",""),          tc),
            Paragraph(item.get("product_name",""),          tc),
            Paragraph(item.get("description",""),           tc),
            Paragraph(str(item.get("quantity",1)),          tm),
            Paragraph(item.get("delivery_time","2-3 Hafta"),tm),
            Paragraph(item.get("unit","Adet"),              tm),
            Paragraph(f"{item.get('unit_price',0):,.2f} {sym}", tr),
            Paragraph(f"{item.get('total_price',0):,.2f} {sym}", tr),
        ])

    t = Table(data, colWidths=col_w, repeatRows=1)
    ts = TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),  COLOR_DARK),
        ("TEXTCOLOR",     (0,0), (-1,0),  colors.white),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("GRID",          (0,0), (-1,-1), 0.5, COLOR_MID_GRAY),
        ("TOPPADDING",    (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("LEFTPADDING",   (0,0), (-1,-1), 4),
        ("RIGHTPADDING",  (0,0), (-1,-1), 4),
    ])
    for i in range(1, len(data)):
        if i % 2 == 0:
            ts.add("BACKGROUND", (0,i), (-1,i), COLOR_ROW_ALT)
    t.setStyle(ts)
    return [t]


def _total_block(offer_data, width, sym):
    total = offer_data.get("total_amount", 0)
    data = [[
        Paragraph("Genel Toplam", _s(11, True, TA_LEFT,  colors.white)),
        Paragraph(f"{total:,.2f} {sym}", _s(11, True, TA_RIGHT, colors.white)),
    ]]
    t = Table(data, colWidths=[width-65*mm, 65*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), COLOR_DARK),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING",    (0,0), (-1,-1), 7),
        ("BOTTOMPADDING", (0,0), (-1,-1), 7),
        ("LEFTPADDING",   (0,0), (-1,-1), 10),
        ("RIGHTPADDING",  (0,0), (-1,-1), 10),
    ]))
    return [t]


def _validity_block(offer_data, width):
    """Teklif geçerlilik süresi (ödeme şartlar tablosunda gösterildiği için burada tekrar edilmez)."""
    validity = offer_data.get("validity", "")
    note     = offer_data.get("validity_note", "")
    elements = []

    if validity:
        text = f"<b>Teklif Geçerlilik Süresi:</b>  {validity}"
        if note:
            text += f"  —  <i>{note}</i>"
        elements.append(
            Paragraph(text, _s(8.5, align=TA_RIGHT, color=colors.HexColor("#cc5500")))
        )
    if elements:
        elements.insert(0, Spacer(1, 2*mm))
    return elements


def _signature_block(company, width):
    n  = _s(8.5, True)
    sm = _s(8.5)
    elements = []

    kur_notu = company.get("pdf_kur_notu", "")
    kdv_notu = company.get("pdf_kdv_notu", "")
    if kur_notu:
        elements.append(Paragraph(kur_notu, _s(7.5)))
    if kdv_notu:
        elements.append(Paragraph(kdv_notu, _s(7.5)))
    elements.append(Spacer(1, 4*mm))

    p1n = company.get("sales_person1_name","")
    p1t = company.get("sales_person1_title","")
    p1e = company.get("sales_person1_email","")
    p2n = company.get("sales_person2_name","")
    p2t = company.get("sales_person2_title","")
    p2e = company.get("sales_person2_email","")

    def person_col(name, title, email, sig_path=None):
        if not name:
            return [Spacer(1, 5*mm)]
        items = [Paragraph(f"<b>{name}</b>", n),
                 Paragraph(title, sm),
                 Paragraph(email, sm)]
        if sig_path and Path(sig_path).exists():
            try:
                items.append(Spacer(1, 2*mm))
                items.append(Image(str(sig_path), width=35*mm, height=14*mm))
            except Exception:
                pass
        return items

    sig = Table(
        [[person_col(p1n,p1t,p1e,str(SIG1_PATH)), person_col(p2n,p2t,p2e,str(SIG2_PATH))]],
        colWidths=[width/2, width/2]
    )
    sig.setStyle(TableStyle([
        ("VALIGN",       (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING",  (0,0), (-1,-1), 0),
        ("RIGHTPADDING", (0,0), (-1,-1), 0),
    ]))
    elements.append(sig)
    elements.append(Spacer(1, 6*mm))

    onay = _s(8.5)
    onay_metni = company.get("pdf_onay_metni", "")
    if onay_metni:
        elements.append(Paragraph(onay_metni, onay))
    elements.append(Spacer(1, 3*mm))

    auth = Table(
        [[Paragraph("Yetkili :", onay),     Paragraph("Onay Tarihi:", onay)],
         [Spacer(1, 10*mm),                 Spacer(1, 10*mm)],
         [Paragraph("Kaşe / İmza :", onay), Paragraph("", onay)]],
        colWidths=[width/2, width/2]
    )
    auth.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP")]))
    elements.append(auth)
    return elements


def _footer_notes(width, company: dict):
    teslim_notu = company.get("pdf_teslim_notu", "")
    iptal_notu  = company.get("pdf_iptal_notu",  "")
    elements = [
        Spacer(1, 3*mm),
        HRFlowable(width=width, thickness=0.5, color=COLOR_MID_GRAY),
        Spacer(1, 2*mm),
    ]
    if teslim_notu:
        elements.append(Paragraph(
            teslim_notu,
            _s(7.5, align=TA_CENTER, color=colors.HexColor("#cc0000"))))
        elements.append(Spacer(1, 1*mm))
    if iptal_notu:
        elements.append(Paragraph(
            iptal_notu,
            _s(7, align=TA_CENTER, color=colors.gray)))
    elements.append(Paragraph(
        f"Baskı Tarihi : {datetime.date.today().strftime('%d.%m.%Y')}",
        _s(7, align=TA_CENTER, color=colors.gray)))
    return elements
