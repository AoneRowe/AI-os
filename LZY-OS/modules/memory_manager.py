"""LZY-OS Memory Manager - 内存管理模块"""
import time

class MemoryBlock:
    """内存块"""
    def __init__(self, start, length):
        self.name = None
        self.start = start
        self.length = length
        self.free = True
    
    def mark_allocated(self, name):
        self.name = name
        self.free = False
    
    def mark_free(self):
        self.name = None
        self.free = True
    
    def __str__(self):
        status = "free" if self.free else f"used({self.name})"
        return f"[{self.start:3d}-{self.start+self.length:3d}] {status:20s} {self.length}KB"

class Memory:
    """内存基类"""
    def __init__(self, size=256):
        self.size = size
        self.blocks = []
    
    def allocate(self, name, size):
        raise NotImplementedError
    
    def deallocate(self, start):
        raise NotImplementedError
    
    def reset(self):
        raise NotImplementedError

class FixedMemory(Memory):
    """固定分区内存"""
    def __init__(self, size, block_size):
        super().__init__(size)
        if isinstance(block_size, list):
            start = 0
            for b in block_size:
                self.blocks.append(MemoryBlock(start, b))
                start += b
        else:
            num = size // block_size
            start = 0
            for _ in range(num):
                self.blocks.append(MemoryBlock(start, block_size))
                start += block_size
            rem = size - num * block_size
            if rem > 0:
                self.blocks.append(MemoryBlock(start, rem))
    
    def allocate(self, name, size):
        for b in self.blocks:
            if b.free and size <= b.length:
                b.mark_allocated(name)
                return b.start
        return None
    
    def deallocate(self, start):
        for b in self.blocks:
            if b.start == start and not b.free:
                b.mark_free()
                return True
        return False
    
    def reset(self):
        for b in self.blocks:
            b.mark_free()
    
    def get_status(self):
        lines = [f"Fixed Partition Memory ({self.size}KB)"]
        lines.append("-" * 40)
        for b in self.blocks:
            lines.append(str(b))
        used = sum(b.length for b in self.blocks if not b.free)
        free = sum(b.length for b in self.blocks if b.free)
        lines.append("-" * 40)
        lines.append(f"used: {used}KB  free: {free}KB  util: {used/self.size*100:.1f}%")
        return "\n".join(lines)

class DynamicMemory(Memory):
    """动态分区内存 - 支持first-fit/best-fit/worst-fit"""
    def __init__(self, size, policy="first-fit"):
        super().__init__(size)
        self.blocks.append(MemoryBlock(0, size))
        self.policy = policy
    
    def allocate(self, name, size):
        candidates = [(i, b) for i, b in enumerate(self.blocks) if b.free and b.length >= size]
        if not candidates:
            return None
        
        if self.policy == "first-fit":
            idx, block = candidates[0]
        elif self.policy == "best-fit":
            idx, block = min(candidates, key=lambda x: x[1].length)
        elif self.policy == "worst-fit":
            idx, block = max(candidates, key=lambda x: x[1].length)
        else:
            idx, block = candidates[0]
        
        allocated = MemoryBlock(block.start, size)
        allocated.mark_allocated(name)
        
        if block.length > size:
            remaining = MemoryBlock(block.start + size, block.length - size)
            self.blocks[idx] = allocated
            self.blocks.insert(idx + 1, remaining)
        else:
            self.blocks[idx] = allocated
        
        return allocated.start
    
    def deallocate(self, start):
        for i, b in enumerate(self.blocks):
            if b.start == start and not b.free:
                b.mark_free()
                self._merge()
                return True
        return False
    
    def _merge(self):
        i = 0
        while i < len(self.blocks) - 1:
            if self.blocks[i].free and self.blocks[i+1].free:
                self.blocks[i].length += self.blocks[i+1].length
                self.blocks.pop(i+1)
            else:
                i += 1
    
    def reset(self):
        self.blocks.clear()
        self.blocks.append(MemoryBlock(0, self.size))
    
    def get_fragmentation(self):
        free_blocks = [b for b in self.blocks if b.free]
        total_free = sum(b.length for b in free_blocks)
        max_free = max((b.length for b in free_blocks), default=0)
        frag = (1 - max_free / total_free) if total_free > max_free else 0
        return len(free_blocks), total_free, max_free, frag
    
    def get_status(self):
        lines = [f"Dynamic Memory ({self.size}KB) [{self.policy}]"]
        lines.append("-" * 45)
        for b in self.blocks:
            lines.append(str(b))
        used = sum(b.length for b in self.blocks if not b.free)
        free = sum(b.length for b in self.blocks if b.free)
        lines.append("-" * 45)
        lines.append(f"used: {used}KB  free: {free}KB  blocks: {len(self.blocks)}")
        return "\n".join(lines)

class MemoryManager:
    """内存管理器"""
    def __init__(self, memory_type="dynamic", size=256, policy_or_block=32):
        self.memory_type = memory_type
        if memory_type == "fixed":
            self.memory = FixedMemory(size, policy_or_block)
        else:
            self.memory = DynamicMemory(size, policy_or_block)
        self.allocations = {}
    
    def allocate(self, name, size):
        start = self.memory.allocate(name, size)
        if start is not None:
            self.allocations[name] = (start, size)
            print(f"[mem] alloc {size}KB -> {name} @{start}")
            return start
        print(f"[mem] alloc failed: {name} ({size}KB)")
        return None
    
    def deallocate(self, name):
        if name in self.allocations:
            start, _ = self.allocations[name]
            self.memory.deallocate(start)
            del self.allocations[name]
            print(f"[mem] free: {name}")
            return True
        return False
    
    def get_status(self):
        return self.memory.get_status()
