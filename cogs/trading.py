"""
Trading cog for iceC Discord Bot
Handles Binance trading features including favorites and position alerts
"""
import os
import json
from discord.ext import commands, tasks
from binance import Client


class Trading(commands.Cog):
    """Binance trading features and commands"""

    def __init__(self, bot):
        self.bot = bot
        self.binance_client = None
        self.channel_id = None
        self.fav_list = {}
        self._initialize_binance()

    def _initialize_binance(self):
        """Initialize Binance client and load favorites"""
        binance_api_key = os.getenv('BINANCE_API_KEY')
        binance_api_secret = os.getenv('BINANCE_API_SECRET')
        self.channel_id = os.getenv('CHANNEL_ID')
        
        if binance_api_key and binance_api_secret:
            try:
                self.binance_client = Client(binance_api_key, binance_api_secret)
                # Load favorites list
                try:
                    with open('FAV_LIST.json') as f:
                        self.fav_list = json.load(f)
                except FileNotFoundError:
                    self.fav_list = {"FUTURES": {}, "SPOT": {}}
            except Exception as e:
                print(f"Failed to initialize Binance client: {e}")
                self.binance_client = None

    def get_future_position(self, symbol):
        """Get future position for a symbol"""
        if not self.binance_client:
            return None
        try:
            position = None
            positions = list(filter(lambda f: (f['symbol'] == symbol), self.binance_client.futures_account()['positions']))
            if positions:
                position = positions[0]
            return position
        except Exception as e:
            print(f"Error getting future position: {e}")
            return None

    @commands.command()
    async def add_fav(self, ctx, account, symbol):
        """Add a symbol to favorites list"""
        if not self.binance_client:
            return await ctx.send("Binance API not configured. Please set BINANCE_API_KEY and BINANCE_API_SECRET in .env")
        
        try:
            FUT_SYMBOLS = [sym['symbol'] for sym in self.binance_client.futures_exchange_info()['symbols']]
            SPOT_SYMBOLS = [sym['symbol'] for sym in self.binance_client.get_all_tickers()]
            
            if account.upper() == "FUT":
                if symbol in FUT_SYMBOLS:
                    self.fav_list['FUTURES'][symbol] = {}
                    await ctx.send(f"Added {symbol} to FUTURES favorites")
                else:
                    await ctx.send("Provided SYMBOL or CRYPTO is not available in Futures")
            elif account.upper() == "SPOT":
                if symbol in SPOT_SYMBOLS:
                    self.fav_list['SPOT'][symbol] = {}
                    await ctx.send(f"Added {symbol} to SPOT favorites")
                else:
                    await ctx.send("Provided SYMBOL or CRYPTO is not available in SPOT")
            else:
                await ctx.send('Provided Account Type is not valid. Please use FUT for Futures and SPOT for spot')
            
            # Save favorites
            with open('FAV_LIST.json', 'w') as f:
                json.dump(self.fav_list, f)
        except Exception as e:
            await ctx.send(f"Error adding favorite: {e}")

    @commands.command()
    async def favs(self, ctx):
        """List favorite cryptocurrencies"""
        if not self.binance_client:
            return await ctx.send("Binance API not configured.")
        
        try:
            message = "FUTURES FAVOURITE LIST\n"
            for i, symbol in enumerate(self.fav_list['FUTURES'].keys()):
                ticker = self.binance_client.get_ticker(symbol=symbol)
                message += str(i+1) + ". " + symbol + "--> Last Price: " + ticker['lastPrice'] + "\n"
            message += "\n\nSPOT FAVOURITE LIST"
            for i, symbol in enumerate(self.fav_list['SPOT'].keys()):
                ticker = self.binance_client.get_ticker(symbol=symbol)
                message += str(i+1) + ". " + symbol + "--> Last Price: " + ticker['lastPrice'] + "\n"
            await ctx.send(message)
        except Exception as e:
            await ctx.send(f"Error fetching favorites: {e}")

    @commands.command()
    async def fubln(self, ctx):
        """Show futures account balance"""
        if not self.binance_client:
            return await ctx.send("Binance API not configured.")
        
        try:
            balance_list = self.binance_client.futures_account_balance()
            message = "-"*35 + "\n"
            message += "-"*3 + "ACCOUNT BALANCE" + "-"*3 + "\n"
            message += "-"*35 + "\n"
            for balance in balance_list:
                message += balance['asset'] + " : " + balance['balance'] + "\n"
            message += "-"*35
            await ctx.send(message)
        except Exception as e:
            await ctx.send(f"Error fetching balance: {e}")

    @tasks.loop(seconds=60)
    async def futures_position_alerts(self):
        """Automated task to monitor futures positions and send alerts"""
        if not self.binance_client or not self.channel_id:
            return
        
        try:
            futures_info = self.binance_client.futures_account()
            positions_info = self.binance_client.futures_position_information()
            positions = futures_info['positions']
            message_channel = await self.bot.fetch_channel(self.channel_id)
            print(f"Got channel {message_channel} for {self.channel_id}")
            
            if float(futures_info['totalMaintMargin'])/float(futures_info['totalMarginBalance']) > 40.0:
                await message_channel.send("Your positions' Margin Ratio is greater than 40%. Please consider taking a look at it.")
            
            for position in positions:
                symbol = position['symbol']
                alert = False
                message = "------" + symbol + " POSITION ALERT!------\n"
                position_info = list(filter(lambda f: (f['symbol'] == symbol), positions_info))[0]
                if float(position_info['positionAmt']) != 0.0:
                    if float(position['unrealizedProfit']) < -1.0:
                        message += "Unrealized Profit is going down! LOSS : " + str(position['unrealizedProfit']) + "\n"
                        alert = True
                    if (float(position_info['markPrice'])-float(position_info['liquidationPrice']))/(float(position_info['entryPrice'])-float(position_info['liquidationPrice'])) <= 0.4:
                        message += "Mark price is moving closer to Liquidation Price. Your position may be liquidated soon.\n Mark Price:" + str(position_info['markPrice']) + "\n Liquidation Price:" + str(position_info['liquidationPrice']) + "\n"
                        alert = True
                if alert:
                    await message_channel.send(message)
        except Exception as e:
            print(f"Error in futures_position_alerts: {e}")

    @futures_position_alerts.before_loop
    async def before_futures_alerts(self):
        """Wait until bot is ready before starting alerts"""
        await self.bot.wait_until_ready()
        print("Finished waiting for futures alerts")


async def setup(bot):
    """Load the Trading cog"""
    trading = Trading(bot)
    await bot.add_cog(trading)
    # Uncomment the line below to enable position alerts
    # trading.futures_position_alerts.start()
