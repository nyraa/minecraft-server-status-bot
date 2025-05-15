from discord.ext import tasks
import os
import re
import json
import time
from mcrcon import MCRcon

class MinecraftServer:
    def __init__(self, server_id: str, mcroot: str, domain_base: str):
        self.visible = False
        self.properties = {}
        self.ops = []
        self.whitelist = []
        self.start_meta = {}
        self.server_type = None
        self.server_id = server_id
        self.server_path = os.path.join(mcroot, server_id)
        self.domain_base = domain_base
        self.autostart = False
        self.mrc = None
        self.max_players = 0
        self.current_players = 0
        self.online_players = []
        self.online = False
        self.no_rcon = True
        self.tps = []   # 1m, 5m, 15m
    
    def __del__(self):
        if self.mrc:
            self.mrc.disconnect()
            self.mrc = None

    def load_data(self) -> bool:
        self.start_meta = self._parse_start_sh(os.path.join(self.server_path, "start.sh"))
        if not self.start_meta:
            return False
        self.server_type = self.start_meta.get("server-type")
        self.properties = self._parse_properties(os.path.join(self.server_path, "server.properties"))
        if not self.properties:
            return False
        self.ops = self._parse_json_names(os.path.join(self.server_path, "ops.json"))
        self.whitelist = self._parse_json_names(os.path.join(self.server_path, "whitelist.json"))
        self.autostart = os.path.exists(os.path.join(self.server_path, "auto-start.sh"))
        self.visible = self.start_meta.get("visible-to-bot", "false") == "true"
        if self.visible:
            if self.properties.get("enable-rcon") == "true" and self.properties.get("rcon.port") and self.properties.get("rcon.password"):
                self.no_rcon = False
                # RCON is enabled, try to connect
                try:
                    if not self.mrc:
                        self.mrc = MCRcon('localhost', port=int(self.properties.get("rcon.port")), password=self.properties.get("rcon.password", ""))
                        self.mrc.connect()
                    if self.mrc:
                        # Connected to RCON, server is online
                        self.online = True

                        # Get online players
                        rcon_response = self.mrc.command("list")
                        if rcon_response:
                            match = re.search(r"(\d+).*?(\d+).*\:(.*)", rcon_response)
                            if match:
                                # Parse the response successfully
                                self.current_players = int(match.group(1))
                                self.max_players = int(match.group(2))
                                self.online_players = [player for raw in match.group(3).split(",") if (player := raw.strip())]
                        
                        # Get TPS
                        if self.server_type in ["paper", "spigot", "bukkit"]:
                            tps_response = self.mrc.command("tps")
                            if tps_response:
                                match = re.search(r"(\d+\.\d+)[^\d]*(\d+\.\d+)[^\d]*(\d+\.\d+)", tps_response)
                                if match:
                                    # Parse the response successfully
                                    self.tps = [float(match.group(1)), float(match.group(2)), float(match.group(3))]

                except ConnectionRefusedError:
                    # RCON on in properties but connection refused, not started
                    self.mrc = None
                    self.online = False
                except Exception as e:
                    # RCON on in properties, unknown error
                    print(f"Error connecting to RCON for server `{self.server_id}`: {type(e).__name__} - {e}")
                    self.mrc = None
                    self.online = False
            else:
                # RCON not set up in properties
                self.mrc = None
                self.no_rcon = True
                self.online = False
        return True

    def run_rcon_command(self, command: str):
        if self.properties.get("enable-rcon") != "true":
            raise ValueError(f"Server `{self.server_id}` does not have RCON enabled.")
        rcon_port = self.properties.get("rcon.port")
        rcon_password = self.properties.get("rcon.password")
        if not rcon_port or not rcon_password:
            raise ValueError(f"Server `{self.server_id}` does not have RCON port or password set.")
        with MCRcon('localhost', port=int(rcon_port), password=rcon_password) as mcr:
            if mcr:
                response = mcr.command(command)
                return response
            else:
                raise ValueError(f"Failed to connect to RCON for server `{self.server_id}`.")

    
    def _parse_start_sh(self, path):
        result = {
            "server-name": None,
            "server-version": None,
            "server-type": "Unknown",
            "server-port": None,
            "server-ip": None,
            "visible-to-bot": "false"
        }
        if not os.path.exists(path):
            return None
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

    def _parse_properties(self, path):
        properties_path = os.path.join(self.server_path, "server.properties")
        if not os.path.exists(properties_path):
            return None
        with open(properties_path, "r") as f:
            properties = {}
            for line in f:
                if "=" in line:
                    key, value = line.split("=", 1)
                    properties[key.strip()] = value.strip()
            return properties

    def _parse_json_names(self, path):
        if not os.path.exists(path):
            return []
        with open(path, "r") as f:
            try:
                data = json.load(f)
                return [entry["name"] for entry in data if "name" in entry]
            except json.JSONDecodeError:
                return []

