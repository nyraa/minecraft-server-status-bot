import discord
from discord.ext import commands, tasks
import json
import os
import re
import time

class MCServerStatus(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.message_to_edit = None
        self.previous_content = None
        self.channel_id = int(os.getenv('CHANNEL_ID'))
        self.domain_base = os.getenv('MCSERVER_DOMAIN')
        self.mcroot = os.getenv('MCSERVER_PATH')
        self.check_for_updates.start()
    
    def cog_unload(self):
        self.check_for_updates.stop()
    
    @tasks.loop(seconds=10)
    async def check_for_updates(self):
        await self.bot.wait_until_ready()
        channel = self.bot.get_channel(self.channel_id)
        new_content = self.generate_mc_summary()
        if new_content != self.previous_content:
            print("Content changed, updating message.")
            self.previous_content = new_content
            try:
                if not self.message_to_edit:
                    with open('message_id.json', 'r') as f:
                        data = json.load(f)
                        message_id = data.get('message_id')
                        if message_id:
                            self.message_to_edit = await channel.fetch_message(message_id)
                # may raise discord.NotFound if the message is deleted
                await self.message_to_edit.edit(content=new_content)
            except (FileNotFoundError, discord.NotFound):
                self.message_to_edit = await channel.send(new_content)
                with open('message_id.json', 'w') as f:
                    json.dump({'message_id': self.message_to_edit.id}, f)
        
    def parse_start_sh(self, path):
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

    def parse_properties(self, path):
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

    def parse_json_names(self, path):
        if not os.path.exists(path):
            return []
        with open(path, "r") as f:
            try:
                data = json.load(f)
                return [entry["name"] for entry in data if "name" in entry]
            except json.JSONDecodeError:
                return []

    def generate_mc_summary(self):
        summary = []
        for server_id in os.listdir(self.mcroot):
            server_path = os.path.join(self.mcroot, server_id)
            if not os.path.isdir(server_path):
                continue

            start_meta = self.parse_start_sh(os.path.join(server_path, "start.sh"))
            if start_meta.get("visible-to-bot", "false") != "true":
                continue

            name = start_meta.get("server-name") or server_id
            version = start_meta.get("server-version") or "unknown"
            type_ = start_meta.get("server-type") or "unknown"

            prop_path = os.path.join(server_path, "server.properties")
            port = start_meta.get("server-port") or self.parse_properties(prop_path) or "????"
            ip = start_meta.get("server-ip") or self.domain_base
            domain = f"{ip}:{port}"

            ops = self.parse_json_names(os.path.join(server_path, "ops.json"))
            whitelist = self.parse_json_names(os.path.join(server_path, "whitelist.json"))

            autostart = os.path.exists(os.path.join(server_path, "auto-start.sh"))

            summary.append(f"""\
### {name}（{version} {type_}）
- ID: `{server_id}`
- IP: `{domain}`
- OPs: {', '.join([f'`{op}`' for op in ops]) if ops else '_None_'}
- 白名單: {', '.join([f'`{player}`' for player in whitelist]) if whitelist else '_None_'}
- 開機自動啟動: {"度" if autostart else "否"}""")

        if not summary:
            return "No visible servers found."
        return """
# 伺服器清單
如果有沒有啥異狀或是要op或白名單就去主頻道tag服主
""" + "\n\n".join(summary) # + "\n\n" + f"最後更新: <t:{int(time.time())}:R>"


async def setup(bot):
    await bot.add_cog(MCServerStatus(bot))
    print("MCServerStatus cog loaded.")