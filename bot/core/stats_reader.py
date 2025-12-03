import json
import os

class StatsReader:
    def __init__(self, stats_dir="/mc-logs/world/stats", usercache_path="/mc-logs/usercache.json"):
        self.stats_dir = stats_dir
        self.usercache_path = usercache_path
        self.uuid_map = {}

    def load_usercache(self):
        """usercache.json 파일을 로드하여 플레이어 이름을 UUID로 매핑합니다."""
        if not os.path.exists(self.usercache_path):
            print(f"[WARN] {self.usercache_path} 에서 usercache를 찾을 수 없습니다.")
            return

        try:
            with open(self.usercache_path, 'r') as f:
                data = json.load(f)
                # usercache 형식: [{"name": "Player", "uuid": "..."}]
                for entry in data:
                    self.uuid_map[entry['name']] = entry['uuid']
        except Exception as e:
            print(f"[ERROR] usercache 로드 실패: {e}")

    def get_diamond_count(self, player_name):
        """플레이어가 캔 다이아몬드 총 개수를 반환합니다."""
        # 플레이어를 찾을 수 없으면 캐시 새로고침 (새로운 플레이어일 수 있음)
        if player_name not in self.uuid_map:
            self.load_usercache()
        
        if player_name not in self.uuid_map:
            return 0

        uuid = self.uuid_map[player_name]
        stats_file = os.path.join(self.stats_dir, f"{uuid}.json")

        if not os.path.exists(stats_file):
            return 0

        try:
            with open(stats_file, 'r') as f:
                data = json.load(f)
                stats = data.get('stats', {})
                mined = stats.get('minecraft:mined', {})
                
                # 다이아몬드 원석과 심층암 다이아몬드 원석 합산
                diamond_ore = mined.get('minecraft:diamond_ore', 0)
                deepslate_diamond = mined.get('minecraft:deepslate_diamond_ore', 0)
                
                return diamond_ore + deepslate_diamond
        except Exception as e:
            print(f"[ERROR] {player_name}의 통계 읽기 실패: {e}")
            return 0
