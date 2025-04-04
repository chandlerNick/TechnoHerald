#!/usr/bin/env python3

import requests
import yfinance as yf
import pandas as pd
from datetime import datetime

# --- CONFIG ---
BOT_TOKEN = "7005296291:AAHl_mQ9vyYfInoHQo6hNpjs9F1Bz6uxMq0"
CHAT_ID = "7568426940"
LOOKBACK = "6mo"
SYMBOL = "SPY"
VIX_SYMBOL = "^VIX"

# --- Analysis Function ---
def detect_dip():
    spy = yf.download(SYMBOL, period=LOOKBACK, interval="1d")
    vix = yf.download(VIX_SYMBOL, period=LOOKBACK, interval="1d")

    if spy.empty or vix.empty:
        return "Data fetch failed."

    spy['RSI'] = compute_rsi(spy['Close'])
    spy['5d_low'] = spy['Low'].rolling(window=5).min()

    last = spy.iloc[-1]
    prev = spy.iloc[-2]

    close = spy['Close'].iloc[-1]
    rsi = spy['RSI'].iloc[-1]
    low_5d = spy['5d_low'].iloc[-1]
    vix_close = vix['Close'].iloc[-1]
    vix_avg = vix['Close'].rolling(5).mean().iloc[-1]

    dip = (close < low_5d).iloc[0]
    oversold = rsi < 35
    vix_spike = (vix_close > vix_avg * 1.1).iloc[0]
    signal = dip and oversold and vix_spike

    
    # Build message
    msg = f"📊 S&P 500 Dip Report — {datetime.now().strftime('%Y-%m-%d')}\n"
    msg += f"📉 Close: ${float(close.iloc[0]):.2f}\n"
    msg += f"📈 RSI: {float(rsi):.2f} ({'Oversold' if oversold else 'Normal'})\n"
    msg += f"📉 5d Low: ${float(low_5d):.2f} ({'Below' if dip else 'Above'})\n"
    msg += f"⚠️ VIX: {float(vix_close.iloc[0]):.2f} ({'Spiking' if vix_spike else 'Calm'})\n"
    msg += f"\n📍 Bottom Signal: {'✅ YES' if signal else '❌ NO'}"
    msg += "\n\nNot investment advice. 🧂"

    return msg

def compute_rsi(series, window=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, data=payload)


# Helper method
def ping_bot():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    response = requests.get(url)
    print(response.json())


# --- Main ---
if __name__ == "__main__":
    report = detect_dip()
    send_telegram(report)