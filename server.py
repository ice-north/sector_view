#!/usr/bin/env python3
"""
セクター株価リアルタイムサーバー
日本株の株価データとニュースをローカルAPIとして提供する
"""

import re
import time
import threading
from datetime import datetime

from flask import Flask, jsonify
from flask_cors import CORS
import yfinance as yf
import feedparser

app = Flask(__name__)
CORS(app)

# =============================================================================
# セクター別銘柄定義（コードは東証コード、.T はサーバー側で付加）
# =============================================================================
SECTOR_COMPANIES = {
    "水産・農林": [
        {"name": "日本水産",       "code": "1332", "cap": 0.15},
        {"name": "マルハニチロ",   "code": "1333", "cap": 0.14},
        {"name": "ホクト",         "code": "1379", "cap": 0.08},
        {"name": "雪国まいたけ",   "code": "1375", "cap": 0.05},
        {"name": "極洋",           "code": "1301", "cap": 0.04},
        {"name": "日本たばこ産業", "code": "2914", "cap": 7.20},
        {"name": "イートアンド",   "code": "2882", "cap": 0.06},
    ],
    "鉱業": [
        {"name": "INPEX",         "code": "1605", "cap": 2.80},
        {"name": "石油資源開発",  "code": "1662", "cap": 0.35},
        {"name": "K&Oエナジー",   "code": "1663", "cap": 0.12},
    ],
    "建設": [
        {"name": "大和ハウス工業", "code": "1925", "cap": 3.80},
        {"name": "積水ハウス",     "code": "1928", "cap": 2.50},
        {"name": "大成建設",       "code": "1801", "cap": 1.20},
        {"name": "鹿島建設",       "code": "1812", "cap": 1.10},
        {"name": "清水建設",       "code": "1803", "cap": 0.90},
        {"name": "大林組",         "code": "1802", "cap": 1.00},
        {"name": "前田建設工業",   "code": "1824", "cap": 0.30},
    ],
    "食料品": [
        {"name": "味の素",           "code": "2802", "cap": 2.80},
        {"name": "キッコーマン",     "code": "2801", "cap": 1.20},
        {"name": "明治HD",           "code": "2269", "cap": 1.50},
        {"name": "日清食品",         "code": "2897", "cap": 1.10},
        {"name": "サントリー食品",   "code": "2587", "cap": 1.80},
        {"name": "アサヒグループ",   "code": "2502", "cap": 3.20},
        {"name": "キリン",           "code": "2503", "cap": 2.10},
        {"name": "日本ハム",         "code": "2282", "cap": 0.80},
    ],
    "繊維製品": [
        {"name": "東レ",       "code": "3402", "cap": 0.90},
        {"name": "帝人",       "code": "3401", "cap": 0.40},
        {"name": "ユニチカ",   "code": "3103", "cap": 0.05},
        {"name": "クラボウ",   "code": "3106", "cap": 0.08},
        {"name": "ワコールHD", "code": "3591", "cap": 0.30},
    ],
    "パルプ・紙": [
        {"name": "王子HD",   "code": "3861", "cap": 0.80},
        {"name": "日本製紙", "code": "3863", "cap": 0.30},
        {"name": "レンゴー", "code": "3941", "cap": 0.50},
        {"name": "大王製紙", "code": "3880", "cap": 0.20},
    ],
    "化学": [
        {"name": "三菱ケミカルG", "code": "4188", "cap": 2.10},
        {"name": "住友化学",      "code": "4005", "cap": 1.20},
        {"name": "旭化成",        "code": "3407", "cap": 1.50},
        {"name": "信越化学工業",  "code": "4063", "cap": 8.50},
        {"name": "資生堂",        "code": "4911", "cap": 1.80},
        {"name": "花王",          "code": "4452", "cap": 2.50},
        {"name": "富士フイルム",  "code": "4901", "cap": 3.20},
    ],
    "医薬品": [
        {"name": "武田薬品工業",   "code": "4502", "cap": 7.20},
        {"name": "アステラス製薬", "code": "4503", "cap": 2.80},
        {"name": "第一三共",       "code": "4568", "cap": 5.50},
        {"name": "中外製薬",       "code": "4519", "cap": 4.20},
        {"name": "エーザイ",       "code": "4523", "cap": 2.10},
        {"name": "大塚HD",         "code": "4578", "cap": 1.80},
        {"name": "塩野義製薬",     "code": "4507", "cap": 1.20},
        {"name": "小野薬品工業",   "code": "4528", "cap": 1.50},
    ],
    "石油・石炭": [
        {"name": "ENEOS",       "code": "5020", "cap": 2.50},
        {"name": "出光興産",    "code": "5019", "cap": 1.20},
        {"name": "コスモエネルギー", "code": "5021", "cap": 0.80},
    ],
    "ゴム製品": [
        {"name": "ブリヂストン",   "code": "5108", "cap": 3.80},
        {"name": "住友ゴム工業",   "code": "5110", "cap": 0.90},
        {"name": "横浜ゴム",       "code": "5101", "cap": 0.60},
        {"name": "東洋ゴム工業",   "code": "5105", "cap": 0.30},
    ],
    "ガラス・土石": [
        {"name": "AGC",           "code": "5201", "cap": 1.50},
        {"name": "日本板硝子",    "code": "5202", "cap": 0.30},
        {"name": "太平洋セメント","code": "5233", "cap": 0.50},
        {"name": "TOTO",          "code": "5332", "cap": 1.20},
    ],
    "鉄鋼": [
        {"name": "日本製鉄",   "code": "5401", "cap": 3.20},
        {"name": "JFE",        "code": "5411", "cap": 1.50},
        {"name": "神戸製鋼所", "code": "5406", "cap": 0.60},
        {"name": "大同特殊鋼", "code": "5471", "cap": 0.40},
    ],
    "非鉄金属": [
        {"name": "住友金属鉱山",       "code": "5713", "cap": 1.80},
        {"name": "三菱マテリアル",     "code": "5711", "cap": 0.80},
        {"name": "三井金属",           "code": "5706", "cap": 0.50},
        {"name": "DOWAホールディングス","code": "5714", "cap": 0.40},
        {"name": "古河電工",           "code": "5801", "cap": 0.60},
    ],
    "金属製品": [
        {"name": "LIXIL",   "code": "5938", "cap": 1.20},
        {"name": "三協立山", "code": "5932", "cap": 0.20},
        {"name": "アルインコ","code": "5933", "cap": 0.10},
    ],
    "機械": [
        {"name": "三菱重工業", "code": "7011", "cap": 5.20},
        {"name": "川崎重工業", "code": "7012", "cap": 1.80},
        {"name": "IHI",        "code": "7013", "cap": 1.20},
        {"name": "クボタ",     "code": "6326", "cap": 3.50},
        {"name": "小松製作所", "code": "6301", "cap": 3.20},
        {"name": "日立建機",   "code": "6305", "cap": 0.90},
        {"name": "ダイキン工業","code": "6367", "cap": 6.80},
        {"name": "ファナック",  "code": "6954", "cap": 4.50},
    ],
    "電気機器": [
        {"name": "ソニーグループ", "code": "6758", "cap": 18.50},
        {"name": "日立製作所",    "code": "6501", "cap": 12.80},
        {"name": "三菱電機",      "code": "6503", "cap":  5.50},
        {"name": "パナソニック",  "code": "6752", "cap":  4.20},
        {"name": "富士通",        "code": "6702", "cap":  3.50},
        {"name": "NEC",           "code": "6701", "cap":  2.80},
        {"name": "キーエンス",    "code": "6861", "cap": 22.50},
    ],
    "輸送用機器": [
        {"name": "トヨタ自動車", "code": "7203", "cap": 42.50},
        {"name": "ホンダ",       "code": "7267", "cap":  8.50},
        {"name": "日産自動車",   "code": "7201", "cap":  1.80},
        {"name": "スズキ",       "code": "7269", "cap":  3.20},
        {"name": "マツダ",       "code": "7261", "cap":  0.90},
        {"name": "SUBARU",       "code": "7270", "cap":  2.80},
        {"name": "いすゞ自動車", "code": "7202", "cap":  1.20},
        {"name": "三菱自動車",   "code": "7211", "cap":  0.60},
    ],
    "精密機器": [
        {"name": "キヤノン",     "code": "7751", "cap": 4.20},
        {"name": "ニコン",       "code": "7731", "cap": 0.60},
        {"name": "オリンパス",   "code": "7733", "cap": 2.50},
        {"name": "テルモ",       "code": "4543", "cap": 3.80},
        {"name": "シチズン時計", "code": "7762", "cap": 0.30},
    ],
    "その他製品": [
        {"name": "任天堂",         "code": "7974", "cap": 8.50},
        {"name": "バンダイナムコHD","code": "7832", "cap": 2.10},
        {"name": "コナミグループ", "code": "9766", "cap": 1.20},
        {"name": "ヤマハ",         "code": "7951", "cap": 1.50},
    ],
    "電気・ガス業": [
        {"name": "東京電力HD", "code": "9501", "cap": 1.20},
        {"name": "関西電力",   "code": "9503", "cap": 1.50},
        {"name": "中部電力",   "code": "9502", "cap": 1.10},
        {"name": "東京ガス",   "code": "9531", "cap": 1.80},
        {"name": "大阪ガス",   "code": "9532", "cap": 0.90},
    ],
    "陸運業": [
        {"name": "JR東日本", "code": "9020", "cap": 3.50},
        {"name": "JR東海",   "code": "9022", "cap": 5.20},
        {"name": "JR西日本", "code": "9021", "cap": 1.80},
        {"name": "ヤマトHD", "code": "9064", "cap": 1.50},
    ],
    "海運業": [
        {"name": "日本郵船",   "code": "9101", "cap": 2.80},
        {"name": "商船三井",   "code": "9104", "cap": 1.50},
        {"name": "川崎汽船",   "code": "9107", "cap": 0.80},
    ],
    "空運業": [
        {"name": "ANA",      "code": "9202", "cap": 1.20},
        {"name": "JAL",      "code": "9201", "cap": 1.10},
        {"name": "スカイマーク","code": "9204", "cap": 0.05},
    ],
    "倉庫・運輸": [
        {"name": "三菱倉庫",   "code": "9301", "cap": 0.60},
        {"name": "三井倉庫HD", "code": "9302", "cap": 0.40},
        {"name": "住友倉庫",   "code": "9303", "cap": 0.30},
        {"name": "日本通運",   "code": "9062", "cap": 1.20},
    ],
    "情報・通信": [
        {"name": "NTT",             "code": "9432", "cap": 15.80},
        {"name": "KDDI",            "code": "9433", "cap": 10.20},
        {"name": "ソフトバンクG",   "code": "9984", "cap":  9.80},
        {"name": "楽天グループ",    "code": "4755", "cap":  1.50},
        {"name": "LINEヤフー",      "code": "4689", "cap":  2.30},
        {"name": "サイバーエージェント","code": "4751","cap":  0.90},
    ],
    "卸売業": [
        {"name": "三菱商事",   "code": "8058", "cap": 12.50},
        {"name": "伊藤忠商事", "code": "8001", "cap": 10.80},
        {"name": "丸紅",       "code": "8002", "cap":  4.20},
        {"name": "住友商事",   "code": "8053", "cap":  5.50},
        {"name": "三井物産",   "code": "8031", "cap":  8.20},
    ],
    "小売業": [
        {"name": "セブン&アイHD",      "code": "3382", "cap":  4.50},
        {"name": "ファーストリテイリング","code": "9983","cap": 12.80},
        {"name": "イオン",             "code": "8267", "cap":  3.20},
        {"name": "ローソン",           "code": "2651", "cap":  0.80},
    ],
    "銀行業": [
        {"name": "三菱UFJ FG", "code": "8306", "cap": 18.50},
        {"name": "三井住友FG", "code": "8316", "cap": 12.80},
        {"name": "みずほFG",   "code": "8411", "cap":  8.20},
        {"name": "りそなHD",   "code": "8308", "cap":  2.50},
    ],
    "証券・商品先物": [
        {"name": "野村HD",     "code": "8604", "cap": 2.80},
        {"name": "大和証券G",  "code": "8601", "cap": 1.50},
        {"name": "SBI HD",     "code": "8473", "cap": 1.20},
    ],
    "保険業": [
        {"name": "東京海上HD",         "code": "8766", "cap": 8.50},
        {"name": "MS&ADインシュアランス","code": "8725", "cap": 4.20},
        {"name": "SOMPOホールディングス","code": "8630","cap": 3.50},
        {"name": "第一生命HD",         "code": "8750", "cap": 3.20},
    ],
    "その他金融": [
        {"name": "オリックス",       "code": "8591", "cap": 3.80},
        {"name": "三井住友トラスト", "code": "8309", "cap": 2.20},
        {"name": "東京センチュリー", "code": "8439", "cap": 0.60},
    ],
    "不動産業": [
        {"name": "三菱地所",     "code": "8802", "cap": 3.80},
        {"name": "三井不動産",   "code": "8801", "cap": 5.20},
        {"name": "住友不動産",   "code": "8830", "cap": 2.80},
        {"name": "東急不動産HD", "code": "3289", "cap": 1.20},
    ],
    "サービス業": [
        {"name": "リクルートHD",  "code": "6098", "cap": 12.50},
        {"name": "電通G",         "code": "4324", "cap":  1.80},
        {"name": "博報堂DYHD",    "code": "2433", "cap":  0.90},
        {"name": "パーソルHD",    "code": "2181", "cap":  0.80},
    ],
    "物流": [
        {"name": "日本通運",         "code": "9062", "cap": 1.20},
        {"name": "SGホールディングス","code": "9143", "cap": 1.50},
        {"name": "日立物流",         "code": "9086", "cap": 0.40},
    ],
    "素材": [
        {"name": "JFEホールディングス","code": "5411", "cap": 1.50},
        {"name": "住友金属鉱山",       "code": "5713", "cap": 1.80},
        {"name": "三井金属",           "code": "5706", "cap": 0.50},
        {"name": "住友化学",           "code": "4005", "cap": 1.20},
    ],
}

