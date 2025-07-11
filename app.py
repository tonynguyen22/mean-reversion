import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Mean-reversion test by Tony", layout="wide")
st.title("📈 Mean-reversion test by Tony")

# Upload Excel file
uploaded_file = st.file_uploader("Tải file excel lên với 3 dòng: 'ticker', 'date', 'close'", type=["xlsx"])

# Sidebar: User input parameters
st.sidebar.header("⚙️ Thông số")
ma_length = st.sidebar.number_input("SMA Length", min_value=10, max_value=300, value=50, step=5)
percentage_offset = st.sidebar.number_input("% giá giảm so với MA", min_value=0.0, max_value=100.0, value=15.0, step=0.5)
cooldown_period = st.sidebar.number_input("Thời gian chờ sau mỗi lệnh (ngày)", min_value=1, max_value=500, value=100, step=5)

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        df.columns = [col.strip().lower() for col in df.columns]
        df['date'] = pd.to_datetime(df['date'], dayfirst=True)
        df['close'] = round(df['close'], 1)
        df.sort_values("date", inplace=True)
        df.reset_index(drop=True, inplace=True)

        # Calculate indicators
        df['ma'] = df['close'].rolling(ma_length).mean()
        df['threshold'] = df['ma'] * (1 - percentage_offset / 100)
        df['buy_signal'] = False

        last_buy_idx = -cooldown_period - 1
        for i in range(ma_length, len(df)):
            if df.loc[i, 'close'] < df.loc[i, 'threshold'] and (i - last_buy_idx > cooldown_period):
                df.loc[i, 'buy_signal'] = True
                last_buy_idx = i

        # Backtest logic
        returns = {'T+90%': [], 'T+180%': [], 'T+360%': []}
        detailed_trades = []
        buy_signals = df[df['buy_signal']]
        buy_count = 0

        for idx, row in buy_signals.reset_index(drop=True).iterrows():
            original_idx = buy_signals.index[idx]
            entry_date = df.loc[original_idx, 'date']
            entry_price = df.loc[original_idx, 'close']
            trade_result = {
                'Entry Date': entry_date,
                'Entry Price': entry_price
            }
            for label, offset in zip(['T+90%', 'T+180%', 'T+360%'], [90, 180, 360]):
                target_idx = original_idx + offset
                if target_idx < len(df):
                    future_price = df.loc[target_idx, 'close']
                    ret = round((future_price - entry_price) / entry_price * 100, 2)
                    returns[label].append(ret)
                    trade_result[label] = ret
                else:
                    trade_result[label] = 'NaN'
            detailed_trades.append(trade_result)
            buy_count += 1

        # Summary
        summary = {
            'Total Trades': buy_count,
            'Avg T+90 Return (%)': round(np.mean(returns['T+90']), 2) if returns['T+90'] else 'Chưa đủ nến',
            'Avg T+180 Return (%)': round(np.mean(returns['T+180']), 2) if returns['T+180'] else 'Chưa đủ nến',
            'Avg T+360 Return (%)': round(np.mean(returns['T+360']), 2) if returns['T+360'] else 'Chưa đủ nến',
        }

        # Output
        st.subheader("📊 Summary")
        st.dataframe(pd.DataFrame([summary]))

        st.subheader("📄 Detailed Trade Log")
        st.dataframe(pd.DataFrame(detailed_trades))

    except Exception as e:
        st.error(f"❌ Error processing file: {e}")
