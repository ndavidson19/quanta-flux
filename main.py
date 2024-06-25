import logging
from data_providers import IBProvider, OtherProvider
from kafka_handler import KafkaProducer, KafkaConsumer
from flink_processor import FlinkProcessor
from spark_processor import SparkProcessor
from duckdb_handler import DuckDBHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    try:
        # Initialize data providers
        ib_provider = IBProvider()
        other_provider = OtherProvider()

        # Initialize Kafka producer
        kafka_producer = KafkaProducer("kafka:29092")

        # Fetch and send data to Kafka
        for provider in [ib_provider, other_provider]:
            raw_data = provider.fetch_data()
            kafka_producer.send("raw_market_data", raw_data)

        # Initialize Flink processor for stream processing
        flink_processor = FlinkProcessor("localhost:9092", "raw_market_data", "processed_market_data")
        flink_processor.start_processing()

        # Initialize Spark processor for batch processing
        spark_processor = SparkProcessor("localhost:9092", "raw_market_data", "batch_processed_data")
        spark_processor.start_processing()

        # Initialize DuckDB handler
        db_handler = DuckDBHandler("market_data.db")

        # Consume processed data from Kafka and store in DuckDB
        kafka_consumer = KafkaConsumer("processed_market_data", "localhost:9092")
        for message in kafka_consumer.consume():
            db_handler.store(message)

    except Exception as e:
        logger.error(f"An error occurred in the ETL process: {str(e)}")

if __name__ == "__main__":
    main()