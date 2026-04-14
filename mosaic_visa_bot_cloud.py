"""
Mosaic Visa Randevu Takip Botu — Cloud Versiyonu
=================================================
Selenium gerektirmez. Railway, Render, PythonAnywhere'de çalışır.
"""

import os
import time
import smtplib
import requests
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, date

# ─────────────────────────────────────────────
#  ⚙️  AYARLAR
# ─────────────────────────────────────────────

TELEGRAM_BOT_TOKEN = "8681089221:AAEJISrx7ppZOchHjtOiFoSGg0mMIr20iao"
TELEGRAM_CHAT_ID   = "8011613197"

# 📧 Gmail Ayarları
EMAIL_SENDER   = "nagmatberdiyev@gmail.com"
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD", "")  # Railway'de Variable olarak ekle
EMAIL_RECEIVER = "nagmatberdiyev@gmail.com"

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


def send_email(office_name: str, new_slots: set, now_str: str, office_id: int):
    """Gmail SMTP ile e-posta bildirimi gönderir."""
    try:
        slots_list = "".join(f"<li>📅 {s}</li>" for s in sorted(new_slots))

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background: #f4f4f4; padding: 20px;">
            <div style="max-width: 500px; margin: auto; background: white; border-radius: 10px; padding: 25px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <h2 style="color: #e74c3c;">🚨 YENİ RANDEVU SLOTU!</h2>
                <p><strong>🏢 Ofis:</strong> {office_name}</p>
                <p><strong>⏰ Tarih:</strong> {now_str}</p>
                <hr>
                <p><strong>📅 Müsait Tarihler:</strong></p>
                <ul style="line-height: 2;">
                    {slots_list}
                </ul>
                <hr>
                <a href="{BASE_URL}/calendar/{office_id}"
                   style="display: inline-block; margin-top: 10px; padding: 12px 24px;
                          background: #2ecc71; color: white; text-decoration: none;
                          border-radius: 6px; font-weight: bold;">
                    🔗 Randevu Al
                </a>
                <p style="margin-top: 20px; color: #999; font-size: 12px;">
                    Bu bildirim Mosaic Visa Takip Botu tarafından gönderilmiştir.
                </p>
            </div>
        </body>
        </html>
        """

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"🚨 Yeni Randevu Slotu — {office_name}"
        msg["From"]    = EMAIL_SENDER
        msg["To"]      = EMAIL_RECEIVER
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())

        log.info("✅ E-posta bil
