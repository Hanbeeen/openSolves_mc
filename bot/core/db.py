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
        print("Database initialized")

    def get_cursor(self):
        if not self.conn or self.conn.closed:
            self.connect()
        return self.conn.cursor(cursor_factory=RealDictCursor)

    def update_stat(self, player, stat_type, value=1):
        """Increment a stat for a player."""
        query = f"""
        INSERT INTO player_stats (player_name, {stat_type})
        VALUES (%s, %s)
        ON CONFLICT (player_name)
        DO UPDATE SET {stat_type} = player_stats.{stat_type} + %s, last_updated = CURRENT_TIMESTAMP;
        """
        with self.get_cursor() as cur:
            cur.execute(query, (player, value, value))

    def get_top_players(self, stat_type, limit=10):
        query = f"SELECT player_name, {stat_type} FROM player_stats ORDER BY {stat_type} DESC LIMIT %s"
        with self.get_cursor() as cur:
            cur.execute(query, (limit,))
            return cur.fetchall()

db = Database()
