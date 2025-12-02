import asyncio
import os
import threading
from contextlib import asynccontextmanager
from fastapi import FastAPI, BackgroundTasks, Request
import discord
from discord.ext import commands
from core.config import Config
from core.db import db
from core.log_parser import LogParser

# Discord Bot Setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Log Parser Instance
log_parser = LogParser()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    # Load extensions
    await bot.load_extension("cogs.admin")
    await bot.load_extension("cogs.stats")
    print("Loaded cogs: admin, stats")

@bot.command()
async def ping(ctx):
    await ctx.send('Pong!')

@bot.command()
async def health(ctx):
    """Checks the health of the bot."""
    latency = round(bot.latency * 1000, 2)
    await ctx.send(f"✅ **System Healthy**\nLatency: `{latency}ms`")

# FastAPI Setup
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Initializing Database...")
    db.connect()
    
    print("Starting Log Parser...")
    parser_thread = threading.Thread(target=log_parser.start, daemon=True)
    parser_thread.start()
    
    # Run Discord Bot in background
    if Config.DISCORD_TOKEN:
        asyncio.create_task(bot.start(Config.DISCORD_TOKEN))
    else:
        print("WARNING: DISCORD_TOKEN not set. Bot will not start.")
        
    yield
    
    # Shutdown
    print("Stopping Log Parser...")
    log_parser.stop()
    
    if not bot.is_closed():
        await bot.close()

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def read_root():
    return {"status": "ok", "message": "Minecraft Bot Server is Running"}

@app.get("/health")
async def health_check():
    """
    Health check endpoint to verify Bot Server status.
    Independent of Minecraft Server status.
    """
    return {
        "status": "healthy",
        "bot_connected": not bot.is_closed() and bot.is_ready(),
        "bot_latency_ms": round(bot.latency * 1000, 2) if bot.is_ready() else None
    }

@app.post("/alert")
async def receive_alert(request: Request):
    """
    Endpoint to receive alerts from Prometheus Alertmanager
    """
    data = await request.json()
    print(f"Received alert: {data}")
    
    # Extract alert info
    alerts = data.get('alerts', [])
    for alert in alerts:
        status = alert.get('status')
        labels = alert.get('labels', {})
        annotations = alert.get('annotations', {})
        
        alert_name = labels.get('alertname', 'Unknown Alert')
        description = annotations.get('description', 'No description')
        
        # Send to a specific Discord channel (You need to set this ID)
        # channel = bot.get_channel(YOUR_CHANNEL_ID)
        # if channel:
        #     await channel.send(f"🚨 **{alert_name}** ({status})\n{description}")
            
    return {"status": "received"}
