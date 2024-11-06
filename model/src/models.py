import json
import pika
import pickle
import numpy as np
from pika.adapters.blocking_connection import BlockingChannel

FEATURES_QUEUE_NAME = "features"
PREDICTION_QUEUE_NAME = "y_pred"


class BColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class RabbitMessage:
    id: str
    body: str

    def __init__(self, id: str, body: str):
        self.id = id
        self.body = body


def publish_message(
        blocking_channel: BlockingChannel,
        queue_name: str,
        identity: str,
        body: any
) -> None:
    """
    Метод публикации сообщения в заданную очередь
    :param identity: Идентификатор сообщения
    :param blocking_channel: Канал публикации
    :param queue_name: Название очереди, куда будет отправлено сообщение
    :param body: Тело сообщения
    :return:
    """
    blocking_channel.queue_declare(queue=queue_name)

    if isinstance(body, np.ndarray):
        # массивы numpy не поддерживаются в стандарте JSON
        body = list(body)

    message = RabbitMessage(identity, body)
    body = json.dumps(message.__dict__)
    blocking_channel.basic_publish(
        exchange="",
        routing_key=queue_name,
        body=body,
    )
    print(f'Сообщение {body} отправлено в очередь {queue_name}')


def callback(ch, method, properties, body):
    body = json.loads(body)

    identity = body['id']
    features = body['body']
    features = np.array(features).reshape(1, -1)
    prediction = regressor.predict(features)[0]
    publish_message(ch, PREDICTION_QUEUE_NAME, identity, json.dumps(prediction))
    print(f"Предсказание {prediction} отправлено в очередь y_pred")


with open("myfile.pkl", "rb") as model_file:
    regressor = pickle.load(model_file)

try:
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
    with connection.channel() as channel:
        channel.queue_declare(queue=FEATURES_QUEUE_NAME)
        channel.basic_consume(queue=FEATURES_QUEUE_NAME, on_message_callback=callback, auto_ack=True)

        print(f'Запущено прослушивание очереди {BColors.OKBLUE}{FEATURES_QUEUE_NAME}{BColors.ENDC}')
        channel.start_consuming()
except Exception as ex:
    print('Не удалось подключиться к очереди')