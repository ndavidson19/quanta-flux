from ib_insync import IB, Contract
import yfinance as yf

class IBProvider:
    def __init__(self):
        self.ib = IB()
        self.ib.connect('127.0.0.1', 7497, clientId=1)

    def fetch_data(self):
        contract = Contract(symbol="AAPL", secType="STK", exchange="SMART", currency="USD")
        bars = self.ib.reqHistoricalData(
            contract, endDateTime='', durationStr='1 D',
            barSizeSetting='1 min', whatToShow='TRADES', useRTH=True
        )
        return [{"timestamp": bar.date, "open": bar.open, "high": bar.high, 
                 "low": bar.low, "close": bar.close, "volume": bar.volume} for bar in bars]

class OtherProvider:
    def fetch_data(self):
        data = yf.download("AAPL", period="1d", interval="1m")
        return data.reset_index().to_dict('records')
    