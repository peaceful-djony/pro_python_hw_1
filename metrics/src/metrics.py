import json

import numpy as np
import pika
from pika.adapters.blocking_connection import BlockingChannel

from pika.spec import Basic, BasicProperties

TARGET_QUEUE_NAME = "y_true"
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


# Словарь с ключом идентификатор и значением предсказания или истинного значения
id_cache: dict[str, float] = {}


def parse_message(message: bytes) -> RabbitMessage:
    return RabbitMessage(**json.loads(message))


def absolute_error_metric(y_true: float, y_pred: float) -> float:
    """Метрика расчета абсолютной ошибки."""
    err = np.abs(y_true - y_pred)
    return err


def target_callback(
        ch: BlockingChannel,
        method: Basic.Deliver,
        properties: BasicProperties,
        body: bytes,
) -> None:
    message = parse_message(body)
    try_log(message, 'target')


def predict_callback(
        ch: BlockingChannel,
        method: Basic.Deliver,
        properties: BasicProperties,
        body: bytes,
) -> None:
    message = parse_message(body)
    try_log(message, 'prediction')


def try_log(
        message: RabbitMessage,
        value_type: str,  # todo enum?
) -> None:
    if value_type == 'target':
        y_pred = float(message.body)
        y_true = id_cache.get(message.id)
        id_cache[message.id] = y_pred
    elif value_type == 'prediction':
        y_pred = id_cache.get(message.id)
        y_true = float(message.body)
        id_cache[message.id] = y_true
    else:
        raise ValueError(f'Unknown value type {value_type}')

    if not y_true or not y_pred:
        # пришел только один компонент и пока невозможно вычислить ошибку
        return

    err = absolute_error_metric(y_true, y_pred)
    # Очистка словаря чтоб не забивать память информацией, которая никогда не пригодится
    del id_cache[message.id]

    # todo set name from env
    with open("logs/metric_log.csv", "a") as metrics_file:
        metrics_file.write(f"{message.id},{y_true},{y_pred},{err}\n")


connection = pika.BlockingConnection(pika.ConnectionParameters("rabbitmq"))
with connection.channel() as channel:
    channel.queue_declare(queue=TARGET_QUEUE_NAME)
    channel.queue_declare(queue=PREDICTION_QUEUE_NAME)

    channel.basic_consume(queue=TARGET_QUEUE_NAME, on_message_callback=target_callback, auto_ack=True)
    channel.basic_consume(queue=PREDICTION_QUEUE_NAME, on_message_callback=predict_callback, auto_ack=True)

    print(f'Запущено прослушивание очередей {BColors.OKBLUE}{TARGET_QUEUE_NAME}{BColors.ENDC} и {BColors.OKBLUE}{PREDICTION_QUEUE_NAME}{BColors.ENDC}')
    channel.start_consuming()
