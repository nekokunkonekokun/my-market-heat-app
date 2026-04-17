import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf
from datetime import datetime
import sys

# --- 1. データ取得 ---
ticker = "NIY=F"
df = yf.download(ticker, period="8mo", interval="1d", auto_adjust=True)

if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.get_level_values(0)

if df.empty:
    print("データ取得失敗")
    sys.exit()

df = df[['Close']].dropna()

# --- 2. 傾き算出 ---
def calc_slope(series, window):
    slopes = [np.nan] * (window - 1)
    for i in range(window - 1, len(series)):
        y = series[i - window + 1 : i + 1].values
        x = np.arange(window)
        slope = np.polyfit(x, y, 1)[0]
        slopes.append(slope)
    return pd.Series(slopes, index=series.index)

# --- 3. メイン計算 ---
periods = [1, 3, 8, 21]
slopes_df = pd.DataFrame(index=df.index)
for p in periods:
    window = p + 1 if p == 1 else p
    slopes_df[f'Slope{p}'] = calc_slope(df['Close'], window)

sigma_window = 120
z_scores = pd.DataFrame(index=slopes_df.index)
for p in periods:
    col = f'Slope{p}'
    rolling_std = slopes_df[col].rolling(window=sigma_window).std()
    slopes_df[f'Upper{p}'] = rolling_std * 2
    slopes_df[f'Lower{p}'] = -rolling_std * 2
    z_scores[f'Z{p}'] = slopes_df[col] / rolling_std

slopes_df['Energy_Deviation'] = 50 + (z_scores.mean(axis=1) * 10)

# --- 4. 可視化 (フルスペック版) ---
plot_df = slopes_df.tail(15)
price_df = df.loc[plot_df.index]
last_price = float(df['Close'].iloc[-1])

plt.rcParams['figure.dpi'] = 100
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(11, 13), sharex=True,
                                     gridspec_kw={'height_ratios': [1, 1.2, 0.8]})

# 上段：価格
ax1.plot(price_df.index, price_df['Close'], color='black', lw=2.5, label='Price')
ax1.set_title(f"{ticker} Energy Analysis (Last: {last_price:.2f})")
ax1.grid(alpha=0.2)

# 中段：エネルギー（2σ補助線含む）
colors = {'1': 'blue', '3': 'orange', '8': 'green', '21': 'red'}
for p in periods:
    p_str = str(p)
    ax2.plot(plot_df.index, plot_df[f'Slope{p}'], color=colors[p_str], lw=2.5, label=f'{p}d')
    ax2.plot(plot_df.index, plot_df[f'Upper{p}'], color=colors[p_str], lw=1, ls='--', alpha=0.4)
    ax2.plot(plot_df.index, plot_df[f'Lower{p}'], color=colors[p_str], lw=1, ls='--', alpha=0.4)
ax2.axhline(0, color='black', lw=1, alpha=0.5)
ax2.legend(loc='upper left', bbox_to_anchor=(1, 1), fontsize='small')
ax2.grid(alpha=0.2, ls=':')

# 下段：偏差値（境界線含む）
ax3.plot(plot_df.index, plot_df['Energy_Deviation'], color='purple', lw=4, label='Deviation')
ax3.axhline(50, color='black', lw=1.5)
ax3.axhline(65, color='red', lw=1, ls=':', label='Overheated')
ax3.axhline(35, color='blue', lw=1, ls=':', label='Compressed')
ax3.set_ylim(20, 80)
ax3.legend(loc='upper left', bbox_to_anchor=(1, 1), fontsize='small')
ax3.grid(alpha=0.2)

plt.tight_layout()

if 'streamlit' in sys.modules:
    import streamlit as st
    st.pyplot(fig)
else:
    plt.show()

print(f"Energy Deviation: {slopes_df['Energy_Deviation'].iloc[-1]:.2f}")
