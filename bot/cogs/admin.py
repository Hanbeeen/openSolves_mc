import discord
from discord.ext import commands
from core.rcon_client import rcon

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        # TODO: 적절한 역할 확인 구현
        # 현재는 모든 사용자 허용 또는 특정 권한 확인
        return True

    @commands.command(name="say")
    async def say(self, ctx, *, message: str):
        """마인크래프트 서버에 메시지를 방송합니다."""
        response = rcon.send_command(f"say {message}")
        await ctx.send(f"서버 응답: `{response}`")

    @commands.command(name="kick")
    async def kick(self, ctx, player: str, *, reason: str = "관리자에 의해 추방됨"):
        """서버에서 플레이어를 추방합니다."""
        response = rcon.send_command(f"kick {player} {reason}")
        await ctx.send(f"서버 응답: `{response}`")

    @commands.command(name="whitelist")
    async def whitelist(self, ctx, action: str, player: str = None):
        """화이트리스트 관리. 사용법: !whitelist add <플레이어> 또는 !whitelist list"""
        if action.lower() == "list":
            response = rcon.send_command("whitelist list")
        elif player:
            response = rcon.send_command(f"whitelist {action} {player}")
        else:
            response = "사용법: !whitelist add <플레이어> | remove <플레이어> | list"
        
        await ctx.send(f"서버 응답: `{response}`")

async def setup(bot):
    await bot.add_cog(Admin(bot))
