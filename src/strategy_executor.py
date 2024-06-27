from src.duckdb_handler import DuckDBHandler
from src.timescale_handler import TimescaleDBHandler
import logging

logger = logging.getLogger(__name__)

class StrategyExecutor:
    def __init__(self, strategies, duckdb_file=':memory:'):
        self.strategies = strategies
        self.duckdb_handler = DuckDBHandler(duckdb_file)
        self.timescale_handler = TimescaleDBHandler()

    def sync_data(self, hours=24):
        logger.info(f"Syncing last {hours} hours of data from TimescaleDB to DuckDB")
        recent_data = self.timescale_handler.fetch_recent_data(hours)
        self.duckdb_handler.store(recent_data)

    def execute_strategies(self):
        for strategy in self.strategies:
            logger.info(f"Executing strategy: {strategy.name}")
            data = self.duckdb_handler.fetch_data_for_strategy(strategy)
            result = strategy.execute(data)
            self.handle_strategy_result(strategy, result)

    def run_strategy(self, strategy, data):
        # This method would contain the logic to run each strategy
        # For now, we'll just return a dummy result
        return {"profit": 100, "trades": 10}


    def handle_strategy_result(self, strategy, result):
        # This method would handle the result of each strategy
        # e.g., place orders, log performance, etc.
        logger.info(f"Strategy {strategy.name} result: {result}")

    def run(self):
        self.sync_data()
        self.execute_strategies()


    def close(self):
        self.duckdb_handler.close()
        self.timescale_handler.close()