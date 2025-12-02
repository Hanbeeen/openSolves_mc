import discord
from discord.ext import commands
from core.rcon_client import rcon

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        # TODO: Implement proper role checking
        # For now, allow everyone or check for specific permission
        return True

    @commands.command(name="say")
    async def say(self, ctx, *, message: str):
        """Broadcasts a message to the Minecraft server."""
        response = rcon.send_command(f"say {message}")
        await ctx.send(f"Server response: `{response}`")

    @commands.command(name="kick")
    async def kick(self, ctx, player: str, *, reason: str = "Kicked by admin"):
        """Kicks a player from the server."""
        response = rcon.send_command(f"kick {player} {reason}")
        await ctx.send(f"Server response: `{response}`")

    @commands.command(name="whitelist")
    async def whitelist(self, ctx, action: str, player: str = None):
        """Manage whitelist. Usage: !whitelist add <player> or !whitelist list"""
        if action.lower() == "list":
            response = rcon.send_command("whitelist list")
        elif player:
            response = rcon.send_command(f"whitelist {action} {player}")
        else:
            response = "Usage: !whitelist add <player> | remove <player> | list"
        
        await ctx.send(f"Server response: `{response}`")

async def setup(bot):
    await bot.add_cog(Admin(bot))
