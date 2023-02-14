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
guild = ctx.guild
member = member:discord.Member
client = discord.Client(intents=intents, command_prefix='..')

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
  memberKick = discord.Embed(title='Kicked', description = f'You have been kicked from {guild.name} for {reason}')
  
  await member.kick(reason=reason)
  await ctx.send(f'User {member} has been kicked.')
  
@client.command()
@has_permissions(ban_members=True, administrator=True)
async def ban(ctx, member:discord.Member,*,reason=None,):
  memberBan = discord.Embed(title = 'Banned', description=f'You were banned from {guild.name} for {reason}')
  
  await member.ban(reason=reason)
  await ctx.send(f'User {member} has been banned.')
  await member.send(embed=memberBan)
  
@client.command()
@has_permissions(ban_members=True, administrator=True)
async def unban(self, ctx, *, member:discord.Member):
  banned_users = await ctx.guild.bans()
  member_name, member_discriminator = member.split('#')
  
  for ban_entry in banned_users:
    user = ban_entry.user
    
    if (user.name, user.discriminator) == (member_name, member_discriminator):
      await ctx.guild.unban(user)
      await ctx.send(f'{user.name}#{user.discriminator} has been unbanned.')
      return

@client.command(pass_context=True)
@has_permissions(manage_messages=True)
async def mute(ctx,member, *, reason = None):
  mutedRole = discord.utils.get(guild.roles, name='Muted')
  memberMute = discord.Embed(title = 'Muted', description=f'You have been muted from {guild.name} for {reason}')
  if role not in guild.roles:
    perms = discord.Permissions(send_messages=False, speak=False)
    await guild.create_role(name='Muted', permissions=perms)
    await member.add_roles(mutedRole)
    await ctx.send('Succesfuly created the [Muted] role and properly assigned it to the user.')
    await member.send(embed=memberMute)
  await ctx.add_roles(member, role)
  embed=discord.Embed(title='User muted!', description=f'**{0}** was muted by **{1}**!'.format(member, ctx.message.author, color=0xff00f6))
  
@client.command(pass_context=True)
@has_permissions(manage_messages=True)
async def unmute(ctx, member, *, reason=None):
  mutedRole = discord.utils.get(guild.roles, name = 'Muted')
  
  memberUnmute = discord.Embed(title = 'Unmuted', description = f'You were unmuted from {guild.name} for {reason}')
  
  await member.remove_roles(mutedRole)
  await ctx.send(f'Unmuted {member.mention} for {reason}')
  await member.send(embed=memberUnmute)

client.run('NzY5NTUzNDcwNjAwMTE4Mjgz.GVK2B6._SIutMAnPTtlUB4iiDoJOgl01AmwRshYFhhyy4')

