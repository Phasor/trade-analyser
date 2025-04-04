import os
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telethon.sync import TelegramClient
from collections import defaultdict
from trade_sentiment import (
    analyze_trade,
    summarize_sentiment,
    generate_summary,
    gpt_asset_summary
)

# Load environment variables
load_dotenv()
api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
channel = os.getenv("CHANNEL")

client = TelegramClient('session', api_id, api_hash)

async def fetch_messages(limit=500, hours_back=24):
    await client.start()
    entity = await client.get_entity(channel)
    cutoff = datetime.utcnow() - timedelta(hours=hours_back)

    messages = []
    async for msg in client.iter_messages(entity, limit=limit):
        if not msg.message:
            continue
        if msg.date < cutoff:
            break
        if "BTC" in msg.message.upper() or "ETH" in msg.message.upper():
            messages.append(msg.message)

    return messages

if __name__ == "__main__":
    HOURS_BACK = 24  # Adjust this to control lookback period
    msgs = asyncio.run(fetch_messages(limit=500, hours_back=HOURS_BACK))

    analyzed = []
    skipped = 0

    for m in msgs:
        result = analyze_trade(m)
        if result:
            analyzed.append(result)
        else:
            skipped += 1

    trades_by_asset = defaultdict(list)
    for trade in analyzed:
        trades_by_asset[trade["asset"]].append(trade)

    print(f"\n🔍 Sentiment Summary (Last {HOURS_BACK}h):\n")
    print(f"📭 Skipped {skipped} non-trade messages.")

    for asset, trades in trades_by_asset.items():
        if not trades:
            continue
        print(f"\n📊 Asset: {asset}")
        sentiment_data = summarize_sentiment(trades)
        summary = generate_summary(sentiment_data)
        gpt_summary = gpt_asset_summary(asset, trades)

        print(summary)
        print("\n🧠 GPT Sentiment Insight:\n" + gpt_summary)
