import subprocess
import time
import csv
import os
from pathlib import Path

class PerformanceMonitor:
    def __init__(self, pid, output_dir="monitoring_data"):
        self.pid = pid
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.monitoring = True
        self.start_time = time.time()

        
        # Файлы для записи данных
        self.files = {
            'cpu': open(self.output_dir / 'cpu_metrics.csv', 'w', newline=''),
            'memory': open(self.output_dir / 'memory_metrics.csv', 'w', newline=''),
            'disk': open(self.output_dir / 'disk_metrics.csv', 'w', newline=''),
            'network': open(self.output_dir / 'network_metrics.csv', 'w', newline=''),
            'threads': open(self.output_dir / 'thread_metrics.csv', 'w', newline=''),
            'tcp': open(self.output_dir / 'tcp_metrics.csv', 'w', newline=''),
            'interrupts': open(self.output_dir / 'interrupt_metrics.csv', 'w', newline=''),
        }

        self.writers = {k: csv.writer(v) for k, v in self.files.items()}
        self._write_headers()

        
    def _write_headers(self):
        """Записать заголовки CSV файлов"""
        self.writers['cpu'].writerow(['timestamp', 'user', 'system', 'iowait', 'idle', 
                                      'proc_user', 'proc_system', 'proc_total', 
                                      'load_1m', 'load_5m', 'load_15m', 'runqueue'])
        

        self.writers['memory'].writerow(['timestamp', 'rss_mb', 'vsz_mb', 'mem_percent',
                                        'total_mem_mb', 'used_mem_mb', 'free_mem_mb',
                                        'cached_mb', 'page_faults_minor', 'page_faults_major'])
        

        self.writers['disk'].writerow(['timestamp', 'reads', 'writes', 'read_kb', 'write_kb',
                                      'io_wait_time', 'proc_read_bytes', 'proc_write_bytes'])
        

        self.writers['network'].writerow(['timestamp', 'rx_packets', 'tx_packets', 'rx_bytes', 
                                         'tx_bytes', 'rx_errors', 'tx_errors', 'rx_dropped', 'tx_dropped'])
        

        self.writers['threads'].writerow(['timestamp', 'num_threads', 'voluntary_switches', 
                                         'involuntary_switches', 'running', 'sleeping', 'disk_sleep'])
        

        self.writers['tcp'].writerow(['timestamp', 'established', 'syn_sent', 'syn_recv', 
                                     'time_wait', 'close_wait', 'recv_q_total', 'send_q_total'])

        
        self.writers['interrupts'].writerow(['timestamp', 'total_irqs', 'net_rx_softirq', 
                                            'net_tx_softirq', 'timer_softirq'])

    def run_cmd(self, cmd):
        """Выполнить команду и вернуть вывод"""
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
            return result.stdout
        except Exception as e:
            print(f"Error running {cmd}: {e}")
            return ""

    def collect_cpu_metrics(self):
        """Сбор метрик CPU"""
        timestamp = time.time() - self.start_time
        

        # Общая статистика CPU
        mpstat = self.run_cmd("mpstat 1 1 | tail -1")
        cpu_parts = mpstat.split()
        
        if len(cpu_parts) >= 10:
            user, system, iowait, idle = cpu_parts[3], cpu_parts[5], cpu_parts[6], cpu_parts[-1]
        else:
            user = system = iowait = idle = 0

        # Статистика процесса
        proc_stat = self.run_cmd(f"ps -p {self.pid} -o %cpu,%mem,time 2>/dev/null | tail -1")
        proc_parts = proc_stat.split()
        proc_cpu = float(proc_parts[0]) if proc_parts else 0

    
        # User и System time процесса из /proc/[pid]/stat
        try:
            with open(f"/proc/{self.pid}/stat") as f:
                stat = f.read().split()
                utime = int(stat[13])  # user time
                stime = int(stat[14])  # system time
                clock_ticks = os.sysconf(os.sysconf_names['SC_CLK_TCK'])
                proc_user = utime / clock_ticks
                proc_system = stime / clock_ticks
        except:
            proc_user = proc_system = 0

        
        # Load average и runqueue
        with open('/proc/loadavg') as f:
            load = f.read().split()
            load_1m, load_5m, load_15m = load[0], load[1], load[2]
            runqueue = load[3].split('/')[0]

        self.writers['cpu'].writerow([
            timestamp, user, system, iowait, idle,
            proc_user, proc_system, proc_cpu,
            load_1m, load_5m, load_15m, runqueue
        ])
        
    def collect_memory_metrics(self):
        """Сбор метрик памяти"""
        timestamp = time.time() - self.start_time

        # Память процесса
        proc_mem = self.run_cmd(f"ps -p {self.pid} -o rss,vsz,%mem 2>/dev/null | tail -1")
        parts = proc_mem.split()
        rss_mb = int(parts[0]) / 1024 if parts else 0
        vsz_mb = int(parts[1]) / 1024 if parts else 0
        mem_percent = float(parts[2]) if len(parts) > 2 else 0

        # Общая память системы
        meminfo = {}
        with open('/proc/meminfo') as f:
            for line in f:
                key, val = line.split(':')
                meminfo[key] = int(val.split()[0])
        
        total_mem = meminfo.get('MemTotal', 0) / 1024
        free_mem = meminfo.get('MemFree', 0) / 1024
        cached = meminfo.get('Cached', 0) / 1024
        used_mem = total_mem - free_mem - cached

        # Page faults
        try:
            with open(f"/proc/{self.pid}/stat") as f:
                stat = f.read().split()
                minor_faults = int(stat[9])
                major_faults = int(stat[11])
        except:
            minor_faults = major_faults = 0

        self.writers['memory'].writerow([
            timestamp, rss_mb, vsz_mb, mem_percent,
            total_mem, used_mem, free_mem, cached,
            minor_faults, major_faults
        ])

    def collect_disk_metrics(self):
        """Сбор метрик диска"""
        timestamp = time.time() - self.start_time

        # Общая статистика I/O
        iostat = self.run_cmd("iostat -x 1 2 | tail -n +4 | tail -1")

        parts = iostat.split()
        if len(parts) >= 10:
            reads = parts[3]
            writes = parts[4]
            read_kb = parts[5]
            write_kb = parts[6]
            await_time = parts[9] if len(parts) > 9 else 0
        else:
            reads = writes = read_kb = write_kb = await_time = 0


        # I/O процесса
        try:
            with open(f"/proc/{self.pid}/io") as f:
                io_data = {}
                for line in f:
                    key, val = line.split(':')
                    io_data[key.strip()] = int(val.strip())
                proc_read = io_data.get('read_bytes', 0) / 1024
                proc_write = io_data.get('write_bytes', 0) / 1024
        except:
            proc_read = proc_write = 0

        
        self.writers['disk'].writerow([
            timestamp, reads, writes, read_kb, write_kb,
            await_time, proc_read, proc_write
        ])

    def collect_network_metrics(self):
        """Сбор сетевых метрик"""
        timestamp = time.time() - self.start_time

        # Статистика сетевых интерфейсов
        netstat = self.run_cmd("cat /proc/net/dev | grep -E 'eth0|ens|enp' | head -1")

        if netstat:
            parts = netstat.split()
            rx_bytes = int(parts[1])
            rx_packets = int(parts[2])
            rx_errors = int(parts[3])
            rx_dropped = int(parts[4])
            tx_bytes = int(parts[9])
            tx_packets = int(parts[10])
            tx_errors = int(parts[11])
            tx_dropped = int(parts[12])
        else:
            rx_bytes = rx_packets = rx_errors = rx_dropped = 0
            tx_bytes = tx_packets = tx_errors = tx_dropped = 0

        self.writers['network'].writerow([
            timestamp, rx_packets, tx_packets, rx_bytes, tx_bytes,
            rx_errors, tx_errors, rx_dropped, tx_dropped
        ])
        
    def collect_thread_metrics(self):
        """Сбор метрик потоков"""
        timestamp = time.time() - self.start_time

        # Количество потоков
        threads = self.run_cmd(f"ps -p {self.pid} -o nlwp 2>/dev/null | tail -1")
        num_threads = int(threads.strip()) if threads.strip() else 0

        # Переключения контекста
        try:
            with open(f"/proc/{self.pid}/status") as f:
                vol_switches = inv_switches = 0
                for line in f:
                    if 'voluntary_ctxt_switches' in line:
                        vol_switches = int(line.split()[1])
                    elif 'nonvoluntary_ctxt_switches' in line:
                        inv_switches = int(line.split()[1])
        except:
            vol_switches = inv_switches = 0

        # Состояния потоков
        thread_states = self.run_cmd(f"ps -L -p {self.pid} -o state 2>/dev/null | tail -n +2")
        running = thread_states.count('R')
        sleeping = thread_states.count('S')
        disk_sleep = thread_states.count('D')

        self.writers['threads'].writerow([
            timestamp, num_threads, vol_switches, inv_switches,
            running, sleeping, disk_sleep
        ])

    def collect_tcp_metrics(self):
        """Сбор TCP метрик"""
        timestamp = time.time() - self.start_time

        # Состояния TCP соединений
        ss_output = self.run_cmd(f"ss -tan | grep -E 'ESTAB|SYN-SENT|SYN-RECV|TIME-WAIT|CLOSE-WAIT'")

        established = ss_output.count('ESTAB')
        syn_sent = ss_output.count('SYN-SENT')
        syn_recv = ss_output.count('SYN-RECV')
        time_wait = ss_output.count('TIME-WAIT')
        close_wait = ss_output.count('CLOSE-WAIT')

        # Recv-Q и Send-Q
        recv_q_total = send_q_total = 0
        for line in ss_output.split('\n'):
            parts = line.split()
            if len(parts) >= 2:
                try:
                    recv_q_total += int(parts[1])
                    send_q_total += int(parts[2])
                except:
                    pass

        self.writers['tcp'].writerow([
            timestamp, established, syn_sent, syn_recv,
            time_wait, close_wait, recv_q_total, send_q_total
        ])

    def collect_interrupt_metrics(self):
        """Сбор метрик прерываний"""
        timestamp = time.time() - self.start_time

        # IRQ
        irq_count = self.run_cmd("cat /proc/interrupts | wc -l")
        total_irqs = int(irq_count) if irq_count else 0

        # SoftIRQ
        softirq = self.run_cmd("cat /proc/softirqs")
        net_rx = net_tx = timer = 0

        for line in softirq.split('\n'):
            if 'NET_RX' in line:
                nums = [int(x) for x in line.split()[1:] if x.isdigit()]
                net_rx = sum(nums)
            elif 'NET_TX' in line:
                nums = [int(x) for x in line.split()[1:] if x.isdigit()]
                net_tx = sum(nums)
            elif 'TIMER' in line:
                nums = [int(x) for x in line.split()[1:] if x.isdigit()]
                timer = sum(nums)

        self.writers['interrupts'].writerow([
            timestamp, total_irqs, net_rx, net_tx, timer
        ])

    def monitor(self, interval=1):
        """Основной цикл мониторинга"""
        print(f"Starting monitoring for PID {self.pid}")
        print(f"Data will be saved to {self.output_dir}")
        print("Press Ctrl+C to stop")

        try:
            while self.monitoring:
                self.collect_cpu_metrics()
                self.collect_memory_metrics()
                self.collect_disk_metrics()
                self.collect_network_metrics()
                self.collect_thread_metrics()
                self.collect_tcp_metrics()
                self.collect_interrupt_metrics()

                # Flush данных
                for f in self.files.values():
                    f.flush()

                time.sleep(interval)

        except KeyboardInterrupt:
            print("\nStopping monitoring...")
        finally:
            self.cleanup()

    def cleanup(self):
        """Закрыть все файлы"""
        for f in self.files.values():
            f.close()

        print(f"Monitoring data saved to {self.output_dir}")