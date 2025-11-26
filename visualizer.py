#!/usr/bin/env python3

"""
Визуализация собранных метрик производительности
Создаёт графики для анализа CPU, памяти, диска, сети и прерываний
"""
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import sys

sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 8)

class MetricsVisualizer:
    def __init__(self, data_dir="monitoring_data"):
        self.data_dir = Path(data_dir)
        self.output_dir = self.data_dir / "plots"
        self.output_dir.mkdir(exist_ok=True)

    def load_data(self, filename):
        """Загрузить CSV файл"""
        filepath = self.data_dir / filename
        if not filepath.exists():
            print(f"Warning: {filepath} not found")
            return None
        return pd.read_csv(filepath)

    def plot_cpu_metrics(self):
        """График CPU метрик"""
        df = self.load_data('cpu_metrics.csv')
        if df is None:
            return

        fig, axes = plt.subplots(3, 2, figsize=(16, 12))

        # CPU usage breakdown
        axes[0, 0].plot(df['timestamp'], df['user'], label='User', alpha=0.7)
        axes[0, 0].plot(df['timestamp'], df['system'], label='System', alpha=0.7)
        axes[0, 0].plot(df['timestamp'], df['iowait'], label='IOWait', alpha=0.7)
        axes[0, 0].set_title('System CPU Usage (%)')
        axes[0, 0].set_xlabel('Time (s)')
        axes[0, 0].set_ylabel('CPU %')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)

        # Process CPU
        axes[0, 1].plot(df['timestamp'], df['proc_total'], label='Total CPU', color='red', linewidth=2)
        axes[0, 1].set_title('Process CPU Usage (%)')
        axes[0, 1].set_xlabel('Time (s)')
        axes[0, 1].set_ylabel('CPU %')
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)

        # Process User vs System time
        axes[1, 0].plot(df['timestamp'], df['proc_user'], label='User Time', alpha=0.7)
        axes[1, 0].plot(df['timestamp'], df['proc_system'], label='System Time', alpha=0.7)
        axes[1, 0].set_title('Process User vs System Time (cumulative)')
        axes[1, 0].set_xlabel('Time (s)')
        axes[1, 0].set_ylabel('Time (s)')
        axes[1, 0].legend()
        axes[1, 0].grid(True, alpha=0.3)

        # Load average
        axes[1, 1].plot(df['timestamp'], df['load_1m'], label='1 min', alpha=0.7)
        axes[1, 1].plot(df['timestamp'], df['load_5m'], label='5 min', alpha=0.7)
        axes[1, 1].plot(df['timestamp'], df['load_15m'], label='15 min', alpha=0.7)
        axes[1, 1].set_title('Load Average')
        axes[1, 1].set_xlabel('Time (s)')
        axes[1, 1].set_ylabel('Load')
        axes[1, 1].legend()
        axes[1, 1].grid(True, alpha=0.3)

        # Runqueue length
        axes[2, 0].plot(df['timestamp'], df['runqueue'], color='purple', linewidth=2)
        axes[2, 0].set_title('Runqueue Length')
        axes[2, 0].set_xlabel('Time (s)')
        axes[2, 0].set_ylabel('Processes')
        axes[2, 0].grid(True, alpha=0.3)

        # IOWait detail
        axes[2, 1].fill_between(df['timestamp'], df['iowait'], alpha=0.5, color='orange')
        axes[2, 1].set_title('IOWait Detail')
        axes[2, 1].set_xlabel('Time (s)')
        axes[2, 1].set_ylabel('IOWait %')
        axes[2, 1].grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(self.output_dir / 'cpu_analysis.png', dpi=150, bbox_inches='tight')
        print(f"Saved: {self.output_dir / 'cpu_analysis.png'}")
        plt.close()
    

    def plot_memory_metrics(self):
        """График метрик памяти"""
        df = self.load_data('memory_metrics.csv')
        if df is None:
            return

        fig, axes = plt.subplots(3, 2, figsize=(16, 12))

        # Process memory (RSS and VSZ)
        axes[0, 0].plot(df['timestamp'], df['rss_mb'], label='RSS', linewidth=2)
        axes[0, 0].plot(df['timestamp'], df['vsz_mb'], label='VSZ', alpha=0.7, linestyle='--')
        axes[0, 0].set_title('Process Memory Usage')
        axes[0, 0].set_xlabel('Time (s)')
        axes[0, 0].set_ylabel('Memory (MB)')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)

        # System memory
        axes[0, 1].plot(df['timestamp'], df['used_mem_mb'], label='Used', alpha=0.7)
        axes[0, 1].plot(df['timestamp'], df['free_mem_mb'], label='Free', alpha=0.7)
        axes[0, 1].plot(df['timestamp'], df['cached_mb'], label='Cached', alpha=0.7)
        axes[0, 1].set_title('System Memory')
        axes[0, 1].set_xlabel('Time (s)')
        axes[0, 1].set_ylabel('Memory (MB)')
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)

        # Process memory percent
        axes[1, 0].fill_between(df['timestamp'], df['mem_percent'], alpha=0.5, color='green')
        axes[1, 0].set_title('Process Memory Usage (%)')
        axes[1, 0].set_xlabel('Time (s)')
        axes[1, 0].set_ylabel('Memory %')
        axes[1, 0].grid(True, alpha=0.3)

        # Page faults
        axes[1, 1].plot(df['timestamp'], df['page_faults_minor'].diff(), 
                        label='Minor Faults/s', alpha=0.7)
        axes[1, 1].plot(df['timestamp'], df['page_faults_major'].diff(), 
                        label='Major Faults/s', alpha=0.7)
        axes[1, 1].set_title('Page Faults Rate')
        axes[1, 1].set_xlabel('Time (s)')
        axes[1, 1].set_ylabel('Faults/s')
        axes[1, 1].legend()
        axes[1, 1].grid(True, alpha=0.3)
    

        # Memory growth rate
        axes[2, 0].plot(df['timestamp'], df['rss_mb'].diff(), color='red', alpha=0.7)
        axes[2, 0].axhline(y=0, color='black', linestyle='--', alpha=0.3)
        axes[2, 0].set_title('RSS Growth Rate')
        axes[2, 0].set_xlabel('Time (s)')
        axes[2, 0].set_ylabel('MB/s')
        axes[2, 0].grid(True, alpha=0.3)


        # Cumulative page faults
        axes[2, 1].plot(df['timestamp'], df['page_faults_minor'], 
                        label='Minor (cumulative)', alpha=0.7)
        axes[2, 1].plot(df['timestamp'], df['page_faults_major'], 
                        label='Major (cumulative)', alpha=0.7)
        axes[2, 1].set_title('Cumulative Page Faults')
        axes[2, 1].set_xlabel('Time (s)')
        axes[2, 1].set_ylabel('Count')
        axes[2, 1].legend()
        axes[2, 1].grid(True, alpha=0.3)

        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'memory_analysis.png', dpi=150, bbox_inches='tight')
        print(f"Saved: {self.output_dir / 'memory_analysis.png'}")
        plt.close()

    def plot_disk_metrics(self):
        """График дисковых метрик"""
        df = self.load_data('disk_metrics.csv')

        if df is None:
            return

        fig, axes = plt.subplots(2, 2, figsize=(16, 10))

        # Process I/O bytes
        axes[0, 0].plot(df['timestamp'], df['proc_read_bytes'].diff(), 
                        label='Read', alpha=0.7)
        axes[0, 0].plot(df['timestamp'], df['proc_write_bytes'].diff(), 
                        label='Write', alpha=0.7)
        axes[0, 0].set_title('Process I/O Rate (KB/s)')
        axes[0, 0].set_xlabel('Time (s)')
        axes[0, 0].set_ylabel('KB/s')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)

        # System I/O operations
        df_numeric = df.apply(pd.to_numeric, errors='coerce')
        axes[0, 1].plot(df['timestamp'], df_numeric['reads'], label='Reads', alpha=0.7)
        axes[0, 1].plot(df['timestamp'], df_numeric['writes'], label='Writes', alpha=0.7)
        axes[0, 1].set_title('System I/O Operations')
        axes[0, 1].set_xlabel('Time (s)')
        axes[0, 1].set_ylabel('Operations')
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)

        # Cumulative I/O
        axes[1, 0].plot(df['timestamp'], df['proc_read_bytes'], 
                        label='Read (cumulative)', alpha=0.7)
        axes[1, 0].plot(df['timestamp'], df['proc_write_bytes'], 
                        label='Write (cumulative)', alpha=0.7)
        axes[1, 0].set_title('Cumulative Process I/O')
        axes[1, 0].set_xlabel('Time (s)')
        axes[1, 0].set_ylabel('KB')
        axes[1, 0].legend()
        axes[1, 0].grid(True, alpha=0.3)

        # I/O wait time
        axes[1, 1].plot(df['timestamp'], df_numeric['io_wait_time'], 
                        color='red', linewidth=2)
        axes[1, 1].set_title('I/O Wait Time')
        axes[1, 1].set_xlabel('Time (s)')
        axes[1, 1].set_ylabel('Time (ms)')
        axes[1, 1].grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(self.output_dir / 'disk_analysis.png', dpi=150, bbox_inches='tight')
        print(f"Saved: {self.output_dir / 'disk_analysis.png'}")
        plt.close()

    def plot_network_metrics(self):
        """График сетевых метрик"""
        df = self.load_data('network_metrics.csv')
        if df is None:
            return

        fig, axes = plt.subplots(2, 2, figsize=(16, 10))

        # Packet rate
        axes[0, 0].plot(df['timestamp'], df['rx_packets'].diff(), 
                        label='RX', alpha=0.7)
        axes[0, 0].plot(df['timestamp'], df['tx_packets'].diff(), 
                        label='TX', alpha=0.7)
        axes[0, 0].set_title('Network Packet Rate (packets/s)')
        axes[0, 0].set_xlabel('Time (s)')
        axes[0, 0].set_ylabel('Packets/s')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)

        
        # Bandwidth
        axes[0, 1].plot(df['timestamp'], df['rx_bytes'].diff() / 1024, 
                        label='RX', alpha=0.7)
        axes[0, 1].plot(df['timestamp'], df['tx_bytes'].diff() / 1024, 
                        label='TX', alpha=0.7)
        axes[0, 1].set_title('Network Bandwidth (KB/s)')
        axes[0, 1].set_xlabel('Time (s)')
        axes[0, 1].set_ylabel('KB/s')
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)

        # Errors
        axes[1, 0].plot(df['timestamp'], df['rx_errors'].diff(), 
                        label='RX Errors', alpha=0.7)
        axes[1, 0].plot(df['timestamp'], df['tx_errors'].diff(), 
                        label='TX Errors', alpha=0.7)
        axes[1, 0].set_title('Network Errors (errors/s)')
        axes[1, 0].set_xlabel('Time (s)')
        axes[1, 0].set_ylabel('Errors/s')
        axes[1, 0].legend()
        axes[1, 0].grid(True, alpha=0.3)

        # Dropped packets
        axes[1, 1].plot(df['timestamp'], df['rx_dropped'].diff(), 
                        label='RX Dropped', alpha=0.7)
        axes[1, 1].plot(df['timestamp'], df['tx_dropped'].diff(), 
                        label='TX Dropped', alpha=0.7)
        axes[1, 1].set_title('Dropped Packets (packets/s)')
        axes[1, 1].set_xlabel('Time (s)')
        axes[1, 1].set_ylabel('Packets/s')
        axes[1, 1].legend()
        axes[1, 1].grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(self.output_dir / 'network_analysis.png', dpi=150, bbox_inches='tight')
        print(f"Saved: {self.output_dir / 'network_analysis.png'}")
        plt.close()

    def plot_thread_metrics(self):
        """График метрик потоков"""
        df = self.load_data('thread_metrics.csv')
        
        if df is None:
            return

        fig, axes = plt.subplots(2, 2, figsize=(16, 10))

        # Thread count
        axes[0, 0].plot(df['timestamp'], df['num_threads'], 
                        color='blue', linewidth=2)
        axes[0, 0].set_title('Number of Threads')
        axes[0, 0].set_xlabel('Time (s)')
        axes[0, 0].set_ylabel('Threads')
        axes[0, 0].grid(True, alpha=0.3)

        # Context switches
        axes[0, 1].plot(df['timestamp'], df['voluntary_switches'].diff(), 
                        label='Voluntary', alpha=0.7)
        axes[0, 1].plot(df['timestamp'], df['involuntary_switches'].diff(), 
                        label='Involuntary', alpha=0.7)
        axes[0, 1].set_title('Context Switches Rate (switches/s)')
        axes[0, 1].set_xlabel('Time (s)')
        axes[0, 1].set_ylabel('Switches/s')
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)

        # Thread states
        axes[1, 0].plot(df['timestamp'], df['running'], label='Running', alpha=0.7)
        axes[1, 0].plot(df['timestamp'], df['sleeping'], label='Sleeping', alpha=0.7)
        axes[1, 0].plot(df['timestamp'], df['disk_sleep'], label='Disk Sleep', alpha=0.7)
        axes[1, 0].set_title('Thread States')
        axes[1, 0].set_xlabel('Time (s)')
        axes[1, 0].set_ylabel('Count')
        axes[1, 0].legend()
        axes[1, 0].grid(True, alpha=0.3)

        # Cumulative context switches
        axes[1, 1].plot(df['timestamp'], df['voluntary_switches'], 
                        label='Voluntary', alpha=0.7)
        axes[1, 1].plot(df['timestamp'], df['involuntary_switches'], 
                        label='Involuntary', alpha=0.7)
        axes[1, 1].set_title('Cumulative Context Switches')
        axes[1, 1].set_xlabel('Time (s)')
        axes[1, 1].set_ylabel('Count')
        axes[1, 1].legend()
        axes[1, 1].grid(True, alpha=0.3)

        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'thread_analysis.png', dpi=150, bbox_inches='tight')
        print(f"Saved: {self.output_dir / 'thread_analysis.png'}")
        plt.close()

    def plot_tcp_metrics(self):
        """График TCP метрик"""
        df = self.load_data('tcp_metrics.csv')
        if df is None:
            return

        fig, axes = plt.subplots(2, 2, figsize=(16, 10))

        # Connection states
        axes[0, 0].plot(df['timestamp'], df['established'], label='Established', alpha=0.7)
        axes[0, 0].plot(df['timestamp'], df['time_wait'], label='Time-Wait', alpha=0.7)
        axes[0, 0].plot(df['timestamp'], df['close_wait'], label='Close-Wait', alpha=0.7)
        axes[0, 0].set_title('TCP Connection States')
        axes[0, 0].set_xlabel('Time (s)')
        axes[0, 0].set_ylabel('Connections')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)

        # SYN states
        axes[0, 1].plot(df['timestamp'], df['syn_sent'], label='SYN-Sent', alpha=0.7)
        axes[0, 1].plot(df['timestamp'], df['syn_recv'], label='SYN-Recv', alpha=0.7)
        axes[0, 1].set_title('TCP SYN States')
        axes[0, 1].set_xlabel('Time (s)')
        axes[0, 1].set_ylabel('Connections')
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)

        # Recv-Q
        axes[1, 0].plot(df['timestamp'], df['recv_q_total'], 

                        color='blue', linewidth=2)
        axes[1, 0].set_title('Total Recv-Q Size')
        axes[1, 0].set_xlabel('Time (s)')
        axes[1, 0].set_ylabel('Bytes')
        axes[1, 0].grid(True, alpha=0.3)

        # Send-Q
        axes[1, 1].plot(df['timestamp'], df['send_q_total'], 

                        color='red', linewidth=2)
        axes[1, 1].set_title('Total Send-Q Size')
        axes[1, 1].set_xlabel('Time (s)')
        axes[1, 1].set_ylabel('Bytes')
        axes[1, 1].grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(self.output_dir / 'tcp_analysis.png', dpi=150, bbox_inches='tight')
        print(f"Saved: {self.output_dir / 'tcp_analysis.png'}")
        plt.close()


    def plot_interrupt_metrics(self):
        """График метрик прерываний"""
        df = self.load_data('interrupt_metrics.csv')
        if df is None:
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(16, 10))


        # SoftIRQ rates
        axes[0, 0].plot(df['timestamp'], df['net_rx_softirq'].diff(), 

                        label='NET_RX', alpha=0.7)
        axes[0, 0].plot(df['timestamp'], df['net_tx_softirq'].diff(), 

                        label='NET_TX', alpha=0.7)
        axes[0, 0].set_title('Network SoftIRQ Rate')
        axes[0, 0].set_xlabel('Time (s)')
        axes[0, 0].set_ylabel('Interrupts/s')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)
        

        # Timer softirq
        axes[0, 1].plot(df['timestamp'], df['timer_softirq'].diff(), 

                        color='orange', linewidth=2)
        axes[0, 1].set_title('Timer SoftIRQ Rate')
        axes[0, 1].set_xlabel('Time (s)')
        axes[0, 1].set_ylabel('Interrupts/s')
        axes[0, 1].grid(True, alpha=0.3)
        

        # Cumulative NET_RX
        axes[1, 0].plot(df['timestamp'], df['net_rx_softirq'], 

                        color='blue', alpha=0.7)
        axes[1, 0].set_title('Cumulative NET_RX SoftIRQ')
        axes[1, 0].set_xlabel('Time (s)')
        axes[1, 0].set_ylabel('Count')
        axes[1, 0].grid(True, alpha=0.3)


        # Cumulative NET_TX
        axes[1, 1].plot(df['timestamp'], df['net_tx_softirq'], 
                        color='red', alpha=0.7)
        axes[1, 1].set_title('Cumulative NET_TX SoftIRQ')
        axes[1, 1].set_xlabel('Time (s)')
        axes[1, 1].set_ylabel('Count')
        axes[1, 1].grid(True, alpha=0.3)

        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'interrupt_analysis.png', dpi=150, bbox_inches='tight')
        print(f"Saved: {self.output_dir / 'interrupt_analysis.png'}")
        plt.close()


    def create_all_plots(self):
        """Создать все графики"""
        print("Creating visualization plots...")
        self.plot_cpu_metrics()
        self.plot_memory_metrics()
        self.plot_disk_metrics()
        self.plot_network_metrics()
        self.plot_thread_metrics()
        self.plot_tcp_metrics()
        self.plot_interrupt_metrics()
        print(f"\nAll plots saved to: {self.output_dir}")

def main():
    data_dir = sys.argv[1] if len(sys.argv) > 1 else "monitoring_data"

    visualizer = MetricsVisualizer(data_dir)
    visualizer.create_all_plots()

if __name__ == "__main__":
    main()
