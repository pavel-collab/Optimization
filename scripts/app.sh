#!/bin/bash

# Параметры по умолчанию
DEFAULT_BINARY="./app"
PID_FILE="/tmp/app.pid"
LOG_FILE="/tmp/app.log"

# Функция для вывода справки
show_help() {
    echo "Использование: $0 [команда] [путь_к_бинарнику]"
    echo ""
    echo "Команды:"
    echo "  start [путь]  - Запустить приложение (путь опционально)"
    echo "  stop          - Остановить приложение"
    echo "  status        - Показать статус приложения"
    echo "  restart [путь]- Перезапустить приложение"
    echo "  help          - Показать эту справку"
    echo ""
    echo "Примеры:"
    echo "  $0 start /usr/local/bin/myapp"
    echo "  $0 start"
    echo "  $0 stop"
    echo "  $0 status"
}

# Функция запуска приложения
start_app() {
    local BINARY="$1"
    
    # Проверка существования бинарника
    if [ ! -f "$BINARY" ]; then
        echo "Ошибка: Файл $BINARY не найден!" >&2
        exit 1
    fi

    # Проверка прав на выполнение
    if [ ! -x "$BINARY" ]; then
        echo "Ошибка: Нет прав на выполнение $BINARY!" >&2
        exit 1
    fi

    # Проверка, не запущено ли уже приложение
    if [ -f "$PID_FILE" ]; then
        local EXISTING_PID=$(cat "$PID_FILE")
        if ps -p "$EXISTING_PID" > /dev/null 2>&1; then
            echo "Приложение уже запущено с PID: $EXISTING_PID"
            exit 1
        else
            # Удаляем старый PID файл если процесс не существует
            rm -f "$PID_FILE"
        fi
    fi

    # Запуск в фоне
    echo "Запуск приложения: $BINARY"
    "$BINARY" >> "$LOG_FILE" 2>&1 &
    local PID=$!

    # Сохраняем PID в файл
    echo "$PID" > "$PID_FILE"
    
    # Ждем немного для инициализации
    sleep 1
    
    # Проверяем, что процесс запустился
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "Приложение успешно запущено:"
        echo "  PID: $PID"
        echo "  PID файл: $PID_FILE"
        echo "  Логи: $LOG_FILE"
        echo "$PID"
    else
        echo "Ошибка: Приложение не запустилось!" >&2
        rm -f "$PID_FILE"
        exit 1
    fi
}

# Функция остановки приложения
stop_app() {
    if [ ! -f "$PID_FILE" ]; then
        echo "PID файл не найден: $PID_FILE"
        echo "Приложение, вероятно, не запущено"
        exit 1
    fi

    local PID=$(cat "$PID_FILE")
    
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "Остановка приложения (PID: $PID)..."
        kill "$PID"
        
        # Ждем завершения процесса
        local TIMEOUT=10
        local COUNTER=0
        while ps -p "$PID" > /dev/null 2>&1 && [ "$COUNTER" -lt "$TIMEOUT" ]; do
            sleep 1
            COUNTER=$((COUNTER + 1))
        done
        
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "Принудительное завершение..."
            kill -9 "$PID"
            sleep 2
        fi
        
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "Ошибка: Не удалось остановить приложение!" >&2
            exit 1
        else
            rm -f "$PID_FILE"
            echo "Приложение успешно остановлено"
        fi
    else
        echo "Процесс с PID $PID не найден"
        rm -f "$PID_FILE"
    fi
}

# Функция проверки статуса
status_app() {
    if [ ! -f "$PID_FILE" ]; then
        echo "Приложение не запущено"
        exit 0
    fi

    local PID=$(cat "$PID_FILE")
    
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "Приложение запущено:"
        echo "  PID: $PID"
        echo "  Команда: $(ps -p "$PID" -o command= 2>/dev/null || echo "недоступно")"
        echo "  Время работы: $(ps -p "$PID" -o etime= 2>/dev/null || echo "недоступно")"
    else
        echo "Приложение не запущено (старый PID файл присутствует: $PID_FILE)"
        rm -f "$PID_FILE"
    fi
}

# Функция перезапуска
restart_app() {
    local BINARY="$1"
    if [ -f "$PID_FILE" ]; then
        stop_app
        sleep 2
    fi
    start_app "$BINARY"
}

# Основная логика
COMMAND="${1:-help}"
BINARY_PATH="${2:-$DEFAULT_BINARY}"

case "$COMMAND" in
    start)
        start_app "$BINARY_PATH"
        ;;
    stop)
        stop_app
        ;;
    status)
        status_app
        ;;
    restart)
        restart_app "$BINARY_PATH"
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "Неизвестная команда: $COMMAND"
        echo "Используйте '$0 help' для просмотра справки"
        exit 1
        ;;
esac
