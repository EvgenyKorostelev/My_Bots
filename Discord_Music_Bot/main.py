"""main program module"""

import asyncio
import discord
from music_cog import music_cog
from help_cog import help_cog
from discord.ext import commands


bot = commands.Bot(command_prefix="+", intents=discord.Intents.all())

with open("token.txt", "r", encoding="utf-8") as file:
    token = file.readlines()[0]


async def main():
    """Delete help command, add cogs and start token"""
    async with bot:
        bot.remove_command("help")
        await bot.add_cog(music_cog(bot))
        await bot.add_cog(help_cog(bot))
        await bot.start(token)


asyncio.run(main())
