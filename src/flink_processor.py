import os
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.table import StreamTableEnvironment, EnvironmentSettings
import requests

class FlinkProcessor:
    def __init__(self, bootstrap_servers, input_topic, output_topic):
        self.bootstrap_servers = bootstrap_servers
        self.input_topic = input_topic
        self.output_topic = output_topic
        self.flink_jobmanager_url = "http://flink-jobmanager:8081"

    def start_processing(self):
        # Create the Flink job
        job_graph = self.create_flink_job()

        # Submit the job to the Flink cluster
        self.submit_job(job_graph)

    def create_flink_job(self):
        env = StreamExecutionEnvironment.get_execution_environment()
        t_env = StreamTableEnvironment.create(env)

        # Define the source table (Kafka input)
        t_env.execute_sql(f"""
            CREATE TABLE source_table (
                timestamp TIMESTAMP(3),
                symbol STRING,
                price DOUBLE,
                volume INT,
                event_time AS CAST(timestamp AS TIMESTAMP(3)),
                WATERMARK FOR event_time AS event_time - INTERVAL '5' SECOND
            ) WITH (
                'connector' = 'kafka',
                'topic' = '{self.input_topic}',
                'properties.bootstrap.servers' = '{self.bootstrap_servers}',
                'format' = 'json',
                'scan.startup.mode' = 'latest-offset'
            )
        """)

        # Define the sink table (Kafka output)
        t_env.execute_sql(f"""
            CREATE TABLE sink_table (
                window_start TIMESTAMP(3),
                window_end TIMESTAMP(3),
                symbol STRING,
                avg_price DOUBLE,
                total_volume BIGINT
            ) WITH (
                'connector' = 'kafka',
                'topic' = '{self.output_topic}',
                'properties.bootstrap.servers' = '{self.bootstrap_servers}',
                'format' = 'json'
            )
        """)

        # Define and execute the query
        t_env.execute_sql("""
            INSERT INTO sink_table
            SELECT 
                TUMBLE_START(event_time, INTERVAL '1' MINUTE) AS window_start,
                TUMBLE_END(event_time, INTERVAL '1' MINUTE) AS window_end,
                symbol,
                AVG(price) AS avg_price,
                SUM(volume) AS total_volume
            FROM source_table
            GROUP BY TUMBLE(event_time, INTERVAL '1' MINUTE), symbol
        """)

        return env.get_execution_plan()

    def submit_job(self, job_graph):
        url = f"{self.flink_jobmanager_url}/jars/upload"
        files = {'jarfile': ('job.jar', job_graph)}
        response = requests.post(url, files=files)
        
        if response.status_code == 200:
            jar_id = response.json()['filename'].split('/')[-1]
            run_url = f"{self.flink_jobmanager_url}/jars/{jar_id}/run"
            run_response = requests.post(run_url)
            
            if run_response.status_code == 200:
                print(f"Job submitted successfully. Job ID: {run_response.json()['jobid']}")
            else:
                print(f"Failed to run job. Status code: {run_response.status_code}")
        else:
            print(f"Failed to upload jar. Status code: {response.status_code}")