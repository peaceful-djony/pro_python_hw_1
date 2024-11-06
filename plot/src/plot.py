import pandas as pd
import time
import matplotlib.pyplot as plt
import os
import seaborn as sns

# Создание директории для логов, если она не существует
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
log_path = os.path.join(log_dir, 'error_distribution.png')

while True:
    df = pd.read_csv("logs/metric_log.csv")

    # Построение гистограммы
    plt.figure(figsize=(10, 6))
    sns.histplot(df['absolute_error'], bins=30, kde=True, color='orange')

    # Сохранение графика в файл
    plt.savefig(log_path)
    plt.close()
    time.sleep(5) # Перерисовка будет через 5 секунд