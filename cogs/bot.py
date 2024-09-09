import discord
from discord.ext import commands
import yt_dlp

# FFmpeg options
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn -b:a 192k'
}

# YDL options
YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'extract-audio': True,
    'audio-format': 'mp3',
    'audio-quality': '192K',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'force-ipv4': True
}

class MusicBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = []

    # The bot is ready
    @commands.Cog.listener()
    async def on_ready(self):
        print(f'{self.bot.user.name} has connected to Discord!')

    # Disconnect if the bot is alone in the voice channel
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after) -> None:
        voice_channel = before.channel or after.channel
        if voice_channel is not None:
            voice_client = discord.utils.get(self.bot.voice_clients, guild=voice_channel.guild)
            if voice_client is not None and voice_client.channel == voice_channel:
                if len(voice_channel.members) == 1:
                    await voice_client.disconnect()
                    self.queue = []

    # Say hello to the user
    @commands.command(name='hello', help='Say hello to the user')
    async def hello(self, ctx: commands.Context) -> None:
        await ctx.send(f'Hello there! {ctx.author.mention}')

    # Join the voice channel
    @commands.command(name='join', help='Join the voice channel')
    async def join(self, ctx: commands.Context) -> None:
        voice_channel = ctx.author.voice.channel if ctx.author.voice else None
        if not voice_channel:
            return await ctx.send('You need to be in a voice channel to use this command!')

        if not ctx.voice_client:
            await voice_channel.connect()
    
    # Leave the voice channel
    @commands.command(name='leave', help='Leave the voice channel')
    async def leave(self, ctx: commands.Context) -> None:
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            self.queue = []
        else:
            await ctx.send('I am not in a voice channel!')

    # play the music
    @commands.command(name='play', help='Play the music')
    async def play(self, ctx: commands.Context, *, queue: str) -> None:
        voice_channel = ctx.author.voice.channel if ctx.author.voice else None
        if not voice_channel:
            return await ctx.send('You need to be in a voice channel to play music!')

        if not ctx.voice_client:
            await voice_channel.connect()

        async with ctx.typing():
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:

                try:
                    info = ydl.extract_info(f"ytsearch:{queue}", download=False)['entries'][0]

                    # Get the info
                    url = info['url']
                    title = info['title']
                    thumbnail = info['thumbnail']
                    channel = info['channel']
                    duration = info['duration']

                    # Add the song to the queue
                    self.queue.append((url, title, thumbnail, channel, duration))
                    await ctx.send(f'Added {title} to the queue')

                except Exception as e:
                    await ctx.send('An error occurred while processing this request!')
        
        if not ctx.voice_client.is_playing():
            await self.play_next(ctx)

    # Play the next song
    async def play_next(self, ctx: commands.Context) -> None:

        if self.queue:
            url, title, thumbnail, channel, duration = self.queue.pop(0)
            source = await discord.FFmpegOpusAudio.from_probe(url, **FFMPEG_OPTIONS)
            ctx.voice_client.play(source, after=lambda _:self.bot.loop.create_task(self.play_next(ctx)))

            # Convert the duration to minutes
            minutes, seconds = divmod(duration, 60)
            duration_str = f"{minutes}:{seconds} minutes"
            
            # embed the current song
            embed = discord.Embed(title="Now Playing", description=title, color=discord.Color.green())
            embed.set_author(name=f"Requested by {ctx.author}", icon_url=ctx.author.avatar)
            embed.add_field(name='Channel', value=channel, inline=True)
            embed.add_field(name='Duration', value=duration_str, inline=True)
            embed.set_image(url=thumbnail)
            await ctx.send(embed=embed)

        else:
            embed = discord.Embed(title='Queue is empty!', color=discord.Color.red())
            await ctx.send(embed=embed)

    # Skip the current song
    @commands.command(name='skip', help='Skip the current song')
    async def skip(self, ctx: commands.Context) -> None:
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            embed = discord.Embed(title='Song Skipped!', color=discord.Color.blue())
            await ctx.send(embed=embed)

    # Show the queue
    @commands.command(name='queue', help='Show the queue')
    async def queue(self, ctx: commands.Context) -> None:
        if self.queue:
            songs_to_display = self.queue[:15]
            
            embed = discord.Embed(title='Current queue', color=discord.Color.yellow())
            for index, item in enumerate(songs_to_display, start=1):

                # Convert the duration to minutes
                minutes, seconds = divmod(item[4], 60)
                duration_str = f"{minutes}:{seconds} minutes"

                embed.add_field(name=f'{index}. {item[1]}', value=f'Duration: {duration_str}', inline=True)
            
            if len(self.queue) > 15:
                embed.set_footer(text=f"And {len(self.queue) - 15} more songs...")
            
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title='Queue is empty!', color=discord.Color.red())
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(MusicBot(bot))