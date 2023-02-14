import os, json
from dotenv import load_dotenv, find_dotenv
import discord
from discord.ext import commands, tasks
import logging
import binance
from discord import Member
from discord.ext.commands import has_permissions, MissingPermissions
from binance import Client, ThreadedWebsocketManager, ThreadedDepthCacheManager

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename = 'discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(name)s:&(message)s'))
logger.addHandler(handler)


load_dotenv(find_dotenv())
token = os.getenv("DISCORD_TOKEN")
channel_id = os.getenv('CHANNEL_ID')
binance_api_key = os.getenv('BINANCE_API_KEY')
binance_api_secret = os.getenv('BINANCE_API_SECRET')

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents, command_prefix='..')

binanceClient = Client(binance_api_key, binance_api_secret)

FAV_LIST = {}
with open('FAV_LIST.json') as f:
  FAV_LIST = json.load(f)

def get_future_position(symbol):
  position = None
  positions = list(filter(lambda f:(f['symbol']==symbol), binanceClient.futures_account()['positions']))
  if positions:
    position = positions[0]
  return position

@client.event
async def on_ready():
  print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.content.startswith('hello'):
      await message.channel.send('Hello!')

@commands.command()
async def add_fav(ctx, account, symbol):
    FUT_SYMBOLS = [sym['symbol'] for sym in binanceClient.futures_exchange_info()['symbols']]
    SPOT_SYMBOLS = [sym['symbol'] for sym in binanceClient.get_all_tickers()]
    if account.upper() == "FUT":
        if symbol in FUT_SYMBOLS:
            FAV_LIST['FUTURES'][symbol] = {}
        else:
            await ctx.send("Provided SYMBOL or CRYPTO is not available in Futures")
    elif account.upper() == "SPOT":
        if symbol in SPOT_SYMBOLS:
            FAV_LIST['SPOT'][symbol] = {}
        else:
            await ctx.send("Provided SYMBOL or CRYPTO is not available in SPOT")
    else:
        await ctx.send('Provided Account Type is not valid. Please use FUT for Futures and SPOT for spot')
    with open('FAV_LIST.json','w') as f:
        json.dump(FAV_LIST, f)


@commands.command()
async def favs(ctx):
    message = "FUTURES FAVOURITE LIST\n"
    for i, symbol in enumerate(FAV_LIST['FUTURES'].keys()):
        message += str(i+1) + ". " + symbol + "--> Last Price: "+ binanceClient.get_ticker(symbol=symbol)['lastPrice']+"\n"
    message += "\n\nSPOT FAVOURITE LIST"
    for i, symbol in enumerate(FAV_LIST['SPOT'].keys()):
        message += str(i+1) + ". " + symbol + "--> Last Price: "+ binanceClient.get_ticker(symbol=symbol)['lastPrice']+ "\n"
    await ctx.send(message)
    
@commands.command()
async def fubln(ctx):
    balance_list = binanceClient.futures_account_balance()
    message = "-"*35 + "\n"
    message += "-"*3 + "ACCOUNT BALANCE" + "-"*3 + "\n"
    message += "-"*35 +"\n"
    for balance in balance_list:
        message += balance['asset']+" : "+balance['balance']+"\n"
    message += "-"*35
    await ctx.send(message)

