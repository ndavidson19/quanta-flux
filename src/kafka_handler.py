from confluent_kafka import Producer, Consumer, KafkaError
import json
import logging
from retry import retry
from src import config

logger = logging.getLogger(__name__)

class KafkaProducer:
    def __init__(self, bootstrap_servers):
        self.producer = Producer({'bootstrap.servers': bootstrap_servers})

    @retry(tries=3, delay=1, backoff=2)
    def send(self, topic, data):
        try:
            self.producer.produce(topic, json.dumps(data).encode('utf-8'), callback=self.delivery_report)
            self.producer.flush()
            logger.info(f"Sent {len(data)} messages to topic {topic}")
        except Exception as e:
            logger.error(f"Failed to send data to Kafka: {str(e)}")
            raise

    def delivery_report(self, err, msg):
        if err is not None:
            logger.error(f"Message delivery failed: {err}")
        else:
            logger.debug(f"Message delivered to {msg.topic()} [{msg.partition()}]")

class KafkaConsumer:
    def __init__(self, topic, bootstrap_servers):
        self.consumer = Consumer({
            'bootstrap.servers': bootstrap_servers,
            'group.id': 'market_data_group',
            'auto.offset.reset': 'earliest',
            'enable.auto.commit': False
        })
        self.consumer.subscribe([topic])
        self.topic = topic

    @retry(tries=3, delay=1, backoff=2)
    def consume(self):
        try:
            while True:
                msg = self.consumer.poll(1.0)
                if msg is None:
                    continue
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        logger.info(f"Reached end of partition for topic {self.topic}")
                        continue
                    else:
                        logger.error(f"Consumer error: {msg.error()}")
                        break
                yield json.loads(msg.value().decode('utf-8'))
                self.consumer.commit(msg)
        except Exception as e:
            logger.error(f"Error in Kafka consumer: {str(e)}")
            raise
        finally:
            self.consumer.close()