import json
import os
import urllib.parse
import urllib.request

TOKEN = os.environ.get("BOT_TOKEN", "")
API = f"https://api.telegram.org/bot{TOKEN}"

# Adminga ogohlantirish yuborish uchun — admin'ning shaxsiy Telegram ID raqami
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID", "")

# Yozish uchun talab qilinadigan minimal taklif (qo'shilgan odam) soni
REQUIRED_INVITES = int(os.environ.get("REQUIRED_INVITES", "2"))

# Upstash Redis (Vercel KV) — ikkala nomdan ham qaysi biri bo'lsa o'qiydi
REDIS_URL = os.environ.get("UPSTASH_REDIS_REST_URL") or os.environ.get("KV_REST_API_URL", "")
REDIS_TOKEN = os.environ.get("UPSTASH_REDIS_REST_TOKEN") or os.environ.get("KV_REST_API_TOKEN", "")


# ===================== Telegram API =====================
def tg(method, payload):
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


def send_message(chat_id, text, parse_mode=None):
    payload = {"chat_id": chat_id, "text": text, "disable_web_page_preview": True}
    if parse_mode:
        payload["parse_mode"] = parse_mode
    return tg("sendMessage", payload)


def get_chat_member(chat_id, user_id):
    return tg("getChatMember", {"chat_id": chat_id, "user_id": user_id})


# ===================== Redis (Upstash REST) =====================
def redis_cmd(*parts):
    """Upstash Redis REST API orqali buyruq yuboradi."""
    if not REDIS_URL or not REDIS_TOKEN:
        return None
    path = "/".join(urllib.parse.quote(str(p), safe="") for p in parts)
    req = urllib.request.Request(
        f"{REDIS_URL}/{path}",
        headers={"Authorization": f"Bearer {REDIS_TOKEN}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8")).get("result")
    except Exception:
        return None


def add_invite(inviter_id, invited_id):
    """inviter_id qo'shgan odamlar to'plamiga invited_id ni qo'shadi (takror sanalmaydi)."""
    redis_cmd("SADD", f"invited:{inviter_id}", invited_id)


def invite_count(user_id):
    """user_id necha xil odam qo'shganini qaytaradi."""
    n = redis_cmd("SCARD", f"invited:{user_id}")
    try:
        return int(n)
    except (TypeError, ValueError):
        return 0


# ===================== Matnlar (RUS tili) =====================
def warn_user_text(count):
    remaining = max(REQUIRED_INVITES - count, 0)
    return (
        "Здравствуйте! 🌸\n\n"
        "Ваше сообщение в группе было удалено, потому что для участия в "
        f"переписке необходимо пригласить минимум {REQUIRED_INVITES} человек(а) "
        "в нашу группу.\n\n"
        f"📊 Вы уже пригласили: {count} из {REQUIRED_INVITES}.\n"
        f"➕ Осталось добавить: {remaining}.\n\n"
        "Как только вы пригласите нужное количество участников, вы сразу "
        "сможете свободно писать в группе. 💐\n\n"
        "Спасибо за понимание и хорошего вам дня!"
    )


