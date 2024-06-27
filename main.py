import logging
from src.data_providers import IBProvider, OtherProvider
from src.kafka_handler import KafkaProducer, KafkaConsumer
from src.flink_processor import FlinkProcessor
from src.spark_processor import SparkProcessor
from src.duckdb_handler import DuckDBHandler
from src.timescale_handler import TimescaleDBHandler
from src.strategy_executor import StrategyExecutor
from prometheus_client import start_http_server, Counter, Gauge
from src import config
import time

logging.basicConfig(level=config.LOG_LEVEL, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Prometheus metrics
PROCESSED_MESSAGES = Counter('processed_messages', 'Number of processed messages')
PROCESSING_TIME = Gauge('processing_time', 'Time taken to process a message')

def main_etl_process(kafka_producer, timescale_handler):
    # Initialize data providers
    ib_provider = IBProvider(config.IB_HOST, config.IB_PORT, config.IB_CLIENT_ID)
    other_provider = OtherProvider()
    logger.info("Data providers initialized")

    # Fetch and send data to Kafka
    for provider in [ib_provider, other_provider]:
        try:
            raw_data = provider.fetch_data()
            kafka_producer.send(config.RAW_DATA_TOPIC, raw_data)
            logger.info(f"Data fetched and sent to Kafka topic {config.RAW_DATA_TOPIC}")
        except Exception as e:
            logger.error(f"Error fetching data from {provider.__class__.__name__}: {str(e)}")

    # Process data (assuming Flink/Spark jobs are running separately)
    # In a real-world scenario, you might want to check the status of these jobs

    # Consume processed data from Kafka and store in TimescaleDB
    kafka_consumer = KafkaConsumer(config.PROCESSED_DATA_TOPIC, config.KAFKA_BOOTSTRAP_SERVERS)
    logger.info(f"Kafka consumer initialized for topic {config.PROCESSED_DATA_TOPIC}")

    for message in kafka_consumer.consume(timeout=10):  # Add a timeout to prevent blocking indefinitely
        try:
            with PROCESSING_TIME.time():
                timescale_handler.store([message])  # Assuming store method accepts a list
            PROCESSED_MESSAGES.inc()
            logger.debug("Message processed and stored in TimescaleDB")
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")

def main():
    try:
        # Start Prometheus metrics server
        start_http_server(config.PROMETHEUS_PORT)
        logger.info(f"Prometheus metrics server started on port {config.PROMETHEUS_PORT}")

        # Initialize Kafka producer
        kafka_producer = KafkaProducer(config.KAFKA_BOOTSTRAP_SERVERS)
        logger.info("Kafka producer initialized")

        # Initialize TimescaleDB handler
        timescale_handler = TimescaleDBHandler()
        logger.info("TimescaleDB handler initialized")

        # Initialize DuckDB handler
        duckdb_handler = DuckDBHandler(config.DUCKDB_FILE)
        logger.info("DuckDB handler initialized")

        # Initialize Flink processor for stream processing
        flink_processor = FlinkProcessor(config.KAFKA_BOOTSTRAP_SERVERS, config.RAW_DATA_TOPIC, config.PROCESSED_DATA_TOPIC)
        flink_processor.start_processing()
        logger.info("Flink processor started")

        # Initialize Spark processor for batch processing
        spark_processor = SparkProcessor(config.KAFKA_BOOTSTRAP_SERVERS, config.RAW_DATA_TOPIC, config.BATCH_PROCESSED_DATA_TOPIC)
        spark_processor.start_processing()
        logger.info("Spark processor started")

        # Initialize StrategyExecutor
        strategy_executor = StrategyExecutor([], duckdb_handler, timescale_handler)
        logger.info("Strategy executor initialized")

        while True:
            main_etl_process(kafka_producer, timescale_handler)
            
            # Sync data from TimescaleDB to DuckDB periodically
            if time.time() % config.SYNC_INTERVAL == 0:
                strategy_executor.sync_data()
            
            # Execute strategies periodically
            if time.time() % config.STRATEGY_EXECUTION_INTERVAL == 0:
                strategy_executor.execute_strategies()

    except Exception as e:
        logger.critical(f"Critical error in the ETL process: {str(e)}")

if __name__ == "__main__":
    main()