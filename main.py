import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(layout="wide", page_title="NIY=F Strategic Fixed Chart")

def flatten_cols(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

@st.cache_data(ttl=600)
def load_data():
    ticker = "NIY=F"
    df_1y = flatten_cols(yf.download(ticker, period="1y", interval="1d"))
    df_25d = flatten_cols(yf.download(ticker, period="25d", interval="1d"))
    return df_1y.dropna(), df_25d.dropna()

try:
    df_1y, df_25d = load_data()
    # Seriesから数値を取り出すために .max() や .iloc[-1] を使用
    p50_base = float(df_1y['High'].max())
    sigma = float(df_25d['Close'].std())
    latest_close = float(df_25d['Close'].iloc[-1])

    levels = {
        'P50': p50_base,
        'P45': p50_base - (sigma * 0.5),
        'P40': p50_base - (sigma * 1.0),
        'P35': p50_base - (sigma * 1.5),
        'P30': p50_base - (sigma * 2.0),
        'P25': p50_base - (sigma * 2.5),
        'P20': p50_base - (sigma * 3.0)
    }

    fig, ax = plt.subplots(figsize=(16, 8))
    ax.plot(df_25d.index, df_25d['Close'], color='black', alpha=0.6, label='Price')
    
    colors = ['red', 'green', 'blue', 'gray', 'purple', 'orange', 'brown']
    for i, (name, val) in enumerate(levels.items()):
        ax.axhline(y=val, color=colors[i], linestyle='--' if i > 0 else '-', label=name, alpha=0.7)

    panel = f" LATEST PRICE\n {latest_close:,.0f}\n -----------------\n TARGET LEVELS\n -----------------\n"
    for name, val in levels.items():
        panel += f" {name:4} : {val:,.0f}\n"
    panel += f" -----------------\n Sigma(25d) : {sigma:,.0f}"
    
    ax.text(1.02, 0.95, panel, transform=ax.transAxes, fontsize=11, 
            verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.9), family='monospace', fontweight='bold')

    ax.grid(True, alpha=0.3)
    st.pyplot(fig)

except Exception as e:
    st.error(f"エラーが発生しました: {e}")
