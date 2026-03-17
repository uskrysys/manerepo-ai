import streamlit as st
import pandas as pd
import datetime
import os
import calendar
import base64
import math
from typing import Any, Optional, List
import plotly.graph_objects as go
import plotly.express as px
try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
except ImportError:
    FPDF_AVAILABLE = False
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

# --- 1. ページ設定 ---
st.set_page_config(page_title="Manerepo - 次世代家計簿・資産管理プラットフォーム", layout="wide", page_icon="💰")

# --- 定数定義 ---
CURRENCY = "円"
UNIT_ASSET = "円"
UNIT_COUNT = "件"
ERROR_DATA_MISSING = "データがありません。入力を開始してください。"


# --- 2. CSSデザイン（プレミアムテーマ） ---
st.markdown("""
<style>
/* ===== ベース ===== */
.main { background-color: #fbfbfd; color: #1d1d1f; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }

/* ===== サイドバー ===== */
section[data-testid="stSidebar"] {
    background-color: #f5f5f7;
    border-right: 1px solid #e5e5ea;
}
section[data-testid="stSidebar"] * {
    color: #1d1d1f !important;
}
/* 入力フィールドのテキスト */
section[data-testid="stSidebar"] input {
    background-color: #ffffff !important;
    border: 1px solid #d2d2d7 !important;
    border-radius: 8px !important;
    padding: 8px 12px !important;
    color: #1d1d1f !important;
    font-weight: 400 !important;
    transition: border-color 0.2s;
}
section[data-testid="stSidebar"] input:focus {
    border-color: #0071e3 !important;
    box-shadow: 0 0 0 3px rgba(0, 113, 227, 0.2) !important;
}

/* ラジオボタン（セグメントコントロール風） */
.stRadio > div { gap: 4px !important; flex-wrap: wrap !important; background: #e5e5ea; padding: 4px; border-radius: 8px; }
.stRadio label { 
    background: transparent !important; 
    padding: 6px 16px !important; 
    border-radius: 6px !important; 
    color: #1d1d1f !important; 
    font-weight: 500 !important; 
    cursor: pointer; 
    transition: background-color 0.2s, color 0.2s;
}
.stRadio [data-baseweb="radio"] { background: transparent !important; }
.stRadio div[aria-checked="true"] label { 
    background: #ffffff !important; 
    box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important; 
} 

/* サイドバーの見出し・フォントウェイト調整 */
section[data-testid="stSidebar"] h1, 
section[data-testid="stSidebar"] h2, 
section[data-testid="stSidebar"] h3 {
    font-weight: 600 !important;
    letter-spacing: -0.02em;
}

/* ボタン類 */
.stButton>button, section[data-testid="stSidebar"] .stFormSubmitButton button {
    background-color: #0071e3 !important;
    color: white !important; 
    border: none !important; 
    border-radius: 18px !important;
    padding: 0.5rem 1.5rem !important; 
    font-weight: 500 !important;
    font-size: 14px !important;
    letter-spacing: -0.01em;
    box-shadow: none !important;
    transition: background-color 0.2s;
}
.stButton>button:hover, section[data-testid="stSidebar"] .stFormSubmitButton button:hover {
    background-color: #0077ed !important;
    cursor: pointer;
}

/* エキパンダー (details) */
section[data-testid="stSidebar"] details { 
    background-color: transparent !important; 
    border: 1px solid #d2d2d7;
    border-radius: 12px; 
    padding: 4px;
}
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
    color: #86868b !important;
    font-size: 12px !important;
}

/* ===== メインコンテンツ - タブ ===== */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px; background: transparent; padding: 0; border-bottom: 1px solid #e5e5ea;
}
.stTabs [data-baseweb="tab"] {
    padding: 12px 16px; font-weight: 500; color: #86868b;
    border: none !important; background: transparent !important;
    transition: color 0.2s;
}
.stTabs [aria-selected="true"] {
    color: #1d1d1f !important;
    border-bottom: 2px solid #1d1d1f !important;
}

/* ===== 見出し ===== */
h1, h2, h3 { color: #1d1d1f !important; font-weight: 600 !important; letter-spacing: -0.02em; }
h1 { font-size: 28px !important; }
h2 { font-size: 22px !important; }
h3 { font-size: 18px !important; }

/* ===== カード ===== */
.metric-card {
    background: #ffffff; 
    border-radius: 18px; 
    padding: 24px;
    border: 1px solid #e5e5ea;
    box-shadow: 0 4px 24px rgba(0,0,0,0.02);
}
.metric-card .label { font-size: 12px; color: #86868b; font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 8px; }
.metric-card .value { font-size: 32px; font-weight: 600; color: #1d1d1f; letter-spacing: -0.03em; }
.metric-card .sub { font-size: 13px; color: #86868b; margin-top: 4px; }

.badge-card {
    background: #ffffff; 
    border-radius: 14px; 
    padding: 16px;
    border: 1px solid #e5e5ea;
    margin-bottom: 12px; 
    display: flex; align-items: center; gap: 14px;
}
.badge-card .icon { font-size: 24px; }
.badge-card .info .title { font-weight: 600; color: #1d1d1f; font-size: 15px; }
.badge-card .info .desc { color: #86868b; font-size: 13px; line-height: 1.4; }

/* ===== カレンダー ===== */
.cal-table { width: 100%; border-collapse: collapse; margin-top: 8px; }
.cal-table th { color: #86868b; padding: 12px 8px; font-size: 12px; font-weight: 500; border-bottom: 1px solid #e5e5ea; }
.cal-table td { padding: 16px 8px; text-align: center; border-bottom: 1px solid #f5f5f7; font-size: 14px; position: relative; }
.cal-spent { color: #ff3b30 !important; font-weight: 500; }
.cal-income { color: #34c759 !important; font-weight: 500; }
.cal-both { color: #0071e3 !important; font-weight: 500; }
.cal-today { font-weight: 700; background-color: #f5f5f7; border-radius: 8px; }

/* ===== 予実テーブル & 収支明細テーブル ===== */
.budget-table, .tx-table { width: 100%; border-collapse: collapse; margin-top: 12px; }
.budget-table th, .tx-table th { 
    color: #86868b; padding: 12px 16px; font-size: 13px; font-weight: 500; 
    text-align: left; border-bottom: 1px solid #e5e5ea; 
}
.budget-table td, .tx-table td { 
    color: #1d1d1f; padding: 14px 16px; font-size: 14px; 
    border-bottom: 1px solid #f5f5f7; 
}
.tx-income { color: #34c759; font-weight: 500; }
.tx-expense { color: #ff3b30; font-weight: 500; }

/* ===== セクション区切り ===== */
.section-header {
    margin: 32px 0 16px 0;
    padding-bottom: 8px;
    border-bottom: 1px solid #e5e5ea;
    font-weight: 600; color: #1d1d1f; font-size: 20px;
    letter-spacing: -0.01em;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

/* カレンダーセルの塗り分け */
.cal-table td { padding: 12px 4px; text-align: center; border-radius: 10px; font-size: 14px; position: relative; transition: all 0.2s; }
.cal-spent { background-color: rgba(255, 59, 48, 0.18) !important; color: #ff3b30 !important; font-weight: 600; }
.cal-income { background-color: rgba(52, 199, 89, 0.18) !important; color: #34c759 !important; font-weight: 600; }
.cal-both { 
    background: linear-gradient(135deg, rgba(52, 199, 89, 0.25) 50%, rgba(255, 59, 48, 0.25) 50%) !important; 
    color: #1d1d1f !important; 
    font-weight: 600; 
}
.cal-today { border: 2px solid #0071e3 !important; }

/* プログレスバー */
.progress-outer { background: #e5e5ea; border-radius: 12px; height: 16px; overflow: hidden; margin: 12px 0; }
.progress-inner { height: 100%; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-weight: 600; font-size: 10px; color: white; }

/* ===== スマホ対応 ===== */
@media (max-width: 768px) {
    .metric-card { padding: 20px; }
    .metric-card .value { font-size: 26px; }
    .cal-table th, .cal-table td { font-size: 12px; padding: 10px 4px; }
    .budget-table, .tx-table { display: block; overflow-x: auto; white-space: nowrap; }
    .section-header { font-size: 18px; margin: 24px 0 12px 0; }
}
</style>
""", unsafe_allow_html=True)

FILENAME = "kakeibo_data_v2.csv"
# --- ユーザー情報の中心管理 ---
def get_current_user_id():
    """
    現在ログインしているユーザーIDを返します。
    将来的に Supabase Auth を実装した際は、ここを return supabase.auth.user().id に変更するだけで済みます。
    """
    # 暫定的に固定のUUID形式（22P02エラー対策）を使用
    DUMMY_UUID = "00000000-0000-0000-0000-000000000000"
    return DUMMY_UUID

if "user_id" not in st.session_state:
    st.session_state.user_id = get_current_user_id()
USER_ID = st.session_state.user_id

if "business_type" not in st.session_state:
    st.session_state.business_type = "給与所得者"

if "family_info" not in st.session_state:
    st.session_state.family_info = {
        "num_children": 0,
        "child_grades": []
    }

if "life_events" not in st.session_state:
    st.session_state.life_events = pd.DataFrame(columns=["年", "年齢", "イベント名", "金額"])

if "sim_params" not in st.session_state:
    st.session_state.sim_params = {
        "years": 10,
        "rate": 3.0,
        "inflation": 2.0,
        "use_tax": False
    }

# 属性に応じたラベル切り替え関数
def get_label(key):
    is_biz = st.session_state.business_type == "個人事業主"
    labels = {
        "income": "売上" if is_biz else "収入",
        "income_all": "累計売上" if is_biz else "累計収入",
        "expense": "経費" if is_biz else "支出",
        "balance": "事業収支" if is_biz else "収支バランス",
    }
    return labels.get(key, key)

# --- レジリエンス（復旧力）管理 ---
if "is_synced" not in st.session_state:
    st.session_state.is_synced = True

def handle_save_error(e):
    st.session_state.is_synced = False
    st.sidebar.error(f"⚠️ サーバー保存に失敗しました。ローカルに一時保存します。再接続時に同期を試みます。")

# --- ライフイベント・税金計算用ロジック ---
def generate_education_events(num_children, child_grades):
    events = []
    this_year = datetime.date.today().year
    
    # 学年(String)から現在の年齢(Int)を推測する概算ロジック
    grade_map = {
        "未就学": 4, "小1": 6, "小2": 7, "小3": 8, "小4": 9, "小5": 10, "小6": 11,
        "中1": 12, "中2": 13, "中3": 14, "高1": 15, "高2": 16, "高3": 17,
        "大1": 18, "大2": 19, "大3": 20, "大4": 21
    }
    
    for i in range(num_children):
        grade = child_grades[i] if i < len(child_grades) else "未就学"
        current_age = grade_map.get(grade, 4)
        
        child_label = f"第{i+1}子"
        # ライフイベントのポイント: 13(中校入学), 16(高校入学), 19(大学入学)
        milestones = [
            (6, "小学校入学", 200000), 
            (12, "中学校入学", 300000), 
            (15, "高校入学", 500000), 
            (18, "大学入学", 1500000)
        ]
        
        for m_age, m_name, m_cost in milestones:
            years_later = m_age - current_age
            if years_later >= 0:
                events.append({
                    "年": this_year + years_later,
                    "年齢": m_age,
                    "イベント名": f"{child_label} {m_name}",
                    "金額": m_cost
                })
    return pd.DataFrame(events).sort_values("年")

def calculate_approx_tax(income, business_type):
    """
    超概算の税金計算。所得税+住民税を合計約20%〜30%とする簡易モデル。
    """
    taxable_income = max(0, income - 480000) # 基礎控除 48万円
    if business_type == "個人事業主":
        taxable_income = max(0, taxable_income - 650000) # 青色申告特別控除 65万円
    
    # 簡易累進課税
    if taxable_income < 3000000:
        tax_rate = 0.15 # 所得税5% + 住民税10%
    elif taxable_income < 7000000:
        tax_rate = 0.25 # 所得税10〜20% + 住民税10%
    else:
        tax_rate = 0.35
    
    tax_amount = int(taxable_income * tax_rate)
    return tax_amount, taxable_income

# --- 前月データからの固定費コピーロジック ---
def register_fixed_costs_from_prev_month(df, user_id, current_month):
    last_month = (current_month - datetime.timedelta(days=1)).replace(day=1)
    # 前月の「固定費」に分類される支出を取得
    prev_month_df = df[(df["user_id"] == user_id) & (df["日付"].apply(lambda x: x.year == last_month.year and x.month == last_month.month))]
    # 固定費マスターに含まれるカテゴリのみ
    fixed_cats = [item for sublist in EXPENSE_MASTER["固定費"] for item in sublist] if isinstance(EXPENSE_MASTER["固定費"], list) else EXPENSE_MASTER["固定費"]
    
    prev_fixed_df = prev_month_df[prev_month_df["カテゴリー"].isin(fixed_cats)]
    
    current_month_df = df[(df["user_id"] == user_id) & (df["日付"].apply(lambda x: x.year == current_month.year and x.month == current_month.month))]
    
    added_rows = []
    skipped_items = []
    
    for _, row in prev_fixed_df.iterrows():
        # 同じカテゴリー・内容のものが今月すでにないかチェック
        exists = current_month_df[(current_month_df["カテゴリー"] == row["カテゴリー"]) & (current_month_df["内容"] == row["内容"])]
        if exists.empty:
            new_row = row.copy()
            new_row["日付"] = current_month.replace(day=1)
            added_rows.append(new_row.to_dict())
        else:
            skipped_items.append(f"{row['カテゴリー']}({row['内容']})")
            
    return added_rows, list(set(skipped_items))




def get_supabase_client():
    if not SUPABASE_AVAILABLE: return None
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except:
        return None

supabase = get_supabase_client()

@st.cache_data(ttl=300)
def load_data(user_id: str):
    if supabase is not None:
        try:
            response = supabase.table("transactions").select("*").eq("user_id", user_id).execute()
            df = pd.DataFrame(response.data)
            if not df.empty:
                df["日付"] = pd.to_datetime(df["日付"]).dt.date
                return df
        except Exception as e:
            st.sidebar.warning(f"Supabase読込エラー: {e} (ローカルCSVにフォールバックします)")
            
    # フォールバック（ローカルCSV）
    try:
        df = pd.read_csv(FILENAME)
        df["日付"] = pd.to_datetime(df["日付"]).dt.date
        if "user_id" not in df.columns: df["user_id"] = user_id
        # 現在のユーザーのデータのみを抽出
        return df[df["user_id"] == user_id].copy()
    except:
        df = pd.DataFrame(columns=["user_id", "日付", "タイプ", "カテゴリー", "内容", "金額", "性質"])
        return df

