import yfinance as yf
import requests
from datetime import datetime, time
import schedule
import time as t
import pytz
import os

# ============================================================
# YOUR DETAILS
# ============================================================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# ============================================================
# YOUR STOCKS WITH RESISTANCE LEVELS
# ============================================================
STOCKS = {
    "HBLENG.NS":        {"name": "HBL Engineering",       "resistance": 480},
    "ANGELONE.NS":      {"name": "Angel One",              "resistance": 2600},
    "NUVAMA.NS":        {"name": "Nuvama",                 "resistance": 6800},
    "TVSMOTOR.NS":      {"name": "TVS Motors",             "resistance": 2600},
    "TATAMOTORS.NS":    {"name": "Tata Motors",            "resistance": 720},
    "PARASDEF.NS":      {"name": "Paras Defence",          "resistance": 950},
    "BEL.NS":           {"name": "Bharat Electronics",     "resistance": 295},
    "ETERNAL.NS":       {"name": "Eternal",                "resistance": 230},
    "IDEAFORGE.NS":     {"name": "IdeaForge",              "resistance": 420},
    "GOKULAGRO.NS":     {"name": "Gokul Agro",             "resistance": 210},
    "LTFOODS.NS":       {"name": "LT Foods",               "resistance": 380},
    "AEGISLOG.NS":      {"name": "Aegis Logistics",        "resistance": 750},
    "BHARTIARTL.NS":    {"name": "Bharti Airtel",          "resistance": 1890},
    "HDFCBANK.NS":      {"name": "HDFC Bank",              "resistance": 820},
    "ICICIBANK.NS":     {"name": "ICICI Bank",             "resistance": 1380},
    "AXISBANK.NS":      {"name": "Axis Bank",              "resistance": 1150},
    "DIXON.NS":         {"name": "Dixon Technologies",     "resistance": 13500},
    "KAJARIACER.NS":    {"name": "Kajaria",                "resistance": 1050},
    "BSE.NS":           {"name": "BSE",                    "resistance": 4800},
    "ASHOKLEY.NS":      {"name": "Ashok Leyland",          "resistance": 230},
    "ADANIPOWER.NS":    {"name": "Adani Power",            "resistance": 580},
    "ADANIPORTS.NS":    {"name": "Adani Ports",            "resistance": 1350},
    "RADICO.NS":        {"name": "Radico Khaitan",         "resistance": 2100},
    "INFY.NS":          {"name": "Infosys",                "resistance": 1620},
    "WIPRO.NS":         {"name": "Wipro",                  "resistance": 265},
    "HAL.NS":           {"name": "HAL",                    "resistance": 4200},
    "MAZDOCK.NS":       {"name": "Mazagon Dock",           "resistance": 2400},
    "GRSE.NS":          {"name": "GRSE",                   "resistance": 1650},
    "DATAPATTNS.NS":    {"name": "Data Patterns",          "resistance": 1800},
    "ASTRAMICRO.NS":    {"name": "Astra Microwave",        "resistance": 220},
    "APOLLOTYRE.NS":    {"name": "Apollo Tyres",           "resistance": 520},
    "YATHARTH.NS":      {"name": "Yatharth Hospitals",     "resistance": 520},
    "KIMS.NS":          {"name": "KIMS",                   "resistance": 550},
}

IST = pytz.timezone("Asia/Kolkata")

# ============================================================
# SEND TELEGRAM MESSAGE
# ============================================================
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": msg,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Telegram error: {e}")

# ============================================================
# GET CURRENT PRICE
# ============================================================
def get_price(symbol):
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="1d", interval="5m")
        if data.empty:
            return None
        return round(data["Close"].iloc[-1], 2)
    except:
        return None

# ============================================================
# CATEGORISE STOCK
# E = Breakout confirmed
# D = Within 5%
# C = Within 10%
# B = Within 15%
# A = Within 20%
# ============================================================
def categorise(pct_away, price, resistance):
    if price >= resistance:
        return "E"
    elif pct_away <= 5:
        return "D"
    elif pct_away <= 10:
        return "C"
    elif pct_away <= 15:
        return "B"
    elif pct_away <= 20:
        return "A"
    else:
        return None

