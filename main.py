import discord
from discord.ext import commands

import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
  print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')

client.run('NzY5NTUzNDcwNjAwMTE4Mjgz.GVK2B6._SIutMAnPTtlUB4iiDoJOgl01AmwRshYFhhyy4')
