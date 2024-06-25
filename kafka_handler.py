from confluent_kafka import Producer, Consumer, KafkaError
import json

class KafkaProducer:
    def __init__(self, bootstrap_servers):
        self.producer = Producer({'bootstrap.servers': bootstrap_servers})

    def send(self, topic, data):
        self.producer.produce(topic, json.dumps(data).encode('utf-8'))
        self.producer.flush()

class KafkaConsumer:
    def __init__(self, topic, bootstrap_servers):
        self.consumer = Consumer({
            'bootstrap.servers': bootstrap_servers,
            'group.id': 'market_data_group',
            'auto.offset.reset': 'earliest'
        })
        self.consumer.subscribe([topic])

    def consume(self):
        while True:
            msg = self.consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    print(f"Consumer error: {msg.error()}")
                    break
            yield json.loads(msg.value().decode('utf-8'))