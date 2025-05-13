import discord
from discord.ext import commands, tasks
import json
import os
import re
import time
from shared.server_data import MinecraftServer, MinecraftServerData

class MCServerStatus(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.shared_data = bot.shared_data
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
        new_content = self.shared_data.generate_mc_summary()
        if new_content != self.previous_content:
            # print("Content changed, updating message.")
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

async def setup(bot):
    await bot.add_cog(MCServerStatus(bot))
    print("MCServerStatus cog loaded.")