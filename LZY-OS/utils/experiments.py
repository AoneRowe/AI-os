"""LZY-OS Experiments - 实验演示模块"""
import threading
import time
from collections import deque
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class BoundedBuffer:
    """有界缓冲区"""
    def __init__(self, capacity):
        self.capacity = capacity
        self.buffer = deque()
        self.lock = threading.Lock()
        self.not_empty = threading.Condition(self.lock)
        self.not_full = threading.Condition(self.lock)
    
    def put(self, item):
        with self.not_full:
            while len(self.buffer) >= self.capacity:
                self.not_full.wait()
            self.buffer.append(item)
            self.not_empty.notify()
            print(f"  [P] + {item} buf={list(self.buffer)}")
    
    def get(self):
        with self.not_empty:
            while len(self.buffer) == 0:
                self.not_empty.wait()
            item = self.buffer.popleft()
            self.not_full.notify()
            print(f"  [C] - {item} buf={list(self.buffer)}")
            return item

class ExperimentDemo:
    """实验演示"""
    
    @staticmethod
    def producer_consumer():
        print("\n[Theory] Producer-Consumer Problem:")
        print("  - Producer: Generate data, put into buffer")
        print("  - Consumer: Get data from buffer")
        print("  - Sync: Mutex + Condition Variables\n")
        
        buf = BoundedBuffer(3)
        
        def producer(name, n):
            for i in range(n):
                buf.put(f"{name}-{i}")
                time.sleep(0.1)
        
        def consumer(name, n):
            for _ in range(n):
                buf.get()
                time.sleep(0.15)
        
        print("[exec] Running: P1(5) -> C1(5)")
        print("-" * 40)
        p = threading.Thread(target=producer, args=("P1", 5))
        c = threading.Thread(target=consumer, args=("C1", 5))
        p.start(); c.start()
        p.join(); c.join()
        print("-" * 40)
        print("[result] Completed\n")
    
    @staticmethod
    def memory_allocation():
        print("\n[Theory] Memory Allocation Strategies:")
        print("  - Fixed: Pre-allocated partitions (simple, wasteful)")
        print("  - Dynamic: Allocate on demand (flexible, fragmentation)\n")
        
        from modules.memory_manager import MemoryManager
        
        # fixed
        print("[1] Fixed Partition (20KB, 4 blocks)")
        print("-" * 50)
        mem = MemoryManager("fixed", size=64, policy_or_block=16)
        print("[alloc] A(10) B(15) C(8)")
        mem.allocate("A", 10)
        mem.allocate("B", 15)
        mem.allocate("C", 8)
        print(mem.get_status())
        print("[dealloc] B")
        mem.deallocate("B")
        print(mem.get_status())
        
        # dynamic
        print("\n[2] Dynamic Partition (64KB, first-fit)")
        print("-" * 50)
        mem2 = MemoryManager("dynamic", size=64, policy_or_block="first-fit")
        print("[alloc] J1(20) J2(15) J3(10)")
        mem2.allocate("J1", 20)
        mem2.allocate("J2", 15)
        mem2.allocate("J3", 10)
        print(mem2.get_status())
        print("[dealloc] J2")
        mem2.deallocate("J2")
        print(mem2.get_status())
        print("[alloc] J4(10)")
        mem2.allocate("J4", 10)
        print(mem2.get_status())
    
    @staticmethod
    def process_scheduling():
        print("\n[Theory] Process Scheduling (Round Robin):")
        print("  - Policy: RR (time slice = 10)")
        print("  - Each process runs until completion\n")
        
        from core.cpu import CPU
        from modules.process_manager import ProcessManager
        from utils.assembler import Assembler, SimpleProgram
        
        # Run each process separately to avoid memory conflicts
        asm = Assembler()
        progs = [
            ("FIBONACCI", SimpleProgram.fibonacci()),
            ("SUM", SimpleProgram.sum()),
            ("MULTIPLY", SimpleProgram.multiply()),
        ]
        
        print("[run] Executing processes sequentially:")
        print("-" * 50)
        
        results = []
        for name, src in progs:
            cpu = CPU(memory_size=256)  # fresh CPU for each
            code = asm.assemble(src)
            cpu.load_program(code)
            
            print("[exec] {} ({} instructions)".format(name, len(code)))
            cycles = 0
            while not cpu.halted and cycles < 100:
                cpu.step()
                cycles += 1
            results.append((name, cycles))
        
        print("-" * 50)
        print("\n[result] Process Execution Summary:")
        print("    NAME              CYCLES")
        print("    " + "-" * 30)
        for name, cycles in results:
            print("    {:15}   {}".format(name, cycles))
    
    @staticmethod
    def filesystem():
        print("\n[Theory] FileSystem (hierarchical inode structure):")
        print("  - inode: file metadata")
        print("  - directory: file name -> inode mapping\n")
        
        from modules.file_manager import FileManager
        
        fm = FileManager()
        print("[current] {}".format(fm.pwd()))
        print("\n[init] ls /:")
        print("-" * 50)
        print(fm.ls("/"))
        
        print("\n[ops] Creating directory structure...")
        print("-" * 50)
        print("[mkdir] /home/user/documents")
        fm.mkdir("/home/user/documents", parents=True)
        
        print("[touch] /home/user/hello.txt")
        fm.touch("/home/user/hello.txt")
        
        print("[echo] /home/user/hello.txt <- 'Hello LZY-OS'")
        fm.echo("/home/user/hello.txt", "Hello LZY-OS")
        
        print("\n[cd] /home/user")
        fm.cd("/home/user")
        
        print("[ls]:")
        print("-" * 50)
        print(fm.ls())
        
        print("\n[cat] /home/user/hello.txt")
        print("-" * 50)
        content = fm.cat("/home/user/hello.txt")
        print(content)
        print("-" * 50)
