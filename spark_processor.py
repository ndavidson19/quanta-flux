from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, TimestampType

class SparkProcessor:
    def __init__(self, bootstrap_servers, input_topic, output_topic):
        self.spark = SparkSession.builder.appName("SparkMarketDataProcessor").getOrCreate()
        self.bootstrap_servers = bootstrap_servers
        self.input_topic = input_topic
        self.output_topic = output_topic

    def start_processing(self):
        # Define the schema for the input data
        schema = StructType([
            StructField("timestamp", TimestampType()),
            StructField("open", DoubleType()),
            StructField("high", DoubleType()),
            StructField("low", DoubleType()),
            StructField("close", DoubleType()),
            StructField("volume", DoubleType())
        ])

        # Read from Kafka
        df = self.spark.readStream.format("kafka") \
            .option("kafka.bootstrap.servers", self.bootstrap_servers) \
            .option("subscribe", self.input_topic) \
            .load()

        # Parse the JSON data
        parsed_df = df.select(from_json(col("value").cast("string"), schema).alias("data")).select("data.*")

        # Apply transformations
        processed_df = self.process_data(parsed_df)

        # Write the processed data back to Kafka
        query = processed_df.selectExpr("to_json(struct(*)) AS value") \
            .writeStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", self.bootstrap_servers) \
            .option("topic", self.output_topic) \
            .option("checkpointLocation", "/tmp/spark_checkpoint") \
            .start()

        query.awaitTermination()

    def process_data(self, df):
        # Implement your batch processing logic here
        # This is a placeholder - you'd typically add columns, aggregate data, etc.
        return df.withColumn("processed", col("close") * 2)