class MinecraftServerData:
    def __init__(self, mcroot: str, domain_base: str):
        self.mcroot = mcroot
        self.domain_base = domain_base
        self.servers = {}
        self._scan_servers.start()

    def __del__(self):
        self._scan_servers.stop()
        
    def get_server_by_id(self, server_id: str) -> MinecraftServer:
        # return a server object by ID, ignore unvisible servers
        server = self.servers.get(server_id)
        if server and server.visible:
            return server
        return None

    def get_server_list(self) -> list:
        # return a list of server IDs with visible to bot
        server_list = []
        for server_id, server in self.servers.items():
            if server.visible:
                server_list.append(server_id)
        return server_list

    def generate_mc_summary(self) -> str:
        summary = []
        for server_id, server in self.servers.items():
            if not server.visible:
                continue


            name = server.start_meta.get("server-name") or server_id
            version = server.start_meta.get("server-version") or "unknown"
            server_type = server.start_meta.get("server-type") or "unknown"

            port = server.start_meta.get("server-port") or server.properties.get('server-port') or "????"
            ip = server.start_meta.get("server-domain") or self.domain_base
            domain = f"{ip}:{port}"

            ops = server.ops
            whitelist = server.whitelist

            autostart = server.autostart

            summary.append(f"""\
### {"❌" if server.no_rcon else ("🟢" if server.online else "🔴")} {name} [{version} {server_type}]{f" - ({server.current_players}/{server.max_players})" if server.online else ""}
- ID: `{server_id}`
- IP: `{domain}`
- OPs: {', '.join([f'`{op}`' for op in ops]) if ops else '_None_'}
- 白名單: {', '.join([f'`{player}`' for player in whitelist]) if whitelist else '_None_'}
""" + 
(f"""\
- 線上玩家: {', '.join([f'`{player}`' for player in server.online_players]) if server.online_players else '_None_'}
- 玩家數: {server.current_players}/{server.max_players}
""" if server.online else "") + 
(f"""\
- TPS: {", ".join(map(str, server.tps))}
""" if server.online and len(server.tps) > 0 else "") +
f"""\
- 開機自動啟動: {"度" if autostart else "否"}""")

        if not summary:
            return "No visible servers found."
        return """
# 伺服器清單
如果有沒有啥異狀或是要op或白名單就去主頻道tag服主
""" + "\n\n".join(summary) + "\n\n" + f"最後更新: <t:{int(time.time())}:R>"

    @tasks.loop(seconds=10)
    async def _scan_servers(self):
        for server_id in os.listdir(self.mcroot):
            existed_server = self.servers.get(server_id)
            if existed_server:
                valid = existed_server.load_data()
                if not valid:
                    print(f"Server {server_id} is invalid, removing from cache.")
                    del self.servers[server_id]
                    continue
                continue
                
            server_path = os.path.join(self.mcroot, server_id)
            if not os.path.isdir(server_path):
                continue
            server = MinecraftServer(server_id, self.mcroot, self.domain_base)
            valid = server.load_data()
            if not valid:
                print(f"Server {server_id} is invalid, removing from cache.")
                continue
            self.servers[server_id] = server
            print(f"Loaded server: {server_id}")
