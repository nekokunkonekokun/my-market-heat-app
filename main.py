import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

st.title("Nikkei 225 Deviation Monitor")

# データ取得
df = yf.download("NIY=F", period="1y", interval="1h")
df.index = df.index.tz_convert('Asia/Tokyo')

# 指標計算
max_price = df['Close'].max()
current_price = df['Close'].iloc[-1]
std = df['Close'].rolling(window=25).std().iloc[-1]
current_time = df.index[-1].strftime('%Y-%m-%d %H:%M')

# 偏差計算 (最高値を50とする)
current_dev = 50 - ((max_price - current_price) / std)

# 表示情報
st.write(f"**Last Update:** {current_time}")
st.metric("Current Price", f"{current_price:.0f}", f"Deviation: {current_dev:.1f}")

# 価格帯パネル
st.subheader("Price Levels")
cols = st.columns(3)
for i, dev in enumerate([50, 40, 30]):
    price = max_price - (50 - dev) * std
    cols[i].metric(f"Dev {dev}", f"{price:.0f}")

# グラフ
fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(df.index[-168:], df['Close'].tail(168), color='black', label='Price')
ax.axhline(max_price, color='red', linestyle='--', label='Dev 50 (Max)')
ax.grid(True)
st.pyplot(fig)
