import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ページレイアウト設定
st.set_page_config(layout="wide", page_title="NIY=F Strategic Chart")

def flatten_cols(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

# データ取得
@st.cache_data(ttl=600) # 10分間キャッシュして効率化
def load_data():
    ticker = "NIY=F"
    df_d = yf.download(ticker, period="90d", interval="1d")
    df_30 = yf.download(ticker, period="5d", interval="30m")
    return flatten_cols(df_d), flatten_cols(df_30)

st.title("NIY=F Strategic 3-Level Chart")

try:
    df_daily_raw, df_30m_raw = load_data()

    # σ算出
    df_daily = df_daily_raw.dropna(subset=['Close'])
    sigma = float(df_daily['Close'].tail(25).std())

    # ロジック
    update_threshold = 100
    round_unit = 50
    df_30m = df_30m_raw.dropna()
    current_high = float(df_30m['High'].iloc[0])
    
    results = []
    for index, row in df_30m.iterrows():
        if float(row['High']) >= (current_high + update_threshold):
            current_high = float(row['High'])
        
        label = f"{index.hour}"
        if index.minute == 30: label += "3"
        if index.hour == 0 and index.minute == 0:
            label = f"{index.day}d\n{label}"
        
        results.append({
            'DateTime': index, 'Label': label, 'Close': float(row['Close']),
            'P50': round(current_high/round_unit)*round_unit,
            'P48': round((current_high - sigma*0.2)/round_unit)*round_unit,
            'P45': round((current_high - sigma*0.5)/round_unit)*round_unit,
            'P40': round((current_high - sigma)/round_unit)*round_unit
        })

    res_df = pd.DataFrame(results).set_index('DateTime').tail(96)
    latest = res_df.iloc[-1]
    
    # 可視化
    fig, ax = plt.subplots(figsize=(16, 8))
    x = np.arange(len(res_df))
    ax.plot(x, res_df['Close'], color='black', alpha=0.4)
    ax.step(x, res_df['P50'], where='post', color='red', linewidth=2, label='P50')
    ax.step(x, res_df['P48'], where='post', color='green', linestyle='-.', label='P48')
    ax.step(x, res_df['P45'], where='post', color='blue', linestyle='--', label='P45')
    ax.step(x, res_df['P40'], where='post', color='gray', linestyle=':', label='P40')

    ax.set_xticks(x[::2])
    ax.set_xticklabels(res_df['Label'].iloc[::2], fontsize=8)
    
    # 右パネル
    panel = (
        f" LATEST PRICE\n {latest['Close']:,.0f}\n"
        f" -----------------\n"
        f" TARGET LEVELS\n -----------------\n"
        f" P50 (Red)  : {latest['P50']:,.0f}\n"
        f" P48 (Green): {latest['P48']:,.0f}\n"
        f" P45 (Blue) : {latest['P45']:,.0f}\n"
        f" P40 (Gray) : {latest['P40']:,.0f}\n"
        f" -----------------\n"
        f" Sigma(25d) : {sigma:,.0f}\n"
        f" -----------------\n"
        f" DIST (P48) : {latest['Close'] - latest['P48']:,.0f}\n"
        f" DIST (P45) : {latest['Close'] - latest['P45']:,.0f}"
    )
    ax.text(1.02, 0.95, panel, transform=ax.transAxes, fontsize=11, 
            verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.9), family='monospace', fontweight='bold')

    ax.grid(True, alpha=0.1)
    st.pyplot(fig)

except Exception as e:
    st.error(f"エラーが発生しました: {e}")

