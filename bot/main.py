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

# 디스코드 봇 설정
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# 로그 파서 인스턴스
# 로그 파서 인스턴스는 lifespan에서 초기화됩니다

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
    """봇의 상태를 확인합니다."""
    latency = round(bot.latency * 1000, 2)
    await ctx.send(f"✅ **System Healthy**\nLatency: `{latency}ms`")

# 킬 스트릭 추적기
kill_streaks = {}

async def handle_log_event(event_type, data):
    channel = bot.get_channel(1346376467000786964) # Replace with actual channel ID or config
    # If channel is not found (e.g. not configured), try to find a default one or just print
    if not channel:
        # Try to find a channel named 'general' or 'minecraft'
        for guild in bot.guilds:
            for ch in guild.text_channels:
                if ch.name in ['general', 'minecraft', 'chat']:
                    channel = ch
                    break
            if channel: break
    
    if not channel:
        print(f"Warning: No channel found to broadcast {event_type}")
        return

    if event_type == 'death':
        victim = data['victim']
        killer = data['killer']
        reason = data['reason']
        is_pvp = data['is_pvp']
        
        # Reset victim's streak
        if victim in kill_streaks:
            if kill_streaks[victim] >= 3:
                await channel.send(f"🛑 **{victim}**님의 {kill_streaks[victim]}연속 킬이 **{killer if killer else reason}**에 의해 저지당했습니다!")
            del kill_streaks[victim]

        # PvP 처리
        if is_pvp and killer:
            kill_streaks[killer] = kill_streaks.get(killer, 0) + 1
            streak = kill_streaks[killer]
            
            if streak == 3:
                await channel.send(f"🔥 **{killer}**님이 **학살**을 시작했습니다! (3킬)")
            elif streak == 5:
                await channel.send(f"🩸 **{killer}**님을 **막을 수 없습니다**! (5킬)")
            elif streak >= 10:
                await channel.send(f"💀 **{killer}**님은 **신**입니다! ({streak}킬)")

            await channel.send(f"⚔️ **{victim}**님이 **{killer}**님에게 살해당했습니다.")

        # 굴욕적인 죽음 처리 (PvE)
        if not is_pvp:
            if "cactus" in reason:
                await channel.send(f"🌵 **{victim}**님이 선인장과 포옹했습니다. 따끔하네요.")
            elif "berry" in reason:
                await channel.send(f"🫐 **{victim}**님이 달콤한 베리 덤불에 찔려 죽었습니다. 부끄럽군요.")
            elif "high place" in reason:
                await channel.send(f"📉 **{victim}**님이 날 수 있다고 믿었습니다.")
            elif "drowned" in reason:
                await channel.send(f"💧 **{victim}**님이 숨쉬는 법을 까먹었습니다.")
            elif "lava" in reason:
                await channel.send(f"🔥 **{victim}**님이 용암 수영을 시도했습니다.")
            else:
                await channel.send(f"☠️ **{victim}**님이 사망했습니다. ({reason})")

    elif event_type == 'advancement':
        player = data['player']
        advancement = data['advancement']
        await channel.send(f"🏆 **{player}**님이 **[{advancement}]** 업적을 달성했습니다!")

    elif event_type == 'login':
        await channel.send(f"👋 **{data['player']}**님이 서버에 접속했습니다!")

    elif event_type == 'logout':
        await channel.send(f"🚪 **{data['player']}**님이 서버에서 나갔습니다.")

# FastAPI 설정
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작
    print("Initializing Database...")
    db.connect()
    
    print("Starting Log Parser...")
    
    # Define callback wrapper for thread safety
    def event_callback(event_type, data):
        if Config.DISCORD_TOKEN and bot.is_ready():
            asyncio.run_coroutine_threadsafe(handle_log_event(event_type, data), bot.loop)
            
    # Initialize parser with callback
    global log_parser
    log_parser = LogParser(event_callback=event_callback)
    
    parser_thread = threading.Thread(target=log_parser.start, daemon=True)
    parser_thread.start()
    
    # Run Discord Bot in background
    if Config.DISCORD_TOKEN:
        asyncio.create_task(bot.start(Config.DISCORD_TOKEN))
    else:
        print("WARNING: DISCORD_TOKEN not set. Bot will not start.")
        
    yield
    
    # 종료
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
    봇 서버 상태를 확인하는 헬스 체크 엔드포인트입니다.
    마인크래프트 서버 상태와는 독립적입니다.
    """
    return {
        "status": "healthy",
        "bot_connected": not bot.is_closed() and bot.is_ready(),
        "bot_latency_ms": round(bot.latency * 1000, 2) if bot.is_ready() else None
    }

@app.post("/alert")
async def receive_alert(request: Request):
    """
    Prometheus Alertmanager로부터 경고를 수신하는 엔드포인트입니다.
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
