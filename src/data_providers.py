from ib_insync import IB, Contract
import yfinance as yf
import logging
from retry import retry
from ratelimit import limits, sleep_and_retry
from src import config

logger = logging.getLogger(__name__)

class IBProvider:
    def __init__(self, host, port, client_id):
        self.ib = IB()
        self.host = host
        self.port = port
        self.client_id = client_id

    @retry(tries=3, delay=1, backoff=2)
    def connect(self):
        try:
            self.ib.connect(self.host, self.port, clientId=self.client_id)
            logger.info(f"Connected to IB on {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to connect to IB: {str(e)}")
            raise

    @sleep_and_retry
    @limits(calls=5, period=60)  # Limit to 5 calls per minute
    @retry(tries=3, delay=1, backoff=2)
    def fetch_data(self):
        if not self.ib.isConnected():
            self.connect()
        
        contract = Contract(symbol="AAPL", secType="STK", exchange="SMART", currency="USD")
        try:
            bars = self.ib.reqHistoricalData(
                contract, endDateTime='', durationStr='1 D',
                barSizeSetting='1 min', whatToShow='TRADES', useRTH=True
            )
            logger.info(f"Fetched {len(bars)} bars from IB")
            return [{"timestamp": bar.date, "open": bar.open, "high": bar.high, 
                     "low": bar.low, "close": bar.close, "volume": bar.volume} for bar in bars]
        except Exception as e:
            logger.error(f"Failed to fetch data from IB: {str(e)}")
            raise

class OtherProvider:
    @sleep_and_retry
    @limits(calls=5, period=60)  # Limit to 5 calls per minute
    @retry(tries=3, delay=1, backoff=2)
    def fetch_data(self):
        try:
            data = yf.download("AAPL", period="1d", interval="1m")
            logger.info(f"Fetched {len(data)} rows from Yahoo Finance")
            return data.reset_index().to_dict('records')
        except Exception as e:
            logger.error(f"Failed to fetch data from Yahoo Finance: {str(e)}")
            raise