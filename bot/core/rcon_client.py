from mcrcon import MCRcon
from .config import Config

class RconClient:
    def __init__(self):
        self.host = Config.RCON_HOST
        self.port = Config.RCON_PORT
        self.password = Config.RCON_PASSWORD

    def send_command(self, command: str) -> str:
        """
        Sends a command to the Minecraft server via RCON.
        Returns the response from the server.
        """
        try:
            with MCRcon(self.host, self.password, port=self.port) as mcr:
                response = mcr.command(command)
                return response
        except Exception as e:
            return f"Error connecting to RCON: {str(e)}"

# Singleton instance
rcon = RconClient()
