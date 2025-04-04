import re
import os
import openai
from collections import defaultdict

def parse_trade_type(message: str) -> str:
    msg = message.lower()

    mapping = {
        "long call spread": "Long Call Spread",
        "long put spread": "Long Put Spread",
        "short call spread": "Short Call Spread",
        "short put spread": "Short Put Spread",
        "long risk reversal": "Long Risk Reversal",
        "short risk reversal": "Short Risk Reversal",
        "long ratio spread": "Long Ratio Spread",
        "short ratio spread": "Short Ratio Spread",
        "long calendar spread": "Long Calendar Spread",
        "short calendar spread": "Short Calendar Spread",
        "long call": "Long Call",
        "long put": "Long Put",
        "short call": "Short Call",
        "short put": "Short Put",
    }

    for key, value in mapping.items():
        if key in msg:
            return value

    return "Unknown"

def extract_volume(message: str) -> float:
    match = re.search(r"\(([\d.]+)x\)", message)
    if match:
        return float(match.group(1))
    return 1.0

def detect_asset(message: str) -> str:
    msg = message.upper()
    if "BTC" in msg:
        return "BTC"
    elif "ETH" in msg:
        return "ETH"
    else:
        return "UNKNOWN"

def infer_sentiment(trade_type: str) -> dict:
    sentiment_map = {
        "Long Call": {
            "sentiment": "Bullish",
            "summary": "Bullish — trader expects significant upside."
        },
        "Long Put": {
            "sentiment": "Bearish",
            "summary": "Bearish — trader is protecting or speculating on downside."
        },
        "Long Call Spread": {
            "sentiment": "Bullish",
            "summary": "Moderately bullish — expecting limited upside move."
        },
        "Long Put Spread": {
            "sentiment": "Bearish",
            "summary": "Moderately bearish — expecting limited downside move."
        },
        "Short Call": {
            "sentiment": "Bearish or Neutral",
            "summary": "Bearish or neutral — trader is capping upside or collecting premium."
        },
        "Short Put": {
            "sentiment": "Bullish or Neutral",
            "summary": "Bullish or neutral — trader expects price to stay above strike."
        },
        "Short Call Spread": {
            "sentiment": "Bearish",
            "summary": "Bearish — trader expects asset to stay below a certain level."
        },
        "Short Put Spread": {
            "sentiment": "Bullish",
            "summary": "Bullish — trader expects asset to remain above a lower level."
        },
        "Short Risk Reversal": {
            "sentiment": "Bearish",
            "summary": "Bearish — selling calls, buying puts — protecting or speculating on downside."
        },
        "Long Risk Reversal": {
            "sentiment": "Bullish",
            "summary": "Bullish — buying calls, selling puts — speculating on upside."
        },
        "Long Ratio Spread": {
            "sentiment": "Bullish with caution",
            "summary": "Bullish with a hedge — wants upside but expects some cap or volatility."
        },
        "Short Ratio Spread": {
            "sentiment": "Bearish with caution",
            "summary": "Bearish with a hedge — selling upside while managing tail risk."
        },
        "Long Calendar Spread": {
            "sentiment": "Neutral to Slightly Bullish",
            "summary": "Trader expects low near-term volatility but potential longer-term move."
        },
        "Short Calendar Spread": {
            "sentiment": "Neutral to Slightly Bearish",
            "summary": "Trader expects near-term volatility and is selling long-dated premium."
        },
    }

    return sentiment_map.get(trade_type, {
        "sentiment": "Unknown",
        "summary": "Could not determine sentiment."
    })

def analyze_trade(message: str) -> dict | None:
    trade_type = parse_trade_type(message)
    if trade_type == "Unknown":
        return None

    sentiment_info = infer_sentiment(trade_type)
    volume = extract_volume(message)
    asset = detect_asset(message)

    return {
        "original_message": message,
        "asset": asset,
        "trade_type": trade_type,
        "sentiment": sentiment_info["sentiment"],
        "summary": sentiment_info["summary"],
        "volume": volume
    }

def summarize_sentiment(trades: list[dict]) -> dict:
    sentiment_totals = defaultdict(float)
    sentiment_examples = defaultdict(list)

    for trade in trades:
        sentiment = trade["sentiment"]
        volume = trade["volume"]
        sentiment_totals[sentiment] += volume
        sentiment_examples[sentiment].append(trade)

    return {
        "volume_by_sentiment": dict(sentiment_totals),
        "examples": sentiment_examples
    }

def generate_summary(sentiment_data: dict) -> str:
    summary = []
    totals = sentiment_data["volume_by_sentiment"]

    if not totals:
        return "No significant trades found."

    sorted_sentiments = sorted(totals.items(), key=lambda x: -x[1])
    for sentiment, volume in sorted_sentiments:
        summary.append(f"→ {sentiment.upper()} sentiment dominated with {volume:.1f}x total volume")

    top_examples = []
    for sentiment, trades in sentiment_data["examples"].items():
        top = sorted(trades, key=lambda x: -x["volume"])[:1]
        for trade in top:
            top_examples.append(f"Top {sentiment.lower()} trade: {trade['original_message']}")

    return "\n".join(summary + [""] + top_examples)

def gpt_asset_summary(asset: str, trades: list[dict]) -> str:
    openai.api_key = os.getenv("OPENAI_API_KEY")

    trade_descriptions = [
        f"- {t['trade_type']} ({t['volume']}x)" for t in sorted(trades, key=lambda x: -x["volume"])
    ]
    trade_list_text = "\n".join(trade_descriptions)

    prompt = f"""
Here are the most significant trades in {asset} over the past 24 hours:

{trade_list_text}

Please summarize the overall market sentiment for {asset} based on these trades. Be specific about why, referencing strategies (e.g., call selling, put spread buying) and volumes where relevant.
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"[GPT Error: {e}]"
