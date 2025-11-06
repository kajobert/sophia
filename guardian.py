#!/usr/bin/env python3
"""SOPHIA Guardian Watchdog - Phoenix Protocol"""
import argparse, logging, subprocess, sys, time, signal, shutil
from datetime import datetime, timedelta
from pathlib import Path
from collections import deque

Path('logs').mkdir(exist_ok=True)
logging.basicConfig(level=logging.INFO, format='%(asctime)s [GUARDIAN] %(levelname)s: %(message)s',
                    handlers=[logging.FileHandler('logs/guardian.log'), logging.StreamHandler(sys.stdout)])
logger = logging.getLogger('guardian')

class CrashHistory:
    def __init__(self, max_crashes=5, time_window_seconds=600):
        self.max_crashes, self.time_window, self.crashes = max_crashes, timedelta(seconds=time_window_seconds), deque(maxlen=max_crashes)
    def record_crash(self): self.crashes.append(datetime.now())
    def is_crash_loop(self): return len(self.crashes) >= self.max_crashes and (self.crashes[-1] - self.crashes[0]) < self.time_window
    def get_crash_rate(self): return "No pattern" if len(self.crashes) < 2 else f"{len(self.crashes)} crashes in {(self.crashes[-1] - self.crashes[0]).total_seconds():.0f}s"

class Guardian:
    def __init__(self, worker_script, max_crashes=5, crash_window=600):
        self.worker_script, self.crash_history, self.process, self.should_stop, self.restart_count = Path(worker_script), CrashHistory(max_crashes, crash_window), None, False, 0
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        logger.info(f"Signal {signum}, shutting down...")
        self.should_stop = True
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try: self.process.wait(timeout=10)
            except subprocess.TimeoutExpired: self.process.kill()
        sys.exit(0)
    
    def _save_crash_log(self, exit_code, stdout, stderr):
        ts, path = datetime.now().strftime("%Y%m%d_%H%M%S"), Path(f"logs/crash_{datetime.now().strftime('%Y%m%d_%H%M%S')}_exit{exit_code}.log")
        with open(path, 'w') as f:
            f.write(f"SOPHIA CRASH REPORT\n{'='*80}\nTimestamp: {datetime.now().isoformat()}\nExit Code: {exit_code}\nWorker: {self.worker_script}\nRestart #: {self.restart_count}\n{'='*80}\n\nSTDOUT:\n{stdout or '(empty)'}\n\nSTDERR:\n{stderr or '(empty)'}\n")
        logger.info(f"Crash log: {path}")
        shutil.copy2(path, "logs/last_crash.log")
        return path
    
    def _start_worker(self, recovery_log=None):
        cmd = [sys.executable, str(self.worker_script)]
        if recovery_log: cmd.extend(['--recovery-from-crash', str(recovery_log)])
        logger.info(f"{'🔄 Recovery' if recovery_log else '🚀 Starting'} worker: {self.worker_script.name}")
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        logger.info(f"PID: {p.pid}")
        return p
    
    def _stream_output(self, p):
        stdout_lines, stderr_lines = [], []
        with open("logs/worker_combined.log", 'a') as log:
            log.write(f"\n{'='*80}\nSession: {datetime.now().isoformat()} PID:{p.pid}\n{'='*80}\n")
            while p.poll() is None:
                if p.stdout and (line := p.stdout.readline()):
                    stdout_lines.append(line)
                    log.write(f"[OUT] {line}")
                    log.flush()
                time.sleep(0.01)
            if p.stdout: stdout_lines.extend(p.stdout.readlines())
            if p.stderr: stderr_lines.extend(p.stderr.readlines())
            log.write(f"\n{'='*80}\nEnded: {datetime.now().isoformat()} Exit:{p.returncode}\n{'='*80}\n")
        return ''.join(stdout_lines), ''.join(stderr_lines)
    
    def _handle_crash_loop(self):
        logger.critical(f"🔥 CRASH LOOP! {self.crash_history.get_crash_rate()}")
        try:
            if subprocess.run(['git', 'rev-parse', '--is-inside-work-tree'], capture_output=True, timeout=5).returncode != 0:
                logger.error("Not a git repo"); return False
            branch = subprocess.run(['git', 'branch', '--show-current'], capture_output=True, text=True, timeout=5).stdout.strip()
            logger.warning(f"Rollback on {branch}: git reset --hard HEAD~1")
            if subprocess.run(['git', 'reset', '--hard', 'HEAD~1'], capture_output=True, timeout=10).returncode == 0:
                logger.info("✅ Rollback OK")
                self.crash_history.crashes.clear()
                self.restart_count = 0
                return True
            logger.error("Rollback failed")
            return False
        except Exception as e:
            logger.error(f"Rollback error: {e}")
            return False
    
    def run(self):
        logger.info("="*80 + "\nSOPHIA GUARDIAN STARTED\n" + "="*80)
        logger.info(f"Monitoring: {self.worker_script}\nCrash limit: {self.crash_history.max_crashes} in {self.crash_history.time_window.total_seconds():.0f}s\nPress Ctrl+C to stop\n" + "="*80)
        recovery_log = None
        while not self.should_stop:
            try:
                self.process = self._start_worker(recovery_log)
                recovery_log = None
                stdout, stderr = self._stream_output(self.process)
                exit_code = self.process.returncode
                if exit_code == 0:
                    logger.info("✅ Normal exit")
                    self.crash_history.crashes.clear()
                    self.restart_count = 0
                    if not self.should_stop: time.sleep(2)
                else:
                    logger.error(f"❌ Crash exit:{exit_code}")
                    self.restart_count += 1
                    crash_log = self._save_crash_log(exit_code, stdout, stderr)
                    self.crash_history.record_crash()
                    if self.crash_history.is_crash_loop():
                        if self._handle_crash_loop(): recovery_log = Path("logs/last_crash.log")
                        else: logger.critical("Rollback failed, stopping"); break
                    else:
                        recovery_log = crash_log
                        logger.info(f"Crash #{self.restart_count}: Restart in 5s... ({self.crash_history.get_crash_rate()})")
                        time.sleep(5)
            except KeyboardInterrupt: logger.info("Interrupt"); break
            except Exception as e: logger.error(f"Error: {e}", exc_info=True); time.sleep(5)
        logger.info("="*80 + f"\nGUARDIAN STOPPED (restarts: {self.restart_count})\n" + "="*80)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='SOPHIA Guardian - Phoenix Protocol')
    parser.add_argument('--worker-script', default='scripts/autonomous_main.py', help='Worker script path')
    parser.add_argument('--max-crashes', type=int, default=5, help='Max crashes before rollback')
    parser.add_argument('--crash-window', type=int, default=300, help='Time window in seconds for crash detection')
    args = parser.parse_args()
    if not Path(args.worker_script).exists(): logger.error(f"Not found: {args.worker_script}"); sys.exit(1)
    Guardian(args.worker_script, args.max_crashes, args.crash_window).run()
