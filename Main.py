import yfinance as yf
import requests
from datetime import datetime, time
import schedule
import time as t
import pytz

BOT_TOKEN = "8378760055:AAGR1YyCPRnRL6cn_Kzyd207PhKhZc1H3AM"
CHAT_ID = "5832045565"

STOCKS = {
    "HBLENG.NS":        {"name": "HBL Engineering",       "resistance": 0},
    "ANGELONE.NS":      {"name": "Angel One",              "resistance": 0},
    "NUVAMA.NS":        {"name": "Nuvama",                 "resistance": 0},
    "TVSMOTOR.NS":      {"name": "TVS Motors",             "resistance": 0},
    "TATAMOTORS.NS":    {"name": "Tata Motors",            "resistance": 0},
    "PARASDEF.NS":      {"name": "Paras Defence",          "resistance": 0},
    "BEL.NS":           {"name": "Bharat Electronics",     "resistance": 0},
    "ETERNAL.NS":       {"name": "Eternal",                "resistance": 0},
    "IDEAFORGE.NS":     {"name": "IdeaForge",              "resistance": 0},
    "GOKULAGRO.NS":     {"name": "Gokul Agro",             "resistance": 0},
    "LTFOODS.NS":       {"name": "LT Foods",               "resistance": 0},
    "AEGISLOG.NS":      {"name": "Aegis Logistics",        "resistance": 0},
    "BHARTIARTL.NS":    {"name": "Bharti Airtel",          "resistance": 0},
    "HDFCBANK.NS":      {"name": "HDFC Bank",              "resistance": 0},
    "ICICIBANK.NS":     {"name": "ICICI Bank",             "resistance": 0},
    "AXISBANK.NS":      {"name": "Axis Bank",              "resistance": 0},
    "DIXON.NS":         {"name": "Dixon Technologies",     "resistance": 0},
    "KAJARIACER.NS":    {"name": "Kajaria",                "resistance": 0},
    "BSE.NS":           {"name": "BSE",                    "resistance": 0},
    "ASHOKLEY.NS":      {"name": "Ashok Leyland",          "resistance": 0},
    "ADANIPOWER.NS":    {"name": "Adani Power",            "resistance": 0},
    "ADANIPORTS.NS":    {"name": "Adani Ports",            "resistance": 0},
    "RADICO.NS":        {"name": "Radico Khaitan",         "resistance": 0},
    "INFY.NS":          {"name": "Infosys",                "resistance": 0},
    "WIPRO.NS":         {"name": "Wipro",                  "resistance": 0},
    "HAL.NS":           {"name": "HAL",                    "resistance": 0},
    "MAZDOCK.NS":       {"name": "Mazagon Dock",           "resistance": 0},
    "GRSE.NS":          {"name": "GRSE",                   "resistance": 0},
    "DATAPATTNS.NS":    {"name": "Data Patterns",          "resistance": 0},
    "ASTRAMICRO.NS":    {"name": "Astra Microwave",        "resistance": 0},
    "APOLLOTYRE.NS":    {"name": "Apollo Tyres",           "resistance": 0},
    "YATHARTH.NS":      {"name": "Yatharth Hospitals",     "resistance": 0},
    "KIMS.NS":          {"name": "KIMS",                   "resistance": 0},
}

alerted_today = set()
IST = pytz.timezone("Asia/Kolkata")

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Telegram error: {e}")

def get_price(symbol):
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="1d", interval="5m")
        if data.empty:
            return None
        return round(data["Close"].iloc[-1], 2)
    except:
        return None

def check_breakouts():
    now = datetime.now(IST).time()
    if not (time(9, 15) <= now <= time(15, 30)):
        return
    for symbol, info in STOCKS.items():
        if info["resistance"] == 0 or symbol in alerted_today:
            continue
        price = get_price(symbol)
        if price is None:
            continue
        resistance = info["resistance"]
        pct_away = round(((resistance - price) / resistance) * 100, 2)
        if price >= resistance:
            msg = (f"🚨 <b>BREAKOUT ALERT!</b>\n\n"
                   f"📈 <b>{info['name']}</b>\n"
                   f"💰 Price: ₹{price}\n"
                   f"🎯 Resistance Broken: ₹{resistance}\n"
                   f"⚡ Status: <b>BREAKOUT CONFIRMED</b>\n"
                   f"⏰ {datetime.now(IST).strftime('%d %b %Y, %I:%M %p')}")
            send_telegram(msg)
            alerted_today.add(symbol)
        elif 0 < pct_away <= 5:
            warn_key = f"{symbol}_warn"
            if warn_key not in alerted_today:
                msg = (f"⚠️ <b>NEAR BREAKOUT!</b>\n\n"
                       f"📊 <b>{info['name']}</b>\n"
                       f"💰 Current: ₹{price}\n"
                       f"🎯 Resistance: ₹{resistance}\n"
                       f"📏 Only <b>{pct_away}%</b> away!\n"
                       f"⏰ {datetime.now(IST).strftime('%I:%M %p')}")
                send_telegram(msg)
                alerted_today.add(warn_key)

def daily_summary():
    now = datetime.now(IST)
    msg_lines = [f"📋 <b>DAILY WATCHLIST SUMMARY</b>",
                 f"📅 {now.strftime('%d %b %Y, %A')}\n"]
    for symbol, info in STOCKS.items():
        if info["resistance"] == 0:
            continue
        price = get_price(symbol)
        if price is None:
            msg_lines.append(f"• {info['name']}: ❌ Unavailable")
            continue
        resistance = info["resistance"]
        pct_away = round(((resistance - price) / resistance) * 100, 2)
        if price >= resistance:
            status = "🚀 BREAKOUT"
        elif pct_away <= 5:
            status = f"🔥 {pct_away}% away"
        elif pct_away <= 10:
            status = f"⚡ {pct_away}% away"
        else:
            status = f"📍 {pct_away}% away"
        msg_lines.append(f"• <b>{info['name']}</b>: ₹{price} | Target ₹{resistance} | {status}")
    send_telegram("\n".join(msg_lines))

def weekly_summary():
    if datetime.now(IST).weekday() != 6:
        return
    now = datetime.now(IST)
    msg_lines = [f"📊 <b>WEEKLY REPORT</b>",
                 f"📅 Week ending {now.strftime('%d %b %Y')}\n"]
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
            msg_lines.append(f"{arrow} <b>{info['name']}</b>\n"
                           f"   Week: ₹{week_open} → ₹{week_close} ({sign}{week_change}%)\n"
                           f"   Target: ₹{info['resistance']} | {pct_to_target}% to go\n")
        except:
            continue
    send_telegram("\n".join(msg_lines))

def reset_alerts():
    alerted_today.clear()

def run_bot():
    send_telegram("🤖 <b>Breakout Bot Started!</b>\n\n"
                 "✅ Checking breakouts every 15 mins\n"
                 "✅ Daily summary at 9:20 AM\n"
                 "✅ Weekly report every Sunday 8 PM\n\n"
                 "Bot is live and watching your stocks!")
    schedule.every(15).minutes.do(check_breakouts)
    schedule.every().day.at("09:20").do(daily_summary)
    schedule.every().day.at("20:00").do(weekly_summary)
    schedule.every().day.at("00:01").do(reset_alerts)
    print("Bot is running...")
    while True:
        schedule.run_pending()
        t.sleep(60)

if __name__ == "__main__":
    run_bot()
