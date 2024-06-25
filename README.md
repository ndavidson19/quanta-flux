# quanta-flux

## Overview
quanta-flux is the data operations service for the Quanta platform. It handles data ingestion, processing, and storage of market data and other relevant financial information.

## Key Features
- Real-time market data ingestion from multiple sources
- Data normalization and cleaning
- Time-series data storage
- Efficient data retrieval APIs
- Historical data management

## Technology Stack
- Python
- Apache Kafka for data streaming
- Apache Flink for stream processing
- InfluxDB for time-series data storage
- FastAPI for API endpoints
- DuckDB for analytical queries

## Setup
1. Clone the repository:
   ```
   git clone https://github.com/quantforge/quanta-flux.git
   cd quanta-flux
   ```
2. Set up a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Set up environment variables:
   ```
   cp .env.example .env
   # Edit .env with your configuration
   ```
5. Start the service:
   ```
   python main.py
   ```

## Data Sources Configuration
Edit `config/data_sources.yaml` to add or modify data sources.

## API Documentation
After starting the service, visit `http://localhost:8000/docs` for Swagger UI API documentation.

## Testing
```
pytest
```

## Contributing
Please read CONTRIBUTING.md for details on our code of conduct and the process for submitting pull requests.

## License
This project is licensed under the MIT License - see the LICENSE file for details.