# 市場指数ティッカー
INDICES = {
    "nikkei": {"ticker": "^N225",  "label": "日経平均"},
    "topix":  {"ticker": "1306.T", "label": "TOPIX"},
    "growth": {"ticker": "2516.T", "label": "グロース250"},
    "usdjpy": {"ticker": "JPY=X",  "label": "ドル円"},
}

# ニュース RSS フィード
NEWS_FEEDS = [
    "https://www.nhk.or.jp/rss/news/cat6.xml",
    "https://news.google.com/rss/search?q=%E6%97%A5%E7%B5%8C%E5%B9%B3%E5%9D%87+OR+%E6%9D%B1%E8%A8%BC+OR+%E6%A0%AA%E5%BC%8F%E5%B8%82%E5%A0%B4&hl=ja&gl=JP&ceid=JP:ja",
]

# =============================================================================
# キャッシュ
# =============================================================================
_cache: dict = {}
_cache_time: dict = {}
_cache_lock = threading.Lock()
CACHE_TTL = 300  # 5分


def get_cached(key: str, fetch_fn):
    now = time.time()
    with _cache_lock:
        if key in _cache and now - _cache_time.get(key, 0) < CACHE_TTL:
            return _cache[key]

    # ロック外で取得（時間がかかる処理）
    data = fetch_fn()

    with _cache_lock:
        _cache[key] = data
        _cache_time[key] = time.time()

    return data


