#!/usr/bin/env python3

import requests
import yfinance as yf
import pandas as pd
from datetime import datetime
import os

# --- CONFIG S&P 500 dip detector ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
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


# --- Bitcoin Messages ---
def summarize_crypto(symbol: str, name: str) -> str:
    ticker = yf.Ticker(symbol)

    try:
        data = ticker.history(period="3y")
        if data.empty:
            return f"{name} data fetch failed."

        now = pd.Timestamp.now(tz='UTC')
        three_months_ago = now - pd.Timedelta(days=90)
        six_months_ago = now - pd.Timedelta(days=180)
        one_year_ago = now - pd.Timedelta(days=365)

        data_3m = data[data.index >= three_months_ago]
        data_6m = data[data.index >= six_months_ago]
        data_1y = data[data.index >= one_year_ago]
        data_3y = data

        last_week = data[data.index >= now - pd.Timedelta(days=7)]
        total_volume = last_week['Volume'].sum()

        # Prices
        current_price = data['Close'].iloc[-1]
        price_3m_ago = data_3m['Close'].iloc[0]
        price_6m_ago = data_6m['Close'].iloc[0]
        price_1y_ago = data_1y['Close'].iloc[0]
        price_3y_ago = data_3y['Close'].iloc[0]

        # % Changes
        pct_change_3m = ((current_price - price_3m_ago) / price_3m_ago) * 100
        pct_change_6m = ((current_price - price_6m_ago) / price_6m_ago) * 100
        pct_change_1y = ((current_price - price_1y_ago) / price_1y_ago) * 100
        pct_change_3y = ((current_price - price_3y_ago) / price_3y_ago) * 100

        # Approx Market Caps (price × volume)
        cap_now = current_price * data['Volume'].iloc[-1]
        cap_3m = price_3m_ago * data_3m['Volume'].iloc[0]
        cap_6m = price_6m_ago * data_6m['Volume'].iloc[0]
        cap_1y = price_1y_ago * data_1y['Volume'].iloc[0]
        cap_3y = price_3y_ago * data_3y['Volume'].iloc[0]

        def money(val): return f"${val:,.2f}"
        def money_b(val): return f"${val / 1e9:,.2f}B"

        msg = f"📊 *{name} Summary* — {now.strftime('%Y-%m-%d')}\n\n"
        msg += f"💰 Price: {money(current_price)}\n"
        msg += f"📈 % Change:\n"
        msg += f"  • 3M: {pct_change_3m:+.2f}%\n"
        msg += f"  • 6M: {pct_change_6m:+.2f}%\n"
        msg += f"  • 1Y: {pct_change_1y:+.2f}%\n"
        msg += f"  • 3Y: {pct_change_3y:+.2f}%\n\n"

        msg += f"🏦 Market Cap Estimates:\n"
        msg += f"  • Now: {money_b(cap_now)}\n"
        msg += f"  • Δ 3M: {money_b(cap_now - cap_3m)}\n"
        msg += f"  • Δ 6M: {money_b(cap_now - cap_6m)}\n"
        msg += f"  • Δ 1Y: {money_b(cap_now - cap_1y)}\n"
        msg += f"  • Δ 3Y: {money_b(cap_now - cap_3y)}\n\n"

        msg += f"🧮 7D Volume: {total_volume / 1e9:.2f}B {name}\n"
        msg += "Not financial advice. 🧂\n"

        return msg

    except Exception as e:
        return f"Error fetching {name} summary: {str(e)}"


def summarize_both_btc_eth():
    btc_summary = summarize_crypto("BTC-USD", "Bitcoin")
    eth_summary = summarize_crypto("ETH-USD", "Ethereum")
    divider = "\n" + "─" * 20 + "\n"
    return f"{btc_summary}{divider}{eth_summary}"





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
    report += "\n\n" + "─" * 20 + "\n"
    report += summarize_both_btc_eth()
    send_telegram(report)
    