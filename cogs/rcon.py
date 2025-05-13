import discord
from discord.ext import commands
from discord import app_commands
import os
from mcrcon import MCRcon

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
        
        print(f"Running RCON command `{command}` on server `{server}`")
        try:
            rcon_response = self.run_rcon_command(server, command)
        except ValueError as e:
            await interaction.followup.send(f"Error: {e}", ephemeral=True)
            return
        if rcon_response:
            await interaction.followup.send(f"RCON response: {rcon_response}", ephemeral=True)
        else:
            await interaction.followup.send("No response from RCON.", ephemeral=True)

    @app_commands.command(name="up", description="Start the Minecraft server")
    async def up(self, interaction: discord.Interaction, server: str):
        await interaction.response.defer(thinking=True)
        server_path = os.path.join(self.mcroot, server)
        if not os.path.exists(server_path):
            await interaction.followup.send(f"Server `{server}` does not exist.", ephemeral=True)
            return
        start_sh_path = os.path.join(server_path, "start.sh")
        if not os.path.exists(start_sh_path):
            await interaction.followup.send(f"Server `{server}` does not have a start.sh file.", ephemeral=True)
            return
        # Here you would implement the logic to start the server
        # For now, we'll just simulate a response
        response = f"Server `{server}` started."
        await interaction.followup.send(response)
    
    @app_commands.command(name="down", description="Stop the Minecraft server")
    async def down(self, interaction: discord.Interaction, server: str):
        await interaction.response.defer(thinking=True)
        server_path = os.path.join(self.mcroot, server)
        if not os.path.exists(server_path):
            await interaction.followup.send(f"Server `{server}` does not exist.", ephemeral=True)
            return
        start_sh_path = os.path.join(server_path, "start.sh")
        if not os.path.exists(start_sh_path):
            await interaction.followup.send(f"Server `{server}` does not have a start.sh file.", ephemeral=True)
            return
        # Here you would implement the logic to stop the server
        # For now, we'll just simulate a response
        response = f"Server `{server}` stopped."
        await interaction.followup.send(response)
    
    
    @up.autocomplete("server")
    @down.autocomplete("server")
    @rcon.autocomplete("server")
    async def server_autocomplete(self, interaction: discord.Interaction, current: str):
        server_dirs = [d for d in os.listdir(self.mcroot) if os.path.isdir(os.path.join(self.mcroot, d))]
        return [app_commands.Choice(name=server, value=server) for server in server_dirs if current.lower() in server.lower()]

    def get_server_properties(self, server: str):
        server_path = os.path.join(self.mcroot, server)
        properties_path = os.path.join(server_path, "server.properties")
        if not os.path.exists(properties_path):
            return None
        with open(properties_path, "r") as f:
            properties = {}
            for line in f:
                if "=" in line:
                    key, value = line.split("=", 1)
                    properties[key.strip()] = value.strip()
            return properties

    def run_rcon_command(self, server: str, command: str):
        server_properties = self.get_server_properties(server)
        if not server_properties:
            raise ValueError(f"Server `{server}` does not have a valid server.properties file.")
        if server_properties.get("enable-rcon") != "true":
            raise ValueError(f"RCON is not enabled for server `{server}`.")
        rcon_port = int(server_properties.get("rcon.port"))
        rcon_password = server_properties.get("rcon.password")
        if not rcon_port or not rcon_password:
            raise ValueError(f"RCON port or password not set for server `{server}`.")
        with MCRcon("127.0.0.1", port=rcon_port, password=rcon_password) as mcr:
            if mcr:
                response = mcr.command(command)
                return response
            else:
                raise ValueError(f"Failed to connect to RCON for server `{server}`.")

async def setup(bot: commands.Bot):
    await bot.add_cog(RCON(bot), guilds=[discord.Object(id=GUILD_ID)])
    print("RCON cog loaded.")