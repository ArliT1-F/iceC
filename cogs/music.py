"""
Music cog for iceC Discord Bot
Handles all music playback, queue management, and playback controls
"""
import os
import datetime
import random
import numpy as np
import logging
from typing import Optional
import nextcord
from nextcord.ext import commands
import wavelink
from wavelink.ext import spotify

logger = logging.getLogger('discord')


# Helper function for voice connectivity check
async def user_connectivity(ctx: commands.Context):
    """Check if user is connected to a voice channel"""
    if not getattr(ctx.author.voice, 'channel', None):
        await ctx.send(embed=nextcord.Embed(description=f'Try after joining a `voice channel`', color=ctx.bot.embed_color))
        return False
    return True


class Music(commands.Cog):
    """Music playback and queue management commands"""

    def __init__(self, bot):
        self.bot = bot
        setattr(wavelink.Player, 'lq', False)

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node):
        """Event fired when a node has finished connecting"""
        print(f'Node {node.identifier} connected successfully')

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, player: wavelink.Player, track: wavelink.Track, reason):
        """Event fired when a track has finished playing"""
        ctx = player.ctx
        vc: wavelink.Player = ctx.voice_client
        
        if vc.loop:
            return await vc.play(track)

        try:
            if not vc.queue.is_empty:
                if vc.lq:
                    vc.queue.put(vc.queue._queue[0])
                next_song = vc.queue.get()
                await vc.play(next_song)
                await ctx.send(embed=nextcord.Embed(description=f'**Current song playing from the `QUEUE`**\\n\\n`{next_song.title}`', color=ctx.bot.embed_color), delete_after=30)
        except Exception as e:
            logger.error(f"Error in on_wavelink_track_end: {e}")
            await vc.stop()
            return await ctx.send(embed=nextcord.Embed(description=f'No songs in the `QUEUE`', color=ctx.bot.embed_color))

    @commands.cooldown(1, 1, commands.BucketType.user)
    @commands.command(name='play', aliases=['p'], help='plays the given track provided by the user', description=',p <song name>')
    async def play_command(self, ctx: commands.Context, *, search: wavelink.YouTubeTrack):
        """Play a song from YouTube"""
        if not getattr(ctx.author.voice, 'channel', None):
            return await ctx.send(embed=nextcord.Embed(description=f'Try after joining voice channel', color=ctx.bot.embed_color))
        elif not ctx.voice_client:
            vc: wavelink.Player = await ctx.author.voice.channel.connect(cls=wavelink.Player)
        else:
            vc: wavelink.Player = ctx.voice_client

        if vc.queue.is_empty and vc.is_playing() is False:
            playString = await ctx.send(embed=nextcord.Embed(description='**searching...**', color=ctx.bot.embed_color))
            await vc.play(search)
            await playString.edit(embed=nextcord.Embed(description=f'**Search found**\\n\\n`{search.title}`', color=ctx.bot.embed_color))
        else:
            await vc.queue.put_wait(search)
            await ctx.send(embed=nextcord.Embed(description=f'Added to the `QUEUE`\\n\\n`{search.title}`', color=ctx.bot.embed_color))
            
        vc.ctx = ctx
        setattr(vc, 'loop', False)
        self.bot.user_dict[search.identifier] = ctx.author.mention

    @commands.cooldown(1, 1, commands.BucketType.user)
    @commands.command(name='splay', aliases=['sp'], help='plays the provided spotify playlist link', description=',sp <spotify playlist link>')
    async def spotifyplay_command(self, ctx: commands.Context, search: str):
        """Play a Spotify playlist"""
        if not getattr(ctx.author.voice, 'channel', None):
            return await ctx.send(embed=nextcord.Embed(description=f'Try after joining voice channel', color=ctx.bot.embed_color))
        elif not ctx.voice_client:
            vc: wavelink.Player = await ctx.author.voice.channel.connect(cls=wavelink.Player)
        else:
            vc: wavelink.Player = ctx.voice_client
        
        async for partial in spotify.SpotifyTrack.iterator(query=search, type=spotify.SpotifySearchType.playlist, partial_tracks=True):
            if vc.queue.is_empty and vc.is_playing() is False:
                await vc.play(partial)
            else:
                await vc.queue.put_wait(partial)
            song_name = await wavelink.tracks.YouTubeTrack.search(partial.title)
            self.bot.user_dict[song_name[0].identifier] = ctx.author.mention
            
        vc.ctx = ctx
        setattr(vc, 'loop', False)

    @commands.cooldown(1, 2, commands.BucketType.user)
    @commands.command(name='pause', aliases=['stop'], help='pauses the current playing track', description=',pause')
    async def pause_command(self, ctx: commands.Context):
        """Pause the current track"""
        if await user_connectivity(ctx) == False:
            return
        else:
            vc: wavelink.Player = ctx.voice_client
            if vc._source:
                if not vc.is_paused():
                    await vc.pause()
                    await ctx.send(embed=nextcord.Embed(description='`PAUSED` the music!', color=ctx.bot.embed_color))
                elif vc.is_paused():
                    await ctx.send(embed=nextcord.Embed(description='Already in `PAUSED State`', color=ctx.bot.embed_color))
            elif not vc._source:
                await ctx.send(embed=nextcord.Embed(description='Player is not `playing`!', color=ctx.bot.embed_color))

    @commands.cooldown(1, 2, commands.BucketType.user)
    @commands.command(name='resume', aliases=[], help='resumes the paused track', description=',resume')
    async def resume_command(self, ctx: commands.Context):
        """Resume the paused track"""
        if await user_connectivity(ctx) == False:
            return
        else:
            vc: wavelink.Player = ctx.voice_client
            if vc.is_paused():
                await vc.resume()
                await ctx.send(embed=nextcord.Embed(description='Music `RESUMED`!', color=ctx.bot.embed_color))
            elif vc.is_playing():
                await ctx.send(embed=nextcord.Embed(description='Already in `RESUMED State`', color=ctx.bot.embed_color))
            else:
                await ctx.send(embed=nextcord.Embed(description='Player is not `playing`!', color=ctx.bot.embed_color))

    @commands.cooldown(1, 2, commands.BucketType.user)
    @commands.command(name='skip', aliases=['next', 's'], help='skips to the next track', description=',s')
    @commands.has_role('tm')
    async def skip_command(self, ctx: commands.Context):
        """Skip to the next track"""
        if await user_connectivity(ctx) == False:
            return
        else:
            vc: wavelink.Player = ctx.voice_client
            if vc.loop == True:
                vclooptxt = 'Disable the `LOOP` to skip | **,loop** again to disable the `LOOP` | Add a new song to disable the `LOOP`'
                return await ctx.send(embed=nextcord.Embed(description=vclooptxt, color=ctx.bot.embed_color))
            elif vc.queue.is_empty:
                await vc.stop()
                await vc.resume()
                return await ctx.send(embed=nextcord.Embed(description=f'Song stopped! No songs in the `QUEUE`', color=ctx.bot.embed_color))
            else:
                await vc.stop()
                vc.queue._wakeup_next()
                await vc.resume()
                return await ctx.send(embed=nextcord.Embed(description=f'`SKIPPED`!', color=ctx.bot.embed_color))

    @commands.cooldown(1, 2, commands.BucketType.user)
    @commands.command(name='disconnect', aliases=['dc', 'leave'], help='disconnects the player from the vc', description=',dc')
    @commands.has_role('tm')
    async def disconnect_command(self, ctx: commands.Context):
        """Disconnect from voice channel"""
        if await user_connectivity(ctx) == False:
            return
        else:
            vc: wavelink.Player = ctx.voice_client
            try:
                await vc.disconnect(force=True)
                await ctx.send(embed=nextcord.Embed(description='**BYE!** Have a great time!', color=ctx.bot.embed_color))
            except Exception as e:
                logger.error(f"Error disconnecting voice client: {e}")
                await ctx.send(embed=nextcord.Embed(description='Failed to disconnect!', color=ctx.bot.embed_color))

    @commands.cooldown(1, 2, commands.BucketType.user)
    @commands.command(name='nowplaying', aliases=['np'], help='shows the current track information', description=',np')
    async def nowplaying_command(self, ctx: commands.Context):
        """Show current track information"""
        if await user_connectivity(ctx) == False:
            return
        else:
            vc: wavelink.Player = ctx.voice_client
            if not vc.is_playing():
                return await ctx.send(embed=nextcord.Embed(description='Not playing anything!', color=ctx.bot.embed_color))

            if vc.loop:
                loopstr = 'enabled'
            else:
                loopstr = 'disabled'

            if vc.is_paused():
                state = 'paused'
            else:
                state = 'playing'
                
            '''numpy array usertag indexing'''
            user_list = list(self.bot.user_dict.items())
            user_arr = np.array(user_list)
            song_index = np.flatnonzero(np.core.defchararray.find(user_arr, vc.track.identifier) == 0)
            if len(song_index) > 0:
                arr_index = int(song_index[0]/2)
                requester = user_arr[arr_index, 1] if arr_index < len(user_arr) else "Unknown"
            else:
                requester = "Unknown"
            
            nowplaying_description = f'[`{vc.track.title}`]({str(vc.track.uri)})\\n\\n**Requested by**: {requester}'
            em = nextcord.Embed(description=f'**Now Playing**\\n\\n{nowplaying_description}', color=ctx.bot.embed_color)
            em.add_field(name='**Song Info**', value=f'• Author: `{vc.track.author}`\\n• Duration: `{str(datetime.timedelta(seconds=vc.track.length))}`')
            em.add_field(name='**Player Info**', value=f'• Player Volume: `{vc._volume}`\\n• Loop: `{loopstr}`\\n• Current State: `{state}`', inline=False)
            return await ctx.send(embed=em)

    @commands.cooldown(1, 2, commands.BucketType.user)
    @commands.command(name='loop', aliases=[], help='•loops the current song\\n•unloops the current song', description=',loop')
    @commands.has_role('tm')
    async def loop_command(self, ctx: commands.Context):
        """Loop/unloop the current song"""
        if await user_connectivity(ctx) == False:
            return
        else:
            vc: wavelink.Player = ctx.voice_client
            if vc._source:
                try:
                    vc.loop ^= True
                except Exception as e:
                    logger.error(f"Error toggling loop: {e}")
                    setattr(vc, 'loop', False)
            else:
                return await ctx.send(embed=nextcord.Embed(description='No song to `loop`', color=ctx.bot.embed_color))
            if vc.loop:
                return await ctx.send(embed=nextcord.Embed(description='**LOOP**: `enabled`', color=ctx.bot.embed_color))
            else:
                return await ctx.send(embed=nextcord.Embed(description='**LOOP**: `disabled`', color=ctx.bot.embed_color))

    @commands.cooldown(1, 2, commands.BucketType.user)
    @commands.command(name='loopqueue', aliases=['lq'], help='starts the loop queue ==> ,lq start or ,lq enable\\nstopes the loop queue ==> ,lq stop or ,lq disable', description=',lq <mode>')
    @commands.has_role('tm')
    async def loopqueue_command(self, ctx: commands.Context, type: str):
        """Enable/disable queue looping"""
        vc: wavelink.Player = ctx.voice_client
        if not vc.queue.is_empty:
            song_count = len(vc.queue)
            if vc.lq == False:
                if type == 'start' or type == 'enable':
                    vc.lq = True
                    await ctx.send(embed=nextcord.Embed(description='**loopqueue**: `enabled`', color=ctx.bot.embed_color))
                    try:
                        if vc._source and vc._source not in vc.queue:
                            vc.queue.put(vc._source)
                    except Exception as e:
                        logger.error(f"Error adding source to queue: {e}")
                        return        
            if vc.lq == True:
                if type == 'stop' or type == 'disable':
                    vc.lq = False
                    await ctx.send(embed=nextcord.Embed(description='**loopqueue**: `disabled`', color=ctx.bot.embed_color))
                    if song_count == 1 and vc.queue._queue and len(vc.queue._queue) > 0 and vc.queue._queue[0] == vc._source:
                        del vc.queue._queue[0]
            if type != 'start' and type != 'enable' and type != 'disable' and type != 'stop':
                await ctx.send(embed=nextcord.Embed(description='check **,help** for **loopqueue**', color=ctx.bot.embed_color))
        else:
            return await ctx.send(embed=nextcord.Embed(description='Unable to loop `QUEUE`, try adding more songs..', color=ctx.bot.embed_color))

    @commands.cooldown(1, 2, commands.BucketType.user)
    @commands.command(name='queue', aliases=['q', 'track'], help='displays the current queue', description=',q')
    async def queue_command(self, ctx: commands.Context):
        """Display the current queue"""
        if await user_connectivity(ctx) == False:
            return
        else:
            vc: wavelink.Player = ctx.voice_client
            if vc.queue.is_empty:
                return await ctx.send(embed=nextcord.Embed(description='**QUEUE**\\n\\n`empty`', color=ctx.bot.embed_color))
            
            lqstr = '`disabled`' if vc.lq == False else '`enabled`'
            if not hasattr(self.bot, 'qem'):
                self.bot.qem = None
            qem = nextcord.Embed(description=f'**QUEUE**\\n\\n**loopqueue**: {lqstr}', color=ctx.bot.embed_color)
            song_queue = vc.queue.copy()
            song_count = 0
            for song in song_queue:
                song_count += 1
                if wavelink.tracks.PartialTrack:
                    title = song.title
                else:
                    title = song.info['title']
                qem.add_field(name=f'‎', value=f'**{song_count} **• {title}', inline=False)
            self.bot.qem = qem
        
            await ctx.send(embed=qem)
            return commands.Paginator(prefix='>', suffix='<', linesep='\\n')

    @commands.cooldown(1, 2, commands.BucketType.user)
    @commands.command(name="shuffle", aliases=['mix'], help='shuffles the existing queue randomly', description=',shuffle')
    @commands.has_role('tm')
    async def shuffle_command(self, ctx: commands.Context):
        """Shuffle the queue"""
        if await user_connectivity(ctx) == False:
            return
        else:
            vc: wavelink.Player = ctx.voice_client
            song_count = len(vc.queue)
            if song_count > 2:
                random.shuffle(vc.queue._queue)
                return await ctx.send(embed=nextcord.Embed(description=f'Shuffled the `QUEUE`', color=ctx.bot.embed_color))
            elif vc.queue.is_empty:
                return await ctx.send(embed=nextcord.Embed(description=f'`QUEUE` is empty', color=ctx.bot.embed_color))
            else:
                return await ctx.send(embed=nextcord.Embed(description=f'`QUEUE` has less than `3 songs`', color=ctx.bot.embed_color))

    @commands.cooldown(1, 2, commands.BucketType.user)
    @commands.command(name='del', aliases=['remove', 'drop'], help='deletes the specified track', description=',del <song number>')
    @commands.has_role('tm')
    async def del_command(self, ctx: commands.Context, position: int):
        """Delete a track from the queue"""
        if await user_connectivity(ctx) == False:
            return
        else:
            vc: wavelink.Player = ctx.voice_client
            if not vc.queue.is_empty:
                song_count = len(vc.queue)
                if position <= 0:
                    return await ctx.send(embed=nextcord.Embed(description=f'Position can not be `ZERO`* or `LESSER`', color=ctx.bot.embed_color))
                elif position > song_count:
                    return await ctx.send(embed=nextcord.Embed(description=f'Position `{position}` is outta range', color=ctx.bot.embed_color))
                else:
                    SongToBeDeleted = vc.queue._queue[position-1].title
                    del vc.queue._queue[position-1]
                    return await ctx.send(embed=nextcord.Embed(description=f'`{SongToBeDeleted}` removed from the QUEUE', color=ctx.bot.embed_color))
            else:
                return await ctx.send(embed=nextcord.Embed(description='No songs in the `QUEUE`', color=ctx.bot.embed_color))

    @commands.cooldown(1, 2, commands.BucketType.user)
    @commands.command(name='skipto', aliases=['goto'], help='skips to the specified track', description=',skipto <song number>')
    @commands.has_role('tm')
    async def skipto_command(self, ctx: commands.Context, position: int):
        """Skip to a specific track in the queue"""
        if await user_connectivity(ctx) == False:
            return
        else:
            vc: wavelink.Player = ctx.voice_client
            if not vc.queue.is_empty:
                song_count = len(vc.queue)
                if position <= 0:
                    return await ctx.send(embed=nextcord.Embed(description=f'Position can not be `ZERO`* or `LESSER`', color=ctx.bot.embed_color))
                elif position > song_count:
                    return await ctx.send(embed=nextcord.Embed(description=f'Position `{position}` is outta range', color=ctx.bot.embed_color))
                else:
                    vc.queue.put_at_front(vc.queue._queue[position-1])
                    del vc.queue._queue[position]
                    return await self.skip_command(ctx)
            else:
                return await ctx.send(embed=nextcord.Embed(description='No songs in the `QUEUE`', color=ctx.bot.embed_color))

    @commands.cooldown(1, 2, commands.BucketType.user)
    @commands.command(name='move', aliases=['set'], help='moves the track to the specified position', description=',move <song number> <position>')
    @commands.has_role('tm')
    async def move_command(self, ctx: commands.Context, song_position: int, move_position: int):
        """Move a track to a different position in the queue"""
        if await user_connectivity(ctx) == False:
            return
        else:
            vc: wavelink.Player = ctx.voice_client
            if not vc.queue.is_empty:
                song_count = len(vc.queue)
                if song_position <= 0 or move_position <= 0:
                    return await ctx.send(embed=nextcord.Embed(description=f'Position can not be `ZERO`* or `LESSER`', color=ctx.bot.embed_color))
                elif song_position > song_count or move_position > song_count:
                    position = song_position if song_position > song_count else move_position
                    return await ctx.send(embed=nextcord.Embed(description=f'Position `{position}` is outta range!', color=ctx.bot.embed_color))
                elif song_position == move_position:
                    return await ctx.send(embed=nextcord.Embed(description=f'Already in that `Position`:{move_position}', color=ctx.bot.embed_color))
                else:
                    move_index = move_position-1 if move_position < song_position else move_position
                    song_index = song_position if move_position < song_position else song_position-1
                    vc.queue.put_at_index(move_index, vc.queue._queue[song_position-1])
                    moved_song = vc.queue._queue[song_index]
                    del vc.queue._queue[song_index]
                    moved_song_name = moved_song.info['title']
                    return await ctx.send(embed=nextcord.Embed(description=f'**{moved_song_name}** moved at Position:`{move_position}`', color=ctx.bot.embed_color))
            else:
                return await ctx.send(embed=nextcord.Embed(description='No songs in the `QUEUE`!', color=ctx.bot.embed_color))

    @commands.cooldown(1, 2, commands.BucketType.user)
    @commands.command(name='volume', aliases=['vol'], help='sets the volume', description=',vol <number>')
    @commands.has_role('tm')
    async def volume_command(self, ctx: commands.Context, playervolume: int):
        """Set the player volume"""
        if await user_connectivity(ctx) == False:
            return
        else:
            vc: wavelink.Player = ctx.voice_client
            if vc.is_connected():
                if playervolume > 100:
                    return await ctx.send(embed=nextcord.Embed(description='**VOLUME** supported upto `100%`', color=ctx.bot.embed_color))
                elif playervolume < 0:
                    return await ctx.send(embed=nextcord.Embed(description='**VOLUME** can not be `negative`', color=ctx.bot.embed_color))
                else:
                    await ctx.send(embed=nextcord.Embed(description=f'**VOLUME**\\nSet to `{playervolume}%`', color=ctx.bot.embed_color))
                    return await vc.set_volume(playervolume)
            elif not vc.is_connected():
                return await ctx.send(embed=nextcord.Embed(description="Player not connected!", color=ctx.bot.embed_color))

    @commands.cooldown(1, 2, commands.BucketType.user)
    @commands.command(name='seek', aliases=[], help='seeks or moves the player to specified track position', description=',seek <duration>')
    @commands.has_role('tm')
    async def seek_command(self, ctx: commands.Context, seekPosition: int):
        """Seek to a position in the track"""
        if await user_connectivity(ctx) == False:
            return
        else:
            vc: wavelink.Player = ctx.voice_client
            if not vc.is_playing():
                return await ctx.send(embed=nextcord.Embed(description='Player not playing!', color=ctx.bot.embed_color))
            elif vc.is_playing():
                if 0 <= seekPosition <= vc.track.length:
                    msg = await ctx.send(embed=nextcord.Embed(description='seeking...', color=ctx.bot.embed_color))
                    await vc.seek(seekPosition*1000)
                    return await msg.edit(embed=nextcord.Embed(description=f'Player SEEKED: `{seekPosition}` seconds', color=ctx.bot.embed_color))
                else:
                    return await ctx.send(embed=nextcord.Embed(description=f'SEEK length `{seekPosition}` outta range', color=ctx.bot.embed_color))

    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.command(name='clear', aliases=[], help='clears the queue', description=',clear')
    @commands.has_role('tm')
    async def clear_command(self, ctx: commands.Context):
        """Clear the entire queue"""
        vc: wavelink.Player = ctx.voice_client
        if await user_connectivity(ctx) == False:
            return
        else:
            if vc.queue.is_empty:
                return await ctx.send(embed=nextcord.Embed(description='No `SONGS` are present', color=ctx.bot.embed_color))
            else:
                vc.queue._queue.clear()
                vc.lq = False
                clear_command_embed = nextcord.Embed(description=f'`QUEUE` cleared', color=ctx.bot.embed_color)
                return await ctx.send(embed=clear_command_embed)

    @commands.cooldown(1, 2, commands.BucketType.user)
    @commands.command(name='save', aliases=['dm'], description=",save\n,save <song number | 'queue' | 'q'>", help='dms the current | specified song to the user')
    async def save_command(self, ctx: commands.Context, savestr: Optional[str]):
        """DM the current song or queue to the user"""
        vc: wavelink.Player = ctx.voice_client
        if await user_connectivity(ctx) == False:
            return
        else:
            user = await self.bot.fetch_user(ctx.author._user.id)
            if vc._source and savestr is None:
                await user.send(embed=nextcord.Embed(description=f'`{vc._source}`', color=ctx.bot.embed_color))
            elif not vc.queue.is_empty and (savestr == 'q' or savestr == 'queue'):
                if hasattr(self.bot, 'qem') and self.bot.qem:
                    await user.send(embed=self.bot.qem)
                else:
                    await ctx.send(embed=nextcord.Embed(description='Queue not available. Please use ,q first.', color=ctx.bot.embed_color))
            elif not vc.queue.is_empty and savestr:
                song_count = len(vc.queue)
                try:
                    position = int(savestr)
                    if position <= 0:
                        return await ctx.send(embed=nextcord.Embed(description=f'Position can not be `ZERO`* or `LESSER`', color=ctx.bot.embed_color))
                    elif position > song_count:
                        return await ctx.send(embed=nextcord.Embed(description=f'Position `{savestr}` is outta range', color=ctx.bot.embed_color))
                    else:
                        song_info = vc.queue._queue[position - 1]
                        em = nextcord.Embed(description=song_info.info['title'], color=ctx.bot.embed_color)
                        await user.send(embed=em)
                except ValueError:
                    return await ctx.send(embed=nextcord.Embed(description='Invalid position. Please provide a number.', color=ctx.bot.embed_color))
            else:
                return await ctx.send(embed=nextcord.Embed(description='There is no `song` | `queue` available', color=ctx.bot.embed_color))


async def setup(bot):
    """Load the Music cog"""
    await bot.add_cog(Music(bot))