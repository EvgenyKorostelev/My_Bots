import discord
from discord.ext import commands

class help_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.embedOrange = 0xeab148

# ready status
    @commands.Cog.listener()
    async def on_ready(self):
        sendToChannels = []
        for guild in self.bot.guilds:
            channel = guild.text_channels[0]
            sendToChannels.append(channel)
        helloEmbed = discord.Embed(
            title = "Здарова бандиты!",
            description = """Я 8™_Бот, для проигрывания музыки с Youtube! Мой префикс **`+`**, для использования команд. Используйте **`+help`**, для получения списка команд.""",
            colour = self.embedOrange
        )
        for channel in sendToChannels:
            await channel.send(embed = helloEmbed)

# help command
    @commands.command(
        name = "help",
        aliases = ["h"],
        help = " -Предоставляет описание всех указанных команд."
    )
    async def help(self, ctx):
        helpCog = self.bot.get_cog('help_cog')
        musicCog = self.bot.get_cog('music_cog')
        commands = helpCog.get_commands() + musicCog.get_commands()
        commandDescription = ""

        for c in commands:
            commandDescription += f"**`+{c.name}`** {c.help}\n"
        commandsEmbed = discord.Embed(
            title = "Список команд",
            description = commandDescription,
            colour = self.embedOrange
        )
        await ctx.send(embed = commandsEmbed)