@tasks.loop(seconds=60)
async def futures_position_alerts():
    futures_info = binanceClient.futures_account()
    positions_info = binanceClient.futures_position_information()
    positions = futures_info['positions']
    message_channel = await client.fetch_channel(channel_id)
    print(f"Got channel {message_channel} for {channel_id}")
    if float(futures_info['totalMaintMargin'])/float(futures_info['totalMarginBalance']) > 40.0:
        await message_channel.send("Your positions' Margin Ratio is greater than 40%. Please consider taking a look at it.")
    for position in positions:
        symbol = position['symbol']
        alert = False
        message = "------"+symbol+" POSITION ALERT!------\n"
        position_info = list(filter(lambda f:(f['symbol']==symbol),positions_info))[0]
        if float(position_info['positionAmt']) != 0.0:
            if float(position['unrealizedProfit']) < -1.0 :
                message += "Unrealized Profit is going down! LOSS : "+ str(position['unrealizedProfit']) +"\n"
                alert = True
            if (float(position_info['markPrice'])-float(position_info['liquidationPrice']))/(float(position_info['entryPrice'])-float(position_info['liquidationPrice'])) <= 0.4:
                message += "Mark price is moving closer to Liquidation Price. Your position may be liquidated soon.\n Mark Price:"+ str(position_info['markPrice']) +"\n Liquidation Price:"+str(position_info['liquidationPrice'])+"\n"
                alert = True
        if alert:
            await message_channel.send(message)

@futures_position_alerts.before_loop
async def before():
    await client.wait_until_ready()
    print("Finished waiting")

futures_position_alerts.start()

#@tasks.loop(seconds=60)
#async def favs_info():
#    message = "INFO of Favourite Crytos\n\n"
#    message += "FUTURES\n"
#    for i, symbol in enumerate(FAV_LIST['FUTURES'].keys()):
#        position = get_future_position(symbol)
#        message += str(i)+". "+position['symbol']+" --> unrealizedProfit : "+position['unrealizedProfit']
#    message_channel = await client.fetch_channel(channel_id)
#    print(f"Got channel {message_channel} for {channel_id}")
#    await message_channel.send(message)

#@favs_info.before_loop
#async def before():
#    await client.wait_until_ready()
#    print("Finished waiting")

#favs_info.start()

# MODERATION COMMANDS #        
@commands.command()
@has_permissions(kick_members=True, administrator=True)
async def kick(ctx, member:discord.Member,*,reason=None):
  guild = ctx.guild
  memberKick = discord.Embed(title='Kicked', description = f'You have been kicked from {guild.name} for {reason}')
  
  await member.kick(reason=reason)
  await ctx.send(f'User {member} has been kicked.')
  
@commands.command()
@has_permissions(ban_members=True, administrator=True)
async def ban(ctx, member:discord.Member,*,reason=None,):
  guild = ctx.guild
  memberBan = discord.Embed(title = 'Banned', description=f'You were banned from {guild.name} for {reason}')
  
  await member.ban(reason=reason)
  await ctx.send(f'User {member} has been banned.')
  await member.send(embed=memberBan)
  
@commands.command()
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

@commands.command(pass_context=True)
@has_permissions(manage_messages=True)
async def mute(ctx,member:discord.Member, reason = None):
  guild = ctx.guild
  mutedRole = discord.utils.get(guild.roles, name='Muted')
  memberMute = discord.Embed(title = 'Muted', description=f'You have been muted from {guild.name} for {reason}')
  if mutedRole not in guild.roles:
    perms = discord.Permissions(send_messages=False, speak=False)
    await guild.create_role(name='Muted', permissions=perms)
    await member.add_roles(mutedRole)
    await ctx.send('Succesfuly created the [Muted] role and properly assigned it to the user.')
  await ctx.add_role(member, mutedRole)
  embed=discord.Embed(title='User muted!', description=f'**{0}** was muted by **{1}**!'.format(member, ctx.message.author, color=0xff00f6))
  
@commands.command(pass_context=True)
@has_permissions(manage_messages=True)
async def unmute(ctx, member:discord.Member, *, reason=None):
  guild = ctx.guild
  mutedRole = discord.utils.get(guild.roles, name = 'Muted')
  
  memberUnmute = discord.Embed(title = 'Unmuted', description = f'You were unmuted from {guild.name} for {reason}')
  
  await member.remove_roles(mutedRole)
  await ctx.send(f'Unmuted {member.mention} for {reason}')
  await member.send(embed=memberUnmute)

client.run(token)
