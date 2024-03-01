# Discord_Bot_for_music
from music_cog import music_cog
from help_cog import help_cog
import asyncio
from discord.ext import commands
import discord


bot = commands.Bot(command_prefix = '+', intents=discord.Intents.all())

with open('token.txt', 'r') as file:
    token = file.readlines()[0]

async def main():
    async with bot:
        bot.remove_command('help')
        await bot.add_cog(music_cog(bot))
        await bot.add_cog(help_cog(bot))
        await bot.start(token)

asyncio.run(main())