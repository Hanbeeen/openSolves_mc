import discord
from discord.ext import commands
from core.db import db

class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="leaderboard", aliases=["lb", "랭킹"])
    async def leaderboard(self, ctx, stat_type: str = "deaths"):
        """랭킹을 보여줍니다. 사용법: !lb [deaths|kills|blocks_broken|diamonds|coal|iron|gold|emerald|lapis|redstone|netherite]"""
        
        # 별칭 매핑
        aliases = {
            "다이아": "diamonds_mined", "diamonds": "diamonds_mined",
            "석탄": "coal_mined", "coal": "coal_mined",
            "철": "iron_mined", "iron": "iron_mined",
            "금": "gold_mined", "gold": "gold_mined",
            "에메랄드": "emerald_mined", "emerald": "emerald_mined",
            "청금석": "lapis_mined", "lapis": "lapis_mined",
            "레드스톤": "redstone_mined", "redstone": "redstone_mined",
            "네더라이트": "netherite_mined", "netherite": "netherite_mined",
            "킬": "kills", "kills": "kills",
            "데스": "deaths", "deaths": "deaths",
            "블럭": "blocks_broken", "blocks_broken": "blocks_broken"
        }
        
        target_stat = aliases.get(stat_type, stat_type)
        
        # 유효성 검사 (DB 컬럼명 기준)
        valid_columns = list(set(aliases.values()))
        
        if target_stat not in valid_columns:
            await ctx.send(f"잘못된 통계 유형입니다. 사용 가능한 통계: {', '.join(set(aliases.keys()))}")
            return

        data = await db.get_top_players(target_stat)
        
        if not data:
            await ctx.send("아직 데이터가 없습니다.")
            return

        embed = discord.Embed(title=f"🏆 랭킹: {target_stat.replace('_mined', '').capitalize()}", color=discord.Color.gold())
        
        description = ""
        for i, row in enumerate(data, 1):
            player = row['player_name']
            value = row[target_stat]
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            description += f"**{medal} {player}**: {value}\n"
        
        embed.description = description
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Stats(bot))
