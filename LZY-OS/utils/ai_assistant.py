#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AI Assistant with semantic understanding and error correction"""

import json
import re
import urllib.request
import urllib.error


class DeepSeekAssistant:
    API_KEY = "sk-fe748bd53ab84387b9d042a530c6a096"
    API_URL = "https://api.deepseek.com/chat/completions"
    MODEL = "deepseek-chat"
    
    SYSTEM_PROMPT = """你是LZY-OS的命令助手。根据用户输入返回要执行的命令。

可用命令:
- help/sysinfo/cpuinfo/meminfo/fsinfo/ai/clear/exit
- ls [path], cd <path>, pwd, mkdir <path>, touch <path>
- cat <path>, echo <path> <content>, rm <path>
- run <fibonacci|sum|hello|multiply>
- ps, asm <prog>, exp <demo>

规则:
1. 识别用户意图，返回JSON命令: {"command":"xxx","args":"yyy"}
2. 路径自动补全/开头
3. 纠正常见拼写错误
4. 简短回复，直接给出命令

示例:
"创建test目录" -> {"command":"mkdir","args":"/test"}
"rm lzy" -> {"command":"rm","args":"/lzy"}
"看看cpu" -> {"command":"cpuinfo","args":""}
"""
    
    # Command aliases and typo corrections (longer/more specific first)
    CMD_ALIASES = {
        # Chinese mappings - System (sorted by specificity)
        '帮助': 'help', '命令': 'help', '指令': 'help',
        '系统信息': 'sysinfo', '系统': 'sysinfo', '信息': 'sysinfo', '版本': 'sysinfo',
        '处理器': 'cpuinfo', '寄存器': 'cpuinfo', 'cpu': 'cpuinfo',
        '内存信息': 'meminfo', '内存': 'meminfo',
        '文件系统': 'fsinfo', '磁盘': 'fsinfo',
        '分析': 'ai',
        '清屏': 'clear', '清空': 'clear',
        '退出': 'exit', '再见': 'exit', '关闭': 'exit',
        
        # Chinese mappings - File (longer patterns first!)
        '当前目录': 'pwd', '显示目录': 'pwd', '工作目录': 'pwd', '哪里': 'pwd', '路径': 'pwd',
        '列出目录': 'ls', '查看目录': 'ls', '目录': 'ls', '列目录': 'ls', '列出': 'ls',
        '进程': 'ps', '任务': 'ps',
        '运行': 'run', '执行': 'run',
        
        # Programs
        '斐波那契': ('run', 'fibonacci'),
        '求和': ('run', 'sum'),
        '乘法': ('run', 'multiply'),
        
        # Experiments  
        '生产者消费者': ('exp', 'producer-consumer'),
        '生产者': ('exp', 'producer-consumer'),
        '消费者': ('exp', 'producer-consumer'),
        '进程调度': ('exp', 'process-scheduling'),
        '调度': ('exp', 'process-scheduling'),
        
        # Common typos
        'hepl': 'help', 'hlep': 'help',
        'exti': 'exit', 'eixt': 'exit',
        'clera': 'clear', 'claer': 'clear',
        'mkdri': 'mkdir', 'mkdr': 'mkdir',
        'touche': 'touch', 'touhc': 'touch',
        'remvoe': 'rm', 'reomve': 'rm', 'delte': 'rm', 'delete': 'rm',
        'cta': 'cat', 'caat': 'cat',
        'ecoh': 'echo',
        'runn': 'run', 'rnu': 'run',
        'systme': 'sysinfo', 'sysifno': 'sysinfo',
        'cpuifno': 'cpuinfo', 'cpuinof': 'cpuinfo',
        'memifno': 'meminfo', 'meminof': 'meminfo',
        'fsinof': 'fsinfo', 'fsifno': 'fsinfo',
    }
    
    def __init__(self):
        self.history = []
        self.enabled = True
        self._test_api()
    
    def _test_api(self):
        try:
            self._call_api([{"role": "user", "content": "hi"}], 5)
            print("[ai] API connected")
        except Exception as e:
            print("[ai] API unavailable: {}".format(str(e)[:50]))
            print("[ai] Using offline mode")
            self.enabled = False
    
    def _call_api(self, messages, max_tokens=512):
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer {}".format(self.API_KEY)
        }
        data = {
            "model": self.MODEL,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.3,
        }
        
        req = urllib.request.Request(
            self.API_URL,
            data=json.dumps(data).encode('utf-8'),
            headers=headers,
            method='POST'
        )
        
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            return result['choices'][0]['message']['content']
    
    def chat(self, user_input):
        """Process input and return (response, command_dict)"""
        # First try local parse for common patterns
        local_result = self._local_parse(user_input)
        if local_result[1]:
            return local_result
        
        # Then try API if enabled
        if self.enabled:
            try:
                messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]
                messages.extend(self.history[-6:])
                messages.append({"role": "user", "content": user_input})
                
                response = self._call_api(messages)
                
                self.history.append({"role": "user", "content": user_input})
                self.history.append({"role": "assistant", "content": response})
                
                cmd = self._extract_cmd(response)
                return self._clean(response), cmd
            except Exception as e:
                pass
        
        # Fallback to local parse
        return self._local_parse(user_input)
    
    def _extract_cmd(self, text):
        """Extract JSON command from response"""
        try:
            match = re.search(r'\{[^{}]*"command"[^{}]*\}', text)
            if match:
                return json.loads(match.group())
        except:
            pass
        return None
    
    def _clean(self, text):
        """Remove JSON blocks from display text"""
        text = re.sub(r'```json\s*\{[^}]*\}\s*```', '', text)
        text = re.sub(r'\{[^{}]*"command"[^{}]*\}', '', text)
        return text.strip()
    
    def _local_parse(self, text):
        """Enhanced local parsing with semantic understanding"""
        text_lower = text.lower().strip()
        
        # Direct command detection (e.g., "rm lzy", "mkdir test")
        direct_cmd = self._parse_direct_cmd(text_lower)
        if direct_cmd:
            return "[local] {}".format(direct_cmd[0]), {"command": direct_cmd[0], "args": direct_cmd[1]}
        
        # Typo correction
        words = text_lower.split()
        if words:
            corrected = self._correct_typo(words[0])
            if corrected != words[0]:
                args = ' '.join(words[1:]) if len(words) > 1 else ''
                if isinstance(corrected, tuple):
                    return "[corrected] {} -> {}".format(words[0], corrected[0]), {"command": corrected[0], "args": corrected[1]}
                return "[corrected] {} -> {}".format(words[0], corrected), {"command": corrected, "args": self._normalize_path(args)}
        
        # Chinese keyword matching (simple and reliable)
        chinese_kw = {
            # System info - keyword detection
            '当前路径': ('pwd', ''), '当前目录': ('pwd', ''), '在哪': ('pwd', ''), '工作目录': ('pwd', ''),
            '看cpu': ('cpuinfo', ''), 'cpu信息': ('cpuinfo', ''), '处理器': ('cpuinfo', ''),
            '看内存': ('meminfo', ''), '内存信息': ('meminfo', ''),
            '看文件系统': ('fsinfo', ''), '磁盘': ('fsinfo', ''),
            '帮助': ('help', ''), '命令': ('help', ''),
            '清屏': ('clear', ''),
        }
        for kw, (cmd, args) in chinese_kw.items():
            if kw in text:
                return "[local] {}".format(cmd), {"command": cmd, "args": args}
        
        # Pattern matching for file operations (supports Chinese and English names)
        # Note: Match name before or after keyword like "目录"
        patterns = [
            # mkdir: "创建xxx目录" or "创建目录xxx"
            (r'(?:创建|新建|建立)\s*([a-zA-Z0-9_]+)\s*(?:目录|文件夹)', 'mkdir'),  # name before
            (r'(?:创建|新建|建立)\s*(?:目录|文件夹)\s*([a-zA-Z0-9_]+)', 'mkdir'),  # name after
            # touch: "创建xxx文件" or "创建文件xxx"
            (r'(?:创建|新建)\s*([a-zA-Z0-9_.]+)\s*文件', 'touch'),  # name before
            (r'(?:创建|新建)\s*文件\s*([a-zA-Z0-9_.]+)', 'touch'),  # name after
            # rm
            (r'(?:删除|移除|删掉|rm)\s*([/a-zA-Z0-9_.]+)', 'rm'),
            # cat  
            (r'(?:查看|读取|cat)\s*([/a-zA-Z0-9_.]+)\s*(?:内容)?$', 'cat'),
            # cd
            (r'(?:进入|切换|cd)\s*([/a-zA-Z0-9_]+)', 'cd'),
            # ls
            (r'(?:列出|显示|看看?)\s*(?:目录|文件)', 'ls'),
        ]
        
        for pattern, cmd in patterns:
            match = re.search(pattern, text)
            if match:
                if cmd == 'ls':
                    return "[pattern] {}".format(cmd), {"command": cmd, "args": ""}
                arg = self._normalize_path(match.group(1))
                return "[pattern] {}".format(cmd), {"command": cmd, "args": arg}
        
        return "[local] Cannot parse. Use 'help' for commands.", None
    
    def _parse_direct_cmd(self, text):
        """Parse direct command input like 'rm lzy', 'mkdir test'"""
        parts = text.split()
        if not parts:
            return None
        
        cmd = parts[0]
        args = ' '.join(parts[1:]) if len(parts) > 1 else ''
        
        # Known commands that take path arguments
        path_cmds = {'rm', 'mkdir', 'touch', 'cd', 'cat', 'ls'}
        # Commands with specific arguments
        prog_cmds = {'run', 'asm', 'exp'}
        # No-arg commands
        simple_cmds = {'help', 'exit', 'quit', 'sysinfo', 'cpuinfo', 'meminfo', 'fsinfo', 'pwd', 'ps', 'clear', 'ai'}
        
        # Correct typos in command
        corrected_cmd = self._correct_typo(cmd)
        if isinstance(corrected_cmd, tuple):
            return corrected_cmd
        cmd = corrected_cmd
        
        if cmd in path_cmds and args:
            return (cmd, self._normalize_path(args))
        elif cmd in prog_cmds:
            return (cmd, args)
        elif cmd in simple_cmds:
            return (cmd, '')
        
        return None
    
    def _correct_typo(self, word):
        """Correct common typos"""
        if word in self.CMD_ALIASES:
            return self.CMD_ALIASES[word]
        
        # Levenshtein-based correction
        valid_cmds = ['help','exit','sysinfo','cpuinfo','meminfo','fsinfo',
                      'ls','cd','pwd','mkdir','touch','cat','echo','rm',
                      'run','ps','clear','exp','asm','ai']
        
        for cmd in valid_cmds:
            if self._distance(word, cmd) <= 1:
                return cmd
        
        return word
    
    def _distance(self, s1, s2):
        """Levenshtein distance"""
        if len(s1) < len(s2):
            return self._distance(s2, s1)
        if not s2:
            return len(s1)
        
        prev = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            curr = [i + 1]
            for j, c2 in enumerate(s2):
                curr.append(min(prev[j+1]+1, curr[j]+1, prev[j]+(c1!=c2)))
            prev = curr
        return prev[-1]
    
    def _normalize_path(self, path):
        """Normalize path to start with /"""
        path = path.strip().strip('"\'')
        if path and not path.startswith('/'):
            path = '/' + path
        return path
    
    def clear_history(self):
        self.history = []
        print("[ai] History cleared")


if __name__ == "__main__":
    a = DeepSeekAssistant()
    tests = ["rm lzy", "创建test目录", "hepl", "mkdri demo", "看看cpu", "运行斐波那契"]
    for t in tests:
        r, c = a._local_parse(t)
        print("{} -> {}".format(t, c))