# ============================================================
# DAILY REPORT — 4:00 PM weekdays only
# ============================================================
def daily_report():
    now = datetime.now(IST)

    # Skip weekends — Saturday=5, Sunday=6
    if now.weekday() >= 5:
        print("Weekend — skipping daily report.")
        return

    print(f"[{now.strftime('%H:%M')}] Sending daily report...")

    bucket_e = []
    bucket_d = []
    bucket_c = []
    bucket_b = []
    bucket_a = []

    for symbol, info in STOCKS.items():
        if info["resistance"] == 0:
            continue

        price = get_price(symbol)
        if price is None:
            continue

        resistance = info["resistance"]
        pct_away = round(((resistance - price) / resistance) * 100, 2)
        category = categorise(pct_away, price, resistance)

        if category is None:
            continue

        entry = {
            "name": info["name"],
            "price": price,
            "resistance": resistance,
            "pct_away": pct_away if price < resistance else 0,
        }

        if category == "E":
            bucket_e.append(entry)
        elif category == "D":
            bucket_d.append(entry)
        elif category == "C":
            bucket_c.append(entry)
        elif category == "B":
            bucket_b.append(entry)
        elif category == "A":
            bucket_a.append(entry)

    # ── Build message ──
    msg_lines = [
        f"┌─────────────────────────┐",
        f"│   📊 BREAKOUT WATCHLIST   │",
        f"└─────────────────────────┘",
        f"📅 {now.strftime('%d %b %Y, %A')}",
        f"⏰ End of Day — 4:00 PM\n",
    ]

    if bucket_e:
        msg_lines.append(f"🚀 <b>E — BREAKOUT CONFIRMED</b>")
        msg_lines.append(f"{'─'*28}")
        for s in bucket_e:
            msg_lines.append(
                f"🟢 <b>{s['name']}</b>\n"
                f"   CMP      : ₹{s['price']}\n"
                f"   Target   : ₹{s['resistance']}\n"
                f"   Status   : ✅ Resistance Broken!\n"
            )

    if bucket_d:
        msg_lines.append(f"🔥 <b>D — WITHIN 5% OF BREAKOUT</b>")
        msg_lines.append(f"{'─'*28}")
        for s in bucket_d:
            msg_lines.append(
                f"🟡 <b>{s['name']}</b>\n"
                f"   CMP      : ₹{s['price']}\n"
                f"   Target   : ₹{s['resistance']}\n"
                f"   % Away   : {s['pct_away']}%\n"
            )

    if bucket_c:
        msg_lines.append(f"⚡ <b>C — WITHIN 10% OF BREAKOUT</b>")
        msg_lines.append(f"{'─'*28}")
        for s in bucket_c:
            msg_lines.append(
                f"🟠 <b>{s['name']}</b>\n"
                f"   CMP      : ₹{s['price']}\n"
                f"   Target   : ₹{s['resistance']}\n"
                f"   % Away   : {s['pct_away']}%\n"
            )

    if bucket_b:
        msg_lines.append(f"💡 <b>B — WITHIN 15% OF BREAKOUT</b>")
        msg_lines.append(f"{'─'*28}")
        for s in bucket_b:
            msg_lines.append(
                f"🔵 <b>{s['name']}</b>\n"
                f"   CMP      : ₹{s['price']}\n"
                f"   Target   : ₹{s['resistance']}\n"
                f"   % Away   : {s['pct_away']}%\n"
            )

    if bucket_a:
        msg_lines.append(f"👀 <b>A — WITHIN 20% OF BREAKOUT</b>")
        msg_lines.append(f"{'─'*28}")
        for s in bucket_a:
            msg_lines.append(
                f"⚪ <b>{s['name']}</b>\n"
                f"   CMP      : ₹{s['price']}\n"
                f"   Target   : ₹{s['resistance']}\n"
                f"   % Away   : {s['pct_away']}%\n"
            )

    if not any([bucket_a, bucket_b, bucket_c, bucket_d, bucket_e]):
        msg_lines.append("📭 No stocks within 20% of breakout today.")

    msg_lines.append(f"{'─'*28}")
    msg_lines.append(f"⚠️ <i>Educational purposes only.\nNot investment advice.</i>")

    send_telegram("\n".join(msg_lines))
    print("Daily report sent.")

# ============================================================
# WEEKLY SUMMARY — Every Sunday 8 PM
# ============================================================
def weekly_summary():
    now = datetime.now(IST)
    if now.weekday() != 6:
        return

    msg_lines = [
        f"┌─────────────────────────┐",
        f"│    📋 WEEKLY SUMMARY      │",
        f"└─────────────────────────┘",
        f"📅 Week ending {now.strftime('%d %b %Y')}\n",
    ]

    for symbol, info in STOCKS.items():
        if info["resistance"] == 0:
            continue
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="5d")
            if hist.empty:
                continue
            week_open = round(hist["Open"].iloc[0], 2)
            week_close = round(hist["Close"].iloc[-1], 2)
            week_change = round(((week_close - week_open) / week_open) * 100, 2)
            pct_to_target = round(((info["resistance"] - week_close) / info["resistance"]) * 100, 2)
            arrow = "📈" if week_change >= 0 else "📉"
            sign = "+" if week_change >= 0 else ""
            status = "🚀 BREAKOUT!" if week_close >= info["resistance"] else f"{pct_to_target}% to breakout"
            msg_lines.append(
                f"{arrow} <b>{info['name']}</b>\n"
                f"   Open   : ₹{week_open}\n"
                f"   Close  : ₹{week_close} ({sign}{week_change}%)\n"
                f"   Target : ₹{info['resistance']}\n"
                f"   Status : {status}\n"
            )
        except:
            continue

    msg_lines.append(f"{'─'*28}")
    msg_lines.append(f"⚠️ <i>Educational purposes only.\nNot investment advice.</i>")
    send_telegram("\n".join(msg_lines))
    print("Weekly summary sent.")

# ============================================================
# RUN BOT
# ============================================================
def run_bot():
    send_telegram(
        "┌─────────────────────────┐\n"
        "│   🤖 BREAKOUT BOT LIVE!   │\n"
        "└─────────────────────────┘\n\n"
        "📊 Daily report at 4:00 PM\n"
        "    (Weekdays only)\n"
        "📋 Weekly summary Sunday 8 PM\n"
        "🚫 No weekend alerts\n\n"
        "─────────────────────────\n"
        "CATEGORIES:\n"
        "🚀 E — Breakout Confirmed\n"
        "🔥 D — Within 5%\n"
        "⚡ C — Within 10%\n"
        "💡 B — Within 15%\n"
        "👀 A — Within 20%\n"
        "─────────────────────────\n"
        "⚠️ <i>Educational purposes only.</i>"
    )

    schedule.every().day.at("16:00").do(daily_report)
    schedule.every().day.at("20:00").do(weekly_summary)

    print("Bot is running...")
    while True:
        schedule.run_pending()
        t.sleep(60)

if __name__ == "__main__":
    run_bot()
