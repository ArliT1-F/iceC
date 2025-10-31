# iceC Discord Bot

A feature-rich Discord bot built with Python, featuring music playback, cryptocurrency trading alerts, and moderation tools

## Features

### Music Bot Features
- **Youtube Music Playback** - Play songs from YouTube in voice channels
- **Spotify Playlist Support** - Play entire Spotify playlists
- **Queue Management** - Add, remove, shuffle, and manage song queues
- **Playback Controls** - Play, pause, resume, skip, seek, and volume control
- **Loop Functions** - Loop single songs or entire queues
- **Now Playing** - View current track information and requester

### Trading Features (Binance Integration)
- **Position Alerts** - Automated alerts for futures positions
- **Margin Ratio Monitoring** - Get notified when margin ratios exceed thresholds
- **Favorite List** - Track favorite cryptocurrencies for SPOT and FUTURES
- **Account Balance** - View futures account balance

### Moderation Features
- **User Management** - Kick, ban, unban, mute, and unmute users
- **Role Management** - Assign roles to users
- **Permission-based Commands** - Role-based access control


## Prequesites

- Python 3.8 or higher
- Discord Bot Token ([Get one here](https://discord.com/developers/applications))
- Binance API Key and Secret (for trading features - optional)
- Spotify Client ID and Secret (for Spotify features - optional)
- A Lavalink server (for music features)

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/ArliT1-F/iceC.git
cd iceC
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Setup

Create a `.env` file in the root directory with the following variables:

```env
 Discord Bot Configuration
DISCORD_TOKEN=your_discord_bot_token_here
CHANNEL_ID=your_channel_id_here

# Binance API (Optional - for trading features)
BINANCE_API_KEY=your_binance_api_key
BINANCE_API_SECRET=your_binance_api_secret

# Spotify API (Optional - for Spotify playlist support)
spotify_id=your_spotify_client_id
spotify_secret=your_spotify_client_secret

# Lavalink Server (Required for music features)
LAVALINK_HOST=node1.kartadharta.xyz
LAVALINK_PORT=443
LAVALINK_PASSWORD=your_lavalink_password_here
```

### 4. Configuration Files

Ensure `FAV_LIST.json` exists with the following structure:
```json
{
    "FUTURES": {},
    "SPOT": {}
}
```

## Usage

### Starting the Bot

```bash
python main.py
```

The bot will connect to Discord and be ready to use once you see the "We have logged in as..." message.

### Command Prefix

The bot uses `!` as the default command prefix.

## Commands

### Music Commands

| Command | Aliases | Description | Example |
|---------|---------|-------------|---------|
| `!play` | `!p` | Play a song from YouTube | `!play never gonna give you up` |
| `!splay` | `!sp` | Play a Spotify playlist | `!sp https://open.spotify.com/playlist/...` |
| `!pause` | `!stop` | Pause the current track | `!pause` |
| `!resume` | - | Resume the paused track | `!resume` |
| `!skip` | `!next`, `!s` | Skip to the next track | `!skip` |
| `!nowplaying` | `!np` | Show current track information | `!np` |
| `!queue` | `!q`, `!track` | Display the current queue | `!queue` |
| `!loop` | - | Loop/unloop the current song | `!loop` |
| `!loopqueue` | `!lq` | Enable/disable queue looping | `!lq start` |
| `!volume` | `!vol` | Set the player volume (0-100) | `!vol 50` |
| `!seek` | - | Seek to position in track (seconds) | `!seek 120` |
| `!shuffle` | `!mix` | Shuffle the queue | `!shuffle` |
| `!del` | `!remove`, `!drop` | Delete a track from queue | `!del 3` |
| `!skipto` | `!goto` | Skip to a specific track in queue | `!skipto 5` |
| `!move` | `!set` | Move a track to a different position | `!move 2 5` |
| `!clear` | - | Clear the entire queue | `!clear` |
| `!disconnect` | `!dc`, `!leave` | Disconnect from voice channel | `!dc` |
| `!save` | `!dm` | DM current song or queue | `!save` or `!save queue` |

### Trading Commands

| Command | Description | Example |
|---------|-------------|---------|
| `!add_fav` | Add a symbol to favorites | `!add_fav FUT BTCUSDT` |
| `!favs` | List favorite cryptocurrencies | `!favs` |
| `!fubln` | Show futures account balance | `!fubln` |

### Moderation Commands

| Command | Description | Permissions Required |
|---------|-------------|---------------------|
| `!kick` | Kick a user from the server | Administrator, Kick Members |
| `!ban` | Ban a user from the server | Administrator, Ban Members |
| `!unban` | Unban a user | Administrator, Ban Members |
| `!mute` | Mute a user | Manage Messages |
| `!unmute` | Unmute a user | Manage Messages |
| `!setrole` | Assign a role to a user | Administrator |

### Utility Commands

| Command | Aliases | Description |
|---------|---------|-------------|
| `!ping` | - | Check bot latency |
| `!info` | `!i` | Show bot information (Owner only) |

## Configuration

### Lavalink Server

The bot connects to a Lavaling server for music playback. By default, it uses:

- Host: `node1.kartadharta.xyz`
- Port: `443`
- Protocol: `HTTPS`

You can modify the connection in the `node_connect()` function in `main.py`.

### Required Intents

Ensure your bot has the following intents enabled in the Discord Developer Portal:
- ✅ Server Members Intent
- ✅ Message Content Intent
- ✅ Voice States Intent
- ✅ Emojis and Stickers Intent

## 📁 Project Structure
```
iceC/
├── main.py              # Main bot file
├── requirements.txt     # Python dependencies
├── FAV_LIST.json       # Trading favorites list
├── .env                # Environment variables (create this)
├── discord.log         # Bot logs (created automatically)
├── LICENSE             # GNU GPL v3 License
└── README.md          # This file
```

## Troubleshooting

### Bot Commands Not Working
- Ensure you're using `commands.Bot()` (already fixed in code)
- Check that the bot has proper permissions in your server
- Verify the command prefix is correct (`!` by default)

### Music Not Playing
- Ensure you have a Lavalink server running and accessible
- Check that the bot has permission to join voice channels
- Verify the node connection in `node_connect()`

### Trading Features Not Working
- Ensure Binance API keys are correctly set in `.env`
- Check that API keys have necessary permissions (read-only recommended)
- Verify `FAV_LIST.json` exists and has correct structure

### Permission Errors
- Ensure the bot has necessary roles/permissions:
  - Send Messages
  - Connect to Voice Channels
  - Speak in Voice Channels
  - Manage Roles (for moderation commands)

## 🔐 Security Notes

- **Never commit your `.env` file** - It contains sensitive tokens
- Use read-only API keys when possible
- Regularly rotate your Discord bot token
- Keep dependencies updated for security patches

## 📝 Environment Variables

All required environment variables:

| Variable | Required | Description |
|----------|----------|-------------|
| `DISCORD_TOKEN` | ✅ Yes | Your Discord bot token |
| `CHANNEL_ID` | ✅ Yes | Channel ID for alerts |
| `LAVALINK_PASSWORD` | ✅ Yes* | Password for Lavalink server (required for music) |
| `LAVALINK_HOST` | ❌ Optional | Lavalink server host (default: node1.kartadharta.xyz) |
| `LAVALINK_PORT` | ❌ Optional | Lavalink server port (default: 443) |
| `BINANCE_API_KEY` | ❌ Optional | Binance API key for trading |
| `BINANCE_API_SECRET` | ❌ Optional | Binance API secret |
| `spotify_id` | ❌ Optional | Spotify client ID |
| `spotify_secret` | ❌ Optional | Spotify client secret |

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- **Repository**: [GitHub - ArliT1-F/iceC](https://github.com/ArliT1-F/iceC)
- **Discord Developer Portal**: [discord.com/developers](https://discord.com/developers)
- **Binance API**: [binance.com/api](https://binance.com/api)
- **Wavelink Documentation**: [wavelink.readthedocs.io](https://wavelink.readthedocs.io/)

## ⚠️ Disclaimer

- This bot is for educational purposes
- Trading features involve financial risks - use at your own discretion
- Ensure compliance with Discord's Terms of Service
- Respect copyright when using music features

## 📞 Support

If you encounter any issues or have questions:
1. Check the [Troubleshooting](#-troubleshooting) section
2. Review the code comments and documentation
3. Open an issue on GitHub

---

**Made with ❤️ by the iceC development team**

*Last updated: 2024*