def save_data(df, user_id: str):
    df = df.copy()
    df["user_id"] = user_id
    
    try:
        df["金額"] = df["金額"].astype(int)
        df["日付"] = pd.to_datetime(df["日付"]).dt.date
    except Exception as e:
        st.error(f"データ型の変換に失敗しました: {e}")
        return

    # キャッシュクリア
    load_data.clear()

    # 1. Supabaseへの保存 (Resilience)
    try:
        if supabase is not None:
            records = df.to_dict(orient="records")
            for r in records:
                if isinstance(r["日付"], (datetime.date, datetime.datetime)):
                    r["日付"] = r["日付"].strftime("%Y-%m-%d")

            supabase.table("transactions").delete().eq("user_id", user_id).execute()
            if records:
                supabase.table("transactions").insert(records).execute()
            st.session_state.is_synced = True
    except Exception as e:
        handle_save_error(e)

    # 2. ローカルCSV(バックアップ/フォールバック)
    try:
        full_df = pd.read_csv(FILENAME) if os.path.exists(FILENAME) else pd.DataFrame()
        if not full_df.empty and "user_id" in full_df.columns:
            full_df = full_df[full_df["user_id"] != user_id]
        full_df = pd.concat([full_df, df], ignore_index=True)
        full_df.to_csv(FILENAME, index=False, encoding='utf-8-sig')
    except Exception as e:
        st.error(f"ローカル保存エラー: {e}")

if 'df' not in st.session_state:
    st.session_state.df = load_data(USER_ID)

# --- バランスシート（BS）データの定義 ---
ASSETS_FILENAME = "assets_data_v2.csv"

@st.cache_data(ttl=300)
def load_assets_data(user_id: str):
    if supabase is not None:
        try:
            response = supabase.table("assets").select("*").eq("user_id", user_id).execute()
            df = pd.DataFrame(response.data)
            if not df.empty:
                df["日付"] = pd.to_datetime(df["日付"]).dt.date
                return df
        except Exception as e:
            st.sidebar.warning(f"Supabase(BS)読込エラー: {e}")
            
    # フォールバック
    try:
        df = pd.read_csv(ASSETS_FILENAME)
        df["日付"] = pd.to_datetime(df["日付"]).dt.date
        if "user_id" not in df.columns: df["user_id"] = user_id
        return df[df["user_id"] == user_id].copy()
    except:
        return pd.DataFrame(columns=["user_id", "日付", "区分", "項目名", "金額"])

def save_assets_data(df, user_id: str):
    df = df.copy()
    df["user_id"] = user_id
    
    try:
        df["金額"] = df["金額"].astype(int)
        df["日付"] = pd.to_datetime(df["日付"]).dt.date
    except Exception as e:
        st.error(f"BSデータ型の変換に失敗しました: {e}")
        return

    # キャッシュクリア
    load_assets_data.clear()

    # 1. Supabaseへの保存
    try:
        if supabase is not None:
            records = df.to_dict(orient="records")
            for r in records:
                if isinstance(r["日付"], (datetime.date, datetime.datetime)):
                    r["日付"] = r["日付"].strftime("%Y-%m-%d")

            supabase.table("assets").delete().eq("user_id", user_id).execute()
            if records:
                supabase.table("assets").insert(records).execute()
    except Exception as e:
        st.sidebar.error(f"Supabase(BS)保存エラー: {e}")

    # 2. ローカルCSV
    try:
        full_df = pd.read_csv(ASSETS_FILENAME) if os.path.exists(ASSETS_FILENAME) else pd.DataFrame()
        if not full_df.empty and "user_id" in full_df.columns:
            full_df = full_df[full_df["user_id"] != user_id]
        full_df = pd.concat([full_df, df], ignore_index=True)
        full_df.to_csv(ASSETS_FILENAME, index=False, encoding='utf-8-sig')
    except Exception as e:
        st.error(f"BSローカル保存エラー: {e}")

if 'assets_df' not in st.session_state:
    st.session_state.assets_df = load_assets_data(USER_ID)

ASSET_TYPES = ["流動資産 (現金・預金)", "固定資産 (投資信託・証券)", "固定資産 (不動産・その他)", "流動負債 (クレカ等)", "固定負債 (ローン)"]

# --- 4. 財務会計ベースのマスターカテゴリ体系（単一ソース） ---
EXPENSE_MASTER = {
    "固定費": ["住居費", "通信費", "保険料", "水道光熱費", "サブスクリプション"],
    "変動費": ["食費", "日用品", "交通費", "娯楽・レジャー", "美容・健康", "その他"],
    "資産移転": ["投資（NISA/iDeCo等）"],
}
INCOME_MASTER = {
    "主収入": ["主収入（給与・事業）"],
    "副次収入": ["副次収入"],
    "運用益": ["資産運用益"],
    "特別利益": ["特別利益"],
}
# フラットリスト（UI選択肢用）
EXPENSE_CATEGORIES = [c for cats in EXPENSE_MASTER.values() for c in cats]
INCOME_CATEGORIES = [c for cats in INCOME_MASTER.values() for c in cats]

# 消費の性質（タグ）
CONSUMPTION_TAGS = ["消費 (Need)", "浪費 (Want)", "投資 (Invest)"]

# 予算デフォルト（マスター準拠）
DEFAULT_BUDGETS = {
    "住居費": 80000, "通信費": 10000, "保険料": 10000, "水道光熱費": 15000, "サブスクリプション": 5000,
    "食費": 40000, "日用品": 10000, "交通費": 10000, "娯楽・レジャー": 15000, "美容・健康": 5000, "その他": 10000,
    "投資（NISA/iDeCo等）": 30000,
}
if 'budgets' not in st.session_state:
    st.session_state.budgets = DEFAULT_BUDGETS.copy()

# --- 固定費・変動費の自動分類（マスター参照） ---
def classify_category(cat):
    """カテゴリをマスター定義に基づき固定費/変動費/資産移転に分類"""
    for cls, items in EXPENSE_MASTER.items():
        if cat in items:
            return cls
    # 後方互換：旧カテゴリ名も推論
    fixed_keywords = ["家賃", "住居", "保険", "通信", "サブスク", "ローン", "光熱"]
    if any(kw in str(cat) for kw in fixed_keywords):
        return "固定費"
    if "投資" in str(cat):
        return "資産移転"
    return "変動費"

def calculate_health_score(income, outgo, balance, total_assets, avg_monthly_expense, emergency_months_target=6):
    """家計の健全性スコア（0-100点）と各指標を返す"""
    savings_rate = ((income - outgo) / income * 100) if income > 0 else 0
    emergency_fund_needed = avg_monthly_expense * emergency_months_target
    invest_capacity = max(0, balance - (emergency_fund_needed / 12)) if balance > 0 else 0
    emergency_months = (total_assets / avg_monthly_expense) if avg_monthly_expense > 0 else 0
    score = 0
    score += min(40.0, savings_rate * 2)
    if invest_capacity > 0:
        score += min(20.0, invest_capacity / 5000 * 20)
    score += min(40.0, (emergency_months / emergency_months_target) * 40)
    score = max(0.0, min(100.0, score))
    return {
        'score': int(score),
        'savings_rate': savings_rate,
        'invest_capacity': invest_capacity,
        'emergency_months': emergency_months,
    }

def generate_ai_advisor_report(df, assets_df, cfp, summaries):
    """1級FP・公認会計士の思考プロセスを模倣するAIアドバイスロジック"""
    
    income = summaries.get('income', 0)
    outgo = summaries.get('outgo', 0)
    balance = summaries.get('balance', 0)
    savings_rate = cfp.get('savings_rate', 0)
    fixed_ratio = cfp.get('fixed_ratio', 0)
    emergency_months = cfp.get('emergency_months', 0)
    
    total_assets = 0
    total_liabilities = 0
    if not assets_df.empty:
        temp_bs = assets_df.copy()
        temp_bs["実額"] = temp_bs.apply(lambda r: r["金額"] if "資産" in str(r["区分"]) else -r["金額"], axis=1)
        total_assets = temp_bs[temp_bs["実額"] > 0]["実額"].sum()
        total_liabilities = abs(temp_bs[temp_bs["実額"] < 0]["実額"].sum())
    
    balance = 0
    current_net_worth = 0
    net_worth = total_assets - total_liabilities
    equity_ratio = (net_worth / total_assets * 100) if total_assets > 0 else 0
    
    rating = "C"
    rating_reason = "データが不足しているか、極めて厳しい財務状況です。"
    if income > 0:
        score = 0
        score += min(40, savings_rate * 2) 
        score += min(30, emergency_months * 5) 
        score += min(30, equity_ratio * 0.3) 
        
        if score >= 85:
            rating = "AAA"
            rating_reason = "【収益性・安全性・成長性】すべてにおいて極めて優秀な「エクセレント家計」です。複利効果による資産の急拡大期に入っています。"
        elif score >= 70:
            rating = "AA"
            rating_reason = "【安全性】が高く、順調に資産形成ができています。【成長性】（投資配分）をさらに高めることでAAAに到達可能です。"
        elif score >= 50:
            rating = "A"
            rating_reason = "健全な「優良家計」です。ただし【収益性】（毎月の黒字幅）がやや物足りないため、固定費の継続的な見直しが鍵となります。"
        elif score >= 30:
            rating = "BBB"
            rating_reason = "標準水準ですが、長期的な【安全性】にやや不安が残ります。「バケツの穴」を塞ぎ、貯蓄グセをつけるフェーズです。"
        elif score >= 15:
            rating = "BB"
            rating_reason = "【収益性】が低く、キャッシュフローが停滞しています。早急な「止血（支出の大幅削減）」が必要です。"
        else:
            rating = "C"
            rating_reason = "【安全性】が危機的状況です。債務超過や慢性的赤字の恐れがあり、抜本的な生活水準の見直しが急務です。"

    persona = "データ不足"
    notes = []
    
    if income == 0 and outgo == 0:
        notes.append("家計データの記録から始めましょう。データがないと、的確な分析はできません。")
    else:
        variable_df = summaries.get('this_month_df', pd.DataFrame())
        if type(variable_df) is pd.DataFrame and not variable_df.empty:
            exp_df = variable_df[variable_df["タイプ"] == "支出"]
            food = exp_df[exp_df["カテゴリー"] == "食費"]["金額"].sum()
            fun = exp_df[exp_df["カテゴリー"] == "娯楽・レジャー"]["金額"].sum()
            invest = exp_df[exp_df["カテゴリー"] == "投資（NISA/iDeCo等）"]["金額"].sum()
            
            if (food + fun) > (outgo * 0.4) and outgo > 0:
                persona = "享楽的・短期目線型"
                notes.append(f"食費や娯楽等の「今を楽しむ支出」が全体の {((food+fun)/outgo*100):.1f}% に達しています。人生を楽しむのは素晴らしいことですが、今の快楽が『未来の自分への借金』になっていないか、冷静に振り返りましょう。")
            elif invest > (outgo * 0.2) and outgo > 0:
                persona = "未来志向・自己規律型"
                notes.append(f"投資への配分が支出全体の {invest/outgo*100:.1f}% に達しています。素晴らしい自己規律です。「今の楽しみ」を適度に味わうことも忘れないでください。")
            elif fixed_ratio > 60:
                persona = "固定費拘束・耐え忍ぶ型"
                notes.append(f"固定費比率が {fixed_ratio:.1f}% と極めて高く、家計の身動きが取れません。住宅ローンや保険、サブスクなど「無意識に引かれるお金」のメス入れが最優先課題です。")
            else:
                persona = "堅実・バランス型"
                notes.append("特筆すべき極端な支出の偏りはなく、バランスの取れたお金の使い方をされています。ここからは『予算の最適化』へとステップアップする時期です。")
                
        if income > 0 and net_worth < (income * 3) and savings_rate > 15:
            notes.append("💡 CF・BS分析 (バケツの穴検知): 毎月の貯蓄率は高いものの、純資産がそれに比例して積み上がっていません。『死蔵されている現金』や『過去の債務返済』に追われている可能性があります。")
        elif net_worth > (outgo * 24) and savings_rate < 5 and outgo > 0:
            notes.append("💡 CF・BS分析 (黒字倒産予備軍): 潤沢な資産（2年以上生活できる額）をお持ちですが、直近のキャッシュフローは停滞しています。典型的な『アセットリッチ・キャッシュプア』であり、インフレ耐性に弱点があります。")
        elif total_liabilities > total_assets and total_liabilities > 0:
            notes.append("🚨 CF・BS分析 (債務超過リスク): 持っている資産より借入が多く、万が一の事態で破綻するリスクがあります。高金利の負債がある場合は、最優先で完済してください。")

        lm_outgo = summaries.get('lm_outgo', 0)
        if outgo > 0 and lm_outgo > 0:
            mom_increase = (outgo - lm_outgo) / lm_outgo * 100
            if mom_increase > 20:
                notes.append(f"⚠️ 異常検知 (ライフスタイル・クリープ): 前月比で支出が {mom_increase:.0f}% も急増しています。季節要因（イベント等）であれば問題ありませんが、無意識な生活水準の切り上げなら危険信号です。")
            elif mom_increase < -10:
                notes.append(f"✨ 改善検知: 前月よりも {abs(mom_increase):.0f}% 支出を抑えられています。この調子で「生活のダウンサイジング」を定着させましょう。")

    scenarios = {
        "最短ルート (Aggressive)": "すべてのサブスクを解約し、外食を月1回に制限。浮いた資金を全額NISA等に回し、最短での資産目標達成を目指すストイックなプラン。",
        "バランスルート (Moderate)": "固定費の最適化のみを実施し、生活の環境（変動費）は維持。毎月の無理のない黒字幅を着実に投資へ回していく王道プラン。",
        "リスク回避ルート (Conservative)": "生活防衛資金の確保を最優先に全額現金貯蓄。投資は極少額に留め、不況やリストラに備えて「防御力」を最大化するプラン。"
    }

    import random
    quotes = [
        "収入が増えたからといって、生活水準を上げるな。(ウォーレン・バフェット)",
        "今日を生き延びるためのお金と、明日を自由に生きるためのお金は違う。",
        "資産とは、あなたのポケットにお金を入れてくれるものだ。(ロバート・キヨサキ)"
    ]
    quote = random.choice(quotes)
    
    next_action = "「今月の固定費（不要なサブスク・保険・通信費）」を1つだけ解約・変更手続きしてください。たったこれだけの行動が、半永久的なリターンを生み出します。"
    if persona == "享楽的・短期目線型":
         next_action = "「コンビニや自販機での無意識な数百円の買い物」を今日から3日間だけ完全にゼロにしてみてください。"
    elif total_liabilities > 0:
         next_action = "持っている負債（リボ、各種ローン等）の「実質年率（金利）」を調べ、一番金利の高いものを今月中に繰り上げ返済してください。"

    return {
        "rating": rating,
        "rating_reason": rating_reason,
        "persona": persona,
        "notes": notes,
        "scenarios": scenarios,
        "quote": quote,
        "next_action": next_action
    }

