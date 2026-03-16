import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional
from difflib import get_close_matches
from collections import Counter

class AssetProjector:
    """
    資産推移シミュレーションエンジン。
    新NISA、3シナリオ投影、ライフイベント加減算をサポート。
    """
    def __init__(self, nisa_limit: float = 18_000_000, tax_rate: float = 0.20315):
        self.nisa_limit = nisa_limit
        self.tax_rate = tax_rate

    def project(
        self,
        initial_amount: float,
        monthly_contribution: float,
        annual_rate_pct: float,
        annual_sigma_pct: float,
        years: int,
        life_events: Optional[Dict[int, float]] = None
    ) -> List[Dict]:
        """
        中央値、楽観(+1σ)、悲観(-1σ)の3シナリオで資産推移を計算。
        """
        results = []
        life_events = life_events or {}
        
        # 月次換算
        mu_annual = annual_rate_pct / 100
        sigma_annual = annual_sigma_pct / 100
        
        # 3シナリオの期待リターン（連続複利近似）
        # 中央値: mu - 0.5 * sigma^2
        # 楽観 (+1σ): mu + sigma
        # 悲観 (-1σ): mu - sigma
        returns = {
            "median": mu_annual,
            "optimistic": mu_annual + sigma_annual,
            "pessimistic": mu_annual - sigma_annual
        }
        
        history = {k: [] for k in returns.keys()}
        
        # 各シナリオごとに計算
        for scenario, r_annual in returns.items():
            curr_nisa_val = initial_amount
            curr_nisa_cost = initial_amount # 元本ベース
            curr_taxable_val = 0
            curr_taxable_cost = 0
            
            monthly_r = r_annual / 12
            
            for m in range(years * 12 + 1):
                y = m // 12
                # 年初のライフイベント処理
                if m > 0 and m % 12 == 0:
                    event_amt = life_events.get(y, 0)
                    # ライフイベントはまず特定口座から、足りなければNISAから引き出す
                    if event_amt != 0:
                        if curr_taxable_val >= abs(event_amt) or event_amt > 0:
                            curr_taxable_val += event_amt
                        else:
                            remain = event_amt + curr_taxable_val
                            curr_taxable_val = 0
                            curr_nisa_val += remain
                            # 元本の調整（簡易化のため引き出し割合で減らす）
                            if curr_nisa_val > 0:
                                curr_nisa_cost *= (curr_nisa_val / (curr_nisa_val - remain))
                
                # 記録（年次）
                if m % 12 == 0:
                    gain_taxable = curr_taxable_val - curr_taxable_cost
                    taxed_taxable = curr_taxable_val - (gain_taxable * self.tax_rate if gain_taxable > 0 else 0)
                    history[scenario].append({
                        "year": y,
                        "total": int(curr_nisa_val + taxed_taxable),
                        "nisa": int(curr_nisa_val),
                        "taxable": int(taxed_taxable)
                    })
                
                # 積立
                if m < years * 12:
                    if curr_nisa_cost < self.nisa_limit:
                        can_invest_nisa = min(monthly_contribution, self.nisa_limit - curr_nisa_cost)
                        curr_nisa_val += can_invest_nisa
                        curr_nisa_cost += can_invest_nisa
                        spillover = monthly_contribution - can_invest_nisa
                        curr_taxable_val += spillover
                        curr_taxable_cost += spillover
                    else:
                        curr_taxable_val += monthly_contribution
                        curr_taxable_cost += monthly_contribution
                    
                    # 運用
                    curr_nisa_val *= (1 + monthly_r)
                    curr_taxable_val *= (1 + monthly_r)
                    
        # データを整形
        for i in range(years + 1):
            results.append({
                "year": i,
                "median": history["median"][i]["total"],
                "optimistic": history["optimistic"][i]["total"],
                "pessimistic": history["pessimistic"][i]["total"],
                "nisa_median": history["median"][i]["nisa"]
            })
            
        return results

class CategoryInference:
    """
    類似性に基づいたカテゴリー推論。
    """
    @staticmethod
    def suggest(query: str, hist_df: pd.DataFrame, threshold: float = 0.6) -> str:
        if hist_df.empty or "内容" not in hist_df.columns or "カテゴリー" not in hist_df.columns:
            return "未分類"
        
        # 1. 完全一致を検索
        exact_match = hist_df[hist_df["内容"] == query]
        if not exact_match.empty:
            return Counter(exact_match["カテゴリー"]).most_common(1)[0][0]
        
        # 2. 類似一致を検索
        memos = hist_df["内容"].unique().tolist()
        matches = get_close_matches(query, memos, n=3, cutoff=threshold)
        
        if matches:
            # マッチした内容に関連するカテゴリーをすべて収集して最頻値を返す
            matched_cats = hist_df[hist_df["内容"].isin(matches)]["カテゴリー"]
            if not matched_cats.empty:
                return Counter(matched_cats).most_common(1)[0][0]
                
        return "未分類"

