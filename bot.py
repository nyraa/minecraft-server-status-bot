import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import json
import os
from dotenv import load_dotenv
import re
from shared.server_data import MinecraftServer, MinecraftServerData

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
# for testing purposes
GUILD_ID = os.getenv('GUILD_ID')

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} - {bot.user.id}')
    await bot.change_presence(
        status=discord.Status.idle,
        activity=discord.Activity(type=discord.ActivityType.watching, name="伺服器們")
    )
    # await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
    # bot.tree.clear_commands(guild=discord.Object(id=GUILD_ID))
    slash = await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
    print(f"Synced {len(slash)} commands to the guild.")
    print('Bot is ready!')

@bot.tree.command(name="reload", description="Reload all cogs", guild=discord.Object(id=GUILD_ID))
@app_commands.checks.has_permissions(administrator=True)
async def reload_cogs(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True, ephemeral=True)
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.reload_extension(f'cogs.{filename[:-3]}')
            print(f'Reloaded extension: {filename[:-3]}')
    await interaction.followup.send("All cogs reloaded successfully!", ephemeral=True)

@bot.tree.command(name="hej", description="問問小精靈在不在線上", guild=discord.Object(id=GUILD_ID))
async def hej(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True, ephemeral=True)
    await interaction.followup.send("燈在這", ephemeral=True)

async def load_extensions():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')
            print(f'Loaded extension: {filename[:-3]}')

async def main():
    async with bot:
        bot.shared_data = MinecraftServerData(MCROOT, DOMAIN_BASE)
        await load_extensions()
        await bot.start(TOKEN)

if __name__ == '__main__':
    asyncio.run(main())