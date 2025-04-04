# Telegram Trade Sentiment Analyzer

📊 A Python tool that reads crypto options trades from the Signal Plus Telegram channel, classifies them by type and sentiment, weights them by volume, and generates a summary — with GPT-powered explanations.

---

## 🔧 Features

- 📥 Fetches trades from any Telegram channel using `Telethon`
- 🔍 Detects trade types (e.g., `Short Call`, `Long Put Spread`)
- 📊 Weights trades by size (e.g., `313.0x`)
- 🧠 Summarizes sentiment using GPT-4 (optional)
- 📁 Groups trades by asset (`BTC`, `ETH`)
- 🛡️ Skips non-trade messages (e.g., charts, tables)

