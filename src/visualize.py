#!/usr/bin/env python3

"""
Визуализация собранных метрик производительности
Создаёт графики для анализа CPU, памяти, диска, сети и прерываний
"""
import sys
from modules import MetricsVisualizer

def main():
    data_dir = sys.argv[1] if len(sys.argv) > 1 else "monitoring_data"

    visualizer = MetricsVisualizer(data_dir)
    visualizer.create_all_plots()

if __name__ == "__main__":
    main()
