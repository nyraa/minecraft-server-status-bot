# Minecraft Server Status Discord Bot
## Feature
- List server status on your computer includes:
  - Server status: online/offline
  - Server ID
  - Server IP:Port
  - OPs
  - Whitelist
  - Online players
  - Online player count
  - Auto start when boot
- Command to start/shutdown server, RCON

## Folder structure
`server1`, `server2`, `server3` will be your server-id.
```
root/
├── server1/
│   ├── auto-start.sh      (optional)
│   ├── start.sh
│   └── server.properties
├── server2/
│   ├── auto-start.sh      (optional)
│   ├── start.sh
│   └── server.properties
├── server3/
│   ├── auto-start.sh      (optional)
│   ├── start.sh
│   └── server.properties
...
```

## Server information
Server information e.g. server name, server version, visible to bot... are writing in `start.sh` in following format:
```bash
# server-name: YOUR SERVER NAME
# server-version: YOUR SERVER VERSION
# server-type: YOUR SERVER TYPE e.g. vanilla, paper, spigot
# server-port: YOUR SERVER PORT (Optional, if your local port is forwarded to other port in NAT, this option will override the default value read from server.properties)
# server-ip: YOUR SERVER IP (Optional, default IP is configurated in .env, this option allows you to override it in individual server)
# visible-to-bot: BOOL, default false, set to true to allow bot showing and manage this server

# your other command to start server
java -Xmx -jar server.jar nogui
```

## RCON
This bot provides RCON command to control your server, the port and password will automatically read from server.properties, ensure to enable it and set port and password if you want to use this feature.

## Discord Command

### /up server-id
This command starts a server via `~/minecraft-launch.sh $server-id`, you can use any way to handle this command and launch the server in tmux for example.
This command considers return value from `minecraft-launch.sh` as:
- `0`: success
- `1`: server already running
- `2`: server-id not found

### /down server-id
This command sends a `stop` command to `$server-id` via RCON to stop the server, set up RCON if you want to use this command.

### /rcon server-id command
This command sends `command` to `$server-id` via RCON.

### /reload
Reload Discord bot cogs, for development.

The commands above requires Discord Admin premission to issue it.

## Setup

### Environment variable
Environment variable is place at `.env` file, following keys are required:
```
DISCORD_BOT_TOKEN=your token
CHANNEL_ID=your channel to send server status
MCSERVER_DOMAIN=your server domain
MCSERVER_PATH=your servers root directory
GUILD_ID=your discord server id, for faster command sync if you only need this bot serve one server