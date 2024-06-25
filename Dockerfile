FROM python:3.9

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]

# requirements.txt
confluent-kafka==1.9.2
apache-flink==1.16.0
pyspark==3.3.2
duckdb==0.7.1
pandas==1.5.3
ib-insync==0.9.70
yfinance==0.2.18