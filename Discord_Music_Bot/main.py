"""main program module"""

import asyncio
import discord
from discord.ext import commands
from music_cog import Music
from help_cog import Help


bot = commands.Bot(command_prefix="+", intents=discord.Intents.all())

with open("token.txt", "r", encoding="utf-8") as file:
    token = file.readlines()[0]


async def main():
    """Delete help command, add cogs and launch bot"""
    async with bot:
        bot.remove_command("help")
        await bot.add_cog(Music(bot))
        await bot.add_cog(Help(bot))
        await bot.start(token)


asyncio.run(main())