def invalidate_cache(key: str):
    with _cache_lock:
        _cache.pop(key, None)
        _cache_time.pop(key, None)


# =============================================================================
# データ取得
# =============================================================================
def fetch_all_stocks() -> dict:
    """全銘柄の前日比変動率を一括取得"""
    all_codes: set = set()
    for companies in SECTOR_COMPANIES.values():
        for c in companies:
            all_codes.add(f"{c['code']}.T")

    tickers_list = sorted(all_codes)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 株価取得中... ({len(tickers_list)}銘柄)")

    try:
        raw = yf.download(
            tickers_list,
            period="5d",
            auto_adjust=True,
            progress=False,
            threads=True,
        )
        # 複数ティッカーの場合 raw["Close"] は DataFrame
        close_df = raw["Close"] if isinstance(raw.columns, object) and "Close" in raw else raw
        if hasattr(close_df, "columns") and "Close" in close_df.columns.get_level_values(0) if hasattr(close_df.columns, "get_level_values") else False:
            close_df = raw["Close"]
    except Exception as e:
        print(f"yfinance エラー: {e}")
        return {}

    change_map: dict = {}
    for ticker in tickers_list:
        try:
            if hasattr(close_df, "columns") and ticker in close_df.columns:
                series = close_df[ticker].dropna()
            else:
                series = close_df.dropna()

            if len(series) >= 2:
                prev = float(series.iloc[-2])
                curr = float(series.iloc[-1])
                if prev > 0:
                    change_map[ticker] = round((curr - prev) / prev * 100, 2)
                    change_map[ticker + "_price"] = round(curr, 0)
        except Exception:
            pass

    ok_count = sum(1 for k in change_map if not k.endswith("_price"))
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 取得完了: {ok_count}銘柄")
    return change_map


