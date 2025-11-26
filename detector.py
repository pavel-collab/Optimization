#!/usr/bin/env python3

"""
Автоматический детектор аномалий в метриках производительности
Анализирует собранные данные и выявляет проблемы
"""
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import json

class AnomalyDetector:
    def __init__(self, data_dir="monitoring_data"):
        self.data_dir = Path(data_dir)
        self.anomalies = []

    def load_data(self, filename):
        """Загрузить CSV файл"""
        filepath = self.data_dir / filename
        if not filepath.exists():
            return None
        return pd.read_csv(filepath)

    def detect_cpu_anomalies(self):
        """Детектирование аномалий CPU"""
        df = self.load_data('cpu_metrics.csv')
        if df is None:
            return

        print("\n=== CPU Anomaly Detection ===")

        # Высокий system time
        high_system = df[df['system'] > 30]
        if not high_system.empty:
            avg_system = high_system['system'].mean()

            self.anomalies.append({
                'category': 'CPU',
                'severity': 'HIGH',
                'issue': 'High System CPU Time',
                'details': f'System time exceeded 30% for {len(high_system)} samples (avg: {avg_system:.2f}%)',
                'suggestion': 'Check for excessive system calls, context switches, or kernel operations'
            })

            print(f"HIGH SYSTEM TIME: Average {avg_system:.2f}% in {len(high_system)} samples")

        # Высокий IOWait
        high_iowait = df[df['iowait'] > 20]

        if not high_iowait.empty:
            avg_iowait = high_iowait['iowait'].mean()

            self.anomalies.append({
                'category': 'CPU',
                'severity': 'HIGH',
                'issue': 'High IOWait',
                'details': f'IOWait exceeded 20% for {len(high_iowait)} samples (avg: {avg_iowait:.2f}%)',
                'suggestion': 'Disk I/O bottleneck detected. Check disk performance and I/O patterns'
            })

            print(f"HIGH IOWAIT: Average {avg_iowait:.2f}% in {len(high_iowait)} samples")

        # Длинная очередь выполнения
        high_runqueue = df[pd.to_numeric(df['runqueue'], errors='coerce') > 5]

        if not high_runqueue.empty:
            avg_runq = pd.to_numeric(high_runqueue['runqueue'], errors='coerce').mean()

            self.anomalies.append({
                'category': 'CPU',
                'severity': 'MEDIUM',
                'issue': 'Long Runqueue',
                'details': f'Runqueue length exceeded 5 for {len(high_runqueue)} samples (avg: {avg_runq:.2f})',
                'suggestion': 'CPU contention detected. Consider reducing concurrency or adding CPU resources'
            })

            print(f"LONG RUNQUEUE: Average {avg_runq:.2f} processes in {len(high_runqueue)} samples")

        # Рост system time процесса
        if 'proc_system' in df.columns:
            system_growth = df['proc_system'].diff()
            high_growth = system_growth[system_growth > 1.0]

            if not high_growth.empty:
                print(f"SYSTEM TIME GROWTH: {len(high_growth)} spikes detected")

                self.anomalies.append({
                    'category': 'CPU',
                    'severity': 'MEDIUM',
                    'issue': 'Process System Time Growth',
                    'details': f'Detected {len(high_growth)} spikes in system time usage',
                    'suggestion': 'Process is making frequent system calls. Profile with strace or perf'
                })

    def detect_memory_anomalies(self):
        """Детектирование аномалий памяти"""
        df = self.load_data('memory_metrics.csv')
        if df is None:
            return

        print("\n=== Memory Anomaly Detection ===")

        # Утечка памяти
        if len(df) > 10:
            rss_start = df['rss_mb'].iloc[:10].mean()
            rss_end = df['rss_mb'].iloc[-10:].mean()
            growth_rate = (rss_end - rss_start) / len(df)

            if growth_rate > 0.1:  # > 0.1 MB/s
                total_growth = rss_end - rss_start

                self.anomalies.append({
                    'category': 'Memory',
                    'severity': 'CRITICAL',
                    'issue': 'Memory Leak Detected',
                    'details': f'RSS grew from {rss_start:.2f}MB to {rss_end:.2f}MB ({total_growth:.2f}MB total, {growth_rate:.4f}MB/sample)',
                    'suggestion': 'Investigate memory allocations with valgrind or heap profiler'
                })

                print(f"MEMORY LEAK: RSS grew {total_growth:.2f}MB (rate: {growth_rate:.4f}MB/sample)")

        

        # Высокие page faults
        if 'page_faults_major' in df.columns:
            major_faults_rate = df['page_faults_major'].diff()
            high_faults = major_faults_rate[major_faults_rate > 10]

            if not high_faults.empty:
                avg_faults = high_faults.mean()

                self.anomalies.append({
                    'category': 'Memory',
                    'severity': 'HIGH',
                    'issue': 'High Major Page Faults',
                    'details': f'Major page faults exceeded 10/s for {len(high_faults)} samples (avg: {avg_faults:.2f}/s)',
                    'suggestion': 'Memory pressure detected. Check if working set exceeds physical memory'
                })

                print(f"HIGH MAJOR PAGE FAULTS: Average {avg_faults:.2f}/s in {len(high_faults)} samples")

        # Высокое использование памяти
        high_mem = df[df['mem_percent'] > 80]

        if not high_mem.empty:
            avg_mem = high_mem['mem_percent'].mean()
            self.anomalies.append({
                'category': 'Memory',
                'severity': 'MEDIUM',
                'issue': 'High Memory Usage',
                'details': f'Memory usage exceeded 80% for {len(high_mem)} samples (avg: {avg_mem:.2f}%)',
                'suggestion': 'Monitor for OOM conditions. Consider increasing memory limits'
            })

            print(f"HIGH MEMORY USAGE: Average {avg_mem:.2f}% in {len(high_mem)} samples")
    

    def detect_disk_anomalies(self):
        """Детектирование аномалий диска"""
        df = self.load_data('disk_metrics.csv')
        if df is None:
            return

        print("\n=== Disk I/O Anomaly Detection ===")

        # Высокая интенсивность записи
        if 'proc_write_bytes' in df.columns:
            write_rate = df['proc_write_bytes'].diff()
            high_write = write_rate[write_rate > 10000]  # > 10MB/s

            if not high_write.empty:
                avg_write = high_write.mean() / 1024

                self.anomalies.append({
                    'category': 'Disk',
                    'severity': 'MEDIUM',
                    'issue': 'High Write Rate',
                    'details': f'Write rate exceeded 10MB/s for {len(high_write)} samples (avg: {avg_write:.2f}MB/s)',
                    'suggestion': 'Check if writes are buffered or if there are many small sync operations'

                })
                print(f"HIGH WRITE RATE: Average {avg_write:.2f}MB/s in {len(high_write)} samples")


        # Высокое время ожидания I/O
        df_numeric = df.apply(pd.to_numeric, errors='coerce')

        if 'io_wait_time' in df_numeric.columns:
            high_wait = df_numeric[df_numeric['io_wait_time'] > 10]
            if not high_wait.empty:
                avg_wait = high_wait['io_wait_time'].mean()

                self.anomalies.append({
                    'category': 'Disk',
                    'severity': 'HIGH',
                    'issue': 'High I/O Wait Time',
                    'details': f'I/O wait time exceeded 10ms for {len(high_wait)} samples (avg: {avg_wait:.2f}ms)',
                    'suggestion': 'Disk latency issue. Check disk health and consider faster storage'
                })
                print(f"⚠️  HIGH I/O WAIT: Average {avg_wait:.2f}ms in {len(high_wait)} samples")

    def detect_network_anomalies(self):
        """Детектирование сетевых аномалий"""
        df = self.load_data('network_metrics.csv')
        if df is None:
            return

        print("\n=== Network Anomaly Detection ===")

        # Ошибки пакетов
        if 'rx_errors' in df.columns and 'tx_errors' in df.columns:
            error_rate = (df['rx_errors'].diff() + df['tx_errors'].diff())
            high_errors = error_rate[error_rate > 0]

            if not high_errors.empty:
                total_errors = high_errors.sum()

                self.anomalies.append({
                    'category': 'Network',
                    'severity': 'HIGH',
                    'issue': 'Packet Errors',
                    'details': f'Detected {total_errors:.0f} packet errors during monitoring',
                    'suggestion': 'Check network interface, cables, and NIC configuration'
                })

                print(f"PACKET ERRORS: {total_errors:.0f} errors detected")

        # Потерянные пакеты
        if 'rx_dropped' in df.columns and 'tx_dropped' in df.columns:
            dropped_rate = (df['rx_dropped'].diff() + df['tx_dropped'].diff())
            high_dropped = dropped_rate[dropped_rate > 0]

            if not high_dropped.empty:
                total_dropped = high_dropped.sum()
                self.anomalies.append({
                    'category': 'Network',
                    'severity': 'MEDIUM',
                    'issue': 'Dropped Packets',
                    'details': f'Detected {total_dropped:.0f} dropped packets during monitoring',
                    'suggestion': 'Check for buffer overflows, increase ring buffer size, or reduce load'
                })

                print(f"DROPPED PACKETS: {total_dropped:.0f} packets dropped")
    

    def detect_thread_anomalies(self):
        """Детектирование аномалий потоков"""
        df = self.load_data('thread_metrics.csv')
        if df is None:
            return

        print("\n=== Thread Anomaly Detection ===")


        # Рост числа потоков
        if len(df) > 10:
            threads_start = df['num_threads'].iloc[:10].mean()
            threads_end = df['num_threads'].iloc[-10:].mean()
            if threads_end > threads_start * 1.5:
                self.anomalies.append({
                    'category': 'Threads',
                    'severity': 'MEDIUM',
                    'issue': 'Thread Count Growth',
                    'details': f'Thread count grew from {threads_start:.0f} to {threads_end:.0f}',
                    'suggestion': 'Check for thread leaks or unbounded thread pool growth'
                })
                print(f"THREAD GROWTH: From {threads_start:.0f} to {threads_end:.0f} threads")

        # Высокая частота переключений контекста

        if 'involuntary_switches' in df.columns:
            inv_switch_rate = df['involuntary_switches'].diff()
            high_switches = inv_switch_rate[inv_switch_rate > 1000]

            if not high_switches.empty:
                avg_switches = high_switches.mean()

                self.anomalies.append({
                    'category': 'Threads',
                    'severity': 'MEDIUM',
                    'issue': 'High Involuntary Context Switches',
                    'details': f'Involuntary switches exceeded 1000/s for {len(high_switches)} samples (avg: {avg_switches:.0f}/s)',
                    'suggestion': 'CPU contention or too many runnable threads. Consider thread affinity'
                })
                print(f"⚠️  HIGH CONTEXT SWITCHES: Average {avg_switches:.0f}/s in {len(high_switches)} samples")

        # Потоки в состоянии disk sleep
        if 'disk_sleep' in df.columns:
            high_dsleep = df[df['disk_sleep'] > 0]

            if not high_dsleep.empty:
                avg_dsleep = high_dsleep['disk_sleep'].mean()

                self.anomalies.append({
                    'category': 'Threads',
                    'severity': 'MEDIUM',
                    'issue': 'Threads in Uninterruptible Sleep',
                    'details': f'Threads in disk sleep state for {len(high_dsleep)} samples (avg: {avg_dsleep:.2f})',
                    'suggestion': 'Threads blocked on I/O operations. Check disk performance'
                })

                print(f"DISK SLEEP: Average {avg_dsleep:.2f} threads blocked on I/O")


    def detect_tcp_anomalies(self):
        """Детектирование TCP аномалий"""
        df = self.load_data('tcp_metrics.csv')

        if df is None:
            return


        print("\n=== TCP Anomaly Detection ===")

        # Много TIME_WAIT соединений
        high_timewait = df[df['time_wait'] > 1000]

        if not high_timewait.empty:
            avg_timewait = high_timewait['time_wait'].mean()

            self.anomalies.append({
                'category': 'TCP',
                'severity': 'MEDIUM',
                'issue': 'High TIME-WAIT Connections',
                'details': f'TIME-WAIT connections exceeded 1000 for {len(high_timewait)} samples (avg: {avg_timewait:.0f})',
                'suggestion': 'Many short-lived connections. Consider connection pooling or SO_REUSEADDR'
            })
            print(f"HIGH TIME-WAIT: Average {avg_timewait:.0f} connections in {len(high_timewait)} samples")

        # Заполненные Recv-Q
        high_recvq = df[df['recv_q_total'] > 1000]

        if not high_recvq.empty:
            avg_recvq = high_recvq['recv_q_total'].mean()
            self.anomalies.append({
                'category': 'TCP',
                'severity': 'HIGH',
                'issue': 'High Recv-Q Size',
                'details': f'Recv-Q exceeded 1000 bytes for {len(high_recvq)} samples (avg: {avg_recvq:.0f})',
                'suggestion': 'Application not reading from sockets fast enough. Check for blocking operations'
            })
            print(f"HIGH RECV-Q: Average {avg_recvq:.0f} bytes in {len(high_recvq)} samples")


        # Заполненные Send-Q
        high_sendq = df[df['send_q_total'] > 1000]

        if not high_sendq.empty:
            avg_sendq = high_sendq['send_q_total'].mean()
            self.anomalies.append({
                'category': 'TCP',
                'severity': 'HIGH',
                'issue': 'High Send-Q Size',
                'details': f'Send-Q exceeded 1000 bytes for {len(high_sendq)} samples (avg: {avg_sendq:.0f})',
                'suggestion': 'Network congestion or slow receiver. Check network bandwidth and RTT'
            })
            print(f"HIGH SEND-Q: Average {avg_sendq:.0f} bytes in {len(high_sendq)} samples")

    def detect_interrupt_anomalies(self):
        """Детектирование аномалий прерываний"""
        df = self.load_data('interrupt_metrics.csv')

        if df is None:
            return
        
        print("\n=== Interrupt Anomaly Detection ===")

        # Высокая частота NET_RX softirq
        if 'net_rx_softirq' in df.columns:
            rx_rate = df['net_rx_softirq'].diff()
            high_rx = rx_rate[rx_rate > 100000]

            if not high_rx.empty:
                avg_rx = high_rx.mean()

                self.anomalies.append({
                    'category': 'Interrupts',
                    'severity': 'MEDIUM',
                    'issue': 'High NET_RX SoftIRQ Rate',
                    'details': f'NET_RX softirq rate exceeded 100k/s for {len(high_rx)} samples (avg: {avg_rx:.0f}/s)',
                    'suggestion': 'High network receive load. Consider interrupt coalescing or RSS tuning'
                })
                print(f"HIGH NET_RX SOFTIRQ: Average {avg_rx:.0f}/s in {len(high_rx)} samples")

    def generate_summary(self):
        """Генерация итогового отчёта"""
        print("\n" + "="*60)
        print("ANOMALY DETECTION SUMMARY")
        print("="*60)

        if not self.anomalies:
            print("\nNo significant anomalies detected")
            return

        # Группировка по категориям
        by_category = {}
        by_severity = {'CRITICAL': [], 'HIGH': [], 'MEDIUM': [], 'LOW': []}

        for anomaly in self.anomalies:
            cat = anomaly['category']
            sev = anomaly['severity']

            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(anomaly)
            by_severity[sev].append(anomaly)

        print(f"\nTotal Anomalies Found: {len(self.anomalies)}")
        print(f"   - Critical: {len(by_severity['CRITICAL'])}")
        print(f"   - High: {len(by_severity['HIGH'])}")
        print(f"   - Medium: {len(by_severity['MEDIUM'])}")
        print(f"   - Low: {len(by_severity['LOW'])}")

        print("\nBy Category:")
        for cat, items in by_category.items():
            print(f"   - {cat}: {len(items)} issues")

        print("\nDetailed Findings:\n")
        for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            if by_severity[severity]:
                print(f"\n{severity} SEVERITY:")

                for i, anomaly in enumerate(by_severity[severity], 1):
                    print(f"\n{i}. [{anomaly['category']}] {anomaly['issue']}")
                    print(f"   Details: {anomaly['details']}")
                    print(f"   Suggestion: {anomaly['suggestion']}")

        # Сохранение в JSON
        output_file = self.data_dir / 'anomaly_report.json'
        with open(output_file, 'w') as f:
            json.dump(self.anomalies, f, indent=2)
        print(f"\nDetailed report saved to: {output_file}")
    

    def run_detection(self):
        """Запустить все детекторы"""
        print("Starting anomaly detection...")

        self.detect_cpu_anomalies()
        self.detect_memory_anomalies()
        self.detect_disk_anomalies()
        self.detect_network_anomalies()
        self.detect_thread_anomalies()
        self.detect_tcp_anomalies()
        self.detect_interrupt_anomalies()
        self.generate_summary()

def main():
    data_dir = sys.argv[1] if len(sys.argv) > 1 else "monitoring_data"

    detector = AnomalyDetector(data_dir)
    detector.run_detection()

if __name__ == "__main__":
    main()
