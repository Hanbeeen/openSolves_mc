import discord
from discord.ext import commands
from core.db import db

class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="leaderboard", aliases=["lb", "랭킹"])
    async def leaderboard(self, ctx, stat_type: str = "deaths"):
        """Shows the leaderboard. Usage: !lb [deaths|kills|blocks_broken]"""
        valid_stats = ["deaths", "kills", "blocks_broken"]
        if stat_type not in valid_stats:
            await ctx.send(f"Invalid stat type. Choose from: {', '.join(valid_stats)}")
            return

        data = db.get_top_players(stat_type)
        
        if not data:
            await ctx.send("No data available yet.")
            return

        embed = discord.Embed(title=f"🏆 Leaderboard: {stat_type.capitalize()}", color=discord.Color.gold())
        
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