def build_sector_data(change_map: dict) -> dict:
    """セクターごとに時価総額加重平均変動率を計算"""
    result: dict = {}
    for sector_name, companies in SECTOR_COMPANIES.items():
        stocks = []
        total_weight = 0.0
        weighted_change = 0.0

        for c in companies:
            ticker_key = f"{c['code']}.T"
            change = change_map.get(ticker_key, None)
            price = change_map.get(ticker_key + "_price", 0)
            cap = c["cap"]

            stocks.append({
                "name": c["name"],
                "code": c["code"],
                "cap": cap,
                "change": change if change is not None else 0.0,
                "price": price,
                "realtime": change is not None,
            })

            if change is not None:
                total_weight += cap
                weighted_change += change * cap

        sector_value = round(weighted_change / total_weight, 2) if total_weight > 0 else 0.0
        result[sector_name] = {
            "value": sector_value,
            "stocks": sorted(stocks, key=lambda x: x["cap"], reverse=True),
            "realtime": total_weight > 0,
        }
    return result


def fetch_market_indices() -> dict:
    """市場指数を取得"""
    result: dict = {}
    for key, info in INDICES.items():
        try:
            hist = yf.Ticker(info["ticker"]).history(period="5d")
            if len(hist) >= 2:
                prev = float(hist["Close"].iloc[-2])
                curr = float(hist["Close"].iloc[-1])
                change = round((curr - prev) / prev * 100, 2)
                result[key] = {
                    "price": round(curr, 2),
                    "change": change,
                    "label": info["label"],
                }
        except Exception as e:
            print(f"指数取得エラー ({key}): {e}")
    return result


