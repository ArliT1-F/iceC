"""
Moderation cog for iceC Discord Bot
Handles moderation commands like kick, ban, mute, etc.
"""
import discord
from discord.ext import commands
from discord.ext.commands import has_permissions
import nextcord


class Moderation(commands.Cog):
    """Moderation commands for server management"""

    def __init__(self, bot):
        self.bot = bot

    @commands.cooldown(1, 2, commands.BucketType.user)
    @commands.command(name='setrole', aliases=['giverole'], help='sets an existing role which are below icy404(role) for a user', pass_context=True, description=',setrole <role name>')
    @commands.has_permissions(administrator=True)
    async def setrole_command(self, ctx, user: nextcord.Member, role: nextcord.Role):
        """Assign a role to a user"""
        await user.add_roles(role)
        embed = nextcord.Embed(description=f"`{user.name}` has been given a role called: **{role.name}**", color=self.bot.embed_color)
        await ctx.send(embed=embed)

    @commands.command()
    @has_permissions(kick_members=True, administrator=True)
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        """Kick a member from the server"""
        guild = ctx.guild
        memberKick = discord.Embed(title='Kicked', description=f'You have been kicked from {guild.name} for {reason}')
        
        await member.kick(reason=reason)
        await ctx.send(f'User {member} has been kicked.')

    @commands.command()
    @has_permissions(ban_members=True, administrator=True)
    async def ban(self, ctx, member: discord.Member, *, reason=None):
        """Ban a member from the server"""
        guild = ctx.guild
        memberBan = discord.Embed(title='Banned', description=f'You were banned from {guild.name} for {reason}')
        
        await member.ban(reason=reason)
        await ctx.send(f'User {member} has been banned.')
        try:
            await member.send(embed=memberBan)
        except:
            pass  # User may have DMs disabled

    @commands.command()
    @has_permissions(ban_members=True, administrator=True)
    async def unban(self, ctx, *, member):
        """Unban a member from the server"""
        banned_users = await ctx.guild.bans()
        member_name, member_discriminator = member.split('#')
        
        for ban_entry in banned_users:
            user = ban_entry.user
            if (user.name, user.discriminator) == (member_name, member_discriminator):
                await ctx.guild.unban(user)
                await ctx.send(f'{user.name}#{user.discriminator} has been unbanned.')
                return
        
        await ctx.send(f"User {member} not found in ban list.")

    @commands.command(pass_context=True)
    @has_permissions(manage_messages=True)
    async def mute(self, ctx, member: discord.Member, reason=None):
        """Mute a member"""
        guild = ctx.guild
        mutedRole = discord.utils.get(guild.roles, name='Muted')
        memberMute = discord.Embed(title='Muted', description=f'You have been muted from {guild.name} for {reason}')
        
        if mutedRole not in guild.roles:
            perms = discord.Permissions(send_messages=False, speak=False)
            mutedRole = await guild.create_role(name='Muted', permissions=perms)
            await member.add_roles(mutedRole)
            await ctx.send('Successfully created the [Muted] role and properly assigned it to the user.')
        else:
            await member.add_roles(mutedRole)
        
        embed = discord.Embed(title='User muted!', description=f'**{member}** was muted by **{ctx.message.author}**!', color=0xff00f6)
        await ctx.send(embed=embed)

    @commands.command(pass_context=True)
    @has_permissions(manage_messages=True)
    async def unmute(self, ctx, member: discord.Member, *, reason=None):
        """Unmute a member"""
        guild = ctx.guild
        mutedRole = discord.utils.get(guild.roles, name='Muted')
        
        memberUnmute = discord.Embed(title='Unmuted', description=f'You were unmuted from {guild.name} for {reason}')
        
        await member.remove_roles(mutedRole)
        await ctx.send(f'Unmuted {member.mention} for {reason}')
        try:
            await member.send(embed=memberUnmute)
        except:
            pass  # User may have DMs disabled


async def setup(bot):
    """Load the Moderation cog"""
    await bot.add_cog(Moderation(bot))