class ExitStrategy:
    """
    取り崩しシミュレーション。
    """
    def simulate(
        self,
        initial_amount: float,
        annual_rate_pct: float,
        withdrawal_type: str, # "rate" or "amount"
        value: float, # 4%なら4, 20万なら200000
    ) -> List[Dict]:
        """
        資産寿命を計算。
        """
        results = []
        curr_val = initial_amount
        monthly_r = annual_rate_pct / 100 / 12
        
        for m in range(1201): # 最大100年
            if m % 12 == 0:
                results.append({"year": m // 12, "balance": int(curr_val)})
            
            if curr_val <= 0:
                break
            
            # 運用
            curr_val *= (1 + monthly_r)
            
            # 取り崩し
            if withdrawal_type == "rate":
                w_amt = (curr_val * (value / 100)) / 12
            else:
                w_amt = value
            
            curr_val -= w_amt
            
        return results

def suggest_category(memo: str, history_df: pd.DataFrame) -> str:
    """内容(memo)に基づいてカテゴリーを推論する（キーワード＋履歴ベース）"""
    if not isinstance(memo, str) or memo == "（未入力）" or not memo:
        return "未分類"
    
    # 1. 過去の履歴から検索(完全一致優先)
    if history_df is not None and not history_df.empty and "内容" in history_df.columns:
        history_match = history_df[history_df["内容"] == memo]
        if not history_match.empty:
            return history_match.iloc[-1]["カテゴリー"]

    # 2. キーワードベースの推論
    keyword_map = {
        "食費": ["スーパー", "セブン", "ローソン", "ファミマ", "ライフ", "イオン", "スシロー", "松屋", "吉野家", "スタバ", "カフェ"],
        "日用品": ["アマゾン", "Amazon", "楽天", "メルカリ", "ドラッグストア", "薬局", "ダイソー", "ニトリ", "無印"],
        "通信費": ["ドコモ", "ソフトバンク", "au", "楽天モバイル", "UQ", "ワイモバイル", "NTT", "Netflix", "Youtube"],
        "交通費": ["JR", "メトロ", "バス", "タクシー", "Suica", "Pasmo", "ガソリン", "駐車場"],
        "住居費": ["家賃", "管理費", "リフォーム"],
        "水道光熱費": ["電気", "ガス", "水道", "電力", "TEPCO"],
        "保険料": ["生命保険", "損害保険", "医療保険"],
        "娯楽・レジャー": ["映画", "遊園地", "旅行", "ホテル", "チケット", "Switch", "PS5"],
        "美容・健康": ["病院", "クリニック", "マッサージ", "美容院", "カット"],
        "投資（NISA/iDeCo等）": ["SBI証券", "楽天証券", "積立", "投資信託", "NISA", "iDeCo"],
        "主収入（給与・事業）": ["給与", "給料", "ボーナス", "賞与"],
        "特別利益": ["還付金", "プレゼント", "お祝い", "ポイント還元"]
    }

    for cat, keywords in keyword_map.items():
        if any(kw.lower() in memo.lower() for kw in keywords):
            return cat
            
    return "未分類"

def get_nature_by_category(category: str) -> str:
    """カテゴリに応じた「性質（消費・浪費・投資）」を自動判定します。"""
    nature_map = {
        "消費 (Need)": ["住居費", "水道光熱費", "日用品", "通信費", "保険料", "交通費", "税金・社会保険料"],
        "浪費 (Want)": ["娯楽・レジャー", "美容・健康", "交際費", "外食", "嗜好品", "サブスクリプション", "その他"],
        "投資 (Invest)": ["投資（NISA/iDeCo等）", "資産運用益"]
    }
    for nature, cats in nature_map.items():
        if category in cats:
            return nature
    return "消費 (Need)"

def suggest_category_advanced(memo: str, history_df: pd.DataFrame) -> Tuple[str, str]:
    """類似度と頻度に基づいた高度なカテゴリー推論と性質付与。"""
    if history_df.empty or not memo or not isinstance(memo, str) or memo == "（未入力）": 
        cat = "未分類"
    else:
        memos = history_df["内容"].unique().tolist()
        matches = get_close_matches(memo, memos, n=3, cutoff=0.5)
        if not matches:
            cat = suggest_category(memo, history_df) # 旧キーワード推論へフォールバック
        else:
            cats = history_df[history_df["内容"].isin(matches)]["カテゴリー"]
            cat = Counter(cats).most_common(1)[0][0]
    
    nature = get_nature_by_category(cat)
    return cat, nature

# --- Verification Script ---
if __name__ == "__main__":
    print("--- 1. 資産推移テスト (3シナリオ + NISA + ライフイベント) ---")
    projector = AssetProjector()
    events = {5: -5_000_000} # 5年目に500万支出（住宅等）
    plan = projector.project(1_000_000, 100_000, 5, 15, 20, life_events=events)
    print(f"20年後(中央値): {plan[-1]['median']:,}円")
    print(f"20年後(楽観): {plan[-1]['optimistic']:,}円")
    
    print("\n--- 2. カテゴリ推論テスト ---")
    data = pd.DataFrame({
        "内容": ["アマゾン 買い物", "アマゾン 雑貨", "セブンイレブン 昼食", "セブンイレブン 弁当", "ユニクロ 服"],
        "カテゴリー": ["日用品", "日用品", "食費", "食費", "衣服"]
    })
    inference = CategoryInference()
    print(f"『ｱﾏｿﾞﾝ』の推論: {inference.suggest('ｱﾏｿﾞﾝ', data)}")
    print(f"『ｾﾌﾞﾝ』の推論: {inference.suggest('ｾﾌﾞﾝ', data)}")

    print("\n--- 3. 出口戦略テスト ---")
    exit_sim = ExitStrategy()
    life = exit_sim.simulate(50_000_000, 4, "rate", 4) # 5000万, 4%運用, 4%取り崩し
    print(f"30年後の残高: {life[30]['balance']:,}円")
