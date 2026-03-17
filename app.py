import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from concurrent.futures import ThreadPoolExecutor

# --- 1. ページ設定 ---
st.set_page_config(page_title="日本株分析アプリ", layout="wide")

WATCHLIST_FILE = 'watchlist.txt'
PORTFOLIO_FILE = 'portfolio.csv'

# --- 2. データ取得・計算ロジック ---
def load_watchlist():
    if os.path.exists(WATCHLIST_FILE):
        with open(WATCHLIST_FILE, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    return []

def save_watchlist(watchlist):
    with open(WATCHLIST_FILE, 'w', encoding='utf-8') as f:
        for item in watchlist:
            f.write(f"{item}\n")

@st.cache_data
def load_master_csv():
    if not os.path.exists('stocks.csv'): return pd.DataFrame()
    df = pd.read_csv('stocks.csv', encoding='utf-8-sig', dtype={'code': str})
    df.columns = [c.lower().strip() for c in df.columns]
    return df.rename(columns={'month': '権利月', 'value': '優待価値', 'sector': 'セクター', 'content': '優待内容'})

def calculate_rsi(data, window=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def fetch_stock_data(code):
    try:
        t = yf.Ticker(f"{code}.T")
        info = t.info
        price = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose', 0)
        div_yield = (info.get('dividendYield', 0) or 0) * 100
        
        if div_yield > 50: div_yield /= 100
        is_anomaly = div_yield > 15.0

        payout = info.get('payoutRatio')
        payout_pct = payout * 100 if payout else None

        equity_ratio = None
        try:
            bs = t.balance_sheet
            if not bs.empty:
                total_assets = bs.loc['Total Assets'].iloc[0] if 'Total Assets' in bs.index else None
                stockholder_equity = bs.loc['Stockholders Equity'].iloc[0] if 'Stockholders Equity' in bs.index else None
                if total_assets and stockholder_equity and total_assets > 0:
                    equity_ratio = (stockholder_equity / total_assets) * 100
        except: pass

        return {
            "code": str(code),
            "株価": price,
            "配当利回り": float(div_yield),
            "配当性向": payout_pct,
            "自己資本比率": equity_ratio,
            "1株配当": info.get('dividendRate', 0),
            "異常フラグ": is_anomaly,
            "PER": info.get('trailingPE'),
            "PBR": info.get('priceToBook'),
            "時価総額": info.get('marketCap', 0) / 10**8
        }
    except: return None

def get_market_indices():
    try:
        tickers = yf.Tickers("^N225 JPY=X")
        n225 = tickers.tickers["^N225"].history(period="5d")
        n_price = n225['Close'].iloc[-1] if not n225.empty else 0
        n_delta = n_price - n225['Close'].iloc[-2] if not n225.empty else 0
        usd = tickers.tickers["JPY=X"].history(period="5d")
        u_price = usd['Close'].iloc[-1] if not usd.empty else 0
        u_delta = u_price - usd['Close'].iloc[-2] if not usd.empty else 0
        return n_price, n_delta, u_price, u_delta
    except: return 0, 0, 0, 0

@st.cache_data(ttl=3600)
def get_all_metrics(codes_tuple, _master_df):
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(fetch_stock_data, codes_tuple))
    
    res_list = [r for r in results if r is not None]
    if not res_list: return pd.DataFrame()
    
    fin_df = pd.DataFrame(res_list)
    merged = pd.merge(fin_df, _master_df, on='code', how='left')
    
    merged['最低購入額'] = merged['株価'] * 100
    val_num = merged['優待価値'].astype(str).str.extract(r'(\d+)')[0]
    merged['優待利回り'] = (pd.to_numeric(val_num, errors='coerce').fillna(0) / merged['最低購入額']) * 100
    merged['総合利回り'] = merged['配当利回り'] + merged['優待利回り']
    
    # --- 重要：KeyError対策のカラム強制生成 ---
    for col in ['異常フラグ', '配当性向', '自己資本比率', '1株配当', 'PER', 'PBR']:
        if col not in merged.columns:
            merged[col] = None
    if '異常フラグ' not in merged.columns or merged['異常フラグ'].isnull().all():
        merged['異常フラグ'] = False
        
    return merged

def highlight_cells(row):
    styles = [''] * len(row)
    try:
        if '配当利回り' in row.index:
            idx = row.index.get_loc('配当利回り')
            if row.get('異常フラグ', False):
                styles[idx] = 'background-color: #fff3cd; color: #856404; font-weight: bold;'
            elif row['配当利回り'] >= 4.0:
                styles[idx] = 'color: red; font-weight: bold;'
        if '配当性向' in row.index and pd.notna(row['配当性向']) and row['配当性向'] <= 80.0:
            styles[row.index.get_loc('配当性向')] = 'color: green; font-weight: bold;'
        if '自己資本比率' in row.index and pd.notna(row['自己資本比率']) and row['自己資本比率'] >= 30.0:
            styles[row.index.get_loc('自己資本比率')] = 'color: green; font-weight: bold;'
    except: pass
    return styles

# --- 3. メインUI ---
st.title("📈 日本株分析アプリ")

n_price, n_delta, u_price, u_delta = get_market_indices()
c_idx1, c_idx2, _ = st.columns([2, 2, 6])
c_idx1.metric("日経平均", f"{n_price:,.0f}円", f"{n_delta:+.0f}円")
c_idx2.metric("ドル円", f"{u_price:.2f}円", f"{u_delta:+.2f}円")
st.divider()

df_master = load_master_csv()
if df_master.empty:
    st.error("stocks.csv が見つかりません。")
else:
    tab1, tab2 = st.tabs(["📊 銘柄分析", "💼 ポートフォリオ"])

    with tab1:
        if 'my_watchlist' not in st.session_state:
            st.session_state.my_watchlist = load_watchlist()

        st.sidebar.header("フィルタ設定")
        stop_loss_pct = st.sidebar.slider("損切目安 (%)", 1, 20, 5)
        
        all_options = (df_master['code'].astype(str) + " " + df_master['name']).unique()
        new_stocks = st.multiselect("監視銘柄を追加", options=all_options, default=st.session_state.my_watchlist)
        if new_stocks != st.session_state.my_watchlist:
            st.session_state.my_watchlist = new_stocks
            save_watchlist(new_stocks)
            st.rerun()

        if st.session_state.my_watchlist:
            codes = [n.split()[0] for n in st.session_state.my_watchlist]
            full_df = get_all_metrics(tuple(codes), df_master)
            
            min_y = st.sidebar.slider("最小配当利回り", 0.0, 10.0, 0.0)
            f_df = full_df[full_df['配当利回り'] >= min_y]

            if not f_df.empty:
                cols = ['code', 'name', '株価', '配当利回り', '優待利回り', '総合利回り', '配当性向', '自己資本比率', 'PER', 'PBR', '権利月']
                st.dataframe(f_df[cols].style.format({
                    '株価':'{:,.0f}円','配当利回り':'{:.2f}%','優待利回り':'{:.2f}%','総合利回り':'{:.2f}%',
                    '配当性向':'{:.1f}%','自己資本比率':'{:.1f}%','PER':'{:.1f}倍','PBR':'{:.2f}倍'
                }).apply(highlight_cells, axis=1), use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row", key="main_table")

                # 詳細エリア
                sel = st.session_state.get("main_table", {}).get("selection", {}).get("rows", [])
                target = f_df.iloc[sel[0]] if sel else f_df.iloc[0]
                
                st.divider()
                d1, d2 = st.columns([1, 2])
                with d1:
                    with st.container(border=True):
                        st.subheader(f"{target['name']} ({target['code']})")
                        if target.get('異常フラグ'): st.error("⚠️ 利回り異常値の可能性あり")
                        m1, m2 = st.columns(2)
                        p_s = f"{target['配当性向']:.1f}%" + (" ✅" if target['配当性向']<=80 else "") if pd.notna(target['配当性向']) else "-"
                        e_s = f"{target['自己資本比率']:.1f}%" + (" ✅" if target['自己資本比率']>=30 else "") if pd.notna(target['自己資本比率']) else "-"
                        m1.metric("配当性向", p_s)
                        m2.metric("自己資本比率", e_s)
                        st.info(f"🎁 優待: {target['優待内容']}")
                with d2:
                    period = st.radio("期間", ["3ヶ月", "1年", "2年"], horizontal=True, key="p_radio")
                    p_map = {"3ヶ月": ("6mo", 60), "1年": ("2y", 245), "2年": ("5y", 490)}
                    h = yf.Ticker(f"{target['code']}.T").history(period=p_map[period][0])
                    if not h.empty:
                        h['MA5'], h['MA25'], h['MA75'] = h['Close'].rolling(5).mean(), h['Close'].rolling(25).mean(), h['Close'].rolling(75).mean()
                        h['RSI'] = calculate_rsi(h['Close'])
                        sub = h.iloc[-p_map[period][1]:]
                        fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.6, 0.2, 0.2])
                        fig.add_trace(go.Candlestick(x=sub.index, open=sub['Open'], high=sub['High'], low=sub['Low'], close=sub['Close'], name='株価'), row=1, col=1)
                        fig.add_trace(go.Scatter(x=sub.index, y=sub['MA5'], name='5日', line=dict(color='green', width=1)), row=1, col=1)
                        fig.add_trace(go.Scatter(x=sub.index, y=sub['MA25'], name='25日', line=dict(color='red', width=1)), row=1, col=1)
                        fig.add_trace(go.Scatter(x=sub.index, y=sub['MA75'], name='75日', line=dict(color='blue', width=1)), row=1, col=1)
                        fig.add_trace(go.Bar(x=sub.index, y=sub['Volume'], name='出来高', marker_color='gray', opacity=0.4), row=2, col=1)
                        fig.add_trace(go.Scatter(x=sub.index, y=sub['RSI'], name='RSI', line=dict(color='purple')), row=3, col=1)
                        fig.update_layout(height=500, margin=dict(l=10, r=10, t=10, b=10), xaxis_rangeslider_visible=False, template="plotly_white")
                        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.header("💼 ポートフォリオ管理")
        pf_df = pd.read_csv(PORTFOLIO_FILE, dtype={'code': str}) if os.path.exists(PORTFOLIO_FILE) else pd.DataFrame(columns=['code', 'shares', 'purchase_price'])
        edited = st.data_editor(pf_df, column_config={"code": st.column_config.TextColumn("コード", required=True), "shares": "株数", "purchase_price": "取得単価"}, num_rows="dynamic", use_container_width=True, key="pf_edit")
        if not edited.equals(pf_df):
            edited.to_csv(PORTFOLIO_FILE, index=False)
            st.rerun()
        if not edited.empty and edited['code'].dropna().any():
            pf_m = get_all_metrics(tuple(edited['code'].dropna().unique()), df_master)
            if not pf_m.empty:
                res = pd.merge(edited, pf_m, on='code', how='left')
                res['配当金'] = res['shares'] * res['1株配当'].fillna(0)
                disp = res[['name', 'shares', 'purchase_price', '配当金', '優待内容', '権利月']].copy()
                disp.columns = ['銘柄名', '保有株数', '取得単価', '予想配当(年)', '優待内容', '権利月']
                st.dataframe(disp.style.format({'保有株数':'{:,.0f}','取得単価':'{:,.0f}円','予想配当(年)':'{:,.0f}円'}), use_container_width=True, hide_index=True)
                st.metric("年間予想配当合計", f"{res['配当金'].sum():,.0f}円")