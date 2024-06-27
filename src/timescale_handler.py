import psycopg2
import logging
from psycopg2.extras import execute_values
from src import config

logger = logging.getLogger(__name__)

class TimescaleDBHandler:
    def __init__(self):
        self.conn = psycopg2.connect(
            host=config.TIMESCALE_HOST,
            port=config.TIMESCALE_PORT,
            dbname=config.TIMESCALE_DB,
            user=config.TIMESCALE_USER,
            password=config.TIMESCALE_PASSWORD
        )
        self.create_hypertable()

    def create_hypertable(self):
        with self.conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS market_data (
                    time TIMESTAMPTZ NOT NULL,
                    symbol TEXT NOT NULL,
                    open DOUBLE PRECISION,
                    high DOUBLE PRECISION,
                    low DOUBLE PRECISION,
                    close DOUBLE PRECISION,
                    volume INTEGER,
                    additional_data JSONB
                );
            """)
            cur.execute("""
                SELECT create_hypertable('market_data', 'time', if_not_exists => TRUE);
            """)
        self.conn.commit()
        logger.info("Market data hypertable created or already exists")

    def store(self, data):
        with self.conn.cursor() as cur:
            execute_values(cur, """
                INSERT INTO market_data (time, symbol, open, high, low, close, volume, additional_data)
                VALUES %s
            """, [(
                row['timestamp'], row.get('symbol', 'UNKNOWN'),
                row['open'], row['high'], row['low'], row['close'], row['volume'],
                {k: v for k, v in row.items() if k not in ['timestamp', 'symbol', 'open', 'high', 'low', 'close', 'volume']}
            ) for row in data])
        self.conn.commit()
        logger.info(f"Stored {len(data)} rows in TimescaleDB")

    def fetch_recent_data(self, hours=24):
        with self.conn.cursor() as cur:
            cur.execute(f"""
                SELECT * FROM market_data
                WHERE time > NOW() - INTERVAL '{hours} hours'
                ORDER BY time DESC
            """)
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]

    def cleanup_old_data(self, days=30):
        with self.conn.cursor() as cur:
            cur.execute(f"""
                DELETE FROM market_data
                WHERE time < NOW() - INTERVAL '{days} days'
            """)
        self.conn.commit()
        logger.info(f"Cleaned up data older than {days} days")

    def close(self):
        self.conn.close()