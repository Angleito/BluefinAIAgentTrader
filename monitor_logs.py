#!/usr/bin/env python3
"""
Script to monitor agent logs in real-time and display them.
"""
import os
import sys
import time
import datetime
import subprocess

def tail_file(file_path, lines=10):
    """Tail a file and return the last n lines"""
    try:
        process = subprocess.Popen(['tail', '-n', str(lines), file_path], stdout=subprocess.PIPE)
        output = process.communicate()[0].decode('utf-8')
        return output
    except Exception as e:
        return f"Error tailing file: {e}"

def monitor_logs(log_file="logs/agent.log", interval=2):
    """Monitor logs in real-time"""
    print(f"Monitoring {log_file} (Press Ctrl+C to stop)")
    
    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)
    
    # Create log file if it doesn't exist
    if not os.path.exists(log_file):
        with open(log_file, "w") as f:
            f.write(f"# Log file created at {datetime.datetime.now().isoformat()}\n")
    
    # Track file position
    file_position = os.path.getsize(log_file)
    
    try:
        while True:
            if os.path.exists(log_file):
                current_size = os.path.getsize(log_file)
                
                if current_size > file_position:
                    # File has grown, read new lines
                    with open(log_file, "r") as f:
                        f.seek(file_position)
                        new_lines = f.read()
                        sys.stdout.write(new_lines)
                        sys.stdout.flush()
                    
                    file_position = current_size
            
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nStopping log monitor")
    except Exception as e:
        print(f"Error monitoring logs: {e}")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Monitor agent logs in real-time")
    parser.add_argument("--file", "-f", default="logs/agent.log", help="Log file to monitor")
    parser.add_argument("--interval", "-i", type=float, default=1.0, help="Check interval in seconds")
    args = parser.parse_args()
    
    # Show the initial tail of the log file if it exists
    if os.path.exists(args.file) and os.path.getsize(args.file) > 0:
        print(f"Last 10 lines of {args.file}:")
        print(tail_file(args.file, 10))
        print("-" * 80)
    
    # Start monitoring
    monitor_logs(args.file, args.interval)

if __name__ == "__main__":
    main() 