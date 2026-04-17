import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf
from datetime import datetime
import sys

# --- 1. データ取得 ---
ticker = "NIY=F"
df = yf.download(ticker, period="8mo", interval="1d", auto_adjust=True)

# yfinanceのマルチインデックス対策
if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.get_level_values(0)

if df.empty:
    print("データが取得できませんでした。")
    sys.exit()

df = df[['Close']].dropna()

# --- 2. 傾き算出関数 ---
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

# --- 4. 可視化 ---
plot_df = slopes_df.tail(15)
price_df = df.loc[plot_df.index]
last_price = float(df['Close'].iloc[-1])

plt.rcParams['figure.dpi'] = 100
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 12), sharex=True,
                                     gridspec_kw={'height_ratios': [1, 1.2, 0.8]})

ax1.plot(price_df.index, price_df['Close'], color='black', lw=2.5, label='Price')
ax1.set_title(f"{ticker} Analysis (Last: {last_price:.2f})")
ax1.grid(alpha=0.3)

colors = {'1': 'blue', '3': 'orange', '8': 'green', '21': 'red'}
for p in periods:
    ax2.plot(plot_df.index, plot_df[f'Slope{p}'], color=colors[str(p)], lw=2.5, label=f'{p}d')
ax2.legend(loc='upper left', bbox_to_anchor=(1, 1))
ax2.grid(alpha=0.3, ls=':')

ax3.plot(plot_df.index, plot_df['Energy_Deviation'], color='purple', lw=4)
ax3.axhline(50, color='black', lw=1.5)
ax3.set_ylim(20, 80)
ax3.grid(alpha=0.3)

plt.tight_layout()

# Streamlit/Colab両対応の表示
if 'streamlit' in sys.modules:
    import streamlit as st
    st.pyplot(fig)
else:
    plt.show()

print(f"Energy Deviation: {slopes_df['Energy_Deviation'].iloc[-1]:.2f}")
