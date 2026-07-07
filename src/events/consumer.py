import os
import json
from confluent_kafka import Consumer, KafkaError, KafkaException

KAFKA_BROKER = os.environ.get("KAFKA_BROKER", "localhost:19092")

def create_consumer():
    conf = {
        'bootstrap.servers': KAFKA_BROKER,
        'group.id': 'marketing_sim_group',
        'auto.offset.reset': 'earliest'
    }
    return Consumer(conf)

def consume_events():
    consumer = create_consumer()
    # Subscribe to the simulation events topics
    consumer.subscribe(['simulation_started', 'simulation_completed'])

    print(f"[*] Started consuming events from {KAFKA_BROKER}...")
    try:
        while True:
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    raise KafkaException(msg.error())
            
            topic = msg.topic()
            value = msg.value().decode('utf-8')
            print(f"[{topic}] Received event: {value}")
            
            # Here we could save events to Supabase or ClickHouse for Analytics
            # e.g., if topic == 'simulation_completed', track success rates.
            
    except KeyboardInterrupt:
        print("[*] Stopped consuming events.")
    finally:
        consumer.close()

if __name__ == "__main__":
    consume_events()
