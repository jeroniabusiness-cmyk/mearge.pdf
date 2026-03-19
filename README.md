# 🤖 Telegram PDF Bot

A powerful Telegram bot for PDF manipulation and conversion with Firebase backend.

## ✨ Features

- 📄 **Merge PDFs** - Combine multiple PDF files into one
- 🖼️ **Images to PDF** - Convert images to PDF format
- 🔄 **Convert PDF** - Convert PDF to images, DOCX, or TXT
- 💾 **Firebase Integration** - User data and operation tracking
- 📊 **Statistics** - Track your usage and operations
- 🔐 **Admin Panel** - Bot-wide statistics for administrators

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- Firebase Project with Firestore enabled

### Installation

1. **Create virtual environment**
```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On Mac/Linux:
source venv/bin/activate
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Setup Firebase**
   - Go to [Firebase Console](https://console.firebase.google.com/)
   - Create a new project
   - Enable Firestore Database
   - Go to Project Settings → Service Accounts
   - Click "Generate New Private Key"
   - Save the JSON file as `config/firebase-credentials.json`

4. **Configure environment**
```bash
copy .env.example .env
```

Edit `.env` file:
```env
BOT_TOKEN=your_bot_token_from_botfather
FIREBASE_CREDENTIALS_PATH=./config/firebase-credentials.json
```

5. **Run the bot**
```bash
python run.py
```

## 📁 Project Structure

```
telegram-pdf-bot/
├── bot/
│   ├── __init__.py
│   └── main.py              # Main bot application
├── handlers/
│   ├── __init__.py
│   └── basic_handlers.py    # Command handlers
├── utils/
│   ├── __init__.py
│   ├── logger.py            # Logging configuration
│   ├── file_handler.py      # File management
│   └── validators.py        # Input validation
├── database/
│   ├── __init__.py
│   ├── firebase_config.py   # Firebase initialization
│   ├── firebase_db.py       # Database operations
│   └── models.py            # Data models
├── config/
│   ├── settings.py          # App configuration
│   └── firebase-credentials.json  # Firebase key (not in git)
├── temp/                    # Temporary files (auto-created)
├── logs/                    # Log files (auto-created)
├── requirements.txt
├── .env
├── .env.example
├── .gitignore
├── run.py                   # Entry point
└── README.md
```

## 🎯 Usage

### For Users

1. Start the bot: `/start`
2. Get help: `/help`
3. View your stats: `/stats`
4. Cancel operation: `/cancel`
5. Clear session: `/clear`

### For Admins

- View bot statistics: `/adminstats`
- Add your user ID to `ADMIN_USER_IDS` in `.env`

## 🔧 Configuration

All configuration is in `.env` file:

| Variable | Description | Default |
|----------|-------------|---------|
| `BOT_TOKEN` | Telegram Bot Token | Required |
| `FIREBASE_CREDENTIALS_PATH` | Path to Firebase JSON | `./config/firebase-credentials.json` |
| `MAX_FILE_SIZE_MB` | Maximum file size in MB | 50 |
| `SESSION_TIMEOUT_MINUTES` | Session timeout | 30 |
| `MAX_FILES_PER_SESSION` | Max files per operation | 20 |
| `ADMIN_USER_IDS` | Comma-separated admin IDs | Empty |

## 📊 Firebase Structure

### Collections

**users** — Stores user profiles and stats  
**operations** — Tracks each bot operation  
**sessions** — Manages temporary user session state  

## 🐛 Troubleshooting

**Firebase Error:**
- Make sure `firebase-credentials.json` is in `config/` folder
- Check Firebase project settings
- Verify Firestore is enabled

**Bot Not Responding:**
- Check `BOT_TOKEN` is correct
- Verify internet connection
- Check `logs/` folder for errors

## 📝 Logs

Logs are stored in `logs/` folder:
- `bot_YYYYMMDD.log` - General logs
- `error_YYYYMMDD.log` - Error logs only

## 🔒 Security

- Never commit `.env` file
- Never commit `firebase-credentials.json`
- Keep your bot token private

## 📜 License

MIT License

---

**Phase 1 Complete!** ✅  
Next Phase: PDF Merging Functionality
