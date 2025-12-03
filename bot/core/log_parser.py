import time
import re
import os
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
        
        # 1. 로그인
        match = self.patterns['login'].search(message)
        if match:
            player = match.group(1)
            if self.event_callback:
                self.event_callback("login", {"player": player})
            return

        # 2. 로그아웃
        match = self.patterns['logout'].search(message)
        if match:
            player = match.group(1)
            
            # 다이아몬드 개수 업데이트 (여기서 읽고 메인에서 저장)
            diamonds = self.stats_reader.get_diamond_count(player)
            
            if self.event_callback:
                self.event_callback("logout", {"player": player, "diamonds": diamonds})
            return

        # 3. 발전 과제
        match = self.patterns['advancement'].search(message)
        if match:
            player = match.group(1)
            advancement = match.group(2)
            if self.event_callback:
                self.event_callback("advancement", {"player": player, "advancement": advancement})
            return

        # 4. 사망
        match = self.patterns['death'].search(message)
        if match:
            victim = match.group(1)
            reason_part = match.group(2)
            killer_part = match.group(3)
            
            is_pvp = False
            killer = None
            
            # 킬러가 플레이어인지 확인 (단순 휴리스틱: 공백이 없거나 알려진 플레이어 목록)
            # 현재는 "was slain by"가 있고 킬러가 비어있지 않으면 PvP로 가정
            if "was slain by" in reason_part and killer_part:
                is_pvp = True
                killer = killer_part.strip()
            
            # 정교한 감지 로직을 여기에 추가 가능
            
            if self.event_callback:
                self.event_callback("death", {
                    "victim": victim, 
                    "killer": killer, 
                    "is_pvp": is_pvp, 
                    "reason": f"{reason_part} {killer_part}".strip()
                })
            return

    def stop(self):
        self._running = False
        self._running = False
