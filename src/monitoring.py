#!/usr/bin/env python3

"""
Комплексная система мониторинга производительности для исследования черного ящика
Собирает метрики CPU, памяти, диска, сети и ядра
"""

import sys
from modules import PerformanceMonitor

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 perf_monitor.py <PID> [output_dir] [interval]")
        sys.exit(1)
    
    pid = int(sys.argv[1])
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "monitoring_data"
    interval = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0

    monitor = PerformanceMonitor(pid, output_dir)
    monitor.monitor(interval)

if __name__ == "__main__":
    main()
