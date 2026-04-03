"""
Mosaic Visa Randevu Takip Botu — Cloud Versiyonu
=================================================
Selenium gerektirmez. Railway, Render, PythonAnywhere'de çalışır.
"""

import time
import requests
import logging
from datetime import datetime, date

# ─────────────────────────────────────────────
#  ⚙️  AYARLAR
# ─────────────────────────────────────────────

TELEGRAM_BOT_TOKEN = "8681089221:AAEJISrx7ppZOchHjtOiFoSGg0mMIr20iao"
TELEGRAM_CHAT_ID   = "8011613197"

# 11 = Ashgabat Normal, 12 = Ashgabat VIP
OFFICE_IDS = [11, 12]

# Kaç dakikada bir kontrol
CHECK_INTERVAL_MINUTES = 5

# Kaç ay ileriye baksın
MONTHS_AHEAD = 2

# ─────────────────────────────────────────────

OFFICE_NAMES = {
    11: "Ashgabat (Normal)",
    12: "Ashgabat (VIP)",
}

BASE_URL = "https://appointment.mosaicvisa.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)


def send_telegram(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
    }
    try:
        r = requests.post(url, json=payload, timeout=15)
        if r.status_code == 200:
            log.info("✅ Telegram bildirimi gönderildi.")
        else:
            log.warning(f"Telegram hatası: {r.status_code} — {r.text}")
    except Exception as e:
        log.error(f"Telegram gönderilemedi: {e}")


def get_available_slots(office_id: int, month: str = None) -> list:
    """Siteyi HTTP ile çeker, müsait günleri döndürür."""
    from bs4 import BeautifulSoup

    url = f"{BASE_URL}/calendar/{office_id}"
    if month:
        url += f"?month={month}"

    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        if r.status_code != 200:
            log.warning(f"HTTP {r.status_code} — {url}")
            return []
    except Exception as e:
        log.warning(f"Bağlantı hatası: {e}")
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    available = []

    months_en = ["January","February","March","April","May","June",
                 "July","August","September","October","November","December"]

    # Tüm hücreleri tara
    for cell in soup.find_all(["td", "tr", "div", "li", "a"]):
        text = cell.get_text(separator=" ", strip=True)

        has_date = any(m in text for m in months_en) and "2026" in text
        has_reserved = "Reserved" in text

        if has_date and not has_reserved and len(text) < 60:
            date_str = text.strip()
            if date_str and date_str not in available:
                available.append(date_str)

    return available


def get_months() -> list:
    """Bu ay + MONTHS_AHEAD ay ilerisi."""
    months = [None]
    now = date.today()
    for i in range(1, MONTHS_AHEAD + 1):
        m = now.month + i
        y = now.year + (m - 1) // 12
        m = ((m - 1) % 12) + 1
        months.append(f"{y}-{m:02d}")
    return months


def main():
    log.info("=" * 50)
    log.info("🤖 Mosaic Visa Bot Başlatıldı (Cloud)")
    log.info(f"   Ofisler : {[OFFICE_NAMES.get(i) for i in OFFICE_IDS]}")
    log.info(f"   Aralık  : Her {CHECK_INTERVAL_MINUTES} dakika")
    log.info("=" * 50)

    send_telegram(
        "🤖 <b>Mosaic Visa Bot Başlatıldı</b>\n"
        f"📍 {', '.join(OFFICE_NAMES.get(i,'') for i in OFFICE_IDS)}\n"
        f"🕐 Her {CHECK_INTERVAL_MINUTES} dakikada kontrol ediyorum..."
    )

    previously_available = {oid: set() for oid in OFFICE_IDS}
    check_count = 0

    while True:
        check_count += 1
        now_str = datetime.now().strftime("%d.%m.%Y %H:%M")
        log.info(f"\n🔍 Kontrol #{check_count} — {now_str}")

        for office_id in OFFICE_IDS:
            office_name = OFFICE_NAMES.get(office_id, str(office_id))
            all_slots = []

            for month in get_months():
                slots = get_available_slots(office_id, month)
                all_slots.extend(slots)
                time.sleep(1)

            all_slots_set = set(all_slots)
            new_slots = all_slots_set - previously_available[office_id]

            if all_slots:
                log.info(f"✅ {office_name}: {len(all_slots)} müsait slot")
            else:
                log.info(f"❌ {office_name}: Müsait slot yok")

            if new_slots:
                slots_text = "\n".join(f"  📅 {s}" for s in sorted(new_slots))
                send_telegram(
                    f"🚨 <b>YENİ RANDEVU SLOTU!</b>\n\n"
                    f"🏢 <b>{office_name}</b>\n"
                    f"🔗 <a href='{BASE_URL}/calendar/{office_id}'>Randevu Al</a>\n\n"
                    f"<b>Müsait Tarihler:</b>\n{slots_text}\n\n"
                    f"⏰ {now_str}"
                )

            previously_available[office_id] = all_slots_set

        log.info(f"💤 {CHECK_INTERVAL_MINUTES} dakika bekleniyor...")
        time.sleep(CHECK_INTERVAL_MINUTES * 60)


if __name__ == "__main__":
    main()
