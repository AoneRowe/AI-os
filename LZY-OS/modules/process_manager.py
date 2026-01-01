"""LZY-OS Process Manager - 进程管理模块"""
from enum import Enum, auto
from collections import deque
import time

class ProcessState(Enum):
    NEW = auto()
    READY = auto()
    RUNNING = auto()
    WAITING = auto()
    TERMINATED = auto()

class PCB:
    """进程控制块"""
    def __init__(self, pid, name, program):
        self.pid = pid
        self.name = name
        self.state = ProcessState.READY
        self.program = program
        self.pc_value = 0
        self.registers_backup = {}
        self.created_time = time.time()
        self.terminated_time = None
        self.total_cycles = 0
        self.priority = 50
    
    def save_context(self, cpu):
        self.pc_value = cpu.pc.value
        self.registers_backup = cpu.registers.copy()
    
    def restore_context(self, cpu):
        cpu.pc.set(self.pc_value)
        for reg, val in self.registers_backup.items():
            if reg in cpu.registers:
                cpu.registers[reg] = val
    
    def __str__(self):
        return f"PID:{self.pid} {self.name} [{self.state.name}] cycles:{self.total_cycles}"

class Scheduler:
    """调度器 - 支持RR/FCFS/SJF/PRIORITY"""
    def __init__(self, policy="RR"):
        self.ready_queue = deque()
        self.running_process = None
        self.terminated_processes = []
        self.policy = policy
        self.time_slice = 10
        self.current_slice = 0
    
    def add_process(self, pcb):
        self.ready_queue.append(pcb)
    
    def schedule(self):
        if not self.ready_queue:
            return None
        dispatch = {
            "RR": self._rr, "FCFS": self._fcfs,
            "SJF": self._sjf, "PRIORITY": self._priority
        }
        return dispatch.get(self.policy, self._fcfs)()
    
    def _rr(self):
        return self.ready_queue.popleft() if self.ready_queue else None
    
    def _fcfs(self):
        return self.ready_queue.popleft() if self.ready_queue else None
    
    def _sjf(self):
        if not self.ready_queue:
            return None
        shortest = min(self.ready_queue, key=lambda p: len(p.program))
        self.ready_queue.remove(shortest)
        return shortest
    
    def _priority(self):
        if not self.ready_queue:
            return None
        highest = max(self.ready_queue, key=lambda p: p.priority)
        self.ready_queue.remove(highest)
        return highest
    
    def recommend_policy(self, processes):
        if not processes:
            return "RR", "default round-robin"
        short = sum(1 for p in processes if len(p.program) < 20)
        total = len(processes)
        if short > total * 0.7:
            return "SJF", f"short jobs: {short}/{total}"
        elif total > 5:
            return "RR", f"many processes: {total}"
        return "FCFS", f"few processes: {total}"

class ProcessManager:
    """进程管理器"""
    def __init__(self, cpu, policy="RR"):
        self.cpu = cpu
        self.scheduler = Scheduler(policy)
        self.processes = {}
        self.next_pid = 1000
        self.clock = 0
    
    def create_process(self, program, name="proc", priority=50):
        pid = self.next_pid
        self.next_pid += 1
        pcb = PCB(pid, name, program)
        pcb.priority = priority
        self.processes[pid] = pcb
        self.scheduler.add_process(pcb)
        print(f"[proc] create: {name} (pid={pid})")
        return pcb
    
    def load_process(self, pcb):
        self.cpu.load_program(pcb.program)
        pcb.restore_context(self.cpu)
        self.cpu.halted = False
    
    def save_process(self, pcb):
        pcb.save_context(self.cpu)
    
    def switch_process(self):
        if self.scheduler.running_process:
            self.save_process(self.scheduler.running_process)
            if not self.cpu.halted:
                self.scheduler.running_process.state = ProcessState.READY
                self.scheduler.add_process(self.scheduler.running_process)
        
        next_proc = self.scheduler.schedule()
        if next_proc:
            self.scheduler.running_process = next_proc
            next_proc.state = ProcessState.RUNNING
            self.load_process(next_proc)
        return next_proc
    
    def run(self, max_cycles=1000, verbose=False):
        if not self.processes:
            print("[proc] no process")
            return
        
        procs = list(self.scheduler.ready_queue)
        policy, reason = self.scheduler.recommend_policy(procs)
        print("[sched] policy: {} ({})".format(policy, reason))
        
        self.switch_process()
        cycles = 0
        
        while cycles < max_cycles and (self.scheduler.running_process or self.scheduler.ready_queue):
            if not self.scheduler.running_process:
                self.switch_process()
            if not self.scheduler.running_process:
                break
            
            self.cpu.step()
            self.scheduler.running_process.total_cycles += 1
            cycles += 1
            self.clock += 1
            
            # time slice check
            if self.scheduler.policy == "RR":
                self.scheduler.current_slice += 1
                if self.scheduler.current_slice >= self.scheduler.time_slice and self.scheduler.ready_queue:
                    if verbose:
                        print("[sched] time slice expired, switching process")
                    self.scheduler.current_slice = 0
                    self.switch_process()
            
            # completion check
            if self.cpu.halted:
                if verbose:
                    print("[proc] {} completed at cycle {}".format(self.scheduler.running_process.name, cycles))
                self.scheduler.running_process.state = ProcessState.TERMINATED
                self.scheduler.running_process.terminated_time = time.time()
                self.scheduler.terminated_processes.append(self.scheduler.running_process)
                self.scheduler.running_process = None
                self.switch_process()
        
        print("[proc] execution completed, total cycles: {}".format(cycles))
    
    def get_process_info(self):
        lines = ["PID      NAME                 STATE        CYCLES"]
        lines.append("-" * 52)
        for pid, pcb in self.processes.items():
            lines.append(f"{pid:<8} {pcb.name:<20} {pcb.state.name:<12} {pcb.total_cycles}")
        return "\n".join(lines)
