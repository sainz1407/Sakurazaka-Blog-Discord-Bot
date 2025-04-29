# Sakurazaka-Blog-Discord-Bot
Automatically monitors Sakurazaka46 official blog and posts newly published images to Discord channels based on the blog author (member)

---

## ⚙️ Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/sakurazaka-discord-bot.git
cd sakurazaka-discord-bot
```

### 2. Install Dependencies

Make sure you have **Python 3.10+**, then install the required packages:

```bash
pip install -r requirements.txt
```

### 3. Configure `.env`

Create a `.env` file in the root folder:

```
BOT_TOKEN=YOUR_DISCORD_BOT_TOKEN
DEFAULT_CHANNEL_ID=123456789012345678

# Member → Channel ID mapping
CHANNEL_山下_瞳月=111111111111111111
CHANNEL_田村_保乃=222222222222222222
CHANNEL_森田_ひかる=333333333333333333
# Add all other members here...
```

> Format: Use underscores (`_`) in place of spaces. The bot will automatically detect and route posts to the appropriate channel.

---

## 🚀 Run the Bot

```bash
python bot_module.py
```

---

## 🤖 Discord Commands

| Command | Description          |
|---------|----------------------|
| `!ping` | Replies with bot latency |
| `!status` | Show bot status |
| `!channels` | Displays configured channel info for each member |
---
