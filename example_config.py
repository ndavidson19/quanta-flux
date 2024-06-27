import os

# Kafka configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:29092')
RAW_DATA_TOPIC = os.getenv('RAW_DATA_TOPIC', 'raw_market_data')
PROCESSED_DATA_TOPIC = os.getenv('PROCESSED_DATA_TOPIC', 'processed_market_data')
BATCH_PROCESSED_DATA_TOPIC = os.getenv('BATCH_PROCESSED_DATA_TOPIC', 'batch_processed_data')

# Database configuration
DUCKDB_FILE = os.getenv('DUCKDB_FILE', 'market_data.db')

# TimescaleDB configuration
TIMESCALE_HOST = os.getenv('TIMESCALE_HOST', 'timescaledb')
TIMESCALE_PORT = int(os.getenv('TIMESCALE_PORT', 5432))
TIMESCALE_USER = os.getenv('TIMESCALE_USER', 'user')
TIMESCALE_PASSWORD = os.getenv('TIMESCALE_PASSWORD', 'password')
TIMESCALE_DB = os.getenv('TIMESCALE_DB', 'marketdata')

# API configuration
IB_HOST = os.getenv('IB_HOST', 'ibkr')
IB_PORT = int(os.getenv('IB_PORT', 8888))
IB_CLIENT_ID = int(os.getenv('IB_CLIENT_ID', 1))
IB_USERNAME = os.getenv('IB_USERNAME', 'USERNAME')
IB_PASSWORD = os.getenv('IB_PASSWORD', 'PASSWORD')

# Logging configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Prometheus configuration
PROMETHEUS_PORT = int(os.getenv('PROMETHEUS_PORT', 8000))

# Environment
ENV = os.getenv('ENV', 'development')

# Strategy execution configuration
SYNC_INTERVAL = int(os.getenv('SYNC_INTERVAL', 3600))  # Default to 1 hour
STRATEGY_EXECUTION_INTERVAL = int(os.getenv('STRATEGY_EXECUTION_INTERVAL', 3600))  # Default to 1 hour