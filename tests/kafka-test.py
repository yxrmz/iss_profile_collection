import matplotlib
matplotlib.use("agg")

from kafka import KafkaProducer, KafkaConsumer

kafka_host = 'cmb01:9092'
mytopic = 'iss-analysis'

producer = KafkaProducer(bootstrap_servers=kafka_host)


producer.send(mytopic, b'test')

consumer = KafkaConsumer(bootstrap_servers=kafka_host,
                         auto_offset_reset='earliest',
                         consumer_timeout_ms=1000)
consumer.subscribe([mytopic])


