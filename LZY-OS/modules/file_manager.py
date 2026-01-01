"""LZY-OS File Manager - 文件系统模块"""
import time

class INode:
    """索引节点"""
    _next_id = 1
    
    def __init__(self, name, is_dir=False, size=0, perm=0o755):
        self.inode_id = INode._next_id
        INode._next_id += 1
        self.name = name
        self.is_directory = is_dir
        self.size = size
        self.permissions = perm
        self.content = {} if is_dir else b''
        self.owner = "root"
        self.created = time.time()
        self.modified = time.time()
        self.parent = None
    
    def __str__(self):
        t = "d" if self.is_directory else "-"
        return f"{t} {oct(self.permissions)[2:]:>4} {self.size:>6} {self.name}"

class FileSystem:
    """文件系统"""
    def __init__(self):
        self.inodes = {}
        self.root = INode("/", is_dir=True)
        self.inodes[self.root.inode_id] = self.root
        self.cwd = self.root
        self._init_dirs()
    
    def _init_dirs(self):
        for d in ["home", "bin", "etc", "tmp", "usr", "var"]:
            self.mkdir(f"/{d}")
    
    def resolve(self, path):
        if not path:
            return self.cwd
        if path == "/":
            return self.root
        
        parts = path.strip("/").split("/")
        cur = self.root if path.startswith("/") else self.cwd
        
        for p in parts:
            if not p or p == ".":
                continue
            elif p == "..":
                if cur.parent:
                    cur = cur.parent
            else:
                if cur.is_directory and p in cur.content:
                    cur = cur.content[p]
                else:
                    return None
        return cur
    
    def touch(self, path, size=0, perm=0o644):
        if "/" in path:
            dirname, fname = path.rsplit("/", 1)
            dirname = dirname or "/"
        else:
            dirname, fname = ".", path
        
        parent = self.resolve(dirname)
        if parent and parent.is_directory:
            if fname in parent.content:
                return False
            node = INode(fname, is_dir=False, size=size, perm=perm)
            node.parent = parent
            parent.content[fname] = node
            self.inodes[node.inode_id] = node
            return True
        return False
    
    def mkdir(self, path, parents=False, perm=0o755):
        if parents:
            parts = path.strip("/").split("/")
            cur_path = "" if path.startswith("/") else "."
            for p in parts:
                if not p:
                    continue
                cur_path = f"/{p}" if cur_path in ["", "/"] else (p if cur_path == "." else f"{cur_path}/{p}")
                if not self.resolve(cur_path):
                    self._mkdir_single(cur_path, perm)
            return True
        return self._mkdir_single(path, perm)
    
    def _mkdir_single(self, path, perm):
        if "/" in path:
            dirname, dname = path.rsplit("/", 1)
            dirname = dirname or "/"
        else:
            dirname, dname = ".", path
        
        parent = self.resolve(dirname)
        if parent and parent.is_directory:
            if dname in parent.content:
                return False
            node = INode(dname, is_dir=True, perm=perm)
            node.parent = parent
            parent.content[dname] = node
            self.inodes[node.inode_id] = node
            return True
        return False
    
    def ls(self, path=None):
        target = self.resolve(path) if path else self.cwd
        if not target or not target.is_directory:
            return None
        return target.content
    
    def cd(self, path):
        target = self.resolve(path)
        if target and target.is_directory:
            self.cwd = target
            return True
        return False
    
    def rm(self, path):
        if "/" in path:
            dirname, fname = path.rsplit("/", 1)
            dirname = dirname or "/"
        else:
            dirname, fname = ".", path
        
        parent = self.resolve(dirname)
        if parent and parent.is_directory and fname in parent.content:
            node = parent.content[fname]
            if not node.is_directory:
                del parent.content[fname]
                del self.inodes[node.inode_id]
                return True
        return False
    
    def rmdir(self, path, recursive=False):
        target = self.resolve(path)
        if not target or not target.is_directory or target == self.root:
            return False
        
        if target.content and not recursive:
            return False
        
        if recursive:
            self._rm_recursive(target)
        
        parent = target.parent
        if parent:
            del parent.content[target.name]
            del self.inodes[target.inode_id]
        return True
    
    def _rm_recursive(self, node):
        if node.is_directory:
            for child in list(node.content.values()):
                self._rm_recursive(child)
                del self.inodes[child.inode_id]
            node.content.clear()
    
    def write(self, path, content):
        node = self.resolve(path)
        if node and not node.is_directory:
            node.content = content.encode() if isinstance(content, str) else content
            node.size = len(node.content)
            node.modified = time.time()
            return True
        return False
    
    def read(self, path):
        node = self.resolve(path)
        if node and not node.is_directory:
            return node.content.decode() if isinstance(node.content, bytes) else node.content
        return None
    
    def pwd(self):
        if self.cwd == self.root:
            return "/"
        parts = []
        cur = self.cwd
        while cur and cur != self.root:
            parts.append(cur.name)
            cur = cur.parent
        return "/" + "/".join(reversed(parts))

class FileManager:
    """文件管理器"""
    def __init__(self):
        self.fs = FileSystem()
    
    def ls(self, path=None):
        contents = self.fs.ls(path)
        if contents is None:
            return None
        if not contents:
            return "(empty)"
        lines = []
        for name, node in contents.items():
            lines.append(str(node))
        return "\n".join(lines)
    
    def cd(self, path):
        return self.fs.cd(path)
    
    def pwd(self):
        return self.fs.pwd()
    
    def mkdir(self, path, parents=False):
        return self.fs.mkdir(path, parents=parents)
    
    def touch(self, path):
        return self.fs.touch(path)
    
    def rm(self, path):
        return self.fs.rm(path)
    
    def rmdir(self, path, recursive=False):
        return self.fs.rmdir(path, recursive=recursive)
    
    def cat(self, path):
        return self.fs.read(path)
    
    def echo(self, path, content):
        return self.fs.write(path, content)
    
    def get_status(self):
        lines = ["File System Status"]
        lines.append("-" * 30)
        lines.append(f"cwd: {self.fs.pwd()}")
        lines.append(f"inodes: {len(self.fs.inodes)}")
        return "\n".join(lines)
