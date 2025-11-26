#!/bin/bash
# Автоматический запуск исследования бинарного файла

# Скрипт запускает приложение, мониторинг и генерацию нагрузки
set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Конфигурация
BINARY_PATH="${1:-./app}"
MONITORING_INTERVAL="${2:-1}"
TEST_DURATION="${3:-300}"
OUTPUT_DIR="performance_analysis_$(date +%Y%m%d_%H%M%S)"
echo -e "${GREEN}=== Black Box Performance Analysis ===${NC}"
echo "Binary: $BINARY_PATH"
echo "Monitoring interval: ${MONITORING_INTERVAL}s"
echo "Test duration: ${TEST_DURATION}s"
echo "Output directory: $OUTPUT_DIR"
echo ""

# Проверка бинарного файла
check_binary() {
    echo -e "${YELLOW}Checking binary file...${NC}"

    if [ ! -f "$BINARY_PATH" ]; then
        echo -e "${RED}Error: Binary file not found: $BINARY_PATH${NC}"
        exit 1
    fi

    if [ ! -x "$BINARY_PATH" ]; then
        echo "Making binary executable..."
        chmod +x "$BINARY_PATH"
    fi

    # Получение информации о бинарнике
    echo "Binary info:"
    file "$BINARY_PATH"
    ls -lh "$BINARY_PATH"

    # Проверка зависимостей
    echo ""
    echo "Library dependencies:"
    ldd "$BINARY_PATH" || true

    echo -e "${GREEN} Binary is ready${NC}"
}

# Запуск приложения
start_application() {
    echo -e "${YELLOW}Starting application...${NC}"

    # Запуск в фоне
    "$BINARY_PATH" > "$OUTPUT_DIR/app_stdout.log" 2> "$OUTPUT_DIR/app_stderr.log" &
    APP_PID=$!

    echo "Application PID: $APP_PID"
    echo $APP_PID > "$OUTPUT_DIR/app.pid"

    # Ждём запуска
    sleep 3

    # Проверка, что процесс жив
    if ! kill -0 $APP_PID 2>/dev/null; then
        echo -e "${RED}Error: Application failed to start${NC}"
        echo "STDOUT:"

        cat "$OUTPUT_DIR/app_stdout.log"
        echo "STDERR:"

        cat "$OUTPUT_DIR/app_stderr.log"
        exit 1
    fi

    echo -e "${GREEN} Application started${NC}"
}

# Запуск мониторинга
start_monitoring() {
    echo -e "${YELLOW}Starting performance monitoring...${NC}"

    python3 ./src/monitoring.py $APP_PID "$OUTPUT_DIR/monitoring_data" $MONITORING_INTERVAL &

    MONITOR_PID=$!

    echo $MONITOR_PID > "$OUTPUT_DIR/monitor.pid"

    echo "Monitor PID: $MONITOR_PID"
    echo -e "${GREEN} Monitoring started${NC}"
}

# Дополнительный детальный мониторинг
detailed_monitoring() {
    echo -e "${YELLOW}Starting detailed monitoring...${NC}"

    # perf для профилирования
    if command -v perf &> /dev/null; then
        echo "Starting perf profiling..."
        sudo perf record -F 99 -p $APP_PID -g -o "$OUTPUT_DIR/perf.data" -- sleep $TEST_DURATION &
        PERF_PID=$!
    fi

    # strace для системных вызовов
    echo "Starting strace..."
    sudo strace -c -p $APP_PID -o "$OUTPUT_DIR/strace_summary.txt" 2>&1 &
    STRACE_PID=$!

    # Периодический сбор дополнительных метрик
    (
        while kill -0 $APP_PID 2>/dev/null; do
            timestamp=$(date +%s)

            # Снимок состояния процесса
            ps -p $APP_PID -o pid,ppid,cmd,%cpu,%mem,vsz,rss,stat,start,time,nlwp >> "$OUTPUT_DIR/process_snapshots.txt"
            echo "---" >> "$OUTPUT_DIR/process_snapshots.txt"

            # Открытые файлы
            lsof -p $APP_PID 2>/dev/null | wc -l >> "$OUTPUT_DIR/open_files_count.txt"

            # Сетевые соединения
            ss -tanp | grep $APP_PID >> "$OUTPUT_DIR/network_connections.txt" 2>/dev/null || true
            echo "--- $(date) ---" >> "$OUTPUT_DIR/network_connections.txt"

            sleep 10
        done
    ) &
    SNAPSHOT_PID=$!

    echo -e "${GREEN} Detailed monitoring started${NC}"
}

