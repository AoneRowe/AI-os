"""LZY-OS Assembler - 汇编器模块"""

class Assembler:
    """简易汇编器"""
    OPCODES = {
        'LOAD': 0x01, 'ADD': 0x02, 'SUB': 0x03, 'JMP': 0x04,
        'DIV': 0x05, 'PRINT': 0x06, 'STORE': 0x07, 'JZ': 0x08,
        'HALT': 0x09, 'MUL': 0x0A, 'MOV': 0x0B,
    }
    NO_OPERAND = {'PRINT', 'HALT'}
    
    def __init__(self):
        self.symbols = {}
        self.program = []
    
    def assemble(self, source):
        """汇编源代码 -> 机器码"""
        self.program = []
        self.symbols = {}
        lines = source.strip().split('\n')
        
        # pass 1: collect labels
        addr = 0
        for line in lines:
            line = line.split('#')[0].strip()
            if not line:
                continue
            if line.endswith(':'):
                self.symbols[line[:-1].strip()] = addr
            else:
                tokens = line.split()
                if tokens and tokens[0].upper() in self.OPCODES:
                    addr += 1
                    if tokens[0].upper() not in self.NO_OPERAND:
                        addr += 1
        
        # pass 2: generate code
        for line in lines:
            line = line.split('#')[0].strip()
            if not line or line.endswith(':'):
                continue
            tokens = line.split()
            if not tokens:
                continue
            
            instr = tokens[0].upper()
            if instr in self.OPCODES:
                self.program.append(self.OPCODES[instr])
                if len(tokens) > 1:
                    op = tokens[1]
                    if op in self.symbols:
                        self.program.append(self.symbols[op])
                    else:
                        try:
                            self.program.append(int(op))
                        except ValueError:
                            self.program.append(0)
        return self.program
    
    def disassemble(self, program):
        """机器码 -> 汇编"""
        rev = {v: k for k, v in self.OPCODES.items()}
        needs_op = [k for k in self.OPCODES if k not in self.NO_OPERAND]
        lines = []
        i = 0
        while i < len(program):
            code = program[i]
            if code in rev:
                name = rev[code]
                if name in needs_op and i + 1 < len(program):
                    lines.append(f"{i:3d}: {name} {program[i+1]}")
                    i += 2
                else:
                    lines.append(f"{i:3d}: {name}")
                    i += 1
            else:
                lines.append(f"{i:3d}: DATA {code}")
                i += 1
        return "\n".join(lines)

class SimpleProgram:
    """示例程序集"""
    @staticmethod
    def fibonacci():
        """计算斐波那契: 1+1+2+1 = 5"""
        return """
        # Fibonacci demo: 1+1+2+1 = 5
        LOAD 1
        STORE 100
        LOAD 1
        ADD 100
        STORE 100
        LOAD 2
        ADD 100
        STORE 100
        LOAD 1
        ADD 100
        PRINT
        HALT
        """
    
    @staticmethod
    def sum():
        """计算求和: 5+10 = 15"""
        return """
        # Sum: 5 + 10 = 15
        LOAD 5
        STORE 100
        LOAD 10
        ADD 100
        PRINT
        HALT
        """
    
    @staticmethod
    def multiply():
        """计算乘法: 5 * 4 = 20"""
        return """
        # Multiply: 5 * 4 = 20
        LOAD 5
        STORE 40
        LOAD 4
        MUL 40
        PRINT
        HALT
        """
    
    @staticmethod
    def hello():
        """输出ASCII码序列"""
        return """
        # ASCII Output: H i
        LOAD 72
        PRINT
        LOAD 105
        PRINT
        HALT
        """
