#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CPU Simulator - 8086-style instruction set"""


class ProgramCounter:
    def __init__(self):
        self.value = 0
    
    def inc(self):
        self.value += 1
    
    def set(self, v):
        self.value = v
    
    def reset(self):
        self.value = 0


class CPU:
    def __init__(self, memory_size=256):
        self.memory = [0] * memory_size
        self.registers = {'ACC': 0, 'FLAGS': 0, 'R1': 0, 'R2': 0}
        self.halted = False
        self.pc = ProgramCounter()
        self.cycles = 0
        self.stats = {}
        
        self.opcodes = {
            0x01: self._load,   # LOAD addr -> ACC
            0x02: self._add,    # ADD addr
            0x03: self._sub,    # SUB addr
            0x04: self._jmp,    # JMP addr
            0x05: self._div,    # DIV addr
            0x06: self._print,  # PRINT ACC
            0x07: self._store,  # STORE addr
            0x08: self._jz,     # JZ addr (jump if zero)
            0x09: self._halt,   # HALT
            0x0A: self._mul,    # MUL addr
            0x0B: self._mov,    # MOV (nop)
        }
        
        self.opnames = {
            0x01:'LOAD', 0x02:'ADD', 0x03:'SUB', 0x04:'JMP',
            0x05:'DIV', 0x06:'PRINT', 0x07:'STORE', 0x08:'JZ',
            0x09:'HALT', 0x0A:'MUL', 0x0B:'MOV'
        }
    
    def load_program(self, prog):
        for i, b in enumerate(prog):
            if i < len(self.memory):
                self.memory[i] = b
    
    def run(self):
        while not self.halted:
            self.step()
    
    def step(self):
        self.execute()
        self.cycles += 1
    
    def fetch(self):
        if self.pc.value < len(self.memory):
            return self.memory[self.pc.value]
        return None
    
    def execute(self):
        op = self.fetch()
        if op is None:
            self.halted = True
            return
        
        if op in self.opnames:
            self.stats[self.opnames[op]] = self.stats.get(self.opnames[op], 0) + 1
        
        if op in self.opcodes:
            self.opcodes[op]()
        else:
            print("[cpu] Unknown opcode: 0x{:02X} at {}".format(op, self.pc.value))
            self.pc.inc()
    
    def dump_registers(self):
        print("\nCPU State")
        print("-" * 30)
        for r, v in self.registers.items():
            print("  {:5s}: {}".format(r, v))
        print("  PC   : {}".format(self.pc.value))
        print("  HALT : {}".format(self.halted))
        print("  CYCLE: {}".format(self.cycles))
    
    def dump_memory(self, start=0, end=16):
        print("\nMemory [{}:{}]".format(start, end))
        print("-" * 30)
        for i in range(start, min(end, len(self.memory))):
            print("  [{:3d}]: {}".format(i, self.memory[i]))
    
    def get_stats(self):
        return {
            'cycles': self.cycles,
            'instructions': dict(self.stats),
            'registers': dict(self.registers)
        }
    
    # Instruction implementations
    def _load(self):
        # LOAD immediate value (not from memory address)
        val = self.memory[self.pc.value + 1]
        self.registers['ACC'] = val
        self.pc.inc()
        self.pc.inc()
    
    def _add(self):
        addr = self.memory[self.pc.value + 1]
        self.registers['ACC'] += self.memory[addr]
        self.pc.inc()
        self.pc.inc()
    
    def _sub(self):
        addr = self.memory[self.pc.value + 1]
        self.registers['ACC'] -= self.memory[addr]
        self.pc.inc()
        self.pc.inc()
    
    def _mul(self):
        addr = self.memory[self.pc.value + 1]
        self.registers['ACC'] *= self.memory[addr]
        self.pc.inc()
        self.pc.inc()
    
    def _div(self):
        addr = self.memory[self.pc.value + 1]
        if self.memory[addr]:
            self.registers['ACC'] //= self.memory[addr]
        self.pc.inc()
        self.pc.inc()
    
    def _jmp(self):
        self.pc.set(self.memory[self.pc.value + 1])
    
    def _jz(self):
        if self.registers['ACC'] == 0:
            self.pc.set(self.memory[self.pc.value + 1])
        else:
            self.pc.inc()
            self.pc.inc()
    
    def _print(self):
        print("[out] Output: {}".format(self.registers['ACC']))
        self.pc.inc()
    
    def _store(self):
        addr = self.memory[self.pc.value + 1]
        self.memory[addr] = self.registers['ACC']
        self.pc.inc()
        self.pc.inc()
    
    def _mov(self):
        self.pc.inc()
    
    def _halt(self):
        self.halted = True
