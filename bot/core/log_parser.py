import time
import re
import os
from .db import db

class LogParser:
    def __init__(self, log_path="/mc-logs/logs/latest.log"):
        self.log_path = log_path
        self._running = False

    def follow(self, file):
        file.seek(0, os.SEEK_END)
        while self._running:
            line = file.readline()
            if not line:
                time.sleep(0.1)
                continue
            yield line

    def start(self):
        self._running = True
        print(f"Starting Log Parser on {self.log_path}...")
        
        # Wait for file to exist
        while not os.path.exists(self.log_path):
            print(f"Waiting for log file: {self.log_path}")
            time.sleep(5)

        try:
            with open(self.log_path, "r", encoding="utf-8", errors='ignore') as f:
                for line in self.follow(f):
                    self.process_line(line)
        except Exception as e:
            print(f"Log Parser Error: {e}")

    def process_line(self, line):
        # Example Log: [12:00:00] [Server thread/INFO]: Steve joined the game
        # Example Death: Steve was shot by Skeleton
        # Example Kill: Steve was slain by Alex
        
        # Simple Regex for Death (Needs refinement based on actual messages)
        # "Player was ..." usually indicates death
        
        # Note: This is a simplified parser. 
        # In production, you'd need robust regex for all death messages.
        
        if "joined the game" in line:
            return # Ignore joins for stats
            
        # Detect Death
        # Pattern: [Time] [Thread/INFO]: <Player> died message...
        # We need to extract Player name.
        
        # Very naive check for testing
        if "was slain by" in line or "fell from a high place" in line or "burned to death" in line:
            # Try to extract player name
            # Assuming standard log format: [HH:MM:SS] [Server thread/INFO]: PlayerName message...
            parts = line.split("]: ")
            if len(parts) > 1:
                message = parts[1].strip()
                words = message.split(" ")
                if len(words) > 0:
                    player_name = words[0]
                    # Update Death Count
                    db.update_stat(player_name, "deaths")
                    print(f"Detected death: {player_name}")

    def stop(self):
        self._running = False
