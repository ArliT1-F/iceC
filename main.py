import os, json
from dotenv import load_dotenv, find_dotenv
import discord
from discord.ext import commands, tasks
import logging
import binance
from discord import Member
from discord.ext.commands import has_permissions, MissingPermissions
from binance import Client, ThreadedWebsocketManager, ThreadedDepthCacheManager
import datetime, random
import nextcord
from nextcord.ext import commands
import wavelink
from wavelink.ext import spotify
from typing import Optional
import numpy as np
import lyricsgenius

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
intents.guild_messages = True
intents.members = True
intents.message_content = True
intents.voice_states = True
intents.emojis_and_stickers = True
all_intents = intents.all()
all_intents= True
intent = discord.Intents.default()


client = discord.Client(command_prefix='!', intents=intents, case_insensitive=True)
global user_arr, user_dict
user_dict = {} 
user_arr = np.array([])
setattr(wavelink.Player, 'lq', False)
embed_color = nextcord.Color.from_rgb(128, 67, 255)

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


@commands.cooldown(1, 2, commands.BucketType.user)
@commands.command(name='setrole', aliases=['giverole'],help='sets an existing role which are below icy404(role) for a user', pass_context=True, description=',setrole <role name>')
@commands.has_permissions(administrator=True)
async def setrole_command(ctx, user: nextcord.Member, role: nextcord.Role):
    await user.add_roles(role)
    embed = nextcord.Embed(description=f"`{user.name}` has been given a role called: **{role.name}**", color=embed_color)
    await ctx.send(embed=embed)
    
@commands.cooldown(1, 2, commands.BucketType.user)
@commands.command(name='ping', help=f"displays client's latency", description=',ping')
async def ping_command(ctx):    
    em = nextcord.Embed(description=f'**Pong!**\n\n`{round(client.latency*1000)}`ms', color=embed_color)
    await ctx.send(embed=em)

async def user_connectivity(ctx: commands.Context):
    # vc: wavelink.Player = ctx.voice_client
    if not getattr(ctx.author.voice, 'channel', None):
        await ctx.send(embed=nextcord.Embed(description=f'Try after joining a `voice channel`', color=embed_color))        
        return False
    #-->code to check if the client is connected to vc??<--

@client.event
async def on_wavelink_node_ready(node: wavelink.Node):
    print(f'Node {node.identifier} connected successfully')

async def node_connect():
    await client.wait_until_ready()
    await wavelink.NodePool.create_node(client=client, host='node1.kartadharta.xyz', port=443, password="kdlavalink", https=True, spotify_client=spotify.SpotifyClient(client_id=os.environ['spotify_id'],client_secret=os.environ['spotify_secret']))
@client.event
async def on_wavelink_track_end(player: wavelink.Player, track: wavelink.Track, reason):
    ctx = player.ctx
    vc: player = ctx.voice_client
    
    if vc.loop:
        return await vc.play(track)

    try:
        if not vc.queue.is_empty:
            if vc.lq:
                vc.queue.put(vc.queue._queue[0])
            next_song = vc.queue.get()
            await vc.play(next_song)
            await ctx.send(embed=nextcord.Embed(description=f'**Current song playing from the `QUEUE`**\n\n`{next_song.title}`', color=embed_color), delete_after=30)
            #{code to remove the song name from the numpy array}
    except:
        await vc.stop()
        return await ctx.send(embed=nextcord.Embed(description=f'No songs in the `QUEUE`', color=embed_color))

@client.event
async def on_command_error(ctx: commands.Context, error):
    if isinstance(error, commands.CommandOnCooldown):
        em = nextcord.Embed(description=f'**Cooldown active**\ntry again in `{error.retry_after:.2f}`s*',color=embed_color)
        await ctx.send(embed=em)
        
