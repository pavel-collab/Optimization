# Описание системы
Исследования проводились на 4й raspberry pi с дистрибутовом linux на основе Debian. 
```
Linux raspberrypi 6.12.34+rpt-rpi-v8 #1 SMP PREEMPT Debian 1:6.12.34-1+rpt1~bookworm (2025-06-26) aarch64 GNU/Linux
```
4 логических ядра процессора, 8 Гб оперативной памяти

Детальная информация о системе в файле docs/system_info.txt

# Описание черного ящика
При базовом запуске приложение запускает некоторый сервер на локальном хосте на порту 8080

Для того, чтобы разархивировать бинарники
```
cd bin 
tar -x -f binaries.py
```

# Установка необходимых инструментов для исследования
```
sudo apt install -y sysstat htop iotop procps linux-perf strace
```

# Запуск скриптов

Запуск/остановка приложения в фоновом режиме
```
./scripts/app start ./bin/app_linux_arm64 # stop -- чтобы остановить
```

# Запуск анализатора

```
python3 ./src/monitoring <app pid>
```

# Визуализация результатов

```
python3 ./src/visualize.py
```

# Анализ результатов

```
python3 ./src/detecting.py
```

# Автоматический запуск скрипта для анализа приложения

```
./scripts/run.sh 1 300
```