import psycopg2
from psycopg2.extras import RealDictCursor
from .config import Config

class Database:
    def __init__(self):
        self.conn = None

    def connect(self):
        try:
            self.conn = psycopg2.connect(
                host=Config.DB_HOST,
                port=Config.DB_PORT,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                dbname=Config.DB_NAME
            )
            self.conn.autocommit = True
            print("Connected to Database")
            self.init_db()
        except Exception as e:
            print(f"Database connection failed: {e}")

    def init_db(self):
        """Initialize tables if they don't exist."""
        queries = [
            """
            CREATE TABLE IF NOT EXISTS player_stats (
                player_name VARCHAR(50) PRIMARY KEY,
                kills INT DEFAULT 0,
                deaths INT DEFAULT 0,
                blocks_broken INT DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        ]
        with self.conn.cursor() as cur:
            for query in queries:
                cur.execute(query)
            
            # Migrations for new features
            migrations = [
                "ALTER TABLE player_stats ADD COLUMN IF NOT EXISTS advancements INT DEFAULT 0;",
                "ALTER TABLE player_stats ADD COLUMN IF NOT EXISTS last_login TIMESTAMP;",
                "ALTER TABLE player_stats ADD COLUMN IF NOT EXISTS last_logout TIMESTAMP;",
                "ALTER TABLE player_stats ADD COLUMN IF NOT EXISTS playtime BIGINT DEFAULT 0;",
                "ALTER TABLE player_stats ADD COLUMN IF NOT EXISTS diamonds_mined INT DEFAULT 0;"
            ]
            for migration in migrations:
                try:
                    cur.execute(migration)
                except Exception as e:
                    print(f"Migration warning: {e}")
                    
        print("Database initialized and migrated")

    def get_cursor(self):
        if not self.conn or self.conn.closed:
            self.connect()
        return self.conn.cursor(cursor_factory=RealDictCursor)

    def update_stat(self, player, stat_type, value=1):
        """플레이어의 통계를 증가시킵니다."""
        query = f"""
        INSERT INTO player_stats (player_name, {stat_type})
        VALUES (%s, %s)
        ON CONFLICT (player_name)
        DO UPDATE SET {stat_type} = player_stats.{stat_type} + %s, last_updated = CURRENT_TIMESTAMP;
        """
        with self.get_cursor() as cur:
            cur.execute(query, (player, value, value))

    def set_stat(self, player, stat_type, value):
        """통계의 특정 값을 설정합니다 (절대값 업데이트)."""
        query = f"""
        INSERT INTO player_stats (player_name, {stat_type})
        VALUES (%s, %s)
        ON CONFLICT (player_name)
        DO UPDATE SET {stat_type} = %s, last_updated = CURRENT_TIMESTAMP;
        """
        with self.get_cursor() as cur:
            cur.execute(query, (player, value, value))

    def update_timestamp(self, player, column):
        """플레이어의 타임스탬프 컬럼을 업데이트합니다."""
        query = f"""
        INSERT INTO player_stats (player_name, {column})
        VALUES (%s, CURRENT_TIMESTAMP)
        ON CONFLICT (player_name)
        DO UPDATE SET {column} = CURRENT_TIMESTAMP, last_updated = CURRENT_TIMESTAMP;
        """
        with self.get_cursor() as cur:
            cur.execute(query, (player,))

    def update_playtime(self, player):
        """Calculate and update playtime on logout."""
        # Calculate duration: current_timestamp - last_login
        # Then add to existing playtime
        query = """
        UPDATE player_stats
        SET playtime = playtime + EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - last_login))::BIGINT,
            last_logout = CURRENT_TIMESTAMP,
            last_updated = CURRENT_TIMESTAMP
        WHERE player_name = %s AND last_login IS NOT NULL;
        """
        with self.get_cursor() as cur:
            cur.execute(query, (player,))

    def get_top_players(self, stat_type, limit=10):
        query = f"SELECT player_name, {stat_type} FROM player_stats ORDER BY {stat_type} DESC LIMIT %s"
        with self.get_cursor() as cur:
            cur.execute(query, (limit,))
            return cur.fetchall()

db = Database()
