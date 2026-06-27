import json
import os
import urllib.request

TOKEN = os.environ.get("BOT_TOKEN", "")
API = f"https://api.telegram.org/bot{TOKEN}"


def tg(method, payload):
    """Telegram API'ga so'rov yuboradi."""
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{API}/{method}",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"ok": False, "error": str(e)}


def delete_message(chat_id, message_id):
    return tg("deleteMessage", {"chat_id": chat_id, "message_id": message_id})


def handle_update(update):
    """Kelgan update'ni tekshiradi va xizmat xabarlarini o'chiradi."""
    msg = update.get("message") or update.get("edited_message")
    if not msg:
        return

    chat_id = msg["chat"]["id"]
    message_id = msg["message_id"]

    # Kirdi / chiqdi va boshqa xizmat xabarlari
    service_keys = (
        "new_chat_members",      # kimdir guruhga qo'shildi
        "left_chat_member",      # kimdir guruhdan chiqdi
        "new_chat_title",        # guruh nomi o'zgardi
        "new_chat_photo",        # guruh rasmi o'zgardi
        "delete_chat_photo",     # guruh rasmi o'chirildi
        "group_chat_created",
        "supergroup_chat_created",
        "channel_chat_created",
        "pinned_message",        # xabar pin qilindi xabari
        "message_auto_delete_timer_changed",
        "video_chat_started",
        "video_chat_ended",
        "video_chat_participants_invited",
        "video_chat_scheduled",
    )

    for key in service_keys:
        if key in msg:
            delete_message(chat_id, message_id)
            return


# ===== Vercel Serverless handler (Python) =====
from http.server import BaseHTTPRequestHandler


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length else b"{}"
        try:
            update = json.loads(body.decode("utf-8"))
            handle_update(update)
        except Exception:
            pass
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"ok":true}')

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write("Flora Cleaner Bot ishlayapti ✅".encode("utf-8"))
