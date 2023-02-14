##These dont work as of right now since im too stupid to fix the .env token hiding. I'll try to fix it later
#import os
#from dotenv import load_dotenv, find_dotenv
import discord
from discord.ext import commands
from discord import Member
from discord.ext.commands import has_permissions, MissingPermissions
#load_dotenv(find_dotenv())
#TOKEN = os.getenv("DISCORD_TOKEN")

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
    if message.content.startswith('hello'):
      await message.channel.send('Hello!')

# MODERATION COMMANDS #        
@client.command()
@has_permissions(kick_members=True, administrator=True)
async def kick(ctx, member:discord.Member,*,reason=None):
  await member.kick(reason=reason)
  await ctx.send(f'User {member} has been kicked.')
  
@client.command()
@has_permissions(ban_members=True, administrator=True)
async def ban(ctx, member:discord.Member,*,reason=None,):
  await member.ban(reason=reason)
  await ctx.send(f'User {member} has been banned.')
  
@client.command(pass_context=True)
@has_permissions(manage_roles=True, kick_members=True, administrator=True)
async def mute(ctx,member:discord.Member):
  role = discord.utils.get(member.server.roles, name='Muted')
  await ctx.add_roles(member, role)
  embed=discord.Embed(title='User muted!', description=f'**{0}** was muted by **{1}**!'.format(member, ctx.message.author, color=0xff00f6))

client.run('NzY5NTUzNDcwNjAwMTE4Mjgz.GVK2B6._SIutMAnPTtlUB4iiDoJOgl01AmwRshYFhhyy4')