def html_escape(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def user_mention(user_id, name, username):
    """Bosiladigan tegli mention qaytaradi (HTML)."""
    if username:
        return f"@{username}"
    return f'<a href="tg://user?id={user_id}">{html_escape(name)}</a>'


def warn_group_text(user_id, name, username, count):
    remaining = max(REQUIRED_INVITES - count, 0)
    mention = user_mention(user_id, name, username)
    return (
        f"🌸 {mention}, ваше сообщение удалено.\n"
        f"Чтобы писать в группе, пригласите ещё {remaining} человек(а) "
        f"(приглашено: {count}/{REQUIRED_INVITES}).\n"
        "Напишите боту в личные сообщения, чтобы получать уведомления. Спасибо! 💐"
    )


def admin_notify_text(name, username, user_id, count, text):
    uname = f"@{username}" if username else "—"
    shown = text if text else "[медиа / без текста]"
    if len(shown) > 500:
        shown = shown[:500] + "…"
    return (
        "⚠️ Уведомление модерации\n\n"
        f"👤 Пользователь: {name} ({uname}, id: {user_id})\n"
        f"📊 Приглашено: {count} из {REQUIRED_INVITES}\n\n"
        "Он(а) написал(а) в группе, не пригласив нужное количество участников.\n\n"
        f"✉️ Текст сообщения:\n«{shown}»\n\n"
        "Сообщение было удалено, пользователь предупреждён."
    )


# ===================== Asosiy logika =====================
SERVICE_KEYS = (
    "new_chat_members",
    "left_chat_member",
    "new_chat_title",
    "new_chat_photo",
    "delete_chat_photo",
    "group_chat_created",
    "supergroup_chat_created",
    "channel_chat_created",
    "pinned_message",
    "message_auto_delete_timer_changed",
    "video_chat_started",
    "video_chat_ended",
    "video_chat_participants_invited",
    "video_chat_scheduled",
)


def full_name(user):
    name = user.get("first_name", "")
    if user.get("last_name"):
        name += " " + user["last_name"]
    return name or "Пользователь"


def handle_update(update):
    msg = update.get("message") or update.get("edited_message")
    if not msg:
        return

    chat = msg["chat"]
    chat_id = chat["id"]
    message_id = msg["message_id"]
    text = msg.get("text", "")
    sender = msg.get("from") or {}

    # --- /start, /help (shaxsiy chatda yoki guruhda) ---
    if text.startswith("/start") or text.startswith("/help"):
        send_message(
            chat_id,
            "Здравствуйте! 🌸 Я бот-помощник группы.\n\n"
            "Я слежу за порядком: удаляю системные сообщения о входе/выходе и "
            f"напоминаю участникам приглашать минимум {REQUIRED_INVITES} человек, "
            "чтобы писать в группе.\n\n"
            "Сохраните этот чат, чтобы получать уведомления. 💐",
        )
        return

    # --- Yangi a'zo qo'shilishi: kim qo'shganini hisoblaymiz ---
    if "new_chat_members" in msg:
        inviter = sender.get("id")
        for member in msg["new_chat_members"]:
            # o'zi kelganini yoki bot qo'shilganini sanamaymiz
            if member.get("is_bot"):
                continue
            if inviter and member.get("id") != inviter:
                add_invite(inviter, member["id"])
        delete_message(chat_id, message_id)
        return

    # --- Boshqa xizmat xabarlari: shunchaki o'chiramiz ---
    for key in SERVICE_KEYS:
        if key in msg:
            delete_message(chat_id, message_id)
            return

    # --- Bu yerdan keyin: oddiy xabar (yozishma) ---
    # Faqat guruh/superguruhda ishlaymiz
    if chat.get("type") not in ("group", "supergroup"):
        return

    user_id = sender.get("id")
    if not user_id or sender.get("is_bot"):
        return

    # Adminlar va guruh egasi cheklovdan ozod
    member = get_chat_member(chat_id, user_id)
    status = (member.get("result") or {}).get("status") if member.get("ok") else None
    if status in ("creator", "administrator"):
        return

    # Taklif sonini tekshiramiz
    count = invite_count(user_id)
    if count >= REQUIRED_INVITES:
        return  # yetarli — yozaversin

    # Yetarli emas: xabarni o'chiramiz va ogohlantiramiz
    delete_message(chat_id, message_id)

    name = full_name(sender)

    # 1) Foydalanuvchining lichkasiga ogohlantirish (rus tilida)
    dm = send_message(user_id, warn_user_text(count))
    if not dm.get("ok"):
        # Lichkaga yuborib bo'lmadi (bot bilan /start bosmagan) — guruhda teglab eslatma
        send_message(
            chat_id,
            warn_group_text(user_id, name, sender.get("username"), count),
            parse_mode="HTML",
        )

    # 2) Adminga xabar (rus tilida)
    if ADMIN_CHAT_ID:
        send_message(
            ADMIN_CHAT_ID,
            admin_notify_text(name, sender.get("username"), user_id, count, text),
        )


# ===================== Vercel Serverless handler =====================
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
        self.wfile.write("Flora Cleaner Bot ishlayapti".encode("utf-8"))