def fetch_rss_news() -> list:
    """RSS フィードからニュースを取得"""
    all_news: list = []
    for feed_url in NEWS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:15]:
                title = entry.get("title", "").strip()
                content = re.sub(r"<[^>]+>", "", entry.get("summary", entry.get("description", ""))).strip()
                published = entry.get("published", "")
                link = entry.get("link", "")
                source = feed.feed.get("title", "")

                if title:
                    all_news.append({
                        "title": title,
                        "content": content[:200],
                        "time": published,
                        "link": link,
                        "source": source,
                    })
        except Exception as e:
            print(f"ニュース取得エラー ({feed_url}): {e}")

    return all_news[:25]


# =============================================================================
# API エンドポイント
# =============================================================================
@app.route("/api/status")
def api_status():
    return jsonify({"status": "ok", "time": datetime.now().isoformat()})


@app.route("/api/stocks")
def api_stocks():
    try:
        change_map = get_cached("change_map", fetch_all_stocks)
        sector_data = build_sector_data(change_map)
        return jsonify({
            "status": "ok",
            "data": sector_data,
            "updated": datetime.now().isoformat(),
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/stocks/refresh")
def api_stocks_refresh():
    """キャッシュを無効化して再取得"""
    invalidate_cache("change_map")
    return api_stocks()


@app.route("/api/market")
def api_market():
    try:
        data = get_cached("market", fetch_market_indices)
        return jsonify({
            "status": "ok",
            "data": data,
            "updated": datetime.now().isoformat(),
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/news")
def api_news():
    try:
        data = get_cached("news", fetch_rss_news)
        return jsonify({
            "status": "ok",
            "data": data,
            "updated": datetime.now().isoformat(),
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    print("=" * 55)
    print("  セクター株価リアルタイムサーバー起動中")
    print("  URL: http://localhost:5000")
    print("  終了: Ctrl+C")
    print("=" * 55)
    app.run(host="0.0.0.0", port=5000, debug=False)