@client.event
async def on_command_error(ctx: commands.Context, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(embed=nextcord.Embed(description="Missing `arguments`", color=embed_color))

@commands.cooldown(1, 2, commands.BucketType.user)
@commands.command(name='info',aliases=['i'], help='shows information about the client')
@commands.is_owner()
@commands.has_role('tm')
async def info_command(ctx: commands.Context):
    await ctx.send(embed=nextcord.Embed(description=f'**Info**\ntotal server count: `{len(client.guilds)}`', color=embed_color))
    
@commands.cooldown(1, 2, commands.BucketType.user)        
@commands.command(name='loopqueue', aliases=['lq'], help='starts the loop queue ==> ,lq start or ,lq enable\nstopes the loop queue ==> ,lq stop or ,lq disable', description=',lq <mode>')
@commands.has_role('tm')
async def loopqueue_command(ctx: commands.Context, type:str):
    vc: wavelink.Player = ctx.voice_client
    if not vc.queue.is_empty:
        if vc.lq == False:
            if type == 'start' or type == 'enable':
                vc.lq = True
                await ctx.send(embed=nextcord.Embed(description='**loopqueue**: `enabled`', color=embed_color))
                try:
                    if vc._source not in vc.queue:
                        vc.queue.put(vc._source)
                    else: ''
                except Exception:
                    return ''        
        if vc.lq == True:
            if type == 'stop' or type == 'disable':
                vc.lq = False
                await ctx.send(embed=nextcord.Embed(description='**loopqueue**: `disabled`', color=embed_color))
                if song_count == 1 and vc.queue._queue[0] == vc._source:
                    del vc.queue._queue[0]
                else:
                    return ''              
        if type != 'start' and type != 'enable' and type != 'disable' and type != 'stop':
            await ctx.send(embed=nextcord.Embed(description='check **,help** for **loopqueue**', color=embed_color))
    else:
        return await ctx.send(embed=nextcord.Embed(description='Unable to loop `QUEUE`, try adding more songs..', color=embed_color))

@commands.cooldown(1, 1, commands.BucketType.user)  
@commands.command(name='play', aliases=['p'], help='plays the given track provided by the user', description=',p <song name>')
async def play_command(ctx: commands.Context, *, search:wavelink.YouTubeTrack):
    
    if not getattr(ctx.author.voice, 'channel', None):
        return await ctx.send(embed=nextcord.Embed(description=f'Try after joining voice channel', color=embed_color))        
    elif not ctx.voice_client:
        vc: wavelink.Player = await ctx.author.voice.channel.connect(cls=wavelink.Player)
    else:
        vc: wavelink.Player = ctx.voice_client

    if vc.queue.is_empty and vc.is_playing() is False:   
        playString = await ctx.send(embed=nextcord.Embed(description='**searching...**', color=embed_color))
        await vc.play(search)
        await playString.edit(embed=nextcord.Embed(description=f'**Search found**\n\n`{search.title}`', color=embed_color))

    else:
        await vc.queue.put_wait(search)
        await ctx.send(embed=nextcord.Embed(description=f'Added to the `QUEUE`\n\n`{search.title}`', color=embed_color))
        
    vc.ctx = ctx 

    setattr(vc, 'loop', False)

    user_dict[search.identifier] = ctx.author.mention
    
@commands.cooldown(1, 1, commands.BucketType.user) 
@commands.command(name='splay', aliases=['sp'], help='plays the provided spotify playlist link', description=',sp <spotify playlist link>')
async def spotifyplay_command(ctx: commands.Context, search: str):
   
    if not getattr(ctx.author.voice, 'channel', None):
        return await ctx.send(embed=nextcord.Embed(description=f'Try after joining voice channel', color=embed_color))        
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
        user_dict[song_name[0].identifier] = ctx.author.mention 
        
    vc.ctx = ctx 
    
    setattr(vc, 'loop', False)
             
@commands.cooldown(1, 2, commands.BucketType.user)  
@commands.command(name='pause', aliases=['stop'], help='pauses the current playing track', description=',pause')
async def pause_command(ctx: commands.Context):
    if await user_connectivity(ctx) == False:
        return
    else:
        vc: wavelink.Player = ctx.voice_client

        if vc._source:
            if not vc.is_paused():
                await vc.pause()
                await ctx.send(embed=nextcord.Embed(description='`PAUSED` the music!', color=embed_color))

            elif vc.is_paused():
                await ctx.send(embed=nextcord.Embed(description='Already in `PAUSED State`', color=embed_color))
        elif not vc._source:
            await ctx.send(embed=nextcord.Embed(description='Player is not `playing`!', color=embed_color))

@commands.cooldown(1, 2, commands.BucketType.user)  
@commands.command(name='resume',aliases=[], help='resumes the paused track', description=',resume')
async def resume_command(ctx: commands.Context):
    if await user_connectivity(ctx) == False:
        return
    else:
        vc: wavelink.Player = ctx.voice_client

        if vc.is_playing():
            if vc.is_paused():
                await vc.resume()
                await ctx.send(embed=nextcord.Embed(description='Music `RESUMED`!', color=embed_color))

            elif vc.is_playing():
                await ctx.send(embed=nextcord.Embed(description='Already in `RESUMED State`', color=embed_color))
        else:
            await ctx.send(embed=nextcord.Embed(description='Player is not `playing`!', color=embed_color))
        
@commands.cooldown(1, 2, commands.BucketType.user)  
@commands.command(name='skip', aliases=['next', 's'], help='skips to the next track', description=',s')
@commands.has_role('tm')
async def skip_command(ctx: commands.Context):
    if await user_connectivity(ctx) == False:
        return
    else:
        vc: wavelink.Player = ctx.voice_client

        if vc.loop == True:
            vclooptxt = 'Disable the `LOOP` to skip | **,loop** again to disable the `LOOP` | Add a new song to disable the `LOOP`'
            return await ctx.send(embed=nextcord.Embed(description=vclooptxt, color=embed_color))

        elif vc.queue.is_empty:
            await vc.stop()
            await vc.resume()
            return await ctx.send(embed=nextcord.Embed(description=f'Song stopped! No songs in the `QUEUE`', color=embed_color))

        else:
            await vc.stop()
            vc.queue._wakeup_next()
            await vc.resume()
            return await ctx.send(embed=nextcord.Embed(description=f'`SKIPPED`!', color=embed_color))

@commands.cooldown(1, 2, commands.BucketType.user)  
@commands.command(name='disconnect', aliases=['dc', 'leave'], help='disconnects the player from the vc', description=',dc')
@commands.has_role('tm')
async def disconnect_command(ctx: commands.Context):
    if await user_connectivity(ctx) == False:
        return
    else:
        vc : wavelink.Player = ctx.voice_client
        try:
            await vc.disconnect(force=True)
            await ctx.send(embed=nextcord.Embed(description='**BYE!** Have a great time!', color=embed_color))
        except Exception:
            await ctx.send(embed=nextcord.Embed(description='Failed to destroy!', color=embed_color))
            
@commands.cooldown(1, 2, commands.BucketType.user)  
@commands.command(name='nowplaying', aliases=['np'], help='shows the current track information', description=',np')
async def nowplaying_command(ctx: commands.Context):
    if await user_connectivity(ctx) == False:
        return
    else:
        vc: wavelink.Player = ctx.voice_client
        if not vc.is_playing():
            return await ctx.send(embed=nextcord.Embed(description='Not playing anything!', color=embed_color))

    #vcloop conditions
        if vc.loop:
            loopstr = 'enabled'
        else:
            loopstr = 'disabled'

        if vc.is_paused():
            state = 'paused'
        else:
            state = 'playing'
            
        '''numpy array usertag indexing'''    
        global user_list
        user_list = list(user_dict.items())
        user_arr = np.array(user_list)
        song_index = np.flatnonzero(np.core.defchararray.find(user_arr,vc.track.identifier) ==0)
        arr_index = int(song_index/2)
        
        requester = user_arr[arr_index,1]
        
        nowplaying_description = f'[`{vc.track.title}`]({str(vc.track.uri)})\n\n**Requested by**: {requester}'
        em = nextcord.Embed(description=f'**Now Playing**\n\n{nowplaying_description}', color=embed_color)
        em.add_field(name='**Song Info**', value=f'• Author: `{vc.track.author}`\n• Duration: `{str(datetime.timedelta(seconds=vc.track.length))}`')
        em.add_field(name='**Player Info**', value=f'• Player Volume: `{vc._volume}`\n• Loop: `{loopstr}`\n• Current State: `{state}`', inline=False)

        return await ctx.send(embed=em)

@commands.cooldown(1, 2, commands.BucketType.user)  
@commands.command(name='loop',aliases=[], help='•loops the current song\n•unloops the current song', description=',loop')
@commands.has_role('tm')
async def loop_command(ctx: commands.Context):
    if await user_connectivity(ctx) == False:
        return
    else:
        vc: wavelink.Player = ctx.voice_client
        if vc._source:
            try:
                vc.loop ^= True
            except Exception:
                setattr(vc, 'loop', False)
        else:
            return await ctx.send(embed= nextcord.Embed(description='No song to `loop`', color=embed_color))
        if vc.loop:
            return await ctx.send(embed= nextcord.Embed(description='**LOOP**: `enabled`', color=embed_color))
        else:
            return await ctx.send(embed=nextcord.Embed(description='**LOOP**: `disabled`', color=embed_color))

@commands.cooldown(1, 2, commands.BucketType.user)  
@commands.command(name='queue', aliases=['q', 'track'], help='displays the current queue', description=',q')
async def queue_command(ctx: commands.Context):
    if await user_connectivity(ctx) == False:
        return
    else:
        vc: wavelink.Player = ctx.voice_client

        if vc.queue.is_empty:
            return await ctx.send(embed= nextcord.Embed(description='**QUEUE**\n\n`empty`', color=embed_color))
        
        lqstr = '`disabled`' if vc.lq == False else '`enabled`'
        global qem
        qem = nextcord.Embed(description=f'**QUEUE**\n\n**loopqueue**: {lqstr}',color=embed_color)
        global song_count, song, song_queue
        song_queue = vc.queue.copy()
        song_count = 0
        for song in song_queue:
            song_count += 1
            if wavelink.tracks.PartialTrack:
                title = song.title
            else:
                title = song.info['title'] 
            qem.add_field(name=f'‎', value=f'**{song_count} **• {title}',inline=False)
    
        await ctx.send(embed=qem)
        return commands.Paginator(prefix='>', suffix='<', linesep='\n')

@commands.cooldown(1, 2, commands.BucketType.user)  
@commands.command(name="shuffle", aliases=['mix'], help='shuffles the existing queue randomly', description=',shuffle')
@commands.has_role('tm')
async def shuffle_command(ctx: commands.Context):
    if await user_connectivity(ctx) == False:
        return
    else:
        vc: wavelink.Player = ctx.voice_client
        if song_count > 2:
            random.shuffle(vc.queue._queue)
            return await ctx.send(embed=nextcord.Embed(description=f'Shuffled the `QUEUE`', color=embed_color))
        elif vc.queue.is_empty:
            return await ctx.send(embed=nextcord.Embed(description=f'`QUEUE` is empty', color=embed_color))
        else:
            return await ctx.send(embed=nextcord.Embed(description=f'`QUEUE` has less than `3 songs`', color=embed_color))

@commands.cooldown(1, 2, commands.BucketType.user)  
@commands.command(name='del', aliases=['remove', 'drop'], help='deletes the specified track', description=',del <song number>')
@commands.has_role('tm')
async def del_command(ctx: commands.Context, position: int):
    if await user_connectivity(ctx) == False:
        return
    else:
        vc: wavelink.Player = ctx.voice_client
        if not vc.queue.is_empty:
            if position <= 0:
                return await ctx.send(embed=nextcord.Embed(description=f'Position can not be `ZERO`* or `LESSER`', color=embed_color))
            elif position > song_count:
                return await ctx.send(embed=nextcord.Embed(description=f'Position `{position}` is outta range', color=embed_color))
            else:
                SongToBeDeleted = vc.queue._queue[position-1].title
                del vc.queue._queue[position-1]
                return await ctx.send(embed=nextcord.Embed(description=f'`{SongToBeDeleted}` removed from the QUEUE', color=embed_color))
        else:
            return await ctx.send(embed=nextcord.Embed(description='No songs in the `QUEUE`', color=embed_color))

@commands.cooldown(1, 2, commands.BucketType.user)  
@commands.command(name='skipto',aliases=['goto'], help='skips to the specified track', description=',skipto <song number>')
@commands.has_role('tm')
async def skipto_command(ctx: commands.Context, position: int):
    if await user_connectivity(ctx) == False:
        return
    else:
        vc: wavelink.Player = ctx.voice_client
        if not vc.queue.is_empty:
            if position <= 0:
                return await ctx.send(embed=nextcord.Embed(description=f'Position can not be `ZERO`* or `LESSER`', color=embed_color))
            elif position > song_count:
                return await ctx.send(embed=nextcord.Embed(description=f'Position `{position}` is outta range', color=embed_color))
            elif position == vc.queue._queue[position-1]:
                return await ctx.send(embed=nextcord.Embed(description='Already in that `Position`!', color=embed_color))
            else:
                vc.queue.put_at_front(vc.queue._queue[position-1])
                del vc.queue._queue[position]    
                return await skip_command(ctx)
        else:
            return await ctx.send(embed=nextcord.Embed(description='No songs in the `QUEUE`', color=embed_color))

@commands.cooldown(1, 2, commands.BucketType.user)  
@commands.command(name='move', aliases=['set'], help='moves the track to the specified position', description=',move <song number> <position>')
@commands.has_role('tm')
async def move_command(ctx: commands.Context, song_position: int, move_position: int):
    if await user_connectivity(ctx) == False:
        return
    else:
        vc: wavelink.Player = ctx.voice_client
        if not vc.queue.is_empty:
            if song_position <= 0 or move_position <= 0:
                return await ctx.send(embed=nextcord.Embed(description=f'Position can not be `ZERO`* or `LESSER`', color=embed_color))
            elif song_position > song_count or move_position > song_count:
                position = song_position if song_position > song_count else move_position
                return await ctx.send(embed=nextcord.Embed(description=f'Position `{position}` is outta range!', color=embed_color))
            elif song_position == move_position:
                return await ctx.send(embed=nextcord.Embed(description=f'Already in that `Position`:{move_position}', color=embed_color))
            else:
                move_index = move_position-1 if move_position < song_position else move_position
                song_index = song_position if move_position < song_position else song_position-1
                vc.queue.put_at_index(move_index, vc.queue._queue[song_position-1])
                moved_song = vc.queue._queue[song_index]
                del vc.queue._queue[song_index]
                moved_song_name = moved_song.info['title']
                return await ctx.send(embed=nextcord.Embed(description=f'**{moved_song_name}** moved at Position:`{move_position}`', color=embed_color))
        else:
            return await ctx.send(embed=nextcord.Embed(description='No songs in the `QUEUE`!', color=embed_color))

@commands.cooldown(1, 2, commands.BucketType.user)  
@commands.command(name='volume',aliases=['vol'], help='sets the volume', description=',vol <number>')
@commands.has_role('tm')
async def volume_command(ctx: commands.Context, playervolume: int):
    if await user_connectivity(ctx) == False:
        return
    else:
        vc: wavelink.Player = ctx.voice_client
        if vc.is_connected():
            if playervolume > 100:
                return await ctx.send(embed= nextcord.Embed(description='**VOLUME** supported upto `100%`', color=embed_color))
            elif playervolume < 0:
                return await ctx.send(embed= nextcord.Embed(description='**VOLUME** can not be `negative`', color=embed_color))
            else:
                await ctx.send(embed=nextcord.Embed(description=f'**VOLUME**\nSet to `{playervolume}%`', color=embed_color))
                return await vc.set_volume(playervolume)
        elif not vc.is_connected():
            return await ctx.send(embed=nextcord.Embed(description="Player not connected!", color=embed_color))

@commands.cooldown(1, 2, commands.BucketType.user)  
@commands.command(name='seek', aliases=[], help='seeks or moves the player to specified track position', description=',seek <duration>')
@commands.has_role('tm')
async def seek_command(ctx: commands.Context, seekPosition: int):
    if await user_connectivity(ctx) == False:
        return
    else:
        vc: wavelink.Player = ctx.voice_client
        if not vc.is_playing():
            return await ctx.send(embed=nextcord.Embed(description='Player not playing!', color=embed_color))
        elif vc.is_playing():
            if 0 <= seekPosition <=  vc.track.length:
                msg = await ctx.send(embed=nextcord.Embed(description='seeking...', color=embed_color))
                await vc.seek(seekPosition*1000)
                return await msg.edit(embed=nextcord.Embed(description=f'Player SEEKED: `{seekPosition}` seconds',color=embed_color))
            else:
                return await ctx.send(embed=nextcord.Embed(description=f'SEEK length `{seekPosition}` outta range', color=embed_color))
            
@commands.cooldown(1, 5, commands.BucketType.user)
@commands.command(name='clear',aliases=[], help='clears the queue', description=',clear')
@commands.has_role('tm')
async def clear_command(ctx: commands.Context):
    vc: wavelink.Player = ctx.voice_client
    if await user_connectivity(ctx) == False:
        return
    else:
        if vc.queue.is_empty:
            return await ctx.send(embed= nextcord.Embed(description='No `SONGS` are present', color=embed_color))
        else:
            vc.queue._queue.clear()
            vc.lq = False
            clear_command_embed = nextcord.Embed(description=f'`QUEUE` cleared', color=embed_color)
            return await ctx.send(embed=clear_command_embed)

@commands.cooldown(1, 2, commands.BucketType.user)
@commands.command(name='save', aliases=['dm'], description=",save\n,save <song number | 'queue' | 'q'>", help='dms the current | specified song to the user')
async def save_command(ctx: commands.Context, savestr: Optional[str]):
    vc: wavelink.Player = ctx.voice_client
    if await user_connectivity(ctx) == False:
        return
    else:
        user = await client.fetch_user(ctx.author._user.id)
        if vc._source and savestr is None:
            await user.send(embed=nextcord.Embed(description=f'`{vc._source}`', color=embed_color))
        elif not vc.queue.is_empty and savestr == 'q' or savestr == 'queue':
            await user.send(embed=qem)
        elif not vc.queue.is_empty and savestr:
            if int(savestr) <= 0:
                return await ctx.send(embed=nextcord.Embed(description=f'Position can not be `ZERO`* or `LESSER`', color=embed_color))
            elif int(savestr) > song_count:
                return await ctx.send(embed=nextcord.Embed(description=f'Position `{savestr}` is outta range', color=embed_color))
            else:
                song_info = vc.queue._queue[int(savestr) - 1]
                em=nextcord.Embed(description=song_info.info['title'], color=embed_color)
                await user.send(embed=em)
        else:
            return await ctx.send(embed=nextcord.Embed(description='There is no `song` | `queue` available', color=embed_color))
        
        
# @commands.cooldown(1,2, commands.BucketType.user)
# @commands.command(name='lyrics', aliases=['l'], description=",lyrics | ,l", help='searches the lyrics for current song being played')
# async def lyrics_command(ctx: commands.Context):
#     vc: wavelink.Player = ctx.voice_client
#     if await user_connectivity(ctx) == False:
#         return
#     else:
#         mylyrics = []
#         genius = lyricsgenius.Genius(access_token=os.environ['lyrics_token'])
#         songstr = vc.track.title
#         searchmssg = await ctx.send(embed=nextcord.Embed(description=f'**searching the lyrics for {vc.track.title}...**', color = embed_color))
#         if '-' and '(' in songstr:
#             song = songstr.split(' - ')[1].split('(')[0]
#             author = songstr.split(' - ')[0]
#         elif '-' and '[' in songstr:
#             song = songstr.split(' - ')[1].split('[')[0]
#             author = songstr.split(' - ')[0]
#         elif '-' and '|' in songstr:
#             song = songstr.split(' - ')[1]
#             author = songstr.split(' - ')[0]
#         elif '|' in songstr:
#             song = songstr.split('|')[0]
#             author = songstr.split('|')[1]
#         else:
#             song = songstr
#             author = vc.track.author
#         # genius.verbose = False # Turn off status messages
#         genius.remove_section_headers = True    
#         songvalue = genius.search_song(song, author)
#         mylyrics.append(songvalue.lyrics)
#         if mylyrics is not None:
#             for i in mylyrics:
#                 await ctx.send(embed=nextcord.Embed(description=f'{i}', color=embed_color))
#                 await searchmssg.edit(embed=nextcord.Embed(description='**Search found!**', color=embed_color))
#         else:
#             await searchmssg.edit(embed=nextcord.Embed(description='**No lyrics found!**', color=embed_color))
'''main'''


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

#futures_position_alerts.start()

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
