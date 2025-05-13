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

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} - {bot.user.id}')
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
        message_to_edit = await channel.send("Server status will be updated here.")
        with open('message_id.json', 'w') as f:
            json.dump({'message_id': message_to_edit.id}, f)
    check_for_updates.start()

@tasks.loop(seconds=10)
async def check_for_updates():
    global message_to_edit, previous_content
    channel = bot.get_channel(CHANNEL_ID)
    new_content = generate_mc_summary()
    if new_content != previous_content:
        print("Content changed, updating message.")
        previous_content = new_content
        if message_to_edit:
            await message_to_edit.edit(content=new_content)
        else:
            message_to_edit = await channel.send(new_content)
            with open('message_id.json', 'w') as f:
                json.dump({'message_id': message_to_edit.id}, f)


def parse_start_sh(path):
    result = {
        "server-name": None,
        "server-version": None,
        "server-type": None,
        "server-port": None,
        "server-ip": None,
        "visible-to-bot": "false"
    }
    if not os.path.exists(path):
        return result
    with open(path, "r") as f:
        for line in f:
            if m := re.match(r"#\s*server-name:\s*(.+)", line):
                result["server-name"] = m.group(1).strip()
            elif m := re.match(r"#\s*server-version:\s*(.+)", line):
                result["server-version"] = m.group(1).strip()
            elif m := re.match(r"#\s*server-type:\s*(.+)", line):
                result["server-type"] = m.group(1).strip()
            elif m := re.match(r"#\s*server-port:\s*(.+)", line):
                result["server-port"] = m.group(1).strip()
            elif m := re.match(r"#\s*server-ip:\s*(.+)", line):
                result["server-ip"] = m.group(1).strip()
            elif m := re.match(r"#\s*visible-to-bot:\s*(.+)", line):
                result["visible-to-bot"] = m.group(1).strip().lower()
    return result

def parse_properties(path):
    port = None
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        for line in f:
            if not line.strip().startswith("server-port"):
                continue
            key, val = line.strip().split("=", 1)
            port = val.strip()
            break
    return port

def parse_json_names(path):
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        try:
            data = json.load(f)
            return [entry["name"] for entry in data if "name" in entry]
        except json.JSONDecodeError:
            return []

def generate_mc_summary():
    summary = []
    for server_id in os.listdir(MCROOT):
        server_path = os.path.join(MCROOT, server_id)
        if not os.path.isdir(server_path):
            continue

        start_meta = parse_start_sh(os.path.join(server_path, "start.sh"))
        if start_meta.get("visible-to-bot", "false") != "true":
            continue

        name = start_meta.get("server-name") or server_id
        version = start_meta.get("server-version") or "unknown"
        type_ = start_meta.get("server-type") or "unknown"

        prop_path = os.path.join(server_path, "server.properties")
        port = start_meta.get("server-port") or parse_properties(prop_path) or "????"
        ip = start_meta.get("server-ip") or DOMAIN_BASE
        domain = f"{ip}:{port}"

        ops = parse_json_names(os.path.join(server_path, "ops.json"))
        whitelist = parse_json_names(os.path.join(server_path, "whitelist.json"))

        autostart = os.path.exists(os.path.join(server_path, "auto-start.sh"))

        summary.append(f"""\
### {name}（{version} {type_}）
- ID: `{server_id}`
- IP: `{domain}`
- OPs: {', '.join(ops) if ops else '_None_'}
- Whitelist: {', '.join(whitelist) if whitelist else '_None_'}
- Auto start: {"Yes" if autostart else "No"}""")

    if not summary:
        return "No visible servers found."
    return "# Minecraft Servers\n\n" + "\n\n".join(summary)

bot.run(TOKEN)