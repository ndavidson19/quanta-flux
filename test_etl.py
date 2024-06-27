import unittest
from unittest.mock import Mock, patch
import pytest
import json
from src.data_providers import IBProvider, OtherProvider
from src.kafka_handler import KafkaProducer, KafkaConsumer
from src.flink_processor import FlinkProcessor
from src.spark_processor import SparkProcessor
from src.duckdb_handler import DuckDBHandler
from src import config

class TestETLProcess(unittest.TestCase):

    def setUp(self):
        self.mock_data = [
            {'timestamp': '2023-06-24 10:00:00', 'open': 150.0, 'high': 151.0, 'low': 149.0, 'close': 150.5, 'volume': 1000}
        ]

    def test_ib_provider(self):
        with patch('ib_insync.IB') as mock_ib:
            mock_ib.return_value.reqHistoricalData.return_value = [
                Mock(date='2023-06-24 10:00:00', open=150.0, high=151.0, low=149.0, close=150.5, volume=1000)
            ]
            provider = IBProvider(config.IB_HOST, config.IB_PORT, config.IB_CLIENT_ID)
            data = provider.fetch_data()
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]['open'], 150.0)

    def test_other_provider(self):
        with patch('yfinance.download') as mock_download:
            mock_download.return_value = Mock(reset_index=lambda: Mock(to_dict=lambda x: self.mock_data))
            provider = OtherProvider()
            data = provider.fetch_data()
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]['open'], 150.0)

    def test_kafka_producer(self):
        with patch('confluent_kafka.Producer') as mock_producer:
            producer = KafkaProducer(config.KAFKA_BOOTSTRAP_SERVERS)
            producer.send(config.RAW_DATA_TOPIC, self.mock_data)
            mock_producer.return_value.produce.assert_called_once()

    @patch('pyflink.datastream.StreamExecutionEnvironment.get_execution_environment')
    def test_flink_processor(self, mock_env):
        processor = FlinkProcessor(config.KAFKA_BOOTSTRAP_SERVERS, config.RAW_DATA_TOPIC, config.PROCESSED_DATA_TOPIC)
        processor.start_processing()
        mock_env.return_value.execute.assert_called_once()

    @patch('pyspark.sql.SparkSession.builder')
    def test_spark_processor(self, mock_spark_builder):
        mock_spark = Mock()
        mock_spark_builder.getOrCreate.return_value = mock_spark
        processor = SparkProcessor(config.KAFKA_BOOTSTRAP_SERVERS, config.RAW_DATA_TOPIC, config.BATCH_PROCESSED_DATA_TOPIC)
        processor.start_processing()
        mock_spark.readStream.format.assert_called_with("kafka")

    def test_duckdb_handler(self):
        with patch('duckdb.connect') as mock_connect:
            handler = DuckDBHandler(config.DUCKDB_FILE)
            handler.store(self.mock_data)
            mock_connect.return_value.executemany.assert_called_once()

    @pytest.mark.integration
    def test_kafka_integration(self):
        producer = KafkaProducer(config.KAFKA_BOOTSTRAP_SERVERS)
        consumer = KafkaConsumer(config.RAW_DATA_TOPIC, config.KAFKA_BOOTSTRAP_SERVERS)

        producer.send(config.RAW_DATA_TOPIC, self.mock_data)
        producer.flush()

        messages = list(consumer.consume(timeout=5))
        self.assertEqual(len(messages), 1)
        self.assertEqual(json.loads(messages[0]), self.mock_data[0])

    @pytest.mark.integration
    def test_end_to_end():
        # Initialize components
        ib_provider = IBProvider(config.IB_HOST, config.IB_PORT, config.IB_CLIENT_ID)
        other_provider = OtherProvider()
        kafka_producer = KafkaProducer(config.KAFKA_BOOTSTRAP_SERVERS)
        kafka_consumer = KafkaConsumer(config.PROCESSED_DATA_TOPIC, config.KAFKA_BOOTSTRAP_SERVERS)
        db_handler = DuckDBHandler(config.DUCKDB_FILE)

        # Fetch and send data
        for provider in [ib_provider, other_provider]:
            data = provider.fetch_data()
            kafka_producer.send(config.RAW_DATA_TOPIC, data)

        # Allow time for processing
        time.sleep(10)

        # Consume processed data
        processed_data = list(kafka_consumer.consume(timeout=5))

        # Store in DuckDB
        db_handler.store(processed_data)

        # Verify data in DuckDB
        result = db_handler.conn.execute("SELECT COUNT(*) FROM market_data").fetchone()[0]
        assert result > 0, "No data found in DuckDB"

        # Clean up
        db_handler.cleanup_old_data(days=1)

if __name__ == '__main__':
    unittest.main()