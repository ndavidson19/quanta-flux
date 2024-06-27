import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from data_providers import IBProvider, OtherProvider
from kafka_handler import KafkaProducer, KafkaConsumer
from flink_processor import FlinkProcessor
from spark_processor import SparkProcessor
from duckdb_handler import DuckDBHandler
from timescale_handler import TimescaleDBHandler
from strategy_executor import StrategyExecutor

# Initialize your components here
ib_provider = IBProvider(os.getenv('IB_HOST'), int(os.getenv('IB_PORT')), int(os.getenv('IB_CLIENT_ID')))
other_provider = OtherProvider()
kafka_producer = KafkaProducer(os.getenv('KAFKA_BOOTSTRAP_SERVERS'))
timescale_handler = TimescaleDBHandler()
duckdb_handler = DuckDBHandler(os.getenv('DUCKDB_FILE'))
flink_processor = FlinkProcessor(os.getenv('KAFKA_BOOTSTRAP_SERVERS'), os.getenv('RAW_DATA_TOPIC'), os.getenv('PROCESSED_DATA_TOPIC'))
spark_processor = SparkProcessor(os.getenv('KAFKA_BOOTSTRAP_SERVERS'), os.getenv('RAW_DATA_TOPIC'), os.getenv('BATCH_PROCESSED_DATA_TOPIC'))
strategy_executor = StrategyExecutor([], duckdb_handler, timescale_handler)

print("Development environment initialized. You can now interact with the components.")