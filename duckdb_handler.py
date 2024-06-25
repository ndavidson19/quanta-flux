import duckdb

class DuckDBHandler:
    def __init__(self, db_file):
        self.conn = duckdb.connect(db_file)
        self.create_table()

    def create_table(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS market_data (
                timestamp TIMESTAMP,
                open DOUBLE,
                high DOUBLE,
                low DOUBLE,
                close DOUBLE,
                volume INTEGER,
                SMA_20 DOUBLE,
                EMA_20 DOUBLE,
                RSI DOUBLE
            )
        """)

    def store(self, data):
        self.conn.executemany("""
            INSERT INTO market_data VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
        """, [(
            row['timestamp'], row['open'], row['high'], row['low'], 
            row['close'], row['volume'], row['SMA_20'], row['EMA_20'], row['RSI']
        ) for row in data])
        self.conn.commit()