# Генерация нагрузки
generate_load() {
    echo -e "${YELLOW}Generating load...${NC}"

    # Определение типа приложения
    if netstat -tuln | grep -q ":808[0-9]"; then
        echo "Detected HTTP server, generating HTTP load..."

        # Простая HTTP нагрузка с curl
        for i in $(seq 1 $TEST_DURATION); do
            curl -s http://localhost:8080/ > /dev/null 2>&1 || true
            curl -s http://localhost:8080/api/data > /dev/null 2>&1 || true
            sleep 1
        done

    else
        echo "Running application in stress mode..."
        # Просто ждём указанное время
        sleep $TEST_DURATION
    fi

    echo -e "${GREEN} Load generation completed${NC}"
}

# Остановка всех процессов
cleanup() {
    echo -e "${YELLOW}Cleaning up...${NC}"

    # Остановка мониторинга
    if [ -f "$OUTPUT_DIR/monitor.pid" ]; then
        MONITOR_PID=$(cat "$OUTPUT_DIR/monitor.pid")
        kill $MONITOR_PID 2>/dev/null || true
    fi

    # Остановка дополнительных мониторов
    [ ! -z "$PERF_PID" ] && sudo kill $PERF_PID 2>/dev/null || true
    [ ! -z "$STRACE_PID" ] && sudo kill $STRACE_PID 2>/dev/null || true
    [ ! -z "$SNAPSHOT_PID" ] && kill $SNAPSHOT_PID 2>/dev/null || true

    # Остановка приложения
    if [ -f "$OUTPUT_DIR/app.pid" ]; then
        APP_PID=$(cat "$OUTPUT_DIR/app.pid")
        echo "Stopping application (PID: $APP_PID)..."
        kill $APP_PID 2>/dev/null || true
        sleep 2
        kill -9 $APP_PID 2>/dev/null || true
    fi

    echo -e "${GREEN} Cleanup completed${NC}"
}

# Генерация отчёта
generate_report() {
    echo -e "${YELLOW}Generating analysis report...${NC}"

    # Визуализация метрик
    python3 ./src/visualize.py "$OUTPUT_DIR/monitoring_data"

    # Генерация текстового отчёта
    cat > "$OUTPUT_DIR/REPORT.md" << EOF

# Performance Analysis Report

**Date:** $(date)
**Binary:** $BINARY_PATH
**Duration:** ${TEST_DURATION}s
**Output Directory:** $OUTPUT_DIR

## Executive Summary
This report contains comprehensive performance analysis of the application.

## Test Configuration
- Monitoring Interval: ${MONITORING_INTERVAL}s
- Test Duration: ${TEST_DURATION}s
- System: $(uname -a)

## Key Findings

### CPU Analysis
See: monitoring_data/plots/cpu_analysis.png

### Memory Analysis
See: monitoring_data/plots/memory_analysis.png

### Disk I/O Analysis
See: monitoring_data/plots/disk_analysis.png

### Network Analysis
See: monitoring_data/plots/network_analysis.png

### Thread Analysis
See: monitoring_data/plots/thread_analysis.png

### TCP Analysis
See: monitoring_data/plots/tcp_analysis.png

### Interrupt Analysis
See: monitoring_data/plots/interrupt_analysis.png

## Raw Data
All raw metrics are available in CSV format in the \`monitoring_data\` directory.

## Additional Information
- Application logs: app_stdout.log, app_stderr.log
- Process snapshots: process_snapshots.txt
- Network connections: network_connections.txt
- Strace summary: strace_summary.txt
EOF

    echo -e "${GREEN} Report generated: $OUTPUT_DIR/REPORT.md${NC}"

    echo -e "${YELLOW} Generate json anomaly report...${NC}"

    python3 ./src/detecting.py "$OUTPUT_DIR/monitoring_data"

    echo -e "${GREEN} Json anomaly report generated${NC}"
}

# Trap для cleanup при прерывании
trap cleanup EXIT INT TERM

# Основной процесс
main() {
    mkdir -p "$OUTPUT_DIR"
    check_binary

    start_application
    sleep 2

    start_monitoring
    detailed_monitoring

    echo ""
    echo -e "${GREEN}=== Monitoring in progress ===${NC}"
    echo "Duration: ${TEST_DURATION}s"
    echo "Press Ctrl+C to stop early"
    echo ""

    generate_load

    # Ждём завершения
    echo ""
    echo "Waiting for monitoring to complete..."

    sleep 5

    cleanup
    generate_report

    echo ""
    echo -e "${GREEN}=== Analysis Complete ===${NC}"
    echo "Results saved to: $OUTPUT_DIR"
    echo ""
    echo "To view the report:"
    echo "  cat $OUTPUT_DIR/REPORT.md"
    echo ""
    echo "To view plots:"
    echo "  ls $OUTPUT_DIR/monitoring_data/plots/"
}

# Проверка прав root для некоторых команд
if [ "$EUID" -ne 0 ]; then 
    echo -e "${YELLOW}Note: Some advanced monitoring features require root privileges${NC}"
    echo "Consider running with sudo for full analysis"
    echo ""
fi

main
