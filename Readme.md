# Quick start

start all the services
```bash
docker-compose up -d --build
```

# Description
Репозиторий представляет собой набор учебных сервисов для обработки данных:
- features производит (producer) признаки и таргет раз в 3 сек. (SLEEP_INTERVAL_IN_SEC)
- metrics потребляет (consumer) таргет и предсказания, вычисляет absolute error и записывает их в логи
- model производит инференс потребляя (consumer) признаки и производя (producer) предсказания
- plot раз в 5 сек. создает гистограмму absolute error и сохраняет ее в файле logs/error_distribution.png 
