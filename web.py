"""
web.py — Botni "uyg'oq" tutish uchun juda kichik veb-server.

Nima uchun kerak: Render.com'ning bepul "Web Service" turi, agar 15 daqiqa davomida
hech qanday tashqi so'rov (HTTP request) kelmasa, dasturni "uxlatib qo'yadi".
Shu mini-server tashqi "uyg'otuvchi xizmat" (masalan UptimeRobot) dan kelgan
so'rovlarga javob berib, dastur doim ishlab turishini ta'minlaydi.

Bu server asosiy bot mantig'iga (main.py) hech qanday aloqasi yo'q —
faqat "OK, men ishlayapman" deb javob qaytaradi.
"""

import os
from http.server import BaseHTTPRequestHandler, HTTPServer


class _HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write("Forex News Bot ishlayapti ✅".encode("utf-8"))

    def log_message(self, format, *args):  # noqa: A002
        # Standart konsolga keraksiz HTTP loglarni yozmaslik uchun
        pass


def start_web_server() -> None:
    """
    Veb-serverni ishga tushiradi. Render avtomatik beradigan PORT muhit
    o'zgaruvchisidan foydalanadi (mahalliy kompyuterda ishga tushirilsa, 10000-portda ochiladi).
    Bu funksiya cheksiz ishlaydi, shuning uchun alohida "thread" (oqim) ichida chaqirilishi kerak.
    """
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), _HealthCheckHandler)
    server.serve_forever()
