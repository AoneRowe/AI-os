#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LZY-OS - Teaching Operating System Simulator"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.cpu import CPU
from modules.process_manager import ProcessManager
from modules.memory_manager import MemoryManager
from modules.file_manager import FileManager
from utils.assembler import Assembler, SimpleProgram
from utils.experiments import ExperimentDemo
from utils.ai_assistant import DeepSeekAssistant


class LZYOS:
    VERSION = "2.1"
    
    def __init__(self):
        self.cpu = CPU(512)
        self.process_manager = ProcessManager(self.cpu, "RR")
        self.memory_manager = MemoryManager("dynamic", 512, "first-fit")
        self.file_manager = FileManager()
        self.assembler = Assembler()
        
        self.running = True
        self.ai_mode = True
        self.ai_assistant = None
        
        self._show_banner()
    
    def _show_banner(self):
        print("\n" + "=" * 60)
        print("  LZY-OS v{} - Operating System".format(self.VERSION))
        print("  Type 'help' for commands, '/mode' to toggle AI mode")
        print("=" * 60)
    
    def _init_ai(self):
        if self.ai_assistant is None:
            print("[init] Loading AI assistant...")
            self.ai_assistant = DeepSeekAssistant()
            status = "online" if self.ai_assistant.enabled else "offline (local parse)"
            print("[init] AI status: {}".format(status))
    
    def run(self):
        if self.ai_mode:
            self._init_ai()
        
        while self.running:
            try:
                mode = "ai" if self.ai_mode else "cmd"
                user_input = input("\nlzy-os[{}]$ ".format(mode)).strip()
                
                if not user_input:
                    continue
                
                if user_input.startswith('/'):
                    self._special_cmd(user_input)
                elif self.ai_mode:
                    self._ai_handle(user_input)
                else:
                    self._exec(user_input)
                    
            except KeyboardInterrupt:
                print("\n[SIGINT] Shutting down...")
                self._shutdown()
            except Exception as e:
                print("[error] {}: {}".format(type(e).__name__, e))
    
    def _special_cmd(self, user_input):
        parts = user_input[1:].split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        if cmd == 'cmd' and args:
            self._exec(args)
        elif cmd == 'mode':
            self.ai_mode = not self.ai_mode
            print("[mode] Switched to: {}".format("AI" if self.ai_mode else "CMD"))
            if self.ai_mode and not self.ai_assistant:
                self._init_ai()
        elif cmd == 'clear' and self.ai_assistant:
            self.ai_assistant.clear_history()
        elif cmd in ('exit', 'quit'):
            self._shutdown()
        elif cmd == 'help':
            self._show_help()
        else:
            print("[error] Unknown: /{}".format(cmd))
    
    def _show_help(self):
        print("""
LZY-OS Command Reference
========================
Special:  /mode /cmd <c> /clear /exit
System:   help sysinfo cpuinfo meminfo fsinfo ai clear exit
File:     ls [path] cd <path> pwd mkdir <path> touch <path>
          cat <path> echo <path> <text> rm <path>
Process:  run <prog> ps
          Programs: fibonacci sum hello multiply
Tools:    asm <prog> exp <demo>
          Demos: producer-consumer memory-allocation
                 process-scheduling filesystem
AI Mode:  Natural language input -> auto command execution
        """)
    
    def _ai_handle(self, user_input):
        print("[ai] Processing...")
        response, cmd_dict = self.ai_assistant.chat(user_input)
        
        if response:
            print("[ai] {}".format(response))
        
        if cmd_dict:
            cmd = cmd_dict.get('command', '')
            args = cmd_dict.get('args', '')
            if cmd:
                print("[exec] {} {}".format(cmd, args))
                self._exec("{} {}".format(cmd, args).strip())
    
    def _exec(self, command):
        parts = command.split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        cmds = {
            'help': lambda a: self._show_help(),
            'exit': lambda a: self._shutdown(),
            'quit': lambda a: self._shutdown(),
            'sysinfo': self._cmd_sysinfo,
            'cpuinfo': lambda a: self.cpu.dump_registers(),
            'meminfo': lambda a: print(self.memory_manager.get_status()),
            'fsinfo': lambda a: print(self.file_manager.get_status()),
            'ls': self._cmd_ls,
            'cd': self._cmd_cd,
            'pwd': lambda a: print(self.file_manager.pwd()),
            'mkdir': lambda a: self.file_manager.mkdir(a, True) if a else print("[error] path required"),
            'touch': lambda a: self.file_manager.touch(a) if a else print("[error] path required"),
            'cat': self._cmd_cat,
            'echo': self._cmd_echo,
            'rm': self._cmd_rm,
            'run': self._cmd_run,
            'ps': lambda a: print(self.process_manager.get_process_info()),
            'clear': lambda a: os.system('cls' if os.name == 'nt' else 'clear'),
            'exp': self._cmd_exp,
            'asm': self._cmd_asm,
            'ai': self._cmd_ai,
        }
        
        if cmd in cmds:
            cmds[cmd](args)
        else:
            print("[error] Unknown command: {}".format(cmd))
            self._suggest_cmd(cmd)
    
    def _suggest_cmd(self, cmd):
        """Command auto-correction"""
        all_cmds = ['help','exit','sysinfo','cpuinfo','meminfo','fsinfo',
                    'ls','cd','pwd','mkdir','touch','cat','echo','rm',
                    'run','ps','clear','exp','asm','ai']
        
        suggestions = []
        for c in all_cmds:
            if cmd in c or c in cmd or self._levenshtein(cmd, c) <= 2:
                suggestions.append(c)
        
        if suggestions:
            print("[hint] Did you mean: {}?".format(', '.join(suggestions)))
    
    def _levenshtein(self, s1, s2):
        """Levenshtein distance for typo correction"""
        if len(s1) < len(s2):
            return self._levenshtein(s2, s1)
        if len(s2) == 0:
            return len(s1)
        
        prev = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            curr = [i + 1]
            for j, c2 in enumerate(s2):
                curr.append(min(prev[j+1]+1, curr[j]+1, prev[j]+(c1!=c2)))
            prev = curr
        return prev[-1]
    
    def _cmd_sysinfo(self, args):
        print("""
LZY-OS System Information
-------------------------
Version:  {} 
CPU:      512B memory, 4 registers, 11 instructions
Memory:   Dynamic partition, first-fit allocation
FS:       Unix-style inode directory tree
Scheduler:Round-Robin (RR), FCFS, SJF, Priority
        """.format(self.VERSION))
    
    def _cmd_ls(self, path):
        result = self.file_manager.ls(path if path else None)
        if result:
            print(result)
    
    def _cmd_cd(self, path):
        if not path:
            print("[error] path required")
            return
        if self.file_manager.cd(path):
            print(self.file_manager.pwd())
        else:
            print("[error] no such directory: {}".format(path))
    
    def _cmd_cat(self, path):
        if not path:
            print("[error] path required")
            return
        content = self.file_manager.cat(path)
        if content is not None:
            print(content)
        else:
            print("[error] no such file: {}".format(path))
    
    def _cmd_echo(self, args):
        parts = args.split(maxsplit=1)
        if len(parts) < 2:
            print("[error] usage: echo <path> <content>")
            return
        self.file_manager.echo(parts[0], parts[1])
    
    def _cmd_rm(self, path):
        if not path:
            print("[error] path required")
            return
        if self.file_manager.rm(path):
            print("[ok] removed: {}".format(path))
        else:
            print("[error] cannot remove: {}".format(path))
    
    def _cmd_run(self, name):
        programs = {
            'fibonacci': ("Fibonacci", SimpleProgram.fibonacci()),
            'sum': ("Sum", SimpleProgram.sum()),
            'hello': ("Hello", SimpleProgram.hello()),
            'multiply': ("Multiply", SimpleProgram.multiply()),
        }
        
        if not name:
            print("[run] Available programs:")
            for prog, desc in programs.items():
                print("      - {} | {}".format(prog, desc[0]))
            return
        
        key = name.lower()
        if key in programs:
            label, asm = programs[key]
            prog = self.assembler.assemble(asm)
            
            # Header
            print("\n" + "=" * 60)
            print("  Program: {}".format(label))
            print("=" * 60)
            
            # Show ASM
            print("\n[asm] Assembly Code:")
            print("-" * 60)
            print(self.assembler.disassemble(prog))
            
            # Show Machine Code
            print("[code] Machine Code ({} bytes):".format(len(prog)))
            print(" ".join('{:02X}'.format(b) for b in prog))
            print("-" * 60)
            
            # Execute
            print("\n[exec] Running...\n")
            self.process_manager.create_process(prog, name=label)
            self.process_manager.run(500, verbose=True)
            
            # Results
            print("\n[result] Execution Summary:")
            print(self.process_manager.get_process_info())
            print("=" * 60 + "\n")
        else:
            print("[error] unknown program: {}".format(name))
    
    def _cmd_asm(self, name):
        programs = {
            'fibonacci': SimpleProgram.fibonacci(),
            'sum': SimpleProgram.sum(),
            'hello': SimpleProgram.hello(),
            'multiply': SimpleProgram.multiply(),
        }
        
        if not name:
            print("[asm] Available programs:")
            for prog in programs.keys():
                print("      - {}".format(prog))
            return
        
        key = name.lower()
        if key in programs:
            prog = self.assembler.assemble(programs[key])
            print("\n[asm] {} Assembly".format(key))
            print("-" * 50)
            print(self.assembler.disassemble(prog))
            print("\n[hex] {}".format(' '.join('{:02X}'.format(b) for b in prog)))
            print("[size] {} bytes\n".format(len(prog)))
        else:
            print("[error] unknown program: {}".format(name))
    
    def _cmd_exp(self, name):
        demos = {
            'producer-consumer': ("Producer-Consumer", ExperimentDemo.producer_consumer),
            'memory-allocation': ("Memory Allocation", ExperimentDemo.memory_allocation),
            'process-scheduling': ("Process Scheduling", ExperimentDemo.process_scheduling),
            'filesystem': ("FileSystem", ExperimentDemo.filesystem),
        }
        
        if not name:
            print("\n[exp] Available Experiments:")
            for key, (desc, _) in demos.items():
                print("      - {} | {}".format(key, desc))
            return
        
        key = name.lower()
        if key in demos:
            label, demo = demos[key]
            print("\n" + "=" * 60)
            print("  Experiment: {}".format(label))
            print("=" * 60)
            demo()
            print("=" * 60 + "\n")
        else:
            print("[error] unknown demo: {}".format(name))
    
    def _cmd_ai(self, args):
        print("[ai] System analysis:")
        print("  CPU cycles: {}".format(self.cpu.cycles))
        print("  Processes: {}".format(len(self.process_manager.processes)))
        print("  Memory type: {}".format(self.memory_manager.memory_type))
        print("  Current dir: {}".format(self.file_manager.pwd()))
    
    def _shutdown(self):
        print("\n[shutdown] LZY-OS terminated.")
        self.running = False
        sys.exit(0)


if __name__ == "__main__":
    LZYOS().run()
