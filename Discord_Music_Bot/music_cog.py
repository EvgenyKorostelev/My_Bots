import discord
from discord_components import Select, SelectOption, Button
from discord.ext import commands
import asyncio
from asyncio import run_coroutine_threadsafe
from urllib import parse, request
import re
import json
import os
from youtube_dl import YoutubeDL

# from discord import utils





class music_cog(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

        self.is_playing = {}
        self.is_paused = {}
        self.musicQueue = {}
        self.queueIndex = {}

        self.YTDL_OPTIONS = {'format': 'bestaudio', 'nonplaylist': 'True'}
        self.FFMPEG_OPTIONS = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
        
        self.embedBlue = 0x2c76dd
        self.embedRed = 0xdf1141
        self.embedGreen = 0x0eaa51
        # self.embedMyColor = 0x290000

        self.vc = {}


#ready      
    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            id = int(guild.id)
            self.musicQueue[id] = []
            self.queueIndex[id] = 0
            self.vc[id] = None
            self.is_paused[id] = self.is_playing[id] = False

#leave if all leave
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        id = int(member.guild.id)
        if member.id != self.bot.user.id and before.channel != None and after.channel != before.channel:
            remainingChannelMembers = before.channel.members
            if len(remainingChannelMembers) == 1 and remainingChannelMembers[0].id == self.bot.user.id:
                self.is_playing[id] = self.is_paused[id] = False
                self.musicQueue[id] = []
                self.queueIndex[id] = 0
                # self.vc[id] = ctx.guild.voice_client
                await self.vc[id].disconnect()
                # self.vc[id] = None

# now playing
    def now_playing_embed(self, ctx, song):
        title = song['title']
        link = song['link']
        thumbnail = song['thumbnail']
        author = ctx.author
        avatar = author.avatar.url

        embed = discord.Embed(
            title = "Сейчас поёт:",
            description = f'[{title}]({link})',
            colour = self.embedBlue,
        )
        embed.set_thumbnail(url=thumbnail)
        embed.set_footer(text=f'Песню добавил: {str(author)}, icon_url=avatar')
        return embed
    
# added song
    def added_song_embed(self, ctx, song):
        title = song['title']
        link = song['link']
        thumbnail = song['thumbnail']
        author = ctx.author
        avatar = author.avatar.url

        embed = discord.Embed(
            title = "Добавлено в очередь:",
            description = f'[{title}]({link})',
            colour = self.embedRed,
        )
        embed.set_thumbnail(url=thumbnail)
        embed.set_footer(text=f'Песню добавил: {str(author)}, icon_url=avatar')
        return embed
    
# remove song 
    def removed_song_embed(self, ctx, song):
        title = song['title']
        link = song['link']
        thumbnail = song['thumbnail']
        author = ctx.author
        avatar = author.avatar.url

        embed = discord.Embed(
            title = "Удалена из очереди:",
            description = f'[{title}]({link})',
            colour = self.embedRed,
        )
        embed.set_thumbnail(url=thumbnail)
        embed.set_footer(
            text=f'Песню удалил: {str(author)}, icon_url=avatar')
        return embed

    
    async def join_VC(self, ctx, channel):
        id = int(ctx.guild.id)
        if self.vc[id] == None or not self.vc[id].is_connected():
            self.vc[id] = await channel.connect()
            if self.vc[id] == None:
                await ctx.send("Не удалось подключится к голосовому каналу!")
                return
        else:
            await self.vc[id].move_to(channel)

    def get_YT_title(self, videoID):        
        params = {"format": "json", "url": "http://www.youtube.com/watch?v=%s" % videoID}
        url = "http://www.youtube.com/oemed"
        queryString = parse.urlencode(params)
        url = url + "?" + queryString
        with request.urlopen(url) as response:
            responseText = response.read()
            data = json.loads(responseText.decode())
            return data['title']

    def search_YT(self, search):
        queryString = parse.urlencode({'search_query': search})
        htmContent = request.urlopen('http://www.youtube.com/results?' + queryString)
        searchResults = re.findall('/watch\?v=(.{11})', htmContent.read().decode())
        return searchResults[0:10]
    
    def extract_YT(self, url):
        with YoutubeDL(self.YTDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
            except:
                return False
        return {
            'link': 'http://www.youtube.com/watch?v=' + url,
            'thumbnail': 'https://i.yting.com/vi/' + url + '/hqdefault.jpg?sqp=-oaymwEcCOADEI4CSFXyq4qpAw4IARUAAIhCGAFwAcABBg==&rs=AOn4CLD5uL4xKN-IUfez6KIW_j5y70mlig',
            'source': info.get('url'),
            'title': info['title']
        }
    
    
    async def play_next(self, ctx):
        id = int(ctx.guild.id)
        if not self.is_playing[id]:
            return
        if self.queueIndex[id] + 1 < len(self.musicQueue[id]):
            self.is_playing[id] = True
            self.queueIndex[id] += 1

            song = self.musicQueue[id][self.queueIndex[id]][0]
            message = self.now_playing_embed(ctx, song)
            coro = ctx.send(embed = message)
            fut = run_coroutine_threadsafe(coro, self.bot.loop)
            try:
                fut.result()
            except:
                pass

            self.vc[id].play(discord.FFmpegPCMAudio(
                song['source'], **self.FFMPEG_OPTIONS), after = lambda e: self.play_next(ctx))
        else:
            self.queueIndex[id] += 1
            self.is_playing[id] = False

    async def play_music(self, ctx):
        id = int(ctx.guild.id)
        if self.queueIndex[id] < len(self.musicQueue[id]):
            self.is_playing = True
            self.is_paused = False

            await self.join_VC(ctx, self.musicQueue[id][self.queueIndex[id]][1])

            song = self.musicQueue[id][self.queueIndex[id]][0]
            message = self.now_playing_embed(ctx, song)
            await ctx.send(embed = message)

            self.vc[id].play(discord.FFmpegPCMAudio(
                song['source'], **self.FFMPEG_OPTIONS), after = lambda e: self.play_next(ctx))
        else:
            await ctx.send("В очереди на воспроизведение нет песен!")
            self.queueIndex[id] += 1
            self.is_playing[id] = False

#play command
    @ commands.command(
        name = "play",
        aliases=["pl"],
        help=""
    )
    async def play(self, ctx, *args):
        search = " ".join(args)
        id = int(ctx.guild.id)
        try:
            userChannel = ctx.author.voice.channel
        except:
            await ctx.send("Вам нужно находиться в голосовом канале!")
            return
        if not args:
            if len(self.musicQueue[id]) == 0:
                await ctx.send("Список воспроизведения пуст!")
                return
            elif not self.is_playing[id]:
                if self.musicQueue[id] == None or self.vc[id] == None:
                    await self.play_music(ctx)
                else:
                    self.is_paused[id] = False
                    self.is_playing[id] = True
                    self.vc[id].resume()
            else:
                return
        else:
            song = self.extract_YT(self.search_YT(search)[0])
            if type(song) == type(True):
                await ctx.send("НЕ нашел! Попробуйте другую фразу для поиска.")
            else:
                self.musicQueue[id].append([song, userChannel])
                if not self.is_playing[id]:
                    await self.play_music(ctx) 
                else:
                    message = self.added_song_embed(ctx, song)
                    await ctx.send(embed=message)
#add command
    @ commands.command(
        name = "add",
        aliases=["a"],
        help=""
    )
    async def add(self, ctx, *args):
        search = " ".join(args)
        try:
            userChannel = ctx.author.voice.channel
        except:
            await ctx.send("Вы должны находиться в голосовом канале")
            return
        if not args:
            await ctx.send("Укажите песню, которую нужно добавить в очередь")
        else: 
            song = self.extract_YT(self.search_YT(search)[0])
            if type(song) == type(False):
                await ctx.send("НЕ нашел! Попробуйте другую фразу для поиска.")
                return
            else:
                self.musicQueue[ctx.guild.id].append([song, userChannel])
                message = self.added_song_embed(ctx, song)
                await ctx.send(embed=message)
        
#remove command
    @ commands.command(
        name = "remove",
        aliases=["rm"],
        help=""
    )
    async def remove(self, ctx):
        id = int(ctx.guild.id)
        if self.musicQueue[id] != []:
            song = self.musicQueue[id][-1][0]
            removeSongEmbed =  self.removed_song_embed(ctx, song)
            await ctx.send(embed=removeSongEmbed)
        else:
            await ctx.send("В очереди НЕТ песен")
        self.musicQueue[id] = self.musicQueue[id][:-1]
        if self.musicQueue[id] == []:
            if self.vc[id] != None and self.is_playing[id]:
                self.is_playing[id] = self.is_paused[id] = False
                await self.vc[id].disconnect()
                self.vc[id] = None
            self.queueIndex[id] = 0
        elif self.queueIndex[id] == len(self.musicQueue[id]) and self.vc[id] != None and self.vc[id]:
            self.vc[id].pause()
            self.queueIndex[id] -= 1
            await self.play_music(ctx)
            
            

#search command
    @ commands.command(
        name = "search",
        aliases=["find","sr"],
        help=""
    )
    async def search(self, ctx, *args):
        search = "".join(args)
        songNames = []
        selectionOptions = []
        embedText = ""

        if not args:
            await ctx.send("Укажите условия поиска")
            return
        try:
            userChannel = ctx.author.voice.channel
        except:
            await ctx.send("Вы должны находиться в голосовом канале")
            return

        await ctx.send("Получение результатов поиска . . .")

        songTokens = self.search_YT(search)

        for i, token in enumerate(songTokens):
            url = 'http://www.youtube.com/watch?v=' + token
            name = self.get_YT_title(token)
            songNames.append(name)
            embedText += f"{i+1} - [{name}]({url})\n"
        for i, title in enumerate(songNames):
            selectionOptions.append(SelectOption(
                label=f"{i+1} - {title[:95]}", value=i))

        searchResults = discord.Embed(
            title="Результаты поиска",
            description=embedText,
            colour=self.embedRed
        )
        selectionComponents = [
            Select(
                placeholder="Опции выбора",
                options=selectionOptions
            ),
            Button(
                label = "Отменить",
                custom_id = "Отменить",
                style = 4
            )
        ]
        message = await ctx.send(embed = searchResults, components = selectionComponents)
        try:
            tasks = [
                asyncio.create_task(self.bot.wait_for(
                    "button_click",
                    timeout = 60.0,
                    check = None
                ),name = "button"),
                asyncio.create_task(self.bot.wait_for(
                    "select_option",
                    timeout = 60.0,
                    check = None
                ),name = "select")
            ]
            done, pending = await asyncio.wait(tasks, return_when = asyncio.FIRST_COMPLETED)
            finished = list(done)[0]

            for task in pending:
                try:
                    task.cancel()
                except asyncio.CancelledError:
                    pass

            if finished == None:
                searchResults.title = "НЕ найдено"
                searchResults.description = ""
                await message.delete()
                await ctx.send(embed = searchResults)
                return
            
            action = finished.get_name()

            if action =="button":
                searchResults.title = "НЕ найдено"
                searchResults.description = ""
                await message.delete()
                await ctx.send(embed = searchResults)
            elif action == "select":
                result = finished.result()
                chosenIndex = int(result.values[0])
                songRef = self.extract_YT(songTokens[chosenIndex])
                if type(songRef) == type(True):
                    await ctx.send("НЕверный формат! Попробуйте другую фразу для поиска.")
                    return
                embedReponse = discord.Embed(
                    title = f"Опция #{chosenIndex + 1} выбрана",
                    description = f"[{songRef['title']}]({songRef['link']}) добавлены в очередь!",
                    colour = self.embedRed
                )
                embedReponse.set_thumbnail(url=songRef['thumbnail'])
                await message.delete()
                await ctx.send(embed=embedReponse)
                self.musicQueue[ctx.guild.id].append([songRef, userChannel])
        except:
            searchResults.title = "НЕ найдено"
            searchResults.description = ""
            await message.delete()
            await ctx.send(embed = searchResults)



#pause command
    @ commands.command(
        name = "pause",
        aliases=["stop","pa"],
        help=""
    )
    async def pause(self, ctx):
        id = int(ctx.guild.id)
        if not self.vc[id]:
            await ctx.send("Нечего паузить!")
        elif self.is_playing[id]:
            await ctx.send("Воспроизведение приостановлено")
            self.is_playing[id] = False
            self.is_paused[id] = True
            self.vc[id].pause()    

#resume command
    @ commands.command(
        name = "resume",
        aliases=["re"],
        help=""
    )
    async def pause(self, ctx):
        id = int(ctx.guild.id)
        if not self.vc[id]:
            await ctx.send("Нет музыки на паузе")
        elif self.is_paused[id]:
            await ctx.send("Воспроизведение продолжено")
            self.is_playing[id] = True
            self.is_paused[id] = False
            self.vc[id].resume()

#join command
    @ commands.command(
        name = "join",
        aliases=["j"],
        help=""
    )
    async def join(self, ctx):
        if ctx.author.voice:
            userChannel = ctx.author.voice.channel
            await self.join_VC(ctx, userChannel)
            await ctx.send(f'Music8_byAvetto вошел в канал: {userChannel}')
        else:
            await ctx.send("Вам нужно находиться в голосовом канале!")
#leave command
    @ commands.command(
        name = "leave",
        aliases=["l"],
        help=""
    )
    async def leave(self, ctx):
        id = int(ctx.guild.id)
        self.is_playing[id] = self.is_paused[id] = False
        self.musicQueue[id] = []
        self.queueIndex[id] = 0
        # self.vc[id] = ctx.guild.voice_client
        if self.vc[id] != None:
            # print(self.vc[id])
            await self.vc[id].disconnect()
            await ctx.send("Music8_byAvetto покинул голосовой канал!")
            self.vc[id] = None
      