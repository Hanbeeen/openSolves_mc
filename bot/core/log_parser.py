import time
import re
import os
from .db import db
from .stats_reader import StatsReader

class LogParser:
    def __init__(self, log_path="/mc-logs/logs/latest.log", event_callback=None):
        self.log_path = log_path
        self._running = False
        self.event_callback = event_callback
        self.stats_reader = StatsReader()
        
        # Regex Patterns
        self.patterns = {
            'login': re.compile(r': (\w+) joined the game'),
            'logout': re.compile(r': (\w+) left the game'),
            'advancement': re.compile(r': (\w+) has made the advancement \[(.+?)\]'),
            'death': re.compile(r': (.+?) (was slain by|walked into a cactus|burned to death|drowned|fell from a high place|tried to swim in lava|blew up|was shot by|withered away|died|was killed by) ?(.*)'),
        }

    def follow(self):
        """로그 파일에서 새로운 라인을 생성하는 제너레이터입니다."""
        self.log_file.seek(0, os.SEEK_END)
        while True:
            line = self.log_file.readline()
            if not line:
                time.sleep(0.1)
                continue
            yield line

    def start(self):
        print(f"Starting Log Parser on {self.log_path}...")
        
        # Wait for file to exist
        while not os.path.exists(self.log_path):
            print(f"Waiting for log file: {self.log_path}")
            time.sleep(5)

        try:
            with open(self.log_path, "r", encoding="utf-8", errors='ignore') as f:
                self.log_file = f # Assign the opened file object
                for line in self.follow():
                    self.process_line(line)
        except Exception as e:
            print(f"Log Parser Error: {e}")

    def process_line(self, line):
        # 메시지 내용을 추출하기 위한 기본 파싱
        # 로그 형식: [Time] [Thread/Level]: Message
        parts = line.split(']: ', 1)
        if len(parts) < 2:
            return
        
        message = ": " + parts[1].strip() # 정규식 일관성을 위해 콜론 추가
        
        # 1. Login
        match = self.patterns['login'].search(message)
        if match:
            player = match.group(1)
            db.update_timestamp(player, "last_login")
            if self.event_callback:
                self.event_callback("login", {"player": player})
            return

        # 2. Logout
        match = self.patterns['logout'].search(message)
        if match:
            player = match.group(1)
            db.update_playtime(player)
            
            # Update Diamond Count
            diamonds = self.stats_reader.get_diamond_count(player)
            db.set_stat(player, "diamonds_mined", diamonds)
            
            if self.event_callback:
                self.event_callback("logout", {"player": player})
            return

        # 3. Advancement
        match = self.patterns['advancement'].search(message)
        if match:
            player = match.group(1)
            advancement = match.group(2)
            db.update_stat(player, "advancements")
            if self.event_callback:
                self.event_callback("advancement", {"player": player, "advancement": advancement})
            return

        # 4. PvP Death
        match = self.patterns['death_pvp'].search(message)
        if match:
            victim = match.group(1)
            killer = match.group(2)
            db.update_stat(victim, "deaths")
            db.update_stat(killer, "kills")
            print(f"Detected PvP: {killer} -> {victim}")
            if self.event_callback:
                self.event_callback("death", {"victim": victim, "killer": killer, "is_pvp": True, "reason": "slain"})
            return

        # 5. PvE Death (Fallback if not PvP)
        match = self.patterns['death_pve'].search(message)
        if match:
            victim = match.group(1)
            reason = match.group(2)
            db.update_stat(victim, "deaths")
            print(f"Detected PvE: {victim} ({reason})")
            if self.event_callback:
                self.event_callback("death", {"victim": victim, "killer": None, "is_pvp": False, "reason": reason})
            return

    def stop(self):
        self._running = False
