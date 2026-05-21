import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("NIY=F Strategic 3-Level Chart")

# データ取得
df = yf.download("NIY=F", period="1y", interval="1h")
df.index = df.index.tz_convert('Asia/Tokyo')

# スカラー値へ変換
max_price = df['Close'].max().item()
current = df['Close'].iloc[-1].item()
std = df['Close'].rolling(window=25).std().iloc[-1].item()
current_time = df.index[-1].strftime('%Y-%m-%d %H:%M')

# サイドバーに定規（Target Levels）を配置
st.sidebar.write(f"**LATEST PRICE**: {current:.0f}")
st.sidebar.write("---")
st.sidebar.subheader("TARGET LEVELS")

levels = {"P50 (Red)": 0, "P48 (Green)": 2, "P45 (Blue)": 5, "P40 (Gray)": 10}
for label, diff in levels.items():
    price_level = max_price - (diff * std)
    st.sidebar.write(f"{label} : {price_level:.0f}")

st.sidebar.write("---")
st.sidebar.write(f"Sigma(25d) : {std:.0f}")
st.sidebar.write(f"Time : {current_time}")

# グラフ描画
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(df.index[-168:], df['Close'].tail(168), color='black', lw=1.2)
colors = ['red', 'green', 'blue', 'gray']
for i, (label, diff) in enumerate(levels.items()):
    ax.axhline(max_price - (diff * std), color=colors[i], linestyle='--', alpha=0.6, label=label)

ax.grid(True, alpha=0.3)
ax.legend(loc='upper left', fontsize='small')
st.pyplot(fig)
