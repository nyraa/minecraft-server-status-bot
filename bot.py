import discord
from discord.ext import commands, tasks
import asyncio

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)
tree = bot.tree

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} - {bot.user.id}')
    await tree.sync()
    print('Bot is ready!')

@tree.command(name='whereami', description='Get the current channel ID')
async def whereami(interaction: discord.Interaction):
    """Get the current channel ID"""
    channel_id = interaction.channel.id
    await interaction.response.send_message(
        content=f"Channel ID: {channel_id}",
        ephemeral=True
    )