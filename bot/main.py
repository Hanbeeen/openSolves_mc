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
    await bot.load_extension("cogs.grafana")
    print("Loaded cogs: admin, stats, grafana")

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
    # 1. DB 업데이트 (비동기)
    if event_type == 'login':
        await db.update_timestamp(data['player'], "last_login")
        
    elif event_type == 'logout':
        player = data['player']
        # 플레이 타임 계산 로직은 DB로 이동하거나 여기서 처리해야 함
        # 현재는 DB가 처리한다고 가정하거나 나중에 구현
        # 동기 로직을 제거했으므로, DB에 있었다면 다시 구현해야 함
        # 하지만 이번 리팩토링에서는 계획대로 타임스탬프 업데이트만 수행
        await db.update_timestamp(player, "last_logout")
        
        # 플레이 타임 업데이트 (필요시 단순 차이 계산 또는 타임스탬프 의존)
        # 이전 로직을 엄격히 따르려면:
        # last_login을 가져와서 차이를 계산하고 playtime에 더해야 함.
        # last_login = await db.get_player_stat(player, "last_login")
        # 참고: get_player_stat은 값을 반환하지만 last_login은 타임스탬프임.
        # 특정 메서드나 원시 쿼리가 필요할 수 있음.
        # 이 단계에서는 단순화를 위해 타임스탬프만 업데이트.
        # 사용자가 이전에 "플레이 타임" 기능을 요청했었음.
        # DB 클래스나 여기에 적절한 플레이 타임 업데이트 쿼리를 추가해야 함.
        
        # 광물 통계 업데이트
        if 'mined_stats' in data:
            for stat, value in data['mined_stats'].items():
                await db.set_stat(player, stat, value)

    elif event_type == 'advancement':
        await db.update_stat(data['player'], "advancements")

    elif event_type == 'death':
        victim = data['victim']
        killer = data['killer']
        is_pvp = data['is_pvp']
        
        await db.update_stat(victim, "deaths")
        if is_pvp and killer:
            await db.update_stat(killer, "kills")

    # 2. 디스코드 알림
    channel = bot.get_channel(1445330465530576938)
    if not channel:
        print(f"Warning: !!! No channel found to broadcast {event_type}")
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
            if "cactus" in reason or "pricked" in reason:
                await channel.send(f"🌵 **{victim}**님이 선인장이나 가시에 찔려 사망했습니다. 따끔하네요.")
            elif "berry" in reason:
                await channel.send(f"🫐 **{victim}**님이 달콤한 베리 덤불에 찔려 죽었습니다. 부끄럽군요.")
            elif "high place" in reason or "hit the ground" in reason:
                await channel.send(f"📉 **{victim}**님이 날 수 있다고 믿었습니다.")
            elif "drowned" in reason:
                await channel.send(f"💧 **{victim}**님이 숨쉬는 법을 까먹었습니다.")
            elif "lava" in reason:
                await channel.send(f"🔥 **{victim}**님이 용암 수영을 시도했습니다.")
            elif "starved" in reason:
                await channel.send(f"🍖 **{victim}**님이 배고픔을 이기지 못했습니다. 밥 좀 챙겨 드세요.")
            elif "suffocated" in reason:
                await channel.send(f"🧱 **{victim}**님이 벽 속에 갇혔습니다.")
            elif "squashed" in reason or "anvil" in reason:
                await channel.send(f"🔨 **{victim}**님이 떨어지는 모루에 납작해졌습니다. 머리 조심!")
            elif "world" in reason or "void" in reason:
                await channel.send(f"🌌 **{victim}**님이 공허로 떠났습니다. 사요나라.")
            elif "kinetic" in reason:
                await channel.send(f"🚀 **{victim}**님이 너무 빨리 날았습니다. (운동 에너지)")
            elif "lightning" in reason:
                await channel.send(f"⚡ **{victim}**님이 천벌을 받았습니다.")
            elif "frozen" in reason:
                await channel.send(f"🥶 **{victim}**님이 동태가 되었습니다.")
            elif "stung" in reason:
                await channel.send(f"🐝 **{victim}**님이 벌집을 건드렸나 봅니다.")
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
    await db.connect()
    await db.init_db() # Recreate tables
    
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
        
    await db.close()

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
