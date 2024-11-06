import datetime as dt
import json
import time
import numpy as np
import pika
from pika.adapters.blocking_connection import BlockingChannel
from sklearn.datasets import load_diabetes


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


def get_id() -> str:
    """Получение идентификатора сообщения"""
    identity = dt.datetime.timestamp(dt.datetime.now())
    return str(identity)


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


TARGET_QUEUE_NAME = "y_true"
FEATURES_QUEUE_NAME = "features"
SLEEP_INTERVAL_IN_SEC = 3

X, y = load_diabetes(return_X_y=True)

try:
    connection = pika.BlockingConnection(pika.ConnectionParameters("rabbitmq"))
    with connection.channel() as channel:
        while True:
                identity = get_id()
                random_row = np.random.randint(0, X.shape[0] - 1)
                publish_message(channel, TARGET_QUEUE_NAME, identity, y[random_row])
                publish_message(channel, FEATURES_QUEUE_NAME, identity, X[random_row])
                print(f"{BColors.OKGREEN}Ожидание следующей порции данных через {SLEEP_INTERVAL_IN_SEC} сек.{BColors.ENDC}")
                time.sleep(SLEEP_INTERVAL_IN_SEC)
except Exception as ex:
    print('Не удалось подключиться к очереди')
