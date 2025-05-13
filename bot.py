import discord
from discord.ext import commands, tasks
import asyncio
import json
import os
from dotenv import load_dotenv
import time

load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
if not TOKEN:
    raise ValueError("No token provided. Please set the DISCORD_BOT_TOKEN environment variable.")
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))
if not CHANNEL_ID:
    raise ValueError("No channel ID provided. Please set the CHANNEL_ID environment variable.")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)
tree = bot.tree

message_to_edit = None

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} - {bot.user.id}')
    await tree.sync()
    print('Bot is ready!')

    # load message id
    try:
        with open('message_id.json', 'r') as f:
            data = json.load(f)
            message_id = data.get('message_id')
        global message_to_edit
        message_to_edit = await bot.get_channel(CHANNEL_ID).fetch_message(message_id)
    except (FileNotFoundError, discord.NotFound):
        print("Message not found or file not found. Sending a new message.")
        channel = bot.get_channel(CHANNEL_ID)
        message_to_edit = await channel.send("This is a test message.")
        with open('message_id.json', 'w') as f:
            json.dump({'message_id': message_to_edit.id}, f)
    update_message.start()

@tree.command(name='whereami', description='Get the current channel ID')
async def whereami(interaction: discord.Interaction):
    """Get the current channel ID"""
    channel_id = interaction.channel.id
    await interaction.response.send_message(
        content=f"Channel ID: {channel_id}",
        ephemeral=True
    )

@tasks.loop(seconds=5)
async def update_message():
    """Update the message every 5 seconds"""
    print("Updating message...")
    global message_to_edit
    if message_to_edit:
        await message_to_edit.edit(content=f"Updated at {time.strftime('%H:%M:%S')}")
    else:
        print("Message not found.")

bot.run(TOKEN)