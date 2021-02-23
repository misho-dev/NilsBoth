import discord
from discord.ext import commands
import os
import youtube_dl
from youtube_search import YoutubeSearch
import env

client = commands.Bot(command_prefix="!")
song_pool = ["song.mp3", "song1.mp3", "song2.mp3", "song3.mp3", "song4.mp3", "song5.mp3"]
CURRENT_SONG = 0

def getNextFromSongPool():
    global CURRENT_SONG
    CURRENT_SONG = (CURRENT_SONG + 1) % 6
    return song_pool[CURRENT_SONG]

@client.command(pass_context=True)
async def play(ctx, *args: str):
    term = " ".join(args[:])

    # determine channel
    channel_to_join_str = 'General'
    try:
       channel_to_join_str = str(ctx.message.author.voice.channel)
    except:
        await ctx.send("User must join a channel with a bot perrmission to join to it.")
        return

    # remove old file
    song_name = getNextFromSongPool()
    song_there = os.path.isfile(song_name)
    try:
        if song_there:
            os.remove(song_name)
    except PermissionError:
        await ctx.send("Wait for current music playing or use stop command")
        return

    # get voice channel
    voice_channel = discord.utils.get(ctx.guild.voice_channels, name=channel_to_join_str)

    # find a song
    await ctx.send('searching ' + term)
    song_object = get_song(term)
    if song_object is None:
        await ctx.send('sorry, nothing was found with given search term :(')
    else:
        await ctx.send('playing ' + song_object.get('title') + "\n"
                       + "https://www.youtube.com" + song_object.get("url_suffix"))

        # connect to voice
        try:
            await voice_channel.connect()
        except:
            print("voice already connected")
        voice = discord.utils.get(client.voice_clients, guild=ctx.guild)

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
            ydl.download(["https://www.youtube.com" + song_object.get("url_suffix")])
        for file in os.listdir("./"):
            if file.endswith(".mp3") and file not in song_pool:
                os.rename(file, song_name)
        # play
        voice.play(discord.FFmpegPCMAudio(song_name))
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
        print(" VOLUME LEVEL IS " + str(volume_level))
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