def generate_cfp_diagnosis(income, outgo, fixed_cost, variable_cost, invest_amount, total_assets, avg_monthly_expense):
    """厳格なCFP（1級FP）基準の定量診断ロジック"""
    savings_rate = (1 - outgo / income) * 100 if income > 0 else 0
    fixed_ratio = fixed_cost / income * 100 if income > 0 else 0
    variable_ratio = variable_cost / income * 100 if income > 0 else 0
    invest_ratio = invest_amount / outgo * 100 if outgo > 0 else 0
    flexibility = 100 - fixed_ratio  # 家計の機動力
    safety_margin = (income - fixed_cost) / income * 100 if income > 0 else 0  # 安全余裕率
    emergency_months = total_assets / avg_monthly_expense if avg_monthly_expense > 0 else 0
    
    advices = []
    # 貯蓄率評価（目標20%）
    if savings_rate < 0:
        advices.append(f"【緊急】貯蓄率が {savings_rate:.1f}%（赤字）。損益分岐点の引き下げが急務です。固定費の再交渉（住居費・保険料）を推奨します。")
    elif savings_rate < 10:
        advices.append(f"【注意】貯蓄率 {savings_rate:.1f}%。目標の20%に対して乖離が大きい状態です。変動費の5%削減を第一目標に設定しましょう。")
    elif savings_rate >= 20:
        advices.append(f"【良好】貯蓄率 {savings_rate:.1f}%。目標20%を達成しています。余剰資金の資産配分最適化を検討しましょう。")
    else:
        advices.append(f"貯蓄率 {savings_rate:.1f}%。目標20%まであと {20 - savings_rate:.1f}pt。達成可能な範囲です。")
    
    # 固定費比率評価（限界利益アプローチ）
    if fixed_ratio > 55:
        advices.append(f"【警告】固定費比率 {fixed_ratio:.1f}%。家計の機動力（柔軟性）が {flexibility:.1f}% と低下しています。サブスク棚卸し・通信費最適化を検討してください。")
    elif fixed_ratio > 45:
        advices.append(f"固定費比率 {fixed_ratio:.1f}%。理想45%以下を目指し、損益分岐点の引き下げを検討しましょう。")
    else:
        advices.append(f"固定費比率 {fixed_ratio:.1f}%。良好な水準です。家計の機動力は {flexibility:.1f}% です。")
    
    # 資産配分評価
    if invest_ratio < 5 and outgo > 0:
        advices.append(f"【提案】投資比率 {invest_ratio:.1f}%。税効果の最適化（NISA満額活用）で資産形成スピードを加速できます。")
    elif invest_ratio >= 15:
        advices.append(f"投資比率 {invest_ratio:.1f}%。積極的な資産形成が行われています。リスク分散の確認を推奨します。")
    
    # 生活防衛資金
    if emergency_months < 3:
        advices.append(f"【注意】生活防衛資金 {emergency_months:.1f}ヶ月分。最低3ヶ月分の確保を優先してください。")
    
    return {
        'savings_rate': savings_rate,
        'fixed_ratio': fixed_ratio,
        'variable_ratio': variable_ratio,
        'invest_ratio': invest_ratio,
        'flexibility': flexibility,
        'safety_margin': safety_margin,
        'emergency_months': emergency_months,
        'advices': advices or [ERROR_DATA_MISSING],
    }

# --- 集計ロジック関数化 (DRY原則) ---
def calculate_summaries(df: pd.DataFrame, target_date: datetime.date = None) -> dict:
    if target_date is None:
        target_date = datetime.date.today()
    
    res = {}
    if df.empty:
        res['this_month_df'] = pd.DataFrame()
        res['last_month_df'] = pd.DataFrame()
        res['total_records'] = 0
        res['total_expense'] = 0
        res['total_income_all'] = 0
        res['invest_actual_all'] = 0
        res['invest_months'] = 0
        res['invest_monthly_avg'] = 0
        res['outgo'] = 0
        res['income'] = 0
        res['balance'] = 0
        res['invest_actual_month'] = 0
        res['lm_outgo'] = 0
        res['lm_income'] = 0
        return res
        
    df = df.copy()
    df["日付"] = pd.to_datetime(df["日付"]).dt.date
    
    # 今月
    this_month_df = df[df["日付"].apply(lambda x: x.month == target_date.month and x.year == target_date.year)]
    res['this_month_df'] = this_month_df
    
    # 全体集計
    res['total_records'] = int(len(df))
    res['total_expense'] = float(df[df["タイプ"] == "支出"]["金額"].sum())
    res['total_income_all'] = float(df[df["タイプ"] == "収入"]["金額"].sum())
    
    # 投資カテゴリー名の取得（マスターに依存）
    invest_cat = "投資（NISA/iDeCo等）"
    invest_df_all = df[(df["タイプ"] == "支出") & (df["カテゴリー"] == invest_cat)]
    res['invest_actual_all'] = float(invest_df_all["金額"].sum())
    invest_months = int(invest_df_all["日付"].apply(lambda x: f"{x.year}-{x.month}").nunique()) if not invest_df_all.empty else 0
    res['invest_months'] = invest_months
    res['invest_monthly_avg'] = float(res['invest_actual_all'] / invest_months) if invest_months > 0 else 0.0
    
    # 今月の集計
    res['outgo'] = float(this_month_df[this_month_df["タイプ"] == "支出"]["金額"].sum()) if not this_month_df.empty else 0.0
    res['income'] = float(this_month_df[this_month_df["タイプ"] == "収入"]["金額"].sum()) if not this_month_df.empty else 0.0
    res['balance'] = float(res['income'] - res['outgo'])
    res['invest_actual_month'] = float(this_month_df[(this_month_df["タイプ"] == "支出") & (this_month_df["カテゴリー"] == invest_cat)]["金額"].sum()) if not this_month_df.empty else 0.0
    
    # 固定費・変動費の分離集計
    if not this_month_df.empty:
        expense_df = this_month_df[this_month_df["タイプ"] == "支出"].copy()
        if not expense_df.empty:
            expense_df["費目分類"] = expense_df["カテゴリー"].apply(classify_category)
            res['fixed_cost'] = float(expense_df[expense_df["費目分類"] == "固定費"]["金額"].sum())
            res['variable_cost'] = float(expense_df[expense_df["費目分類"] == "変動費"]["金額"].sum())
        else:
            res['fixed_cost'] = 0.0
            res['variable_cost'] = 0.0
    else:
        res['fixed_cost'] = 0.0
        res['variable_cost'] = 0.0
    
    # 固定費率・変動費率・貯蓄率
    if res['income'] > 0:
        res['fixed_cost_ratio'] = float(res['fixed_cost'] / res['income'] * 100)
        res['variable_cost_ratio'] = float(res['variable_cost'] / res['income'] * 100)
        res['savings_ratio'] = float(max(0.0, (res['income'] - res['outgo']) / res['income'] * 100))
    else:
        res['fixed_cost_ratio'] = 0.0
        res['variable_cost_ratio'] = 0.0
        res['savings_ratio'] = 0.0
    
    # 先月の集計
    last_month = (target_date.replace(day=1) - datetime.timedelta(days=1))
    last_month_df = df[df["日付"].apply(lambda x: x.month == last_month.month and x.year == last_month.year)]
    res['last_month_df'] = last_month_df
    res['lm_outgo'] = last_month_df[last_month_df["タイプ"] == "支出"]["金額"].sum() if not last_month_df.empty else 0
    res['lm_income'] = last_month_df[last_month_df["タイプ"] == "収入"]["金額"].sum() if not last_month_df.empty else 0
    
    # 月平均支出（全期間）
    all_expense_df = df[df["タイプ"] == "支出"]
    if not all_expense_df.empty:
        months_active = all_expense_df["日付"].apply(lambda x: f"{x.year}-{x.month}").nunique()
        res['avg_monthly_expense'] = int(all_expense_df["金額"].sum() / max(1, months_active))
    else:
        res['avg_monthly_expense'] = 0
    
    return res


def get_historical_data(df, months=6):
    """過去Nヶ月分の月次集計（収入・支出・余剰金）をリストで返す"""
    if df.empty:
        return pd.DataFrame()
    
    today = datetime.date.today()
    history = []
    for i in range(months - 1, -1, -1):
        target_month = (today.replace(day=1) - pd.DateOffset(months=i)).date()
        m_df = df[pd.to_datetime(df["日付"]).apply(lambda x: x.month == target_month.month and x.year == target_month.year)]
        
        inc = float(m_df[m_df["タイプ"] == "収入"]["金額"].sum())
        exp = float(m_df[m_df["タイプ"] == "支出"]["金額"].sum())
        
        expense_df = m_df[m_df["タイプ"] == "支出"].copy()
        if not expense_df.empty:
            expense_df["費目分類"] = expense_df["カテゴリー"].apply(classify_category)
            fix = float(expense_df[expense_df["費目分類"] == "固定費"]["金額"].sum())
        else:
            fix = 0.0
            
        history.append({
            "年月": target_month.strftime("%Y/%m"),
            "収入": inc,
            "支出": exp,
            "余剰金": inc - exp,
            "固定費": fix
        })
    return pd.DataFrame(history)


# --- 投資シミュレーション関数 (DRY原則) ---
@st.cache_data
def calculate_compound_interest(initial_amount, monthly_contribution, annual_rate_pct, years, tax_rate=0.20315, inflation_rate_pct=0.0):
    """複利計算の結果をリストで返す。各年のNISA・特定口座・投資元本 + 実質価値を記録。"""
    monthly_rate = annual_rate_pct / 100 / 12
    annual_inflation = inflation_rate_pct / 100
    future_val_nisa = initial_amount
    total_invested = initial_amount
    
    results = [{
        "年": 0,
        "NISA口座 (非課税)": int(future_val_nisa),
        "特定口座 (課税後)": int(future_val_nisa),
        "投資元本": int(total_invested),
        "実質価値 (NISA)": int(future_val_nisa),
    }]
    
    for i in range(years * 12):
        total_invested += monthly_contribution
        future_val_nisa = (future_val_nisa + monthly_contribution) * (1 + monthly_rate)
        
        if (i + 1) % 12 == 0:
            yr = (i + 1) // 12
            current_gain = future_val_nisa - total_invested
            net_taxed = future_val_nisa - (current_gain * tax_rate) if current_gain > 0 else future_val_nisa
            # インフレ割引後の実質価値
            deflator = (1 + annual_inflation) ** yr if annual_inflation > 0 else 1
            real_val_nisa = future_val_nisa / deflator
            results.append({
                "年": yr,
                "NISA口座 (非課税)": int(future_val_nisa),
                "特定口座 (課税後)": int(net_taxed),
                "投資元本": int(total_invested),
                "実質価値 (NISA)": int(real_val_nisa),
            })
    
    return results, future_val_nisa, total_invested


def calculate_years_to_goal(goal, initial_amount, monthly_contribution, annual_rate_pct):
    """目標額までの年数を計算する。到達不可能な場合は None を返す。"""
    monthly_rate = annual_rate_pct / 100 / 12
    if monthly_rate <= 0 or monthly_contribution <= 0:
        return None
    
    r = monthly_rate
    pmt = monthly_contribution
    pv = initial_amount
    fv = goal
    
    numerator = pmt + r * pv
    denominator = pmt + r * pv - r * fv
    
    if numerator <= 0 or denominator <= 0:
        return None
    
    try:
        months_needed = math.log(numerator / denominator) / math.log(1 + r)
        return months_needed / 12
    except (ValueError, ZeroDivisionError):
        return None


# --- 固定費テンプレート ---
FIXED_COST_TEMPLATE = [
    {"カテゴリー": "住居費",   "内容": "毎月の家賃",       "金額": 80000},
    {"カテゴリー": "通信費", "内容": "スマホ・ネット代", "金額": 10000},
    {"カテゴリー": "保険料", "内容": "生命保険・損保",   "金額": 15000},
    {"カテゴリー": "水道光熱費", "内容": "電気・ガス・水道", "金額": 12000},
    {"カテゴリー": "サブスクリプション", "内容": "動画・音楽等", "金額": 2000},
]


def register_fixed_costs(df, template, user_id, target_date=None):
    """固定費を一括登録する。重複がある場合はスキップし、結果メッセージを返す。"""
    if target_date is None:
        target_date = datetime.date.today()
    first_of_month = target_date.replace(day=1)
    
    added = []
    skipped = []
    
    for item in template:
        if item["金額"] <= 0:
            continue
        
        # 重複チェック: 同月・同カテゴリー・同内容が既にあればスキップ
        if not df.empty:
            df_dates = pd.to_datetime(df["日付"]).dt.date
            same_month = df[
                (df_dates.apply(lambda x: x.year == first_of_month.year and x.month == first_of_month.month)) &
                (df["カテゴリー"] == item["カテゴリー"]) &
                (df["内容"] == item["内容"]) &
                (df["タイプ"] == "支出")
            ]
            if not same_month.empty:
                skipped.append(f"{item['カテゴリー']}（{item['内容']}）")
                continue
        
        added.append({
            "user_id": user_id,
            "日付": first_of_month,
            "タイプ": "支出",
            "カテゴリー": item["カテゴリー"],
            "内容": item["内容"],
            "金額": item["金額"],
            "性質": "消費 (Need)"
        })
    
    return added, skipped


