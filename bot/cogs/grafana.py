import discord
from discord.ext import commands
import aiohttp
import io
import os
import json

class Grafana(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.grafana_url = os.getenv("GRAFANA_URL", "http://grafana:3000")
        self.grafana_token = os.getenv("GRAFANA_TOKEN")
        # Default Dashboard UID
        self.dashboard_uid = "minecraft-server" 
        self.charts = {} # Name -> ID mapping

    async def sync_dashboard_panels(self):
        """
        Fetches the dashboard definition from Grafana and updates the chart mapping.
        """
        if not self.grafana_token:
            print("WARNING: GRAFANA_TOKEN not set. Cannot sync charts.")
            return False

        api_url = f"{self.grafana_url}/api/dashboards/uid/{self.dashboard_uid}"
        headers = {
            "Authorization": f"Bearer {self.grafana_token}",
            "Content-Type": "application/json"
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, headers=headers) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    print(f"Failed to fetch dashboard: {resp.status} | URL: {api_url}")
                    print(f"Response: {text}")
                    return False

                data = await resp.json()
                dashboard = data.get("dashboard", {})
                panels = dashboard.get("panels", [])

                new_charts = {}
                for panel in panels:
                    # Handle Row panels which might contain other panels (if nested)
                    # But usually top-level panels are what we want.
                    # We use the panel 'title' as the key.
                    title = panel.get("title")
                    p_id = panel.get("id")

                    if title and p_id is not None:
                        # Normalize title: lowercase, remove spaces for easier typing?
                        # Let's keep it simple: lowercase.
                        key = title.lower()
                        new_charts[key] = p_id

                self.charts = new_charts
                print(f"Synced {len(self.charts)} charts from Grafana: {list(self.charts.keys())}")
                return True

    @commands.Cog.listener()
    async def on_ready(self):
        # Try to sync on startup
        await self.sync_dashboard_panels()

    @commands.command(name="sync")
    async def sync_charts_cmd(self, ctx):
        """
        Manually triggers a sync with Grafana Dashboard.
        Use this if you added new panels to Grafana.
        """
        success = await self.sync_dashboard_panels()
        if success:
            available = ", ".join(self.charts.keys())
            await ctx.send(f"✅ **Synced Successfully!**\nFound {len(self.charts)} charts: `{available}`")
        else:
            await ctx.send("❌ **Sync Failed.** Check logs or Token.")

    @commands.command(name="set_dashboard")
    async def set_dashboard(self, ctx, uid: str):
        """
        Sets the Grafana Dashboard UID and re-syncs.
        """
        self.dashboard_uid = uid
        await self.sync_dashboard_panels()
        await ctx.send(f"✅ Dashboard UID set to `{uid}` and synced.")

    @commands.command(name="chart")
    async def get_chart(self, ctx, *, chart_name: str = None):
        """
        Fetches a chart from Grafana.
        Usage: !chart <name> (e.g., !chart players)
        """
        if not self.grafana_token:
            await ctx.send("⚠️ **Configuration Error**: `GRAFANA_TOKEN` is not set.")
            return

        if not self.charts:
            # Try syncing if empty
            await self.sync_dashboard_panels()

        if not chart_name:
            available = ", ".join(self.charts.keys())
            await ctx.send(f"ℹ️ **Available Charts**: {available}\nUsage: `!chart <name>`")
            return

        # Fuzzy match or exact match
        target_id = self.charts.get(chart_name.lower())

        if not target_id:
            await ctx.send(f"⚠️ **Unknown Chart**: `{chart_name}`\nAvailable: {', '.join(self.charts.keys())}\nTry `!sync` if you just added it.")
            return

        # Construct Render URL
        render_url = (
            f"{self.grafana_url}/render/d-solo/{self.dashboard_uid}/dashboard"
            f"?panelId={target_id}&from=now-1h&to=now&width=1000&height=500&tz=Asia%2FSeoul"
        )

        headers = {
            "Authorization": f"Bearer {self.grafana_token}"
        }

        async with ctx.typing():
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(render_url, headers=headers) as resp:
                        if resp.status != 200:
                            await ctx.send(f"❌ **Grafana Error** ({resp.status})")
                            return

                        data = await resp.read()
                        file = discord.File(io.BytesIO(data), filename=f"{chart_name}.png")
                        await ctx.send(f"📊 **{chart_name.upper()}**", file=file)
            except Exception as e:
                await ctx.send(f"❌ **System Error**: {str(e)}")

async def setup(bot):
    await bot.add_cog(Grafana(bot))