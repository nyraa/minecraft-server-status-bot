import discord
from discord.ext import commands
from discord import app_commands
import os

GUILD_ID = os.getenv('GUILD_ID')
class RCON(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.mcroot = os.getenv('MCSERVER_PATH')
    
    @app_commands.command(name="rcon", description="Send a command to the Minecraft server")
    async def rcon(self, interaction: discord.Interaction, server: str, command: str):
        await interaction.response.defer(thinking=True)
        server_path = os.path.join(self.mcroot, server)
        if not os.path.exists(server_path):
            await interaction.followup.send(f"Server `{server}` does not exist.", ephemeral=True)
            return
        start_sh_path = os.path.join(server_path, "start.sh")
        if not os.path.exists(start_sh_path):
            await interaction.followup.send(f"Server `{server}` does not have a start.sh file.", ephemeral=True)
            return
        # Here you would implement the logic to send the command to the server using RCON
        # For now, we'll just simulate a response
        response = f"Command `{command}` sent to server `{server}`."
        await interaction.followup.send(response)

async def setup(bot: commands.Bot):
    await bot.add_cog(RCON(bot), guilds=[discord.Object(id=GUILD_ID)])
    print("RCON cog loaded.")