# --- 共通のデータ管理UI (DRY原則適用) ---
def manage_data_ui(
    edited_df: pd.DataFrame, 
    original_df: pd.DataFrame, 
    session_key: str, 
    backup_key: str, 
    save_func, 
    required_cols: list, 
    is_bs: bool = False
):
    """
    データエディタ（st.data_editor）からの変更を保存・取り消し・削除するための共通UIとロジック。
    is_bsフラグで「バランスシート」か「一般取引データ」かのエラーチェック挙動を切り替える。
    """
    
    # リアルタイム反映＆バックグランド保存 (Resilience & Async-like experience)
    realtime_df = edited_df.drop(columns=["🗑️ 選択"], errors='ignore')
    if not realtime_df.equals(original_df):
        st.session_state[session_key] = realtime_df.copy()
        # 必須項目が埋まっている場合のみ自動保存を試みる
        if not realtime_df.isnull().any().any():
            save_func(realtime_df, USER_ID)
            st.toast("✅ 変更を自動保存しました")
        else:
            st.warning("✏️ 編集中のため未保存です（必須項目を埋めてください）。")

    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
    prefix = "bs" if is_bs else "tab4"
    name = "BSデータ" if is_bs else "DB/CSV"
    
    with col_btn1:
        if st.button(f"💾 {name}に永続保存", use_container_width=True, key=f"btn_save_{prefix}"):
            save_df = edited_df.drop(columns=["🗑️ 選択"], errors='ignore')
            
            # 必須項目が欠落している行を弾く
            save_df.dropna(subset=required_cols, how="any", inplace=True)
            
            error_messages = []
            
            if is_bs:
                empty_text_mask = save_df["区分"].astype(str).str.strip() == ""
                empty_text_mask |= save_df["項目名"].astype(str).str.strip() == ""
                save_df = save_df[~empty_text_mask]

            if save_df.isnull().any().any():
                error_messages.append("⚠️ 入力されていない項目（空のセル）があります。")

            try:
                save_df["金額"] = save_df["金額"].astype(int)
                if not is_bs and (save_df["金額"] <= 0).any():
                    error_messages.append("⚠️ 金額に0以下の数値が含まれています。")
            except (ValueError, TypeError):
                error_messages.append("⚠️ 金額欄に数値以外の文字が含まれています。")

            try:
                temp_dates = pd.to_datetime(save_df["日付"]).dt.date
                if not is_bs and (temp_dates > datetime.date.today()).any():
                    future_count = (temp_dates > datetime.date.today()).sum()
                    error_messages.append(f"⚠️ 未来の日付が {future_count} 件あります。今日以前の日付にしてください。")
            except:
                error_messages.append("⚠️ 日付の形式が正しくありません。")

            if error_messages:
                for msg in error_messages:
                    st.error(msg)
                st.info("💡 修正してから再度保存を押してください。")
            else:
                try:
                    save_df["日付"] = pd.to_datetime(save_df["日付"]).dt.date
                except Exception:
                    pass
                st.session_state[backup_key] = st.session_state[session_key].copy()
                st.session_state[session_key] = save_df
                save_func(save_df, USER_ID)
                st.success(f"✅ データの整合性チェックを通過し、{name}に保存されました！")
                st.rerun()
                
    with col_btn2:
        if backup_key in st.session_state and not st.session_state[backup_key].empty:
            if st.button("↩️ 直前の状態に戻す (UNDO)", use_container_width=True, key=f"btn_undo_{prefix}"):
                st.session_state[session_key] = st.session_state[backup_key].copy()
                save_func(st.session_state[session_key], USER_ID)
                del st.session_state[backup_key]
                st.warning("⚠️ データを直前の状態に復元しました。")
                st.rerun()

    with col_btn3:
        if "🗑️ 選択" in edited_df.columns and edited_df["🗑️ 選択"].any():
            selected_count = edited_df["🗑️ 選択"].sum()
            target_name = "BSレコード" if is_bs else "レコード"
            if st.button(f"🗑️ 選択した {int(selected_count)} 件を削除", use_container_width=True, type="primary", key=f"btn_del_{prefix}"):
                keep_df = edited_df[~edited_df["🗑️ 選択"]].drop(columns=["🗑️ 選択"], errors='ignore')
                st.session_state[backup_key] = st.session_state[session_key].copy()
                st.session_state[session_key] = keep_df.reset_index(drop=True)
                save_func(st.session_state[session_key], USER_ID)
                st.success(f"✅ {int(selected_count)} 件の{target_name}を削除しました。")
                st.rerun()

# --- 5. サイドバー ---
st.sidebar.markdown("## 🧭 マネレポ ユニバーサル・コントロール")

# --- 案内メッセージ ---
st.sidebar.info("💡 **ガイド**\n\nデータの入力・編集は各タブ内のエディタ（表の最下部など）で行ってください。")
st.sidebar.markdown("---")

# --- ユーザー属性設定 ---
st.sidebar.markdown("### 👤 ユーザー属性")
is_biz = st.sidebar.radio(
    "事業形態", 
    ["給与所得者", "個人事業主"], 
    index=0 if st.session_state.business_type == "給与所得者" else 1,
    horizontal=True,
    help="事業主を選択すると、『給与』が『売上』に、『支出』が『経費』に切り替わります。"
)
st.session_state.business_type = is_biz

# --- 共通パラメータ一括管理 ---
st.sidebar.markdown("### ⚙️ 共通パラメータ")
# 集計期間、利回り、インフレ率
st.session_state.sim_params["years"] = st.sidebar.slider("⏳ 運用・集計期間 (年)", 1, 50, st.session_state.sim_params["years"])
st.session_state.sim_params["rate"] = st.sidebar.slider("📈 想定利回り (%)", 0.0, 15.0, st.session_state.sim_params["rate"], step=0.1)
st.session_state.sim_params["inflation"] = st.sidebar.slider("📉 想定インフレ率 (%)", 0.0, 10.0, st.session_state.sim_params["inflation"], step=0.1)

st.sidebar.markdown("---")

# --- データポータビリティ（最下部） ---
st.sidebar.markdown("### 📥 データポータビリティ")
col_exp1, col_exp2 = st.sidebar.columns(2)
with col_exp1:
    csv_data = st.session_state.df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📦 CSV",
        data=csv_data,
        file_name=f"manerepo_data_{datetime.date.today()}.csv",
        mime='text/csv',
        use_container_width=True
    )
with col_exp2:
    json_data = st.session_state.df.to_json(orient="records", force_ascii=False)
    st.download_button(
        label="💾 JSON",
        data=json_data,
        file_name=f"manerepo_backup_{datetime.date.today()}.json",
        mime='application/json',
        use_container_width=True
    )

st.sidebar.markdown("---")

# --- 6. メイン画面 ---
today = datetime.date.today()
if "view_date" not in st.session_state:
    st.session_state.view_date = today.replace(day=1)

# --- 1. 常に「現在の月」のデータに基づいた指標を計算（ダッシュボード着地予測用）
curr_summaries = calculate_summaries(st.session_state.df, today)
actual_balance_current = curr_summaries.get('balance', 0)

# 2. 表示月（ナビゲーションで変更可能）に基づいた指標を計算（タブ内表示用）
summaries = calculate_summaries(st.session_state.df, st.session_state.view_date)

# 変数のグローバル初期化（NameError対策）
income = summaries.get('income', 0)
outgo = summaries.get('outgo', 0)
balance = summaries.get('balance', 0)
invest_actual_month = summaries.get('invest_actual_month', 0)
invest_actual_all = summaries.get('invest_actual_all', 0)
invest_monthly_avg = summaries.get('invest_monthly_avg', 0)
lm_outgo = summaries.get('lm_outgo', 0)
lm_income = summaries.get('lm_income', 0)
fixed_cost = summaries.get('fixed_cost', 0)
variable_cost = summaries.get('variable_cost', 0)
fixed_cost_ratio = summaries.get('fixed_cost_ratio', 0)
variable_cost_ratio = summaries.get('variable_cost_ratio', 0)
savings_ratio = summaries.get('savings_ratio', 0)
avg_monthly_expense = summaries.get('avg_monthly_expense', 0)
this_month_df = summaries.get('this_month_df', pd.DataFrame())
last_month_df = summaries.get('last_month_df', pd.DataFrame())
total_records = summaries.get('total_records', 0)
total_income_all = summaries.get('total_income_all', 0)
total_expense = summaries.get('total_expense', 0)
current_net_worth = 0
predicted_net_worth = 0

# 財務コンサルタントによる診断ロジックの実行 (dashboadでも使用するため早めに実行)
cfp = generate_cfp_diagnosis(
    income=income, outgo=outgo, 
    fixed_cost=fixed_cost, variable_cost=variable_cost, 
    invest_amount=invest_actual_month, 
    total_assets=invest_actual_all, 
    avg_monthly_expense=avg_monthly_expense
)

label_inc = get_label("income")
label_exp = get_label("expense")
st.title("Manerepo - 次世代家計簿・資産管理プラットフォーム")
st.subheader(f"💼 {st.session_state.business_type}モード")

