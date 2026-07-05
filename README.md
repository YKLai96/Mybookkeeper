# 🧾 AI Telegram Bookkeeper (Enterprise MVP)

![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)
![Telegram Bot API](https://img.shields.io/badge/Telegram-Bot-blue?logo=telegram)
![Google Gemini](https://img.shields.io/badge/AI-Gemini%201.5%20Flash-orange)
![License](https://img.shields.io/badge/license-MIT-green)

An automated, AI-powered Telegram bot for seamless receipt recognition and financial bookkeeping. Designed for small teams and startups to upload receipts via Telegram, automatically extract financial data using **Google Gemini 1.5**, and sync the structured records directly to **Google Sheets** while archiving the receipt images to **Google Drive**.

## ✨ Core Features

* **🤖 AI-Powered OCR & Parsing:** Utilizes Gemini 1.5 Flash to accurately extract Vendor, Tax, Amount, Date, and Category from messy receipt images.
* **📱 Telegram Bot Interface:** Simple, conversational UI for users to upload receipts and approve/edit extracted data via inline keyboards.
* **☁️ Google Ecosystem Integration:**
  * Syncs transaction data directly to Google Sheets as a database.
  * Uploads receipt images to Google Drive for audit compliance and zero-cost object storage.
* **⚡ Asynchronous Architecture:** Non-blocking operations (via `asyncio` threads) ensure smooth multi-user interactions without freezing the bot's event loop.
* **💰 Zero-Cost Setup:** Built entirely on free-tier tools (Telegram API, Google Workspace APIs, Gemini API, local SQLite caching).

---

## 🏗️ System Architecture Flow

```text
User (Telegram) 
  │
  ├─[Upload Photo]─> Telegram Bot (Async) 
                       │
                       ├─> 1. Cache locally via SQLite (WAL mode)
                       ├─> 2. Extract Data via Google Gemini 1.5 Flash
                       │
  ├─[Confirm/Edit] <─> UI Inline Keyboard
  │
  ├─[Submit] ──────> Background Threads (asyncio.to_thread)
                       ├─> 3. Upload image to Google Drive
                       ├─> 4. Append record & Drive URL to Google Sheets
                       └─> 5. Cleanup local temp files
```


## 🚀 Quick Start
### 1. Prerequisites

Before you begin, ensure you have the following:
A Telegram Bot Token (Get it from @BotFather)
A Google Gemini API Key (From Google AI Studio)
Google Cloud Console configured with Google Drive API and Google Sheets API enabled.
Downloaded OAuth 2.0 Client ID JSON file (rename it to credentials.json).


### 2. Installation

Clone the repository to your local machine or server:
```text
git clone https://github.com/YOUR_GITHUB_USERNAME/Mybookkeeper.git
cd Mybookkeeper
```

Install the required Python dependencies (Virtual environment recommended):
```text
pip install python-telegram-bot google-generativeai gspread google-api-python-client google-auth-httplib2 google-auth-oauthlib dotenv backoff
```


### 3. Configuration

Create a .env file in the root directory and add your secret credentials:

```text
TELEGRAM_TOKEN=your_telegram_bot_token_here
GEMINI_API_KEY=your_gemini_api_key_here
SPREADSHEET_NAME=your_google_sheet_name_here
```
⚠️ SECURITY WARNING: Never commit your .env, credentials.json, or token.json to GitHub! Ensure they are listed in your .gitignore.


### 4. Run the Application
Start the bot engine:
```text
python run.py
```
Note: On the very first run, a browser window will open asking you to log into your Google Account to authorize the application. This will generate a token.json file for future automated authentications.


## 📝 Logging & Monitoring
The application includes a built-in DevSecOps daemon that rotates logs automatically. Check the logs/system.log file to monitor API latencies, AI parsing errors, or system health.

## 📄 License
This project is licensed under the MIT License - see the LICENSE file for details.
