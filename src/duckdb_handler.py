import duckdb
import logging
import pandas as pd

logger = logging.getLogger(__name__)

class DuckDBHandler:
    def __init__(self, db_file=':memory:'):
        self.conn = duckdb.connect(db_file)
        self.create_table()

    def create_table(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS market_data (
                time TIMESTAMP,
                symbol VARCHAR,
                open DOUBLE,
                high DOUBLE,
                low DOUBLE,
                close DOUBLE,
                volume INTEGER,
                additional_data JSON
            )
        """)
        logger.info("Market data table created or already exists in DuckDB")

    def store(self, data):
        df = pd.DataFrame(data)
        self.conn.execute("INSERT INTO market_data SELECT * FROM df")
        logger.info(f"Stored {len(data)} rows in DuckDB")

    def fetch_data_for_strategy(self, strategy_config):
        query = strategy_config.get('query', "SELECT * FROM market_data")
        return self.conn.execute(query).fetchdf()

    def run_query(self, query):
        return self.conn.execute(query).fetchdf()

    def calculate_indicators(self):
        self.conn.execute("""
            ALTER TABLE market_data ADD COLUMN IF NOT EXISTS sma_20 DOUBLE;
            ALTER TABLE market_data ADD COLUMN IF NOT EXISTS ema_20 DOUBLE;
            ALTER TABLE market_data ADD COLUMN IF NOT EXISTS rsi_14 DOUBLE;
            
            UPDATE market_data
            SET sma_20 = (
                SELECT AVG(close)
                FROM market_data m2
                WHERE m2.symbol = market_data.symbol
                  AND m2.time <= market_data.time
                ORDER BY m2.time DESC
                LIMIT 20
            ),
            ema_20 = (
                SELECT SUM(close * (1-0.0952380952)^ROW_NUMBER() OVER (ORDER BY time DESC))
                     / SUM((1-0.0952380952)^ROW_NUMBER() OVER (ORDER BY time DESC))
                FROM market_data m2
                WHERE m2.symbol = market_data.symbol
                  AND m2.time <= market_data.time
                LIMIT 20
            ),
            rsi_14 = (
                SELECT 100 - (100 / (1 + (
                    SUM(CASE WHEN diff > 0 THEN diff ELSE 0 END) /
                    SUM(CASE WHEN diff < 0 THEN -diff ELSE 0 END)
                )))
                FROM (
                    SELECT close - LAG(close) OVER (PARTITION BY symbol ORDER BY time) AS diff
                    FROM market_data m2
                    WHERE m2.symbol = market_data.symbol
                      AND m2.time <= market_data.time
                    ORDER BY m2.time DESC
                    LIMIT 15
                ) t
            );
        """)
        logger.info("Calculated indicators in DuckDB")

    def close(self):
        self.conn.close()