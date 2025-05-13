import discord
from discord.ext import commands
from discord import app_commands
import os
import subprocess
from shared.server_data import MinecraftServer, MinecraftServerData

GUILD_ID = os.getenv('GUILD_ID')
class RCON(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.shared_data: MinecraftServerData = bot.shared_data
        self.mcroot = os.getenv('MCSERVER_PATH')
    
    @app_commands.command(name="rcon", description="Send a command to the Minecraft server")
    @app_commands.checks.has_permissions(administrator=True)
    async def rcon(self, interaction: discord.Interaction, server_id: str, command: str):
        await interaction.response.defer(thinking=True)
        server = self.shared_data.get_server_by_id(server_id)
        
        print(f"Running RCON command `{command}` on server `{server_id}`")
        try:
            rcon_response = server.run_rcon_command(command)
        except ValueError as e:
            await interaction.followup.send(f"Error: {e}", ephemeral=True)
            return
        if rcon_response:
            await interaction.followup.send(f"RCON response: {rcon_response}", ephemeral=True)
        else:
            await interaction.followup.send("No response from RCON.", ephemeral=True)

    @app_commands.command(name="up", description="Start the Minecraft server")
    @app_commands.checks.has_permissions(administrator=True)
    async def up(self, interaction: discord.Interaction, server_id: str):
        print(f"Starting server `{server_id}`")
        await interaction.response.defer(thinking=True)
        
        # check if server id exists
        server = self.shared_data.get_server_by_id(server_id)
        if not server:
            await interaction.followup.send(f"Server `{server_id}` not found.", ephemeral=True)
            return
        # Run the server start script
        script_path = os.path.expanduser("~/minecraft-launch.sh")
        process = subprocess.run([script_path, server_id], capture_output=True, text=True)
        
        # Handle the return code
        if process.returncode == 0:
            response = f"Server `{server_id}` started successfully."
        elif process.returncode == 1:
            response = f"Server `{server_id}` is already running."
        elif process.returncode == 2:
            response = f"Server `{server_id}` not found."
        else:
            response = f"Failed to start server `{server_id}`. Error: {process.stderr}"
        await interaction.followup.send(response)
    
    @app_commands.command(name="down", description="Stop the Minecraft server")
    @app_commands.checks.has_permissions(administrator=True)
    async def down(self, interaction: discord.Interaction, server_id: str):
        await interaction.response.defer(thinking=True)
        print(f"Stopping server `{server_id}`")
        # check if server id exists
        server = self.shared_data.get_server_by_id(server_id)
        if not server:
            await interaction.followup.send(f"Server `{server_id}` not found.", ephemeral=True)
            return
        
        # Stop the server via RCON
        try:
            rcon_response = server.run_rcon_command("stop")
        except ValueError as e:
            await interaction.followup.send(f"Error: {e}", ephemeral=True)
            return
        await interaction.followup.send(rcon_response)
    
    
    @up.autocomplete("server_id")
    @down.autocomplete("server_id")
    @rcon.autocomplete("server_id")
    @app_commands.checks.has_permissions(administrator=True)
    async def server_autocomplete(self, interaction: discord.Interaction, current: str):
        server_dirs = self.shared_data.get_server_list()
        return [app_commands.Choice(name=server, value=server) for server in server_dirs if current.lower() in server.lower()]

async def setup(bot: commands.Bot):
    await bot.add_cog(RCON(bot), guilds=[discord.Object(id=GUILD_ID)])
    print("RCON cog loaded.")