# --- リアルタイム統合メトリック（着地予測） ---
if not st.session_state.df.empty:
    # PL目線(収支)とBS目線(純資産)の統合：着地予測純資産の計算
    if not st.session_state.assets_df.empty:
        temp_assets = st.session_state.assets_df.copy()
        temp_assets["実額"] = temp_assets.apply(lambda r: r["金額"] if "資産" in str(r["区分"]) else -r["金額"], axis=1)
        current_net_worth = temp_assets["実額"].sum()
    
    # ダッシュボードは「現在の実際の収支」を加算して予測値を出す
    predicted_net_worth = current_net_worth + actual_balance_current
    
    col_dash1, col_dash2 = st.columns([1, 1])
    with col_dash1:
        nw_color = "#43a047" if predicted_net_worth >= 0 else "#e53935"
        st.markdown(f"""
        <div style="background: white; border-radius: 16px; padding: 24px; border-left: 10px solid {nw_color}; box-shadow: 0 4px 20px rgba(0,0,0,0.08);">
            <div style="font-size: 0.9rem; color: #757575; font-weight: 700; text-transform: uppercase; letter-spacing: 1px;">🏁 今月末の着地予測純資産</div>
            <div style="font-size: 2.8rem; font-weight: 900; color: {nw_color}; margin: 8px 0;">{predicted_net_worth:,.0f} <span style="font-size: 1.2rem;">円</span></div>
            <div style="font-size: 0.85rem; color: #555;">現在 {current_net_worth:,}円 ＋ 今月予測 {actual_balance_current:+,}円</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_dash2:
        # 生活防衛資金アラート
        em_val = float(cfp.get('emergency_months', 0.0))
        if em_val < 3:
            st.error(f"🚨 **生活防衛資金アラート**: 現在の資産は月平均支出の {em_val:.1f} ヶ月分です。最低3ヶ月分の確保（あと {max(0, 3-em_val):.1f} ヶ月分）を最優先してください。")
        elif em_val < 6:
            st.warning(f"⚠️ **生活防衛資金アドバイス**: 生活防衛資金は {em_val:.1f} ヶ月分です。目標の6ヶ月分に向けて、着実に積み立てを続けましょう。")
        else:
            st.success(f"✨ **財務健全性チェック**: 生活防衛資金は {em_val:.1f} ヶ月分確保されており、非常に健全です。余剰金は積極的に投資に回しましょう。")
        
        if not st.session_state.is_synced:
            st.info("🔄 **オフラインモード**: 現在データをローカルに保存しています。接続復帰時に自動同期されます。")
else:
    st.warning("👋 **Welcome!** まだデータがありません。「⚙️ データ管理」タブからCSVインポートをして、あなた専用の財務分析を開始しましょう！")

tab1, tab_ai, tab_bs, tab2, tab3, tab4 = st.tabs(["🏆 診断・スコア", "🤖 AIアドバイス", "🏦 純資産(BS)", "📊 財務分析", "📈 投資シミュ", "⚙️ データ管理"])

# 財務コンサルタントによる診断ロジックの実行
cfp = generate_cfp_diagnosis(
    income=income, outgo=outgo, 
    fixed_cost=fixed_cost, variable_cost=variable_cost, 
    invest_amount=invest_actual_month, 
    total_assets=invest_actual_all, 
    avg_monthly_expense=avg_monthly_expense
)



# ================================================================
# Tab 1: 診断・スコア
# ================================================================
with tab1:
    # --- 月移動ナビゲーション ---
    nav_col1, nav_col2, nav_col3 = st.columns([1, 2, 1])
    with nav_col1:
        if st.button("◀ 前の月", key="prev_month_btn", use_container_width=True):
            prev_m = (st.session_state.view_date - datetime.timedelta(days=1)).replace(day=1)
            st.session_state.view_date = prev_m
            st.rerun()
    with nav_col2:
         st.markdown(f'<h3 style="text-align:center; margin:0;">{st.session_state.view_date.strftime("%Y年%m月")}</h3>', unsafe_allow_html=True)
    with nav_col3:
        if st.button("次の月 ▶", key="next_month_btn", use_container_width=True):
            next_m = (st.session_state.view_date + datetime.timedelta(days=32)).replace(day=1)
            st.session_state.view_date = next_m
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    label_bal = get_label("balance")
    c1, c2, c3 = st.columns(3)
    with c1:
        delta_income = income - lm_income if lm_income > 0 else None
        st.metric(f"💰 今月の{label_inc}", f"{income:,.0f} 円", delta=f"{delta_income:+,.0f} 円" if delta_income is not None else None)
    with c2:
        delta_outgo = outgo - lm_outgo if lm_outgo > 0 else None
        st.metric(f"💸 今月の{label_exp}", f"{outgo:,.0f} 円", delta=f"{delta_outgo:+,.0f} 円" if delta_outgo is not None else None, delta_color="inverse")
    with c3:
        lm_balance = lm_income - lm_outgo
        delta_balance = balance - lm_balance if (lm_income > 0 or lm_outgo > 0) else None
        st.metric(f"⚖️ {label_bal}", f"{balance:,.0f} 円", delta=f"{delta_balance:+,.0f} 円" if delta_balance is not None else None)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- 財務健全性スコアリングダッシュボード ---
    st.markdown('<div class="section-header">🏆 家計 健全性スコア</div>', unsafe_allow_html=True)
    
    sc1, sc2, sc3, sc4 = st.columns(4)
    # 総合評価（貯蓄率目標20%ベース）
    # cfp['savings_rate'] は float である前提
    rate_val = float(cfp.get('savings_rate', 0.0))
    health_score = int(min(100.0, max(0.0, rate_val * 5.0)))
    score_color = "#43a047" if health_score >= 80 else ("#ff9800" if health_score >= 40 else "#e53935")
    
    with sc1:
        st.markdown(f"""<div class="metric-card" style="border-left-color:{score_color}; text-align:center;">
            <div class="label">📊 貯蓄率 (Saving Rate)</div>
            <div class="value" style="color:{score_color}; font-size:2rem;">{rate_val:.1f}%</div>
            <div class="sub">目標: 20%以上</div>
        </div>""", unsafe_allow_html=True)
    with sc2:
        flex_val = float(cfp.get('flexibility', 0.0))
        flex_color = "#43a047" if flex_val >= 55.0 else "#ff9800"
        st.markdown(f"""<div class="metric-card" style="border-left-color:{flex_color};">
            <div class="label">🏃 家計の機動力</div>
            <div class="value" style="color:{flex_color}; font-size:2rem;">{flex_val:.1f}%</div>
            <div class="sub">100 - 固定費比率</div>
        </div>""", unsafe_allow_html=True)
    with sc3:
        safety_val = float(cfp.get('safety_margin', 0.0))
        st.markdown(f"""<div class="metric-card" style="border-left-color:#5c6bc0;">
            <div class="label">🛡️ 安全余裕率</div>
            <div class="value" style="color:#5c6bc0; font-size:2rem;">{safety_val:.1f}%</div>
            <div class="sub">(収入-固定費)/収入</div>
        </div>""", unsafe_allow_html=True)
    with sc4:
        em_val = float(cfp.get('emergency_months', 0.0))
        em_color = "#43a047" if em_val >= 6.0 else ("#ff9800" if em_val >= 3.0 else "#e53935")
        st.markdown(f"""<div class="metric-card" style="border-left-color:{em_color};">
            <div class="label">🛡️ 生活防衛資金</div>
            <div class="value" style="color:{em_color}; font-size:2rem;">{em_val:.1f}<span style="font-size:0.9rem;"> ヶ月分</span></div>
            <div class="sub">目標: 6ヶ月以上</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- 固定費・変動費・貯蓄 理想比率比較 ---
    st.markdown('<div class="section-header">📊 固定費・変動費・貯蓄バランス</div>', unsafe_allow_html=True)
    ratio_cols = st.columns(2)
    with ratio_cols[0]:
        st.markdown("##### 🎯 理想比率")
        ideal_data = pd.DataFrame([{"項目": "固定費", "割合(%)": 45}, {"項目": "変動費", "割合(%)": 35}, {"項目": "貯蓄", "割合(%)": 20}])
        fig_ideal = px.pie(ideal_data, values='割合(%)', names='項目', hole=0.4,
                           color_discrete_map={"固定費": "#5c6bc0", "変動費": "#ff7043", "貯蓄": "#66bb6a"})
        fig_ideal.update_layout(height=250, margin=dict(t=10, b=10, l=10, r=10), showlegend=True)
        st.plotly_chart(fig_ideal, use_container_width=True)
    with ratio_cols[1]:
        st.markdown("##### 📊 あなたの現状")
        if income > 0:
            actual_data = pd.DataFrame([{"項目": "固定費", "割合(%)": fixed_cost_ratio}, {"項目": "変動費", "割合(%)": variable_cost_ratio}, {"項目": "貯蓄", "割合(%)": savings_ratio}])
            fig_actual = px.pie(actual_data, values='割合(%)', names='項目', hole=0.4,
                               color_discrete_map={"固定費": "#5c6bc0", "変動費": "#ff7043", "貯蓄": "#66bb6a"})
            fig_actual.update_layout(height=250, margin=dict(t=10, b=10, l=10, r=10), showlegend=True)
            st.plotly_chart(fig_actual, use_container_width=True)
        else:
            st.info("収入データがないため比率を計算できません。")
    
    # 比率の評価コメント
    if income > 0:
        if fixed_cost_ratio > 50:
            st.warning(f"⚠️ 固定費率が {fixed_cost_ratio:.1f}% と高めです（理想45%以下）。通信費やサブスクの見直しを検討しましょう。")
        elif fixed_cost_ratio <= 45 and savings_ratio >= 15:
            st.success(f"✅ 素晴らしいバランスです！固定費 {fixed_cost_ratio:.1f}% / 変動費 {variable_cost_ratio:.1f}% / 貯蓄 {savings_ratio:.1f}%")
        if savings_ratio < 10 and income > 0:
            st.info(f"💡 貯蓄率が {savings_ratio:.1f}% です。まずは10%を目標に、変動費の削減から始めましょう。")

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- ガチ診断レポート (PDF出力) ---
    st.markdown('<div class="section-header">📑 マネレポ AI 診断レポート（PDF）</div>', unsafe_allow_html=True)
    st.caption("AIがあなたの浪費パターンを分析し、翌月の予算案や具体的なアクションを提案するPDFレポートを出力します。")
    
    score = 100
    budget_total = sum(st.session_state.budgets.values())
    if outgo > budget_total: score -= 30
    if income < outgo: score -= 20
    if income == 0 and outgo == 0: score -= 10 # 収入も支出も0の場合の調整
    score = max(0, score)

    if FPDF_AVAILABLE:
        if st.button("📄 AI診断レポートを作成", key="btn_pdf_gen"):
            with st.spinner("思考中...AI財テクくんがデータ分析を実行しています..."):
                    try:
                        pdf = FPDF()
                        pdf.add_page()
                        
                        # --- デプロイ環境(Streamlit Cloud等)に対応するための強力なフォント探索ロジック ---
                        base_dir = os.path.dirname(__file__)
                        font_candidates = [
                            os.path.join(base_dir, "fonts", "ipaexg.ttf"),
                            os.path.join(base_dir, "fonts", "MPLUS1p-Regular.ttf"),
                            os.path.join(base_dir, "ipaexg.ttf"), # 同一ディレクトリ内
                            "C:\\Windows\\Fonts\\msgothic.ttc",   # Windowsローカル用
                            "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf" # Linux用
                        ]
                        
                        font_path_to_use = None
                        for path in font_candidates:
                            if os.path.exists(path):
                                font_path_to_use = path
                                break
                        
                        has_japanese_font = False
                        font_name = "helvetica"
                        
                        if font_path_to_use:
                            try:
                                pdf.add_font("jp_font", "", font_path_to_use, uni=True)
                                font_name = "jp_font"
                                has_japanese_font = True
                            except Exception as font_err:
                                st.error(f"デバッグログ（開発者向け）: 選択されたフォント '{font_path_to_use}' の追加に失敗しました。詳細: {font_err}")
                        else:
                            st.warning("⚠️ 日本語フォントファイルが見つかりません。PDFの一部が文字化けする可能性があります。(プロジェクトの fonts/ フォルダに ipaexg.ttf 等が含まれているか確認してください)")
                        
                        if not has_japanese_font:
                            pdf.set_font("helvetica", size=16)
                            pdf.cell(200, 10, txt="AI Report", ln=True, align="C")
                        else:
                            pdf.set_font(font_name, size=16)
                            pdf.cell(200, 10, txt=" マネレポ AI ガチ診断レポート", ln=True, align="C")
                            pdf.set_font(font_name, size=12)

                        
                        pdf.ln(10)
                        
                        if has_japanese_font:
                            pdf.cell(200, 10, txt=f"【対象月】 {st.session_state.view_date.year}年{st.session_state.view_date.month}月", ln=True)
                            pdf.cell(200, 10, txt=f"収入: {income:,.0f}円 / 支出: {outgo:,.0f}円 / 収支: {balance:,.0f}円", ln=True)
                        else:
                            pdf.cell(200, 10, txt=f"Month: {st.session_state.view_date.year}-{st.session_state.view_date.month}", ln=True)
                            pdf.cell(200, 10, txt=f"Income: {income:,.0f} / Expense: {outgo:,.0f} / Balance: {balance:,.0f}", ln=True)
                        pdf.ln(5)
                        
                        if outgo > 0:
                            top_exp = this_month_df[this_month_df["タイプ"] == "支出"].groupby("カテゴリー")["金額"].sum().nlargest(3)
                            if has_japanese_font:
                                pdf.cell(190, 10, txt="■ 支出ワースト3カテゴリー：", ln=True)
                                for cat, amt in top_exp.items():
                                    pdf.cell(190, 10, txt=f"  - {cat}: {amt:,.0f}円", ln=True)
                            else:
                                pdf.cell(190, 10, txt="Top 3 Expenses:", ln=True)
                                for cat, amt in top_exp.items():
                                    pdf.cell(190, 10, txt=f"  - {cat}: {amt:,.0f}", ln=True)
                            pdf.ln(5)

                            if has_japanese_font:
                                pdf.cell(190, 10, txt="■ 💡 マネレポ AI プロフェッショナル診断アドバイス：", ln=True)
                                pdf.set_font(font_name, size=11)
                                for advice in cfp['advices']:
                                    pdf.multi_cell(w=190, h=8, txt=f"・{advice}", ln=1)
                                
                                pdf.ln(3)
                                pdf.multi_cell(w=190, h=8, txt="【財務指標の定量評価】", ln=1)
                                pdf.set_font(font_name, size=10)
                                pdf.multi_cell(w=190, h=7, txt=f"  - 貯蓄率: {cfp['savings_rate']:.1f}% (目標20%)", ln=1)
                                pdf.multi_cell(w=190, h=7, txt=f"  - 固定費比率: {cfp['fixed_ratio']:.1f}% (機動力: {cfp['flexibility']:.1f}%)", ln=1)
                                pdf.multi_cell(w=190, h=7, txt=f"  - 安全余裕率: {cfp['safety_margin']:.1f}%", ln=1)
                                pdf.multi_cell(w=190, h=7, txt=f"  - 資産配分（投資比率）: {cfp['invest_ratio']:.1f}%", ln=1)
                                
                                pdf.ln(3)
                                pdf.multi_cell(w=190, h=8, txt="【総評】", ln=1)
                                if cfp['savings_rate'] < 10:
                                    pdf.multi_cell(w=190, h=8, txt="・キャッシュフローの安全性が懸念されます。固定費の削減および損益分岐点の引き下げを断行してください。", ln=1)
                                else:
                                    pdf.multi_cell(w=190, h=8, txt="・財務構造は安定しています。税効果の最適化に向けた長期資産運用の配分維持を推奨します。", ln=1)
                                
                        else:
                            if has_japanese_font:
                                pdf.cell(190, 10, txt="データが不足しているため詳細な分析ができません。", ln=True)
                            else:
                                pdf.cell(190, 10, txt="Not enough data for detailed analysis.", ln=True)
                        
                        pdf_output = pdf.output(dest="S")
                        b64 = base64.b64encode(pdf_output).decode()
                        href = f'<a download="diagnosis_report.pdf" href="data:application/pdf;base64,{b64}" style="text-decoration:none;"><button style="background-color:#1b5e20;color:white;padding:10px 20px;border:none;border-radius:25px;font-weight:bold;cursor:pointer;">📥 レポートをダウンロード</button></a>'
                        st.markdown(href, unsafe_allow_html=True)
                        st.success("レポートの作成が完了しました。")
                    except Exception as e:
                        st.error(f"PDF生成エラー: {e}")
    else:
        st.info("PDF生成機能を利用するには fpdf2 のインストールが必要です。")

    st.markdown("<br>", unsafe_allow_html=True)

    # --- スコア & バッジ ---
    col_score, col_badge = st.columns([3, 2])
    with col_score:
        st.markdown('<div class="section-header">🏆 マネー資産形成スコア</div>', unsafe_allow_html=True)
        score_color = "#43a047" if score >= 80 else ("#ff9800" if score >= 50 else "#e53935")
        st.markdown(f"""
        <div style="text-align:center; background:white; border-radius:20px; padding:30px; box-shadow:0 4px 20px rgba(0,0,0,0.06); margin:12px 0;">
            <div style="font-size:5rem; font-weight:900; color:{score_color}; line-height:1;">{score}</div>
            <div style="font-size:1.2rem; color:#757575; font-weight:600;">/ 100 点</div>
            <div style="margin-top:16px;">
                <div class="progress-outer">
                    <div class="progress-inner" style="width:{score}%; background:linear-gradient(90deg, {score_color}, {score_color}88);">
                        {score}%
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_badge:
        st.markdown('<div class="section-header">🎖 称号バッジ</div>', unsafe_allow_html=True)
        days = this_month_df["日付"].nunique() if (isinstance(this_month_df, pd.DataFrame) and not this_month_df.empty) else 0
        badges = []
        if days >= 1: badges.append(("💰", "財テクの卵", "記録を開始しました！"))
        if days >= 7: badges.append(("🤖", "AIマスター", "7日以上継続中"))
        if outgo < budget_total and outgo > 0: badges.append(("🛡️", "資産守護者", "予算クリア"))
        if balance > 0: badges.append(("📈", "成長モード", "黒字達成！"))

        if badges:
            for icon, title, desc in badges:
                st.markdown(f"""<div class="badge-card">
                    <div class="icon">{icon}</div>
                    <div class="info"><div class="title">{title}</div><div class="desc">{desc}</div></div>
                </div>""", unsafe_allow_html=True)
        else:
            st.info("データを記録するとバッジが獲得できます。")

    st.markdown("<br>", unsafe_allow_html=True)

    # --- 収支カレンダー ---
    st.markdown('<div class="section-header">📆 収支カレンダー</div>', unsafe_allow_html=True)
    cal = calendar.monthcalendar(st.session_state.view_date.year, st.session_state.view_date.month)
    spent_days = set(this_month_df[this_month_df["タイプ"] == "支出"]["日付"].apply(lambda x: x.day)) if (isinstance(this_month_df, pd.DataFrame) and not this_month_df.empty) else set()
    income_days = set(this_month_df[this_month_df["タイプ"] == "収入"]["日付"].apply(lambda x: x.day)) if (isinstance(this_month_df, pd.DataFrame) and not this_month_df.empty) else set()
    weekdays = ["月", "火", "水", "木", "金", "土", "日"]

    cal_html = '<table class="cal-table"><tr>'
    for wd in weekdays: cal_html += f'<th>{wd}</th>'
    cal_html += '</tr>'
    for week in cal:
        cal_html += '<tr>'
        for day in week:
            if day == 0:
                cal_html += '<td style="background:transparent;"></td>'
            else:
                classes = []
                has_spent = day in spent_days
                has_income = day in income_days
                
                # 色分けクラスの選定
                if has_spent and has_income: classes.append("cal-both")
                elif has_spent: classes.append("cal-spent")
                elif has_income: classes.append("cal-income")

                # 今日の判定
                is_today = (day == datetime.date.today().day and 
                           st.session_state.view_date.month == datetime.date.today().month and 
                           st.session_state.view_date.year == datetime.date.today().year)
                if is_today: classes.append("cal-today")
                
                cls = ' '.join(classes)
                cal_html += f'<td class="{cls}">{day}</td>'
        cal_html += '</tr>'
    cal_html += '</table>'
    st.markdown(cal_html, unsafe_allow_html=True)
    st.caption("🟥赤 = 支出　🟩緑 = 収入　🟥🟩半分ずつ = 支出・収入両方あり")

    st.markdown("<br>", unsafe_allow_html=True)

    # --- 当月の収支明細 ---
    st.markdown('<div class="section-header">📋 直近の取引明細</div>', unsafe_allow_html=True)
    if isinstance(this_month_df, pd.DataFrame) and not this_month_df.empty:
        sorted_df = this_month_df.sort_values("日付", ascending=False)
        tx_html = '<table class="tx-table"><tr><th>日付</th><th>タイプ</th><th>カテゴリー</th><th>内容</th><th style="text-align:right;">金額</th></tr>'
        for _, row in sorted_df.iterrows():
            type_class = "tx-income" if row["タイプ"] == "収入" else "tx-expense"
            type_icon = "💵" if row["タイプ"] == "収入" else "🛒"
            content = row["内容"] if pd.notna(row["内容"]) and row["内容"] != "" else "ー"
            tx_html += f'''<tr>
                <td>{row["日付"]}</td>
                <td class="{type_class}">{type_icon} {row["タイプ"]}</td>
                <td>{row["カテゴリー"]}</td>
                <td>{content}</td>
                <td class="{type_class}" style="text-align:right;">{row["金額"]:,.0f} 円</td>
            </tr>'''
        bal_color_tx = "#1b5e20" if balance >= 0 else "#c62828"
        tx_html += f'''<tr style="border-top:3px solid #2e7d32;">
            <td colspan="3" style="background:#e8f5e9; font-weight:800; font-size:0.95rem;">📊 合計</td>
            <td style="background:#e8f5e9; font-weight:700; text-align:right;"><span class="tx-income">収入 {income:,.0f} 円</span></td>
            <td style="background:#e8f5e9; font-weight:700; text-align:right;"><span class="tx-expense">支出 {outgo:,.0f} 円</span></td>
        </tr>
        <tr>
            <td colspan="4" style="background:#f1f8e9; font-weight:800; text-align:right;">⚖️ 収支差額</td>
            <td style="background:#f1f8e9; font-weight:800; text-align:right; color:{bal_color_tx}; font-size:1.1rem;">{balance:,.0f} 円</td>
        </tr></table>'''
        st.markdown(tx_html, unsafe_allow_html=True)
    else:
        st.info("データがありません。")

# ================================================================
# Tab AI: パーソナル AIアドバイス
# ================================================================
with tab_ai:
    st.markdown('<div class="section-header">🤖 パーソナル財務アドバイザー (AI診断)</div>', unsafe_allow_html=True)
    st.caption("1級FP・公認会計士の思考プロセスを模倣し、あなたの現状を多角的に分析・診断します。")

    if income == 0 and outgo == 0 and st.session_state.assets_df.empty:
        st.info("💡 記録データが不足しています。「📝 記録する」または「🏦 純資産(BS)」タブからデータを入力してください。")
    else:
        # AIコンサルタントによる解析実行
        ai_report = generate_ai_advisor_report(
            st.session_state.df, 
            st.session_state.assets_df, 
            cfp, 
            summaries
        )

        # 2-1. 【サマリー】現在のあなたの「家計格付け」
        rating = ai_report['rating']
        rating_color = "#1b5e20" if "A" in rating else ("#f57f17" if "B" in rating else "#b71c1c")
        st.markdown(f"""
        <div style="background-color: white; border-radius: 12px; padding: 24px; border-left: 8px solid {rating_color}; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 24px;">
            <div style="font-size: 14px; color: #757575; font-weight: 600; text-transform: uppercase;">📊 家計・財務総合格付け</div>
            <div style="display: flex; align-items: baseline; gap: 16px; margin-top: 8px;">
                <div style="font-size: 3rem; font-weight: 900; color: {rating_color}; line-height: 1;">{rating}</div>
                <div style="font-size: 1.1rem; color: #424242; font-weight: 500;">ランク</div>
            </div>
            <div style="margin-top: 12px; font-size: 15px; color: #333; line-height: 1.6;">
                {ai_report['rating_reason']}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 2-2. 【パーソナル診断】コンサルタントの眼
        st.markdown('#### 👁️ コンサルタントの眼 (データ解析結果)')
        # ノートが空の場合はメッセージを表示
        display_notes = ai_report['notes'] if ai_report['notes'] else [ERROR_DATA_MISSING]
        st.markdown(f"""
        <div style="background-color: #f8f9fa; border: 1px solid #e0e0e0; border-radius: 8px; padding: 16px; margin-bottom: 24px;">
            <div style="font-weight: bold; color: #1976d2; margin-bottom: 8px;">👤 診断された家計性格: 「{ai_report['persona']}」</div>
            <ul style="margin: 0; padding-left: 20px; color: #424242; line-height: 1.8;">
                {"".join([f"<li>{note}</li>" for note in display_notes])}
            </ul>
        </div>
        """, unsafe_allow_html=True)

        # 2-3. 【戦略提案】プロが描く3つのシナリオ
        st.markdown('#### 🗺️ プロが描く3つの戦略シナリオ')
        st.caption("あなたの性格や目標に合わせて、最適なアプローチを選んでください。")
        
        scenario_cols = st.columns(3)
        colors = ["#e3f2fd", "#e8f5e9", "#fff3e0"]
        borders = ["#2196f3", "#4caf50", "#ff9800"]
        titles = list(ai_report['scenarios'].keys())
        descs = list(ai_report['scenarios'].values())
        
        for i, col in enumerate(scenario_cols):
            with col:
                st.markdown(f"""
                <div style="background-color: {colors[i]}; border-top: 4px solid {borders[i]}; border-radius: 8px; padding: 16px; height: 100%;">
                    <div style="font-weight: 700; color: #333; margin-bottom: 10px;">{titles[i]}</div>
                    <div style="font-size: 13.5px; color: #555; line-height: 1.5;">{descs[i]}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # 2-4. 【格言とNext Action】
        st.markdown('#### 🚀 Next Action')
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1d1d1f 0%, #434343 100%); border-radius: 12px; padding: 24px; color: white;">
            <div style="font-size: 18px; font-weight: bold; margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
                <span>🎯</span> 明日からこれだけはやってください
            </div>
            <div style="font-size: 15px; line-height: 1.6; margin-bottom: 20px; background: rgba(255,255,255,0.1); padding: 16px; border-radius: 8px;">
                {ai_report['next_action']}
            </div>
            <div style="font-style: italic; color: #aaa; font-size: 13px; text-align: right; border-top: 1px solid rgba(255,255,255,0.2); padding-top: 12px;">
                "{ai_report['quote']}"
            </div>
        </div>
        """, unsafe_allow_html=True)

# ================================================================
# Tab 2: 財務分析・予実
# ================================================================
with tab2:
    st.markdown('<div class="section-header">📊 6ヶ月キャッシュフロー推移 & 損益分岐点 (BEP)</div>', unsafe_allow_html=True)
    st.caption("過去6ヶ月の収支動態を可視化します。点線は平均固定費（損益分岐点）を示し、これを超える収入が「安全余裕」となります。")
    
    hist_df = get_historical_data(st.session_state.df)
    if not hist_df.empty:
        # BEPライン（平均固定費）
        avg_fixed = hist_df["固定費"].mean()
        
        fig_cf = go.Figure()
        # 収入・支出のエリアチャート
        fig_cf.add_trace(go.Scatter(x=hist_df["年月"], y=hist_df["収入"], name=f"総{label_inc}", fill='tozeroy', 
                                    line={"color": "rgba(67, 160, 71, 0.8)", "width": 3}, fillcolor='rgba(67, 160, 71, 0.2)'))
        fig_cf.add_trace(go.Scatter(x=hist_df["年月"], y=hist_df["支出"], name=f"総{label_exp}", fill='tozeroy', 
                                    line={"color": "rgba(229, 57, 53, 0.8)", "width": 3}, fillcolor='rgba(229, 57, 53, 0.2)'))
        # BEPライン（平均固定費）を重畳
        fig_cf.add_trace(go.Scatter(x=hist_df["年月"], y=[avg_fixed]*len(hist_df), name=f"損益分岐点 (平均固定{label_exp})", 
                                    line={"color": "rgba(33, 33, 33, 0.6)", "dash": "dash"}, mode='lines'))
        
        fig_cf.update_layout(height=400, margin={"t": 10, "b": 10, "l": 10, "r": 10}, hovermode="x unified",
                             legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1})
        st.plotly_chart(fig_cf, use_container_width=True)
        
        # 安全余裕率の補足
        current_safety = cfp['safety_margin']
        st.info(f"💡 【財務分析結果】過去6ヶ月の平均固定費は **{avg_fixed:,.0f}円** です。現在の安全余裕率は **{current_safety:.1f}%** であり、固定費を差し引いた後の「生活の耐性」を評価しています。")
    else:
        st.info("データが不足しているため、推移チャートを表示できません。")

    st.markdown('<div class="section-header">📊 予算 vs 実績 (今月)</div>', unsafe_allow_html=True)
    
    budget_data = []
    for cat, b_amt in st.session_state.budgets.items():
        actual = this_month_df[(this_month_df["カテゴリー"] == cat) & (this_month_df["タイプ"] == "支出")]["金額"].sum() if not this_month_df.empty else 0
        budget_data.append({"カテゴリー": cat, "予算": b_amt, "実績": actual})
    
    b_df = pd.DataFrame(budget_data)
    if isinstance(b_df, pd.DataFrame) and not b_df.empty:
        fig_budget = go.Figure()
        fig_budget.add_trace(go.Bar(name='予算', x=b_df['カテゴリー'], y=b_df['予算'], marker_color='#E0E0E0'))
        fig_budget.add_trace(go.Bar(name='実績', x=b_df['カテゴリー'], y=b_df['実績'], marker_color='#43A047'))
        fig_budget.update_layout(barmode='overlay', height=400, margin={"t": 20, "b": 20, "l": 20, "r": 20},
                                 legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1})
        st.plotly_chart(fig_budget, use_container_width=True)

    if isinstance(this_month_df, pd.DataFrame) and not this_month_df.empty:
        # 動的分析ドリルダウン
        st.markdown('<div class="section-header">📊 支出の動的分析 (インタラクティブ)</div>', unsafe_allow_html=True)
        st.caption("円グラフをクリック・ホバーすることで、カテゴリごとの割合や金額の詳細を確認できます。")
        
        # --- 追加: 貯蓄率 (Savings Rate) と FIRE診断の強化 ---
        st.markdown('#### 🎯 今月の貯蓄率 (Savings Rate) と FIRE診断')
        sr_col1, sr_col2 = st.columns([1, 1])
        
        with sr_col1:
            # 貯蓄率ゲージチャート
            savings_rate_val = cfp.get('savings_rate', 0.0)
            
            fig_sr = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = savings_rate_val,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "今月の貯蓄率 (%)", 'font': {'size': 18}},
                number = {'suffix': "%", 'font': {'size': 36}},
                gauge = {
                    'axis': {'range': [-20, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
                    'bar': {'color': "#43a047" if savings_rate_val >= 20 else ("#ff9800" if savings_rate_val >= 0 else "#e53935")},
                    'bgcolor': "white",
                    'borderwidth': 2,
                    'bordercolor': "gray",
                    'steps': [
                        {'range': [-20, 0], 'color': 'rgba(229, 57, 53, 0.2)'},
                        {'range': [0, 20], 'color': 'rgba(255, 152, 0, 0.2)'},
                        {'range': [20, 100], 'color': 'rgba(67, 160, 71, 0.2)'}],
                    'threshold': {
                        'line': {'color': "red", 'width': 3},
                        'thickness': 0.75,
                        'value': 20} # FIRE推奨の最低ライン
                }
            ))
            fig_sr.update_layout(height=300, margin=dict(t=50, b=20, l=20, r=20))
            st.plotly_chart(fig_sr, use_container_width=True)
            
        with sr_col2:
            st.markdown("""<div style="padding-top: 1.5rem;"></div>""", unsafe_allow_html=True)
            st.info("💡 **貯蓄率 (Savings Rate)** はFIRE (経済的自立と早期リタイア) 達成における**最重要指標**です。（目標: **20%以上**）")
            
            # FIRE 年数計算ロジック
            # 現在の純資産
            current_net_worth = 0
            if not st.session_state.assets_df.empty:
                temp_assets = st.session_state.assets_df.copy()
                temp_assets["実額"] = temp_assets.apply(lambda r: r["金額"] if "資産" in str(r["区分"]) else -r["金額"], axis=1)
                current_net_worth = temp_assets["実額"].sum()
                
            # 年間支出推定
            annual_exp_est = outgo * 12 if outgo > 0 else avg_monthly_expense * 12
            fire_target_est = annual_exp_est * 25 # 4%ルール
            
            # 推定貯蓄・投資額 (月)
            monthly_saving_power = balance if balance > 0 else 0
            
            if annual_exp_est > 0 and monthly_saving_power > 0:
                # 割引率(期待リターン) 4% で計算
                years_to_fire = calculate_years_to_goal(
                    goal=fire_target_est, 
                    initial_amount=max(0, current_net_worth), 
                    monthly_contribution=monthly_saving_power, 
                    annual_rate_pct=4.0
                )
                
                if years_to_fire:
                    st.success(f"🔥 今治の**生活水準を維持**し、**余剰金({monthly_saving_power:,.0f}円/月)**を全額 年利4% で運用した場合、\n\n**FIRE達成（推定必要額: {fire_target_est:,.0f}円）まで... 約 {years_to_fire:.1f} 年** です！")
                else:
                    st.warning("⚠️ 現在のペースではFIRE達成の計算が困難です。")
            elif annual_exp_est > 0 and monthly_saving_power <= 0:
                st.error("⚠️ 今月の収支が赤字またはプラマイゼロのため、現在のペースではFIREに到達できません。支出を下げるか収入を増やす必要があります。")
            elif annual_exp_est == 0:
                st.warning("今月の支出データが入力されていないため、FIRE到達年数を計算できません。")
                
        st.markdown("<br>", unsafe_allow_html=True)
        
        outgo_df = this_month_df[this_month_df["タイプ"] == "支出"]
        if not outgo_df.empty:
            cat_data = outgo_df.groupby("カテゴリー")["金額"].sum().reset_index()
            # Plotly Express によるインタラクティブパイチャート
            fig_pie = px.pie(cat_data, values='金額', names='カテゴリー', hole=0.4, 
                             color_discrete_sequence=px.colors.sequential.Greens_r)
            fig_pie.update_traces(textposition='inside', textinfo='percent+label', marker=dict(line=dict(color='#ffffff', width=2)))
            fig_pie.update_layout(height=400, margin=dict(t=20, b=20, l=20, r=20), showlegend=True)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("支出データがありません")

        st.markdown("<br>", unsafe_allow_html=True)

        # --- 資金繰りフロー (サンキーダイアグラム) ---
        st.markdown('<div class="section-header">🌊 資金繰りフロー (サンキーダイアグラム)</div>', unsafe_allow_html=True)
        if income > 0:
            in_cats = this_month_df[this_month_df["タイプ"] == "収入"].groupby("カテゴリー")["金額"].sum()
            out_cats = this_month_df[this_month_df["タイプ"] == "支出"].groupby("カテゴリー")["金額"].sum()
            labels = list(in_cats.index) + [f"総{label_inc}"] + list(out_cats.index)
            if balance > 0: labels.append("残額（貯蓄・繰越）")
            elif balance < 0: labels.append(f"赤字補填 ({label_exp}超過)")
            
            # 定番カテゴリのカラーマップ定義
            cd_map = {
                "食費": "rgba(255, 112, 67, 0.7)",   # オレンジ系
                "家賃": "rgba(121, 134, 203, 0.7)",  # ブルー系
                "交通費": "rgba(186, 104, 200, 0.7)", # パープル系
                "日用品": "rgba(141, 110, 99, 0.7)",  # ブラウン系
                "投資": "rgba(77, 182, 172, 0.7)",     # ターコイズ系
                "娯楽": "rgba(240, 98, 146, 0.7)",    # ピンク系
            }
            
            src, tgt, vals, node_colors, link_colors = [], [], [], [], []
            center_idx = len(in_cats)
            
            for i, cat in enumerate(in_cats.index):
                src.append(i); tgt.append(center_idx); vals.append(in_cats[cat]); link_colors.append("rgba(67, 160, 71, 0.4)")
                node_colors.append("rgba(67, 160, 71, 0.8)") # 収入ノード色
            
            node_colors.append("rgba(33, 33, 33, 0.7)") # 中央「総収入」ノード色
            
            if balance < 0:
                src.append(len(labels)-1); tgt.append(center_idx); vals.append(abs(balance)); link_colors.append("rgba(229, 57, 53, 0.4)")
                
            for i, cat in enumerate(out_cats.index):
                src.append(center_idx); tgt.append(center_idx + 1 + i); vals.append(out_cats[cat])
                color = cd_map.get(cat, "rgba(255, 152, 0, 0.5)")
                link_colors.append(color.replace("0.7", "0.4").replace("0.5", "0.3"))
                node_colors.append(color)

            if balance > 0:
                src.append(center_idx); tgt.append(len(labels)-1); vals.append(balance); link_colors.append("rgba(21, 101, 192, 0.4)")
                node_colors.append("rgba(21, 101, 192, 0.8)") # 残額ノード色
            elif balance < 0:
                node_colors.append("rgba(229, 57, 53, 0.8)") # 赤字補填ノード色

            fig_sankey = go.Figure(data=[go.Sankey(
                arrangement="fixed",
                node=dict(pad=30, thickness=10, line=dict(color="black", width=0.5), label=labels, color=node_colors),
                link=dict(source=src, target=tgt, value=vals, color=link_colors)
            )])
            fig_sankey.update_layout(height=450, margin=dict(l=5, r=5, t=10, b=10), font=dict(size=11))
            st.plotly_chart(fig_sankey, use_container_width=True)
        else:
            st.info("収入データがないため、資金フローを表示できません。")
    else:
        st.info("データがありません。")

