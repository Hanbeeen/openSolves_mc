import discord
from discord.ext import commands
from core.db import db

class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="leaderboard", aliases=["lb", "랭킹"])
    async def leaderboard(self, ctx, stat_type: str = "deaths"):
        """랭킹을 보여줍니다. 사용법: !lb [deaths|kills|blocks_broken]"""
        valid_stats = ["deaths", "kills", "blocks_broken"]
        if stat_type not in valid_stats:
            await ctx.send(f"잘못된 통계 유형입니다. 다음 중에서 선택하세요: {', '.join(valid_stats)}")
            return

        data = db.get_top_players(stat_type)
        
        if not data:
            await ctx.send("아직 데이터가 없습니다.")
            return

        embed = discord.Embed(title=f"🏆 랭킹: {stat_type.capitalize()}", color=discord.Color.gold())
        
        description = ""
        for i, row in enumerate(data, 1):
            player = row['player_name']
            value = row[stat_type]
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            description += f"**{medal} {player}**: {value}\n"
        
        embed.description = description
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Stats(bot))
