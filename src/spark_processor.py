from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, to_json, struct, window, col, avg, stddev
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, TimestampType

class SparkProcessor:
    def __init__(self, bootstrap_servers, input_topic, output_topic):
        self.spark = SparkSession.builder.appName("SparkMarketDataProcessor").getOrCreate()
        self.bootstrap_servers = bootstrap_servers
        self.input_topic = input_topic
        self.output_topic = output_topic

    def start_processing(self):
        # Define schema for incoming data
        schema = StructType([
            StructField("timestamp", TimestampType()),
            StructField("open", DoubleType()),
            StructField("high", DoubleType()),
            StructField("low", DoubleType()),
            StructField("close", DoubleType()),
            StructField("volume", DoubleType()),
            StructField("symbol", StringType())
        ])

        # Read from Kafka
        df = self.spark.readStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", self.bootstrap_servers) \
            .option("subscribe", self.input_topic) \
            .option("startingOffsets", "earliest") \
            .load()

        # Parse JSON data
        parsed_df = df.select(from_json(col("value").cast("string"), schema).alias("data")).select("data.*")

        # Process the data
        processed_df = self.process_data(parsed_df)

        # Write results back to Kafka
        query = processed_df \
            .select(to_json(struct("*")).alias("value")) \
            .writeStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", self.bootstrap_servers) \
            .option("topic", self.output_topic) \
            .option("checkpointLocation", "/tmp/spark_checkpoints") \
            .start()

        query.awaitTermination()

    def process_data(self, df):
        # Calculate metrics over a sliding window
        return df \
            .withWatermark("timestamp", "1 minute") \
            .groupBy(
                window("timestamp", "5 minutes", "1 minute"),
                "symbol"
            ) \
            .agg(
                avg("close").alias("avg_price"),
                stddev("close").alias("price_volatility"),
                avg("volume").alias("avg_volume")
            ) \
            .select(
                col("window.start").alias("window_start"),
                col("window.end").alias("window_end"),
                "symbol",
                "avg_price",
                "price_volatility",
                "avg_volume"
            )