# ================================================================
# Tab 3: 投資シミュレーション
# ================================================================
with tab3:
    st.markdown('<div class="section-header">📈 投資シミュレーター</div>', unsafe_allow_html=True)
    
    ic1, ic2, ic3 = st.columns(3)
    with ic1:
        st.markdown(f"""<div class="metric-card" style="border-left-color:#5c6bc0;">
            <div class="label">🗓 今月の投資額</div>
            <div class="value" style="color:#5c6bc0; font-size:1.5rem;">{invest_actual_month:,.0f}<span style="font-size:0.9rem;"> 円</span></div>
        </div>""", unsafe_allow_html=True)
    with ic2:
        st.markdown(f"""<div class="metric-card" style="border-left-color:#1565c0;">
            <div class="label">🏦 累計投資額</div>
            <div class="value" style="color:#1565c0; font-size:1.5rem;">{invest_actual_all:,.0f}<span style="font-size:0.9rem;"> 円</span></div>
        </div>""", unsafe_allow_html=True)
    with ic3:
        st.markdown(f"""<div class="metric-card" style="border-left-color:#00897b;">
            <div class="label">📊 月平均投資額</div>
            <div class="value" style="color:#00897b; font-size:1.5rem;">{invest_monthly_avg:,.0f}<span style="font-size:0.9rem;"> 円</span></div>
        </div>""", unsafe_allow_html=True)

    # --- ライフイベント表の表示・編集 ---
    st.markdown('<div class="section-header">📅 未来のライフイベント表 (手動調整可能)</div>', unsafe_allow_html=True)
    st.caption("イベント名や金額を直接編集したり、行を追加して独自プランを作成できます。")
    edited_events = st.data_editor(
        st.session_state.life_events,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "年": st.column_config.NumberColumn("年", format="%d", min_value=2024),
            "金額": st.column_config.NumberColumn("想定コスト (円)", format="%d", min_value=0),
        },
        key="life_event_editor"
    )
    if not edited_events.equals(st.session_state.life_events):
        st.session_state.life_events = edited_events
        st.toast("ライフイベントを保存しました。")
    
    total_life_event_costs = edited_events["金額"].sum()
    st.info(f"💡 未来のライフイベント合計予測コスト: **{total_life_event_costs:,.0f} 円**")

    # --- 事業所得・節税シミュレーター (個人事業主のみ) ---
    if st.session_state.business_type == "個人事業主":
        st.markdown('<div class="section-header">💼 事業所得・節税シミュレーター</div>', unsafe_allow_html=True)
        biz_col1, biz_col2 = st.columns([1, 1])
        with biz_col1:
            # 直近3ヶ月平均をデフォルトにするなどの工夫も可能だが、今回は手動入力を活かす
            est_sales = st.number_input("想定月間売上 (円)", min_value=0, value=int(income) if income > 0 else 500000, step=10000)
            est_costs = st.number_input("想定月間経費 (円)", min_value=0, value=int(outgo) if outgo > 0 else 200000, step=10000)
            annual_biz_income = (est_sales - est_costs) * 12
        
        with biz_col2:
            tax_amt, taxable_inc = calculate_approx_tax(annual_biz_income, "個人事業主")
            tax_amt_no_blue, _ = calculate_approx_tax(annual_biz_income, "給与所得者") # 控除なし比較
            tax_saving = max(0, tax_amt_no_blue - tax_amt)
            
            st.markdown(f"""<div style="background:#f1f8e9; border-radius:12px; padding:20px; border:1px solid #c5e1a5;">
                <div style="font-size:0.85rem; color:#558b2f; font-weight:700;">青色申告控除(65万)適用後の実質所得</div>
                <div style="font-size:1.8rem; font-weight:900; color:#2e7d32; line-height:1;">{(annual_biz_income - tax_amt):,}<span style="font-size:0.9rem;"> 円/年</span></div>
                <div style="margin-top:10px; font-size:0.85rem; color:#666;">
                    推定納税額: {tax_amt:,} 円<br>
                    <span style="color:#d32f2f; font-weight:700;">✨ 節税効果: {tax_saving:,} 円/年</span>
                </div>
            </div>""", unsafe_allow_html=True)
            
        st.caption(f"※この節税分（{tax_saving:,}円）を毎年 3% で 20年運用すると、将来 **{int(tax_saving * ((1.03**20 - 1)/0.03)):,}円** の追加資産になります。")

    col_param, col_result = st.columns([1, 1])
    default_invest = int(invest_monthly_avg) if invest_monthly_avg > 0 else 10000

    with col_param:
        st.markdown("""<div style="background:white; border-radius:16px; padding:24px; box-shadow:0 4px 20px rgba(0,0,0,0.06);">
            <h3 style="margin-top:0;">⚙️ シミュレーション設定</h3>
            <p style="font-size:0.8rem; color:#666;">※サイドバーの共通パラメータと同期しています</p>
        </div>""", unsafe_allow_html=True)
        reduction = st.slider("💰 毎月の追加投資額 (円)", 0, 200000, default_invest, step=1000)
        years = st.slider("⏳ 運用期間 (年)", 1, 30, st.session_state.sim_params["years"], key="sim_years")
        rate_pct = st.slider("📈 想定利回り (%)", 1.0, 10.0, st.session_state.sim_params["rate"], step=0.5, key="sim_rate")
        
        with st.expander("🛠 高度なシミュレーション設定"):
            st.session_state.sim_params["inflation"] = st.slider("📉 想定インフレ率 (%)", 0.0, 5.0, st.session_state.sim_params["inflation"], step=0.5,
                                       help="将来の金額を現在の価値に換算するための物価上昇率です。日本の近年の目標は2%前後です。")
            use_tax = st.checkbox("💸 特定口座（税金 20.315% を考慮する）", value=st.session_state.sim_params["use_tax"], help="チェックを入れると、運用益に対して20.315%の税金が引かれた手取り額を試算します。（NISA口座なら非課税のためチェック不要）")

    inflation_pct = st.session_state.sim_params["inflation"]
    # --- 関数呼び出しによる複利計算（インフレ調整済み） ---
    TAX_RATE = 0.20315
    values, future_val_nisa, total_invested = calculate_compound_interest(
        initial_amount=invest_actual_all,
        monthly_contribution=reduction,
        annual_rate_pct=rate_pct,
        years=years,
        tax_rate=TAX_RATE,
        inflation_rate_pct=inflation_pct
    )
    
    gain_nisa = future_val_nisa - total_invested
    final_taxed_val = future_val_nisa - (gain_nisa * TAX_RATE) if gain_nisa > 0 else future_val_nisa
    gain_taxed = final_taxed_val - total_invested
    
    display_future_val = final_taxed_val if use_tax else future_val_nisa
    display_gain = gain_taxed if use_tax else gain_nisa
    tax_cost_str = f"（税金: -{int(gain_nisa * TAX_RATE):,}円）" if use_tax and gain_nisa > 0 else ""
    
    # インフレ割引後の実質価値
    deflator_final = (1 + inflation_pct / 100) ** years if inflation_pct > 0 else 1
    real_value_final = display_future_val / deflator_final

    with col_result:
        r1, r2 = st.columns(2)
        with r1:
            st.markdown(f"""<div class="metric-card" style="border-left-color:#1565c0;">
                <div class="label">🏦 最終 投資元本</div>
                <div class="value" style="color:#1565c0; font-size:1.5rem;">{total_invested:,.0f}<span style="font-size:0.9rem;"> 円</span></div>
            </div>""", unsafe_allow_html=True)
        with r2:
            st.markdown(f"""<div class="metric-card" style="border-left-color:#f57c00;">
                <div class="label">🌟 運用益 { "（手取り）" if use_tax else "(非課税)" }</div>
                <div class="value" style="color:#f57c00; font-size:1.5rem;">{display_gain:,.0f}<span style="font-size:0.9rem;"> 円</span></div>
                <div class="sub" style="color:#e53935;">{tax_cost_str}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown(f"""<div class="metric-card" style="border-left-color:#2e7d32; margin-top:12px;">
            <div class="label">🚀 {years}年後の合計資産 { "（課税後）" if use_tax else "（NISA非課税）" }</div>
            <div class="value">{display_future_val:,.0f}<span style="font-size:1rem;"> 円</span></div>
            <div class="sub">現在額 {invest_actual_all:,} 円 ＋ 追加月額 {reduction:,} 円</div>
        </div>""", unsafe_allow_html=True)
        
        # インフレ調整済み実質価値カード
        if inflation_pct > 0:
            st.markdown(f"""<div class="metric-card" style="border-left-color:#7b1fa2; margin-top:12px;">
                <div class="label">💴 実質価値（インフレ{inflation_pct}%調整後）</div>
                <div class="value" style="color:#7b1fa2; font-size:1.5rem;">{real_value_final:,.0f}<span style="font-size:0.9rem;"> 円</span></div>
                <div class="sub">{display_future_val:,.0f}円 の名目額が 現在の {real_value_final:,.0f}円 に相当</div>
            </div>""", unsafe_allow_html=True)
        
    st.markdown("---")
    goal_target = st.number_input("🎯 目標資産額 (円)", min_value=1000000, max_value=200000000, value=20000000, step=1000000)
    
    # --- 関数呼び出しによる目標到達年数の計算 ---
    if reduction > 0:
        years_needed = calculate_years_to_goal(goal_target, invest_actual_all, reduction, rate_pct)
        if years_needed is not None:
            st.info(f"💡 現在のペース ({rate_pct}%運用) で **{goal_target:,.0f}円** に到達する予想時期は、約 **{years_needed:.1f} 年後** です！")
        else:
            st.warning("⚠️ 現在の設定では目標額に到達できない見込みです。投資額または利回りを見直してください。")
    else:
        st.info("💡 毎月の追加投資額を設定すると、目標額への到達予想時期が計算できます。")

    # --- FIRE達成率 (4%ルール) の追加 ---
    st.markdown("---")
    st.markdown('<div class="section-header">🔥 FIRE進捗率 (4%ルール)</div>', unsafe_allow_html=True)
    st.caption("年間支出を運用資産の4%で賄える状態（経済的自立）を100%とした場合の進捗度合いです。")
    
    # 年間支出の見積もり
    annual_expense = 0
    if not st.session_state.df.empty:
        expense_df = st.session_state.df[st.session_state.df["タイプ"] == "支出"]
        if not expense_df.empty:
            months_recorded = len(expense_df["日付"].apply(lambda x: x.strftime("%Y-%m")).unique())
            if months_recorded > 0:
                monthly_avg_expense = expense_df["金額"].sum() / months_recorded
                annual_expense = monthly_avg_expense * 12
        
    if annual_expense > 0:
        # FIRE必要額 (年間支出の25倍)
        fire_target = annual_expense * 25
        
        # 現在の進捗率
        current_progress = (invest_actual_all / fire_target) * 100 if fire_target > 0 else 0
        
        # シミュレーション年数後の進捗率
        future_progress = (display_future_val / fire_target) * 100 if fire_target > 0 else 0

        # UI表示
        fire_col1, fire_col2 = st.columns(2)
        with fire_col1:
            st.markdown(f"""<div class="metric-card" style="border-left-color:#ef6c00;">
                <div class="label">🎯 目安となるFIRE必要額</div>
                <div class="value" style="color:#ef6c00;">{fire_target:,.0f} <span style="font-size:1rem;">円</span></div>
                <div class="sub">現在の推定年間支出: {annual_expense:,.0f}円 × 25年分</div>
            </div>""", unsafe_allow_html=True)
            
        with fire_col2:
            prg_color = "#43a047" if future_progress >= 100 else "#fb8c00"
            st.markdown(f"""<div style="background:white; border-radius:12px; padding:20px; box-shadow:0 2px 10px rgba(0,0,0,0.05); text-align:center;">
                <div style="font-size:0.9rem; color:#757575; font-weight:600; margin-bottom:8px;">{years}年後のFIRE達成率</div>
                <div style="font-size:2.5rem; font-weight:900; color:{prg_color}; line-height:1;">{min(100, future_progress):.1f}%</div>
                <div class="sub" style="margin-top:8px;">現在: {min(100, current_progress):.1f}%</div>
            </div>""", unsafe_allow_html=True)
            
            # 進捗バー
            st.markdown(f"""
            <div style="width:100%; height:12px; background-color:#e0e0e0; border-radius:6px; margin-top:10px; overflow:hidden;">
                <div style="width:{min(100, future_progress)}%; height:100%; background:linear-gradient(90deg, #ffb74d, #f57c00);"></div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("💡 支出データが蓄積されると、あなたの生活水準に基づいたリアルなFIRE達成状況が計算されます。")

    st.markdown('<div class="section-header">📈 資産推移チャート (NISA vs 特定口座)</div>', unsafe_allow_html=True)
    chart_caption = "緑 = NISA(非課税)、オレンジ = 特定口座(税引後)、青 = 投資元本"
    if inflation_pct > 0:
        chart_caption += f"、紫 = 実質価値(インフレ{inflation_pct}%調整)"
    st.caption(chart_caption)
    if values:
        chart_df = pd.DataFrame(values).set_index("年")
        chart_cols = ["NISA口座 (非課税)", "特定口座 (課税後)", "投資元本"]
        color_map = {
            "NISA口座 (非課税)": "#2e7d32", 
            "特定口座 (課税後)": "#f57c00",
            "投資元本": "#90caf9"
        }
        if inflation_pct > 0:
            chart_cols.append("実質価値 (NISA)")
            color_map["実質価値 (NISA)"] = "#7b1fa2"
        fig_line = px.area(chart_df, y=chart_cols, color_discrete_map=color_map)
        fig_line.update_layout(height=450, margin=dict(l=0, r=0, t=20, b=20), 
                               legend_title_text='項目', xaxis_title="経過年数", yaxis_title="金額 (円)")
        st.plotly_chart(fig_line, use_container_width=True)

# ================================================================
# Tab 4: データ管理
# ================================================================
with tab4:
    # --- 固定費一括登録セクション ---
    st.markdown('<div class="section-header">📌 今月の固定費を一括登録</div>', unsafe_allow_html=True)
    st.caption("サイドバーで設定した固定費テンプレートを、今月1日付けで一括登録します。同じ月に既に登録済みの項目は自動的にスキップされます。")
    
    template_to_use = st.session_state.get('fixed_costs', FIXED_COST_TEMPLATE)
    
    # テンプレートのプレビュー
    preview_cols = st.columns(len(template_to_use))
    for idx, item in enumerate(template_to_use):
        with preview_cols[idx]:
            st.markdown(f"""<div class="metric-card" style="border-left-color:#7986cb; padding:12px;">
                <div class="label" style="font-size:0.75rem;">{item['カテゴリー']}</div>
                <div style="font-weight:700; color:#1b5e20; font-size:0.85rem;">{item['内容']}</div>
                <div style="font-weight:800; color:#5c6bc0;">¥{item['金額']:,}</div>
            </div>""", unsafe_allow_html=True)
    
    if st.button("🔌 今月の固定費を一括登録する", use_container_width=True, key="btn_fixed_cost_bulk"):
        template_to_use = st.session_state.get('fixed_costs', FIXED_COST_TEMPLATE)
        added_rows, skipped_items = register_fixed_costs(st.session_state.df, template_to_use, USER_ID)
        if added_rows:
            st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame(added_rows)], ignore_index=True)
            save_data(st.session_state.df, USER_ID)
            st.success(f"✅ {len(added_rows)} 件登録完了")
        if skipped_items:
            st.warning(f"⚠️ {len(skipped_items)} 件スキップ（登録済）")
        if added_rows: st.rerun()

    st.markdown('<div class="section-header">📋 前月の固定費から賢くコピー</div>', unsafe_allow_html=True)
    st.caption("前月に利用した実データから、カテゴリが『固定費』のものを抽出して今月の1日にコピーします。")
    if st.button("✨ 前月分を一括コピー (スマート複製)", use_container_width=True):
        added_rows, skipped_items = register_fixed_costs_from_prev_month(st.session_state.df, USER_ID, datetime.date.today())
        if added_rows:
            st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame(added_rows)], ignore_index=True)
            save_data(st.session_state.df, USER_ID)
            st.success(f"✅ {len(added_rows)} 件をコピーしました！")
        if skipped_items:
            st.info(f"💡 {len(skipped_items)} 件は既に今月に存在するためスキップしました。")
        if added_rows: st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # --- サマリーカード ---
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""<div class="metric-card" style="border-left-color:#5c6bc0;">
            <div class="label">🧾 総レコード数</div>
            <div class="value" style="color:#5c6bc0;">{total_records}</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="metric-card" style="border-left-color:#43a047;">
            <div class="label">💰 {get_label("income_all")}</div>
            <div class="value" style="font-size:1.5rem;">{total_income_all:,.0f}<span style="font-size:0.9rem;"> 円</span></div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="metric-card" style="border-left-color:#ef6c00;">
            <div class="label">💸 累計{label_exp}</div>
            <div class="value" style="color:#ef6c00; font-size:1.5rem;">{total_expense:,.0f}<span style="font-size:0.9rem;"> 円</span></div>
        </div>""", unsafe_allow_html=True)

    st.markdown('<div class="section-header">💾 データ編集・管理</div>', unsafe_allow_html=True)
    st.info("✨ **編集のヒント**: 表の**最下部にある空行**をクリックすると、新しいデータを直接追加できます。")
    st.caption("テーブルを編集すると画面上のサマリーやグラフに即座に反映されます。編集内容は自動的に保存されます。")

    # 選択列を追加して一括削除用チェックボックスを作成
    display_df = st.session_state.df.copy()
    display_df.insert(0, "🗑️ 選択", False)

    edited_df = st.data_editor(
        display_df,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "🗑️ 選択": st.column_config.CheckboxColumn("🗑️", default=False, help="チェックして一括削除"),
            "user_id": st.column_config.TextColumn("User ID", disabled=True),
            "日付": st.column_config.DateColumn("日付", required=True),
            "タイプ": st.column_config.SelectboxColumn("タイプ", options=["支出", "収入"], required=True),
            "カテゴリー": st.column_config.SelectboxColumn("カテゴリー", options=EXPENSE_CATEGORIES + INCOME_CATEGORIES, required=True),
            "性質": st.column_config.SelectboxColumn("性質", options=CONSUMPTION_TAGS + ["収入"], required=True),
            "金額": st.column_config.NumberColumn("金額", min_value=0, step=100, required=True, format="%d"),
        },
        key="data_editor_main"
    )

    manage_data_ui(
        edited_df=edited_df,
        original_df=st.session_state.df,
        session_key="df",
        backup_key="df_backup",
        save_func=save_data,
        required_cols=["日付", "カテゴリー", "金額"],
        is_bs=False
    )

    st.markdown('<div class="section-header">📥 銀行・クレカCSVインポート (インテリジェント読込)</div>', unsafe_allow_html=True)
    st.caption("銀行やクレジットカードのCSVをアップロード後、列名をマッピングして一括登録できます。")
    uploaded_csv = st.file_uploader("CSVファイルを選択してください", type="csv")
    if uploaded_csv:
        try:
            # 文字コードの自動判別（UTF-8かShift-JISか）
            raw_data = uploaded_csv.read()
            uploaded_csv.seek(0) # ポインタを戻す
            
            try:
                csv_df = pd.read_csv(uploaded_csv, encoding='utf-8')
            except UnicodeDecodeError:
                uploaded_csv.seek(0)
                csv_df = pd.read_csv(uploaded_csv, encoding='shift-jis')
            
            st.write("プレビュー (最初の5行):", csv_df.head())
            
            st.markdown("#### 🔄 カラムのマッピング")
            st.caption("アップロードしたCSVのどの列が、アプリ内の各項目に対応するかを選択してください。")
            cols = csv_df.columns.tolist()
            
            # カラム推測ロジック
            def guess_col(keywords, columns):
                for c in columns:
                    if any(kw in str(c) for kw in keywords):
                        return columns.index(c) + 1
                return 0

            map_c1, map_c2, map_c3, map_c4 = st.columns(4)
            with map_c1:
                idx_date = guess_col(["日付", "年月日", "date", "Date"], cols)
                date_col = st.selectbox("📅 日付 に該当する列", options=["（選択しない）"] + cols, index=idx_date)
            with map_c2:
                idx_amt = guess_col(["金額", "振込", "支払", "amount", "Amount", "税込"], cols)
                amt_col = st.selectbox("💰 金額 に該当する列", options=["（選択しない）"] + cols, index=idx_amt)
            with map_c3:
                idx_memo = guess_col(["内容", "摘要", "メモ", "memo", "Description", "利用店"], cols)
                memo_col = st.selectbox("📝 内容 に該当する列", options=["（選択しない）"] + cols, index=idx_memo)
            with map_c4:
                idx_type = guess_col(["タイプ", "入出", "区分", "type", "Type"], cols)
                type_col = st.selectbox("🔄 タイプ(収入/支出) 列", options=["（選択しない）"] + cols, index=idx_type)
            
            # TODO: 収入・支出の固定指定や、金額の正負での判定も可能だが、今回はシンプルなマッピングを優先
            default_type_fallback = st.radio("「タイプ」列がない場合のデフォルト:", ["支出", "収入"], horizontal=True)
            
            if st.button("🚀 マッピング設定でインポートする", use_container_width=True):
                if date_col == "（選択しない）" or amt_col == "（選択しない）":
                    st.error("⚠️ 最低限、「日付」と「金額」の列はマッピングしてください。")
                else:
                    mapped_df = pd.DataFrame()
                    mapped_df["user_id"] = USER_ID
                    
                    # 日付
                    mapped_df["日付"] = pd.to_datetime(csv_df[date_col], errors="coerce").dt.date
                    
                    # 金額 (カンマ、円記号などを除去して数値化)
                    amt_series = csv_df[amt_col].astype(str).str.replace(r'[^\d\-]', '', regex=True)
                    mapped_df["金額"] = pd.to_numeric(amt_series, errors="coerce").fillna(0).astype(int)
                    
                    # 内容
                    if memo_col != "（選択しない）":
                        mapped_df["内容"] = csv_df[memo_col].fillna("（未入力）")
                    else:
                        mapped_df["内容"] = "（未入力）"
                        
                    # タイプ
                    if type_col != "（選択しない）":
                        mapped_df["タイプ"] = csv_df[type_col].apply(lambda x: "収入" if "入" in str(x) or "収" in str(x) else "支出")
                        # 万が一文字がなくても、通常は支出扱いにする
                        mapped_df["タイプ"] = mapped_df["タイプ"].fillna("支出")
                    else:
                        mapped_df["タイプ"] = default_type_fallback
                        
                    # エラーでNaNになった日付・金額の行を除外
                    before_len = len(mapped_df)
                    mapped_df = mapped_df.dropna(subset=["日付", "金額"])
                    dropped_len = before_len - len(mapped_df)
                    
                    # デフォルトカテゴリ設定
                    mapped_df["カテゴリー"] = "未分類"
                    mapped_df["性質"] = mapped_df.apply(lambda row: "収入" if row["タイプ"] == "収入" else "消費 (Need)", axis=1)
                    
                    if dropped_len > 0:
                        st.warning(f"⚠️ {dropped_len} 件のデータが不正な日付・金額のため除外されました。")
                        
                    if len(mapped_df) > 0:
                        st.session_state.df = pd.concat([st.session_state.df, mapped_df], ignore_index=True)
                        save_data(st.session_state.df)
                        st.success(f"✅ {len(mapped_df)} 件のデータをインポートしました！")
                        st.rerun()
                    else:
                        st.error("有効なデータが1件もありませんでした。CSVの形式を確認してください。")
                    
        except Exception as e:
            st.error(f"CSVの読み込みに失敗しました: {e}")

    st.markdown("<br><br>", unsafe_allow_html=True)

# ================================================================
# Tab BS: バランスシート（純資産管理）
# ================================================================
with tab_bs:
    st.markdown('<div class="section-header">🏦 バランスシート（資産・負債管理）</div>', unsafe_allow_html=True)
    st.caption("現在の資産（持っているもの）と負債（借りているもの）を記録して、純資産の推移を可視化します。")
    
    bs_col1, bs_col2 = st.columns([1, 1])
    
    with bs_col1:
        st.markdown("##### 📝 資産・負債の記録")
        
        # 3. 削除機能の整合性 (Tab4と同様の「🗑️ 選択」カラム追加)
        display_bs_df = st.session_state.assets_df.copy()
        display_bs_df.insert(0, "🗑️ 選択", False)

        new_bs_df = st.data_editor(
            display_bs_df,
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "🗑️ 選択": st.column_config.CheckboxColumn("🗑️", default=False, help="チェックして一括削除"),
                "日付": st.column_config.DateColumn("基準日", required=True),
                "区分": st.column_config.SelectboxColumn("区分", options=ASSET_TYPES, required=True),
                "項目名": st.column_config.TextColumn("項目名 (例: 楽天銀行, 住宅ローン)", required=True),
                "金額": st.column_config.NumberColumn("金額 (円)", min_value=0, required=True, format="%d"),
            },
            key="bs_editor"
        )
        
        manage_data_ui(
            edited_df=new_bs_df,
            original_df=st.session_state.assets_df,
            session_key="assets_df",
            backup_key="assets_df_backup",
            save_func=save_assets_data,
            required_cols=["日付", "区分", "項目名", "金額"],
            is_bs=True
        )

    with bs_col2:
        st.markdown("##### 📈 純資産推移")
        if not st.session_state.assets_df.empty:
            bs_df = st.session_state.assets_df.copy()
            bs_df["日付"] = pd.to_datetime(bs_df["日付"])
            # 資産と負債の極性を設定
            bs_df["実額"] = bs_df.apply(lambda r: r["金額"] if "資産" in str(r["区分"]) else -r["金額"], axis=1)
            
            # 月次で集計
            bs_df["年月"] = bs_df["日付"].dt.strftime("%Y/%m")
            monthly_bs = bs_df.groupby(["年月", "区分"])["金額"].sum().unstack().fillna(0)
            
            # 純資産の計算
            net_worth = bs_df.groupby("年月")["実額"].sum().reset_index()
            
            fig_nw = go.Figure()
            fig_nw.add_trace(go.Scatter(x=net_worth["年月"], y=net_worth["実額"], name="純資産 (資産-負債)", 
                                        line={"color": "#43a047", "width": 4}, mode='lines+markers',
                                        fill='tozeroy', fillcolor='rgba(67, 160, 71, 0.1)'))
            fig_nw.update_layout(height=400, margin={"t": 10, "b": 10, "l": 10, "r": 10}, hovermode="x unified")
            st.plotly_chart(fig_nw, use_container_width=True)
            
            current_nw = net_worth.iloc[-1]["実額"] if not net_worth.empty else 0
            nw_color = "#43a047" if current_nw >= 0 else "#e53935"
            st.markdown(f"""<div class="metric-card" style="border-left-color:{nw_color};">
                <div class="label">現在の純資産総額</div>
                <div class="value" style="color:{nw_color};">{current_nw:,.0f} <span style="font-size:1rem;">円</span></div>
            </div>""", unsafe_allow_html=True)
            
            # --- アセットアロケーション (資産構成比) の追加 ---
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("##### 🥧 資産構成比 (アセットアロケーション)")
            
            # 資産のみを抽出して最新の割合を計算
            assets_only = bs_df[bs_df["実額"] > 0]
            if not assets_only.empty:
                # 最新月のみを取得
                latest_month = assets_only["年月"].max()
                latest_assets = assets_only[assets_only["年月"] == latest_month]
                
                if not latest_assets.empty:
                    allocation = latest_assets.groupby("区分")["金額"].sum().reset_index()
                    
                    fig_pie_assets = px.pie(
                        allocation, values='金額', names='区分', hole=0.4,
                        color_discrete_sequence=px.colors.sequential.Tealgrn_r
                    )
                    fig_pie_assets.update_traces(textposition='inside', textinfo='percent+label', marker=dict(line=dict(color='#ffffff', width=2)))
                    fig_pie_assets.update_layout(height=300, margin=dict(t=10, b=10, l=10, r=10), showlegend=False)
                    st.plotly_chart(fig_pie_assets, use_container_width=True)
            else:
                 st.info("プラスの資産が登録されていません。")
        else:
            st.info("BSデータを入力すると、純資産の推移チャート・構成比が表示されます。")