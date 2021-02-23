import discord
from discord.ext import commands
import os
import youtube_dl
from youtube_search import YoutubeSearch
import env
import asyncio

client = commands.Bot(command_prefix="!")
CURRENT_SONG = 0

loop = asyncio.get_event_loop()

ffmpeg_options = {
    'options': '-vn'
}

@client.command(pass_context=True)
async def play(ctx, *args: str):
    global loop
    term = " ".join(args[:])

    # determine channel
    channel_to_join_str = 'General'
    try:
       channel_to_join_str = str(ctx.message.author.voice.channel)
    except:
        await ctx.send("User must join a channel with a bot perrmission to join to it.")
        return

    # get voice channel
    voice_channel = discord.utils.get(ctx.guild.voice_channels, name=channel_to_join_str)

    # find a song
    song_object = get_song(term)
    if song_object is None:
        await ctx.send('sorry, nothing was found with given search term :(')
    else:

        # connect to voice
        try:
            await voice_channel.connect()
        except:
            print("voice already connected")
        voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
        if voice.is_playing():
            await ctx.send("Song already playing")
            return
        if voice.is_paused():
            await ctx.send("Previoius song is paused")
            return
        await ctx.send('playing ' + song_object.get('title') + "\n"
                       + "https://www.youtube.com" + song_object.get("url_suffix"))

        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192'
            }]
        }
        # download
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            loop = loop or asyncio.get_event_loop()
            data = await loop.run_in_executor(None, lambda: ydl.extract_info("https://www.youtube.com" + song_object.get("url_suffix"), download=False))

            if 'entries' in data:
                # take first item from a playlist
                data = data['entries'][0]

            filename = data['url']
            ydl.prepare_filename(data)
            voice.play(discord.FFmpegPCMAudio(filename, **ffmpeg_options))
            voice.source = discord.PCMVolumeTransformer(voice.source, volume=1.0)


@client.command()
async def leave(ctx):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    try:
        await voice.disconnect()
    except:
        await ctx.send("Bot is not connected to a voice channel.")


@client.command()
async def pause(ctx):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    try:
        voice.pause()
    except:
        await ctx.send("Bot is not singing at the moment.")


@client.command()
async def resume(ctx):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    try:
        voice.resume()
    except:
        await ctx.send("Bot is singing at the moment.")


@client.command()
async def stop(ctx):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    try:
        voice.stop()
    except:
        print("cant stop")

@client.command()
async def commands(ctx):
    await ctx.send("Useful commands: \n"
                   "!play <song name> \n"
                   "!pause \n"
                   "!resume \n"
                   "!leave \n"
                   "!stop")

@client.command()
async def volume(ctx, volume_int):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    try:
        volume_level = int(volume_int)
        if volume_level > 10 or volume_level < 1:
            await ctx.send("enter valid value betweeen 1 and 10.")
            return
        voice.source.volume = volume_level/10
    except Exception as e:
        await ctx.send("enter valid value betweeen 1 and 10.---" + str(e))

def get_song(search_term):
    search_results = YoutubeSearch(search_term, max_results=10)
    if len(search_results.videos) == 0:
        return None
    else:
        return search_results.videos[0]


client.run(env.TOKEN)
