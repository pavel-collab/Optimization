#!/usr/bin/env python3

"""
Автоматический детектор аномалий в метриках производительности
Анализирует собранные данные и выявляет проблемы
"""
import sys
from .modules import AnomalyDetector

def main():
    data_dir = sys.argv[1] if len(sys.argv) > 1 else "monitoring_data"

    detector = AnomalyDetector(data_dir)
    detector.run_detection()

if __name__ == "__main__":
    main()
