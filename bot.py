import discord
from discord.ext import commands, tasks
import asyncio
import json
import os
from dotenv import load_dotenv
import re

load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
if not TOKEN:
    raise ValueError("No token provided. Please set the DISCORD_BOT_TOKEN environment variable.")
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))
if not CHANNEL_ID:
    raise ValueError("No channel ID provided. Please set the CHANNEL_ID environment variable.")
DOMAIN_BASE = os.getenv('MCSERVER_DOMAIN')
if not DOMAIN_BASE:
    raise ValueError("No Minecraft server domain provided. Please set the MCSERVER_DOMAIN environment variable.")
MCROOT = os.getenv('MCSERVER_PATH')
if not MCROOT:
    raise ValueError("No Minecraft server path provided. Please set the MCSERVER_PATH environment variable.")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

message_to_edit = None
previous_content = None

# for testing purposes
GUILD_ID = os.getenv('GUILD_ID')

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} - {bot.user.id}')
    await bot.change_presence(
        status=discord.Status.idle,
        activity=discord.Activity(type=discord.ActivityType.watching, name="伺服器們")
    )
    print('Bot is ready!')

async def load_extensions():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')
            print(f'Loaded extension: {filename[:-3]}')

async def main():
    async with bot:
        await load_extensions()
        await bot.start(TOKEN)

if __name__ == '__main__':
    asyncio.run(main())