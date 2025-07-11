import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Mean-reversion test by Tony", layout="wide")
st.title("📈 Mean-reversion test by Tony")

# Upload Excel file
uploaded_file = st.file_uploader("Tải file Excel với 3 cột: 'ticker', 'date', 'close'", type=["xlsx"])

# Sidebar: User input parameters
st.sidebar.header("⚙️ Thông số chiến lược")
ma_length = st.sidebar.number_input("SMA Length", min_value=10, max_value=300, value=50, step=5)
percentage_offset = st.sidebar.number_input("% giá giảm so với SMA", min_value=0.0, max_value=100.0, value=15.0, step=0.5)
cooldown_period = st.sidebar.number_input("Thời gian cách mỗi lệnh (ngày)", min_value=1, max_value=500, value=100, step=5)

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        df.columns = [col.strip().lower() for col in df.columns]
        df['date'] = pd.to_datetime(df['date'], dayfirst=True)
        df['close'] = round(df['close'], 1)
        df.sort_values("date", inplace=True)
        df.reset_index(drop=True, inplace=True)

        # Tính MA và ngưỡng
        df['ma'] = df['close'].rolling(ma_length).mean()
        df['threshold'] = df['ma'] * (1 - percentage_offset / 100)
        df['buy_signal'] = False

        last_buy_idx = -cooldown_period - 1
        for i in range(ma_length, len(df)):
            if df.loc[i, 'close'] < df.loc[i, 'threshold'] and (i - last_buy_idx > cooldown_period):
                df.loc[i, 'buy_signal'] = True
                last_buy_idx = i

        # Backtest logic
        horizons = [5, 10, 15, 20, 30, 40, 50, 60]
        labels = [f'T+{h} (%)' for h in horizons]
        returns = {label: [] for label in labels}
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

            for h, label in zip(horizons, labels):
                target_date = entry_date + pd.Timedelta(days=h)
                future_row = df[df['date'] >= target_date].head(1)
                if not future_row.empty:
                    future_price = future_row['close'].values[0]
                    ret = round((future_price - entry_price) / entry_price * 100, 2)
                    returns[label].append(ret)
                    trade_result[label] = ret
                else:
                    trade_result[label] = 'Chưa đủ nến'
            detailed_trades.append(trade_result)
            buy_count += 1

        # Summary
        summary = {'Số lệnh': buy_count}
        for label in labels:
            summary[f'AVG {label}'] = (
                round(np.mean(returns[label]), 2) if returns[label] else 'Chưa đủ nến'
            )

        # Style functions
        def highlight_and_format(val):
            if isinstance(val, (float, int)):
                color = 'green' if val > 0 else 'red' if val < 0 else 'black'
                return f'color: {color}; text-align: right'
            return ''

        def format_return(val):
            if isinstance(val, (float, int)):
                return f"{val:.2f}%"
            return val

        # Show summary
        st.subheader("📊 Kết quả tổng hợp")
        ketqua_df = pd.DataFrame([summary])
        avg_cols = [col for col in ketqua_df.columns if 'AVG' in col]
        ketqua = (
            ketqua_df.style
            .applymap(highlight_and_format, subset=avg_cols)
            .format({col: format_return for col in avg_cols})
        )
        st.dataframe(ketqua, use_container_width=True)

        # Show trade log
        st.subheader("📄 Chi tiết các lệnh mua")
        detailed_df = pd.DataFrame(detailed_trades)
        styled_df = (
            detailed_df.style
            .applymap(highlight_and_format, subset=labels)
            .format({**{col: format_return for col in labels}, 'Entry ccfPrice': '{:.1f}'})
        )
        st.dataframe(styled_df, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Lỗi xử lý file: {e}")
