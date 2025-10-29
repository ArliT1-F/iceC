"""
iceC Discord Bot - Main File
A feature-rich Discord bot with music, trading, and moderation features
"""
import os
import json
from dotenv import load_dotenv, find_dotenv
import discord
from discord.ext import commands
import logging
import numpy as np
import nextcord
import wavelink
from wavelink.ext import spotify

# Setup logging
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(name)s:%(message)s'))
logger.addHandler(handler)

# Load environment variables
load_dotenv(find_dotenv())
token = os.getenv("DISCORD_TOKEN")

# Setup Discord intents
intents = discord.Intents.default()
intents.guild_messages = True
intents.members = True
intents.message_content = True
intents.voice_states = True
intents.emojis_and_stickers = True

# Create bot instance
bot = commands.Bot(command_prefix='!', intents=intents, case_insensitive=True)
client = bot  # Alias for backwards compatibility

# Initialize bot attributes
bot.user_dict = {}
bot.user_arr = np.array([])
bot.embed_color = nextcord.Color.from_rgb(128, 67, 255)
bot.qem = None  # For storing queue embed

# Setup Wavelink Player attribute
setattr(wavelink.Player, 'lq', False)


async def node_connect():
    """Connect to Lavalink node for music playback"""
    await bot.wait_until_ready()
    try:
        await wavelink.NodePool.create_node(
            client=bot,
            host='node1.kartadharta.xyz',
            port=443,
            password="kdlavalink",
            https=True,
            spotify_client=spotify.SpotifyClient(
                client_id=os.environ.get('spotify_id'),
                client_secret=os.environ.get('spotify_secret')
            )
        )
    except Exception as e:
        logger.error(f"Failed to connect to Lavalink node: {e}")


@bot.event
async def on_ready():
    """Event fired when bot is ready"""
    print(f'We have logged in as {bot.user}')
    print(f'Bot is in {len(bot.guilds)} guilds')
    
    # Connect to Lavalink
    await node_connect()
    
    print('Bot is ready!')


@bot.event
async def on_command_error(ctx: commands.Context, error):
    """Global error handler for commands"""
    if isinstance(error, commands.CommandOnCooldown):
        em = nextcord.Embed(
            description=f'**Cooldown active**\ntry again in `{error.retry_after:.2f}`s*',
            color=bot.embed_color
        )
        await ctx.send(embed=em)
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(embed=nextcord.Embed(description="Missing `arguments`", color=bot.embed_color))
    elif isinstance(error, commands.CommandNotFound):
        pass  # Ignore unknown commands
    else:
        logger.error(f"Unhandled command error: {error}")


async def load_cogs():
    """Load all cogs"""
    try:
        await bot.load_extension('cogs.music')
        print('✓ Loaded music cog')
    except Exception as e:
        print(f'✗ Failed to load music cog: {e}')
    
    try:
        await bot.load_extension('cogs.trading')
        print('✓ Loaded trading cog')
    except Exception as e:
        print(f'✗ Failed to load trading cog: {e}')
    
    try:
        await bot.load_extension('cogs.moderation')
        print('✓ Loaded moderation cog')
    except Exception as e:
        print(f'✗ Failed to load moderation cog: {e}')
    
    try:
        await bot.load_extension('cogs.utility')
        print('✓ Loaded utility cog')
    except Exception as e:
        print(f'✗ Failed to load utility cog: {e}')

# Run the bot
async def main():
    """Main function to start the bot"""
    if not token:
        print("ERROR: DISCORD_TOKEN not found in environment variables!")
        print("Please create a .env file with your Discord bot token.")
        return
    
    # Load all cogs before starting
    async with bot:
        await load_cogs()
        await bot.start(token)


if __name__ == '__main__':
    try:
        import asyncio
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"Failed to start bot: {e}")
