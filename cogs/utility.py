"""
Utility cog for iceC Discord Bot
Handles utility commands like ping, info, etc.
"""
import nextcord
from nextcord.ext import commands


class Utility(commands.Cog):
    """Utility commands"""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle simple message responses"""
        if message.author == self.bot.user:
            return
        if message.content.startswith('hello'):
            await message.channel.send('Hello!')

    @commands.cooldown(1, 2, commands.BucketType.user)
    @commands.command(name='ping', help=f"displays client's latency", description=',ping')
    async def ping_command(self, ctx):
        """Check bot latency"""
        em = nextcord.Embed(description=f'**Pong!**\\n\\n`{round(self.bot.latency*1000)}`ms', color=self.bot.embed_color)
        await ctx.send(embed=em)

    @commands.cooldown(1, 2, commands.BucketType.user)
    @commands.command(name='info', aliases=['i'], help='shows information about the client')
    @commands.is_owner()
    @commands.has_role('tm')
    async def info_command(self, ctx: commands.Context):
        """Show bot information (Owner only)"""
        await ctx.send(embed=nextcord.Embed(description=f'**Info**\\ntotal server count: `{len(self.bot.guilds)}`', color=self.bot.embed_color))


async def setup(bot):
    """Load the Utility cog"""
    await bot.add_cog(Utility(bot))
