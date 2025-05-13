import discord
from discord.ext import commands
from discord import app_commands
import os
from shared.server_data import MinecraftServer, MinecraftServerData

GUILD_ID = os.getenv('GUILD_ID')
class RCON(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.shared_data = bot.shared_data
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
        await interaction.response.defer(thinking=True)
        
        # Here you would implement the logic to start the server
        # For now, we'll just simulate a response
        response = f"Server `{server_id}` started."
        await interaction.followup.send(response)
    
    @app_commands.command(name="down", description="Stop the Minecraft server")
    @app_commands.checks.has_permissions(administrator=True)
    async def down(self, interaction: discord.Interaction, server_id: str):
        await interaction.response.defer(thinking=True)
        
        # Here you would implement the logic to stop the server
        # For now, we'll just simulate a response
        response = f"Server `{server_id}` stopped."
        await interaction.followup.send(response)
    
    
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