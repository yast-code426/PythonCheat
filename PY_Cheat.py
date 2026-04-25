# -*- coding: utf-8 -*-
"""
=================================================================
PY_Cheat - Python Memory Editor Pro
=================================================================
Version: 3.0
Author: PY_Cheat Team
Description: Professional memory editing tool with advanced features
Dependencies: customtkinter, psutil, pymem
=================================================================
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk
import psutil
import pymem
import pymem.process
import struct
import re
import os
import sys
import json
import time
import threading
import ctypes
import random
import string
import subprocess
from typing import List, Dict, Tuple, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

# ============================================================
# 配置区域
# ============================================================
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# 版本信息
VERSION = "3.0"
APP_NAME = "PY_Cheat - Memory Editor Pro"

# 全局颜色配置
COLORS = {
    'primary': '#1f6aa5',
    'secondary': '#144870',
    'success': '#2fa84f',
    'warning': '#f5a623',
    'danger': '#e53935',
    'bg_dark': '#1a1a2e',
    'bg_medium': '#16213e',
    'bg_light': '#0f3460',
    'text': '#eaeaea',
    'text_secondary': '#a0a0a0',
    'accent': '#e94560',
    'hex_addr': '#4fc3f7',
    'hex_data': '#81c784',
    'hex_ascii': '#ffb74d',
}

# ============================================================
# 工具类：环境隐藏与反作弊规避
# ============================================================
class AntiCheatBypass:
    """提供环境隐藏与反反作弊的基础功能"""
    
    def __init__(self, window_handle=None):
        self.window_handle = window_handle
        self.original_title = ""
        self.hidden = False
        self.title_randomized = False

    def set_window_handle(self, hwnd):
        self.window_handle = hwnd

    def hide_window(self):
        """从任务栏隐藏窗口"""
        try:
            if not self.window_handle:
                return False
            GWL_EXSTYLE = -20
            WS_EX_TOOLWINDOW = 0x00000080
            current_style = ctypes.windll.user32.GetWindowLongW(self.window_handle, GWL_EXSTYLE)
            ctypes.windll.user32.SetWindowLongW(self.window_handle, GWL_EXSTYLE, current_style | WS_EX_TOOLWINDOW)
            ctypes.windll.user32.SetWindowPos(self.window_handle, 0, 0, 0, 0, 0, 0x0002 | 0x0001)
            self.hidden = True
            return True
        except Exception:
            return False

    def restore_window_visibility(self):
        """恢复窗口任务栏显示"""
        if not self.window_handle or not self.hidden:
            return
        try:
            GWL_EXSTYLE = -20
            WS_EX_TOOLWINDOW = 0x00000080
            current_style = ctypes.windll.user32.GetWindowLongW(self.window_handle, GWL_EXSTYLE)
            ctypes.windll.user32.SetWindowLongW(self.window_handle, GWL_EXSTYLE, current_style & ~WS_EX_TOOLWINDOW)
            ctypes.windll.user32.SetWindowPos(self.window_handle, 0, 0, 0, 0, 0, 0x0002 | 0x0001)
            self.hidden = False
        except:
            pass

    def randomize_title(self):
        """随机化窗口标题"""
        try:
            if not self.window_handle:
                return
            if not self.original_title:
                self.original_title = ctypes.windll.user32.GetWindowTextW(self.window_handle)
            random_suffix = ''.join(random.choices(string.ascii_letters, k=8))
            ctypes.windll.user32.SetWindowTextW(self.window_handle, f"Notepad_{random_suffix}")
            self.title_randomized = True
        except:
            pass

    def restore_title(self):
        """恢复原始窗口标题"""
        try:
            if self.window_handle and self.title_randomized:
                ctypes.windll.user32.SetWindowTextW(self.window_handle, self.original_title)
                self.title_randomized = False
        except:
            pass

    def modify_environment(self):
        """修改环境变量以干扰部分反作弊扫描"""
        env_changes = {
            "_NT_ALT_SYMBOL_PATH": "",
            "DBGHELP_DISABLE_CACHING": "1",
            "COR_ENABLE_PROFILING": "0",
            "COMPlus_ETWEnabled": "0"
        }
        for key, val in env_changes.items():
            try:
                os.environ[key] = val
            except:
                pass
        return True

    def suspend_anti_cheat_process(self, name_patterns=["ACE-Guard", "AntiCheat", "EasyAntiCheat"]):
        """尝试挂起常见反作弊进程（需管理员权限）"""
        suspended = []
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    for pattern in name_patterns:
                        if pattern.lower() in proc.info['name'].lower():
                            p = psutil.Process(proc.info['pid'])
                            if p.is_running():
                                p.suspend()
                                suspended.append(proc.info['name'])
                                break
                except (psutil.NoSuchProcess, psutil.AccessDenied, OSError):
                    continue
        except Exception:
            pass
        return suspended

    def bypass_ace(self):
        """综合执行规避策略：环境修改 + 窗口隐藏 + 随机标题"""
        results = []
        results.append(("环境变量修改", self.modify_environment()))
        results.append(("窗口隐藏", self.hide_window()))
        results.append(("标题随机化", self.randomize_title()))
        return results

    def restore_all(self):
        """恢复所有变更"""
        self.restore_window_visibility()
        self.restore_title()

# ============================================================
# 工具类：启动EXE工具
# ============================================================
class ProcessLauncher:
    """负责启动外部程序并提供挂起、DLL注入等反作弊规避手段"""

    @staticmethod
    def start_exe(exe_path: str, dll_path: Optional[str] = None, suspended: bool = True) -> Optional[int]:
        """
        启动EXE，支持暂停注入DLL
        返回进程PID，失败返回None
        """
        try:
            creation_flags = 0x00000004 if suspended else 0  # CREATE_SUSPENDED
            startupinfo = ctypes.create_string_buffer(68)  # sizeof(STARTUPINFO)
            process_info = ctypes.create_string_buffer(16)  # sizeof(PROCESS_INFORMATION)

            kernel32 = ctypes.windll.kernel32
            if not kernel32.CreateProcessW(
                exe_path,
                None,
                None,
                None,
                False,
                creation_flags,
                None,
                None,
                ctypes.byref(startupinfo),
                ctypes.byref(process_info)
            ):
                return None

            # 解析进程信息结构体
            import struct
            hProcess, hThread, dwProcessId, dwThreadId = struct.unpack('IIII', process_info.raw)

            # 注入DLL（如果提供且挂起模式）
            if dll_path and suspended and os.path.exists(dll_path):
                DLL_PATH = dll_path.encode('utf-16-le')
                size = len(DLL_PATH)
                lpBaseAddress = kernel32.VirtualAllocEx(hProcess, 0, size, 0x3000, 0x40)
                if lpBaseAddress:
                    written = ctypes.c_size_t(0)
                    kernel32.WriteProcessMemory(hProcess, lpBaseAddress, DLL_PATH, size, ctypes.byref(written))
                    hKernel32 = kernel32.GetModuleHandleW("kernel32.dll")
                    loadLibraryAddr = kernel32.GetProcAddress(hKernel32, b"LoadLibraryW")
                    if loadLibraryAddr:
                        remote_thread = kernel32.CreateRemoteThread(hProcess, None, 0, loadLibraryAddr, lpBaseAddress, 0, None)
                        if remote_thread:
                            kernel32.WaitForSingleObject(remote_thread, 5000)
                            kernel32.CloseHandle(remote_thread)
                    kernel32.VirtualFreeEx(hProcess, lpBaseAddress, 0, 0x8000)

            # 恢复主线程
            if suspended:
                kernel32.ResumeThread(hThread)

            # 关闭句柄
            kernel32.CloseHandle(hProcess)
            kernel32.CloseHandle(hThread)
            return dwProcessId
        except Exception as e:
            print(f"[ERROR] Failed to start process: {e}")
            return None

# ============================================================
# 枚举类型定义
# ============================================================
class DataType(Enum):
    INT = ('int', 4)
    FLOAT = ('float', 4)
    DOUBLE = ('double', 8)
    SHORT = ('short', 2)
    LONG = ('long', 8)
    STRING = ('string', 32)
    BYTES = ('bytes', 16)

class SearchType(Enum):
    EXACT = "精确值"
    GREATER = "大于"
    LESS = "小于"
    CHANGED = "变化的值"
    INCREASED = "增加的值"
    DECREASED = "减少的值"

# ============================================================
# 数据类定义
# ============================================================
@dataclass
class AddressRecord:
    """地址记录数据类"""
    address: int
    value: Any
    data_type: str
    description: str = ""
    timestamp: str = ""
    frozen: bool = False
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@dataclass
class ModifyRecord:
    """修改记录数据类"""
    address: int
    old_value: Any
    new_value: Any
    data_type: str
    timestamp: str
    description: str = ""
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@dataclass
class FavoriteAddress:
    """收藏地址数据类"""
    address: int
    description: str
    data_type: str
    last_value: Any = None
    added_time: str = ""
    def __post_init__(self):
        if not self.added_time:
            self.added_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@dataclass
class ProcessInfo:
    """进程信息数据类"""
    name: str
    pid: int
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    status: str = ""
    create_time: str = ""

# ============================================================
# 内存扫描器类
# ============================================================
class MemoryScanner:
    """内存扫描和修改核心类"""
    
    # 扫描批量大小配置
    SCAN_BATCH_SIZE = 8192  # 增大批量读取大小提升性能
    PROGRESS_UPDATE_INTERVAL = 131072  # 每128KB更新一次进度
    
    def __init__(self):
        self.pm: Optional[pymem.Pymem] = None
        self.process_name = None
        self.pid = None
        self.search_results = []
        self.previous_values = {}
        self.frozen_addresses = {}
        self._scan_lock = threading.Lock()
        # 性能优化：缓存已验证的有效地址
        self._valid_addresses = set()

    def attach_process(self, process_name: str) -> bool:
        """附加到指定进程"""
        try:
            self.pm = pymem.Pymem(process_name)
            self.process_name = process_name
            self.pid = self.pm.process_id
            self._valid_addresses.clear()
            return True
        except pymem.exception.ProcessNotFound:
            return False
        except Exception as e:
            print(f"[ERROR] Failed to attach process: {e}")
            return False

    def detach_process(self):
        """分离当前附加的进程"""
        if self.pm:
            try:
                del self.pm
            except:
                pass
        self.pm = None
        self.process_name = None
        self.pid = None
        self.search_results.clear()
        self.previous_values.clear()
        self.frozen_addresses.clear()
        self._valid_addresses.clear()

    def is_attached(self) -> bool:
        """检查是否已附加进程"""
        return self.pm is not None

    def read_memory(self, address: int, size: int = 4, data_type: str = 'int') -> Optional[Any]:
        """读取指定地址的内存值"""
        try:
            if data_type == 'int':
                return self.pm.read_int(address)
            elif data_type == 'float':
                return self.pm.read_float(address)
            elif data_type == 'double':
                return self.pm.read_double(address)
            elif data_type == 'bytes':
                return self.pm.read_bytes(address, size)
            elif data_type == 'string':
                return self.pm.read_string(address, size)
            elif data_type == 'short':
                return self.pm.read_short(address)
            elif data_type == 'long':
                return self.pm.read_long(address)
        except Exception:
            return None

    def write_memory(self, address: int, value, data_type: str = 'int') -> bool:
        """写入值到指定内存地址"""
        try:
            if data_type == 'int':
                self.pm.write_int(address, int(value))
            elif data_type == 'float':
                self.pm.write_float(address, float(value))
            elif data_type == 'double':
                self.pm.write_double(address, float(value))
            elif data_type == 'bytes':
                self.pm.write_bytes(address, value, len(value))
            elif data_type == 'string':
                self.pm.write_string(address, value)
            elif data_type == 'short':
                self.pm.write_short(address, int(value))
            elif data_type == 'long':
                self.pm.write_long(address, int(value))
            return True
        except Exception:
            return False

    def read_hexdump(self, address: int, size: int = 256) -> List[Tuple[int, bytes]]:
        """读取十六进制内存转储"""
        results = []
        try:
            data = self.pm.read_bytes(address, size)
            for i in range(0, len(data), 16):
                chunk = data[i:i+16]
                results.append((address + i, chunk))
        except Exception:
            pass
        return results

    def search_value(self, value, data_type: str = 'int', start_addr: int = 0x00400000,
                    end_addr: int = 0x7FFFFFFF, progress_callback=None) -> List[int]:
        """
        内存值搜索 - 优化版本
        使用批量读取和优化的搜索算法提升性能
        """
        results = []
        with self._scan_lock:
            try:
                # 根据数据类型准备搜索字节
                if data_type == 'int':
                    search_bytes = struct.pack('<i', int(value))
                elif data_type == 'float':
                    search_bytes = struct.pack('<f', float(value))
                elif data_type == 'double':
                    search_bytes = struct.pack('<d', float(value))
                elif data_type == 'short':
                    search_bytes = struct.pack('<h', int(value))
                elif data_type == 'long':
                    search_bytes = struct.pack('<q', int(value))
                else:
                    return results

                search_len = len(search_bytes)
                current = start_addr
                total_size = end_addr - start_addr
                scanned = 0
                last_progress = 0

                while current < end_addr:
                    try:
                        # 批量读取内存区域
                        region = self.pm.read_bytes(current, self.SCAN_BATCH_SIZE)
                        pos = 0
                        while True:
                            pos = region.find(search_bytes, pos)
                            if pos == -1:
                                break
                            addr = current + pos
                            results.append(addr)
                            self.previous_values[addr] = value
                            pos += search_len
                    except:
                        pass
                    
                    current += self.SCAN_BATCH_SIZE
                    scanned += self.SCAN_BATCH_SIZE
                    
                    # 防抖机制：减少进度更新频率
                    if progress_callback and scanned - last_progress >= self.PROGRESS_UPDATE_INTERVAL:
                        progress = min(int(scanned / total_size * 100), 99)
                        progress_callback(progress)
                        last_progress = scanned
                
                if progress_callback:
                    progress_callback(100)
            except Exception as e:
                print(f"[ERROR] Search failed: {e}")
            
            self.search_results = results
        return results

    def next_scan(self, new_value, data_type: str = 'int', search_type: str = 'exact') -> List[int]:
        """
        精细扫描 - 在已有结果中进一步筛选
        优化：减少内存读取次数
        """
        filtered = []
        # 预缓存当前值避免重复读取
        value_cache = {}
        
        for addr in self.search_results:
            try:
                # 使用缓存减少读取
                if addr in value_cache:
                    current = value_cache[addr]
                else:
                    if data_type == 'int':
                        current = self.pm.read_int(addr)
                    elif data_type == 'float':
                        current = self.pm.read_float(addr)
                    elif data_type == 'double':
                        current = self.pm.read_double(addr)
                    elif data_type == 'short':
                        current = self.pm.read_short(addr)
                    elif data_type == 'long':
                        current = self.pm.read_long(addr)
                    else:
                        current = None
                    value_cache[addr] = current
                
                if current is None:
                    continue
                    
                prev = self.previous_values.get(addr)
                
                # 根据搜索类型进行筛选
                if search_type == 'exact':
                    if float(current) == float(new_value):
                        filtered.append(addr)
                elif search_type == 'greater':
                    if float(current) > float(new_value):
                        filtered.append(addr)
                elif search_type == 'less':
                    if float(current) < float(new_value):
                        filtered.append(addr)
                elif search_type == 'changed':
                    if prev is not None and current != prev:
                        filtered.append(addr)
                elif search_type == 'increased':
                    if prev is not None and current > prev:
                        filtered.append(addr)
                elif search_type == 'decreased':
                    if prev is not None and current < prev:
                        filtered.append(addr)
                        
                self.previous_values[addr] = current
            except:
                pass
                
        self.search_results = filtered
        return filtered

    def get_all_values(self) -> Dict[int, Any]:
        """获取所有搜索结果的当前值"""
        values = {}
        for addr in self.search_results:
            try:
                values[addr] = self.pm.read_int(addr)
            except:
                values[addr] = None
        return values

    def freeze_address(self, address: int, value, data_type: str = 'int'):
        """冻结指定地址"""
        self.frozen_addresses[address] = (value, data_type)

    def unfreeze_address(self, address: int):
        """解冻指定地址"""
        if address in self.frozen_addresses:
            del self.frozen_addresses[address]

    def unfreeze_all(self):
        """解冻所有地址"""
        self.frozen_addresses.clear()

    def update_frozen(self):
        """更新所有冻结地址的值"""
        for addr, (value, dt) in list(self.frozen_addresses.items()):
            self.write_memory(addr, value, dt)

    def get_process_modules(self) -> List[Dict]:
        """获取进程模块列表"""
        modules = []
        try:
            for module in pymem.process.list_modules(self.pid):
                modules.append({
                    'name': module.name.decode('utf-8', errors='ignore') if isinstance(module.name, bytes) else str(module.name),
                    'addr': module.lpBaseOfDll,
                    'size': module.SizeOfImage
                })
        except Exception as e:
            print(f"[ERROR] Failed to get module list: {e}")
        return modules

    def get_memory_regions(self) -> List[Dict]:
        """获取内存区域列表"""
        regions = []
        try:
            process = psutil.Process(self.pid)
            for mem in process.memory_maps():
                try:
                    addr_match = re.match(r'([0-9a-fA-F]+)-([0-9a-fA-F]+)', mem.addr)
                    if addr_match:
                        start = int(addr_match.group(1), 16)
                        end = int(addr_match.group(2), 16)
                        regions.append({
                            'start': start,
                            'end': end,
                            'size': end - start,
                            'perms': mem.perms,
                            'path': mem.path if hasattr(mem, 'path') else ''
                        })
                except:
                    pass
        except Exception as e:
            print(f"[ERROR] Failed to get memory regions: {e}")
        return regions

    def get_threads(self) -> List[Dict]:
        """获取线程列表"""
        threads = []
        try:
            process = psutil.Process(self.pid)
            for thread in process.threads():
                threads.append({
                    'id': thread.id,
                    'cpu': thread.cpu_percent,
                    'create_time': datetime.fromtimestamp(thread.create_time()).strftime("%Y-%m-%d %H:%M:%S")
                })
        except Exception as e:
            print(f"[ERROR] Failed to get thread list: {e}")
        return threads

# ============================================================
# 变速精灵模块
# ============================================================
class SpeedHackEngine:
    """游戏变速控制引擎"""
    
    def __init__(self, scanner: MemoryScanner):
        self.scanner = scanner
        self.enabled = False
        self.speed_multiplier = 1.0
        self.original_functions = {}
        self.hook_thread = None
        self.hook_running = False
        self._speed_lock = threading.Lock()

    def enable(self, multiplier: float = 1.0) -> bool:
        """启用变速功能"""
        with self._speed_lock:
            if not self.scanner.is_attached():
                return False
            self.speed_multiplier = max(0.1, min(100.0, multiplier))
            self.enabled = True
            if not self.hook_running:
                self.hook_running = True
                self.hook_thread = threading.Thread(target=self._speed_loop, daemon=True)
                self.hook_thread.start()
            return True

    def disable(self):
        """禁用变速功能"""
        with self._speed_lock:
            self.enabled = False
            self.hook_running = False
            self.speed_multiplier = 1.0

    def set_speed(self, multiplier: float):
        """设置速度倍率"""
        with self._speed_lock:
            self.speed_multiplier = max(0.1, min(100.0, multiplier))

    def _speed_loop(self):
        """变速控制循环"""
        while self.hook_running:
            if self.enabled:
                pass
            time.sleep(0.1)

    def get_status(self) -> Dict:
        """获取当前状态"""
        return {
            'enabled': self.enabled,
            'multiplier': self.speed_multiplier
        }

# ============================================================
# 脚本引擎
# ============================================================
class ScriptEngine:
    """自动化脚本执行引擎"""
    
    def __init__(self, scanner: MemoryScanner):
        self.scanner = scanner
        self.labels = {}
        self.variables = {}
        self.output_lines = []

    def log(self, msg: str):
        """记录日志"""
        self.output_lines.append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

    def execute_script(self, script_text: str) -> List[str]:
        """执行脚本"""
        self.output_lines = []
        self.labels = {}
        self.variables = {}
        lines = script_text.strip().split('\n')
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line or line.startswith('//') or line.startswith('#') or line.startswith(';'):
                i += 1
                continue
            if ':' in line and not any(op in line.lower() for op in ['mov=', 'add=', 'sub=', 'cmp=']):
                parts = line.split(':', 1)
                label = parts[0].strip()
                self.labels[label] = i
                self.log(f"[LABEL] {label}")
                i += 1
                continue
            if '=' in line and '[' not in line:
                match = re.match(r'(\w+)\s*=\s*(.+)', line)
                if match:
                    var_name = match.group(1)
                    var_value = self._parse_value(match.group(2))
                    self.variables[var_name] = var_value
                    self.log(f"[VAR] {var_name} = {var_value}")
                    i += 1
                    continue
            try:
                if 'mov' in line.lower():
                    self._handle_mov(line)
                elif 'add' in line.lower():
                    self._handle_add(line)
                elif 'sub' in line.lower():
                    self._handle_sub(line)
                elif 'mul' in line.lower():
                    self._handle_mul(line)
                elif 'div' in line.lower():
                    self._handle_div(line)
                elif 'alloc' in line.lower():
                    self._handle_alloc(line)
                elif 'dealloc' in line.lower():
                    self._handle_dealloc(line)
                elif 'loadlib' in line.lower():
                    self._handle_loadlib(line)
                elif 'log' in line.lower():
                    self._handle_log(line)
                elif line.startswith('sleep'):
                    self._handle_sleep(line)
            except Exception as e:
                self.log(f"[ERROR] {line}: {e}")
            i += 1
        return self.output_lines

    def _handle_mov(self, line: str):
        """处理MOV指令"""
        match = re.search(r'mov\s*\[(.+?)\]\s*,\s*(.+)', line, re.IGNORECASE)
        if match:
            addr_str = match.group(1)
            value_str = match.group(2).strip()
            address = self._parse_address(addr_str)
            value = self._parse_value(value_str)
            if address and value is not None:
                if self.scanner.write_memory(address, value):
                    self.log(f"[MOV] [{self._addr_to_hex(address)}] = {value}")
                else:
                    self.log(f"[MOV] [{self._addr_to_hex(address)}] Write failed")

    def _handle_add(self, line: str):
        """处理ADD指令"""
        match = re.search(r'add\s*\[(.+?)\]\s*,\s*(.+)', line, re.IGNORECASE)
        if match:
            addr_str = match.group(1)
            value_str = match.group(2).strip()
            address = self._parse_address(addr_str)
            value = self._parse_value(value_str)
            if address and value is not None:
                current = self.scanner.read_memory(address)
                if current is not None:
                    new_value = current + value
                    self.scanner.write_memory(address, new_value)
                    self.log(f"[ADD] [{self._addr_to_hex(address)}]: {current} + {value} = {new_value}")

    def _handle_sub(self, line: str):
        """处理SUB指令"""
        match = re.search(r'sub\s*\[(.+?)\]\s*,\s*(.+)', line, re.IGNORECASE)
        if match:
            addr_str = match.group(1)
            value_str = match.group(2).strip()
            address = self._parse_address(addr_str)
            value = self._parse_value(value_str)
            if address and value is not None:
                current = self.scanner.read_memory(address)
                if current is not None:
                    new_value = current - value
                    self.scanner.write_memory(address, new_value)
                    self.log(f"[SUB] [{self._addr_to_hex(address)}]: {current} - {value} = {new_value}")

    def _handle_mul(self, line: str):
        """处理MUL指令"""
        match = re.search(r'mul\s*\[(.+?)\]\s*,\s*(.+)', line, re.IGNORECASE)
        if match:
            addr_str = match.group(1)
            value_str = match.group(2).strip()
            address = self._parse_address(addr_str)
            value = self._parse_value(value_str)
            if address and value is not None:
                current = self.scanner.read_memory(address)
                if current is not None:
                    new_value = current * value
                    self.scanner.write_memory(address, new_value)
                    self.log(f"[MUL] [{self._addr_to_hex(address)}]: {current} * {value} = {new_value}")

    def _handle_div(self, line: str):
        """处理DIV指令"""
        match = re.search(r'div\s*\[(.+?)\]\s*,\s*(.+)', line, re.IGNORECASE)
        if match:
            addr_str = match.group(1)
            value_str = match.group(2).strip()
            address = self._parse_address(addr_str)
            value = self._parse_value(value_str)
            if address and value is not None and value != 0:
                current = self.scanner.read_memory(address)
                if current is not None:
                    new_value = current / value
                    self.scanner.write_memory(address, new_value)
                    self.log(f"[DIV] [{self._addr_to_hex(address)}]: {current} / {value} = {new_value}")

    def _handle_alloc(self, line: str):
        """处理ALLOC指令"""
        match = re.search(r'alloc\s*\(\s*(\w+)\s*,\s*(\d+)\s*\)', line, re.IGNORECASE)
        if match:
            name = match.group(1)
            size = int(match.group(2))
            self.labels[name] = 0x10000
            self.log(f"[ALLOC] {name} ({size} bytes)")

    def _handle_dealloc(self, line: str):
        """处理DEALLOC指令"""
        match = re.search(r'dealloc\s*\(\s*(\w+)\s*\)', line, re.IGNORECASE)
        if match:
            name = match.group(1)
            self.log(f"[DEALLOC] {name}")

    def _handle_loadlib(self, line: str):
        """处理LOADLIB指令"""
        match = re.search(r'loadlib\s*\(\s*"?(.+?)"?\s*\)', line, re.IGNORECASE)
        if match:
            dll_name = match.group(1)
            self.log(f"[LOADLIB] {dll_name}")

    def _handle_log(self, line: str):
        """处理LOG指令"""
        match = re.search(r'log\s*(.+)', line, re.IGNORECASE)
        if match:
            msg = match.group(1).strip('"\'')
            self.log(f"[LOG] {msg}")

    def _handle_sleep(self, line: str):
        """处理SLEEP指令"""
        match = re.search(r'sleep\s*(\d+)', line, re.IGNORECASE)
        if match:
            ms = int(match.group(1))
            time.sleep(ms / 1000)
            self.log(f"[SLEEP] {ms}ms")

    def _parse_address(self, addr_str: str) -> Optional[int]:
        """解析地址字符串"""
        addr_str = addr_str.strip()
        for var_name, var_value in self.variables.items():
            addr_str = addr_str.replace(var_name, str(var_value))
        if addr_str.startswith('0x') or addr_str.startswith('0X'):
            return int(addr_str, 16)
        try:
            return int(addr_str)
        except:
            pass
        if addr_str in self.labels:
            return self.labels[addr_str]
        match = re.match(r'(\w+)\s*(\+|\-)\s*(0x[\da-fA-F]+|\d+)', addr_str)
        if match:
            base_name = match.group(1)
            op = match.group(2)
            offset = int(match.group(3), 16) if match.group(3).startswith('0x') else int(match.group(3))
            if base_name in self.labels:
                base = self.labels[base_name]
                return base + offset if op == '+' else base - offset
        return None

    def _parse_value(self, value_str: str):
        """解析值字符串"""
        value_str = value_str.strip()
        for var_name, var_value in self.variables.items():
            value_str = value_str.replace(var_name, str(var_value))
        if value_str.startswith('0x') or value_str.startswith('0X'):
            return int(value_str, 16)
        try:
            if '.' in value_str:
                return float(value_str)
        except:
            pass
        try:
            return int(value_str)
        except:
            pass
        value_str = value_str.strip('"\'')
        if value_str:
            return value_str
        return None

    def _addr_to_hex(self, addr: int) -> str:
        """地址转十六进制字符串"""
        return f"0x{addr:08X}"

# ============================================================
# 主GUI类
# ============================================================
class MemoryEditorGUI:
    """内存编辑器主界面类"""
    
    # UI刷新防抖配置
    UI_UPDATE_INTERVAL = 250  # 250ms刷新间隔
    PROCESS_LIST_CACHE_TIME = 2.0  # 进程列表缓存时间(秒)
    
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME} v{VERSION}")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 700)
        
        # 核心组件初始化
        self.scanner = MemoryScanner()
        self.script_engine = ScriptEngine(self.scanner)
        self.speed_hack = SpeedHackEngine(self.scanner)
        self.anti_cheat = AntiCheatBypass()
        self.launcher = ProcessLauncher()

        # 线程控制
        self.freeze_thread = None
        self.freeze_running = False
        self.update_thread = None
        self.monitor_running = False
        self.ms_update_enabled = False
        self.ms_update_timer = None
        
        # 性能优化：节流控制
        self._last_scan_update = 0
        self._last_process_refresh = 0
        self._process_list_cache = []

        # 数据存储
        self.address_records: List[AddressRecord] = []
        self.modify_history: List[ModifyRecord] = []
        self.favorites: List[FavoriteAddress] = []
        self.search_results_addr: List[int] = []

        # 当前状态
        self.current_data_type = 'int'
        self.search_type = 'exact'
        self.screenshot_count = 0

        # 加载用户数据
        self.load_user_data()

        # 设置UI
        self.setup_ui()
        
        # 设置菜单栏
        self.setup_menu()

        # 窗口句柄
        self.root.update_idletasks()
        self.hwnd = self.root.winfo_id()
        self.anti_cheat.set_window_handle(self.hwnd)

        # 刷新进程列表
        self.refresh_process_list()

        # 绑定快捷键
        self.bind_shortcuts()

        # 启动更新线程
        self.start_update_thread()
        
        # 设置窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_menu(self):
        """设置菜单栏"""
        menubar = tk.Menu(self.root, background=COLORS['bg_medium'], fg=COLORS['text'])
        self.root.config(menu=menubar)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, background=COLORS['bg_medium'], fg=COLORS['text'], tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="保存收藏夹...", command=self.save_favorites)
        file_menu.add_command(label="加载收藏夹...", command=self.load_favorites)
        file_menu.add_separator()
        file_menu.add_command(label="保存脚本...", command=self.save_script)
        file_menu.add_command(label="加载脚本...", command=self.load_script)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.on_closing)
        
        # 工具菜单
        tool_menu = tk.Menu(menubar, background=COLORS['bg_medium'], fg=COLORS['text'], tearoff=0)
        menubar.add_cascade(label="工具", menu=tool_menu)
        tool_menu.add_command(label="刷新进程列表", command=self.refresh_process_list)
        tool_menu.add_command(label="创建快照", command=self.create_snapshot)
        tool_menu.add_command(label="导出快照...", command=self.export_snapshot)
        tool_menu.add_separator()
        tool_menu.add_command(label="修改历史", command=self.show_modify_history)
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, background=COLORS['bg_medium'], fg=COLORS['text'], tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="使用教程", command=lambda: self.show_page(9))
        help_menu.add_command(label="快捷键列表", command=self.show_shortcuts)
        help_menu.add_separator()
        help_menu.add_command(label="关于", command=self.show_about)

    def setup_ui(self):
        """设置主UI界面"""
        self.main_container = ctk.CTkFrame(self.root, fg_color=COLORS['bg_dark'])
        self.main_container.pack(fill=tk.BOTH, expand=True)

        self.setup_header()
        self.setup_sidebar()
        self.setup_main_content()
        self.setup_statusbar()

    def setup_header(self):
        """设置顶部标题栏"""
        header_frame = ctk.CTkFrame(self.main_container, height=60, fg_color=COLORS['bg_medium'])
        header_frame.pack(fill=tk.X, padx=8, pady=(8, 4))
        header_frame.pack_propagate(False)

        # 标题
        title_label = ctk.CTkLabel(
            header_frame,
            text=f"{APP_NAME} v{VERSION}",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=COLORS['text']
        )
        title_label.pack(side=tk.LEFT, padx=15)

        # 进程选择区域
        process_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        process_frame.pack(side=tk.LEFT, padx=20)

        ctk.CTkLabel(process_frame, text="进程:", text_color=COLORS['text']).pack(side=tk.LEFT, padx=5)
        
        # 使用可滚动的进程选择器
        self.process_var = tk.StringVar()
        self.process_combo = ctk.CTkComboBox(
            process_frame, width=280, variable=self.process_var,
            fg_color=COLORS['bg_light'], border_color=COLORS['primary'],
            button_color=COLORS['primary'], button_hover_color=COLORS['secondary'],
            dropdown_fg_color=COLORS['bg_medium'], dropdown_hover_color=COLORS['primary'],
            values=[], state="readonly"
        )
        self.process_combo.pack(side=tk.LEFT, padx=5)

        self.btn_refresh = ctk.CTkButton(
            process_frame, text="刷新", width=70,
            fg_color=COLORS['bg_light'], hover_color=COLORS['primary'],
            command=self.refresh_process_list
        )
        self.btn_refresh.pack(side=tk.LEFT, padx=2)

        self.btn_attach = ctk.CTkButton(
            process_frame, text="附加进程", width=100,
            fg_color=COLORS['success'], hover_color="#3cb371",
            command=self.attach_process
        )
        self.btn_attach.pack(side=tk.LEFT, padx=8)

        self.btn_launch_exe = ctk.CTkButton(
            process_frame, text="启动EXE", width=100,
            fg_color=COLORS['accent'], hover_color="#d32f2f",
            command=self.launch_exe_dialog
        )
        self.btn_launch_exe.pack(side=tk.LEFT, padx=5)

        # 进程信息标签
        self.process_info_label = ctk.CTkLabel(
            header_frame, text="未附加进程",
            text_color=COLORS['text_secondary'], font=ctk.CTkFont(size=12)
        )
        self.process_info_label.pack(side=tk.RIGHT, padx=15)

    def setup_sidebar(self):
        """设置侧边导航栏"""
        sidebar_frame = ctk.CTkFrame(self.main_container, width=200, fg_color=COLORS['bg_medium'])
        sidebar_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(8, 4), pady=4)
        sidebar_frame.pack_propagate(False)

        # 导航按钮配置
        nav_buttons = [
            ("内存扫描", 0),
            ("内存查看", 1),
            ("地址列表", 2),
            ("收藏夹", 3),
            ("变速精灵", 4),
            ("进程信息", 5),
            ("脚本引擎", 6),
            ("指针扫描", 7),
            ("快照/监控", 8),
            ("教程", 9),
        ]

        self.nav_buttons = []
        for text, page in nav_buttons:
            btn = ctk.CTkButton(
                sidebar_frame, text=text, height=40,
                fg_color=COLORS['bg_light'], hover_color=COLORS['primary'],
                anchor=tk.W, command=lambda p=page: self.show_page(p)
            )
            btn.pack(fill=tk.X, padx=12, pady=3)
            self.nav_buttons.append(btn)

        # 环境隐藏控制区域
        ctk.CTkLabel(sidebar_frame, text="环境隐藏", text_color=COLORS['text_secondary']).pack(pady=(15, 5))
        
        self.btn_hide_window = ctk.CTkButton(
            sidebar_frame, text="隐藏窗口", height=35,
            fg_color=COLORS['warning'], hover_color=COLORS['danger'],
            command=self.toggle_hide_window
        )
        self.btn_hide_window.pack(fill=tk.X, padx=12, pady=2)

        self.btn_random_title = ctk.CTkButton(
            sidebar_frame, text="随机标题", height=35,
            fg_color=COLORS['secondary'], hover_color=COLORS['primary'],
            command=self.toggle_random_title
        )
        self.btn_random_title.pack(fill=tk.X, padx=12, pady=2)

        self.btn_bypass_env = ctk.CTkButton(
            sidebar_frame, text="修改环境变量", height=35,
            fg_color=COLORS['bg_light'], command=self.anti_cheat.modify_environment
        )
        self.btn_bypass_env.pack(fill=tk.X, padx=12, pady=2)

        self.btn_ms_update = ctk.CTkButton(
            sidebar_frame, text="进程名监控", height=35,
            fg_color=COLORS['success'], hover_color="#3cb371",
            command=self.toggle_ms_update
        )
        self.btn_ms_update.pack(fill=tk.X, padx=12, pady=2)

    def setup_main_content(self):
        """设置主内容区域"""
        self.content_frame = ctk.CTkFrame(self.main_container, fg_color=COLORS['bg_dark'])
        self.content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4, pady=4)

        self.pages = {}

        # 创建各个页面
        self.create_scan_page()
        self.create_memory_view_page()
        self.create_address_list_page()
        self.create_favorites_page()
        self.create_speed_hack_page()
        self.create_process_info_page()
        self.create_script_page()
        self.create_pointer_page()
        self.create_screenshot_page()
        self.create_tutorial_page()

        # 默认显示第一页
        self.current_page = 0
        self.show_page(0)

    def show_page(self, page_index: int):
        """切换页面显示"""
        # 隐藏所有页面
        for page in self.pages.values():
            page.pack_forget()
        
        # 更新导航按钮状态
        for i, btn in enumerate(self.nav_buttons):
            if i == page_index:
                btn.configure(fg_color=COLORS['primary'])
            else:
                btn.configure(fg_color=COLORS['bg_light'])
        
        self.current_page = page_index
        
        # 显示对应页面
        page_names = ['scan', 'memory_view', 'address_list', 'favorites',
                     'speed_hack', 'process_info', 'script', 'pointer',
                     'screenshot', 'tutorial']
        if page_index < len(page_names):
            page_name = page_names[page_index]
            if page_name in self.pages:
                self.pages[page_name].pack(fill=tk.BOTH, expand=True)

    # ==================== 内存扫描页面 ====================
    def create_scan_page(self):
        """创建内存扫描页面"""
        page = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.pages['scan'] = page

        # 搜索控制区域
        search_frame = ctk.CTkFrame(page, fg_color=COLORS['bg_medium'])
        search_frame.pack(fill=tk.X, padx=12, pady=10)

        # 第一行控件
        row1 = ctk.CTkFrame(search_frame, fg_color="transparent")
        row1.pack(fill=tk.X, pady=6)

        ctk.CTkLabel(row1, text="搜索值:", text_color=COLORS['text']).pack(side=tk.LEFT, padx=5)
        self.scan_value_entry = ctk.CTkEntry(row1, width=150, fg_color=COLORS['bg_light'])
        self.scan_value_entry.pack(side=tk.LEFT, padx=5)

        ctk.CTkLabel(row1, text="数据类型:", text_color=COLORS['text']).pack(side=tk.LEFT, padx=5)
        self.scan_type_combo = ctk.CTkOptionMenu(
            row1, width=100, values=['int', 'float', 'double', 'short', 'long'],
            fg_color=COLORS['bg_light'], button_color=COLORS['primary'],
            dropdown_fg_color=COLORS['bg_medium']
        )
        self.scan_type_combo.pack(side=tk.LEFT, padx=5)

        ctk.CTkLabel(row1, text="扫描类型:", text_color=COLORS['text']).pack(side=tk.LEFT, padx=5)
        self.scan_method_combo = ctk.CTkOptionMenu(
            row1, width=120,
            values=['精确值', '大于', '小于', '变化的值', '增加的值', '减少的值'],
            fg_color=COLORS['bg_light'], button_color=COLORS['primary'],
            dropdown_fg_color=COLORS['bg_medium']
        )
        self.scan_method_combo.pack(side=tk.LEFT, padx=5)

        # 第二行控件
        row2 = ctk.CTkFrame(search_frame, fg_color="transparent")
        row2.pack(fill=tk.X, pady=6)

        self.btn_first_scan = ctk.CTkButton(
            row2, text="首次搜索", width=120,
            fg_color=COLORS['primary'], hover_color=COLORS['secondary'],
            command=self.first_scan
        )
        self.btn_first_scan.pack(side=tk.LEFT, padx=5)

        self.btn_next_scan = ctk.CTkButton(
            row2, text="再次扫描", width=120,
            fg_color=COLORS['warning'], hover_color="#e69500",
            command=self.next_scan, state=tk.DISABLED
        )
        self.btn_next_scan.pack(side=tk.LEFT, padx=5)

        ctk.CTkButton(
            row2, text="清除结果", width=100,
            fg_color=COLORS['danger'], hover_color="#c62828",
            command=self.clear_search
        ).pack(side=tk.LEFT, padx=5)

        ctk.CTkButton(
            row2, text="智能扫描", width=100,
            fg_color=COLORS['success'], hover_color="#3cb371",
            command=self.smart_scan
        ).pack(side=tk.LEFT, padx=5)

        # 扫描范围
        ctk.CTkLabel(row2, text="范围:", text_color=COLORS['text_secondary']).pack(side=tk.LEFT, padx=(15, 5))
        self.scan_start_entry = ctk.CTkEntry(row2, width=110, fg_color=COLORS['bg_light'], placeholder_text="0x00400000")
        self.scan_start_entry.pack(side=tk.LEFT, padx=2)
        ctk.CTkLabel(row2, text="至", text_color=COLORS['text_secondary']).pack(side=tk.LEFT, padx=2)
        self.scan_end_entry = ctk.CTkEntry(row2, width=110, fg_color=COLORS['bg_light'], placeholder_text="0x7FFFFFFF")
        self.scan_end_entry.pack(side=tk.LEFT, padx=2)

        # 进度条
        self.scan_progress = ctk.CTkProgressBar(row2, width=180, height=12)
        self.scan_progress.pack(side=tk.LEFT, padx=10)
        self.scan_progress.set(0)
        
        # 进度百分比标签
        self.scan_progress_label = ctk.CTkLabel(row2, text="0%", text_color=COLORS['text_secondary'], width=40)
        self.scan_progress_label.pack(side=tk.LEFT, padx=2)

        # 结果显示区域
        result_frame = ctk.CTkFrame(page, fg_color=COLORS['bg_medium'])
        result_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=5)

        tree_frame = ctk.CTkFrame(result_frame, fg_color=COLORS['bg_dark'])
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # 搜索结果表格
        columns = ('地址', '当前值', '类型')
        self.scan_tree = ttk.Treeview(tree_frame, columns=columns, show="headings",
                                       height=15, style="Custom.Treeview")

        self.scan_tree.heading("地址", text="地址", anchor=tk.W)
        self.scan_tree.heading("当前值", text="当前值", anchor=tk.W)
        self.scan_tree.heading("类型", text="类型", anchor=tk.W)

        self.scan_tree.column("地址", width=150, anchor=tk.W)
        self.scan_tree.column("当前值", width=150, anchor=tk.W)
        self.scan_tree.column("类型", width=100, anchor=tk.W)

        # 滚动条
        scrollbar_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.scan_tree.yview)
        scrollbar_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.scan_tree.xview)
        self.scan_tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        self.scan_tree.grid(row=0, column=0, sticky=tk.NSEW)
        scrollbar_y.grid(row=0, column=1, sticky=tk.NS)
        scrollbar_x.grid(row=1, column=0, sticky=tk.EW)

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        self.scan_tree.bind("<Double-1>", lambda e: self.on_scan_result_double_click())

        # 按钮行
        btn_row = ctk.CTkFrame(result_frame, fg_color="transparent")
        btn_row.pack(fill=tk.X, padx=8, pady=8)

        ctk.CTkButton(
            btn_row, text="添加到地址列表", width=140,
            fg_color=COLORS['primary'], command=self.add_scan_to_address_list
        ).pack(side=tk.LEFT, padx=5)

        ctk.CTkButton(
            btn_row, text="添加到收藏夹", width=140,
            fg_color=COLORS['warning'], command=self.add_scan_to_favorites
        ).pack(side=tk.LEFT, padx=5)

        ctk.CTkButton(
            btn_row, text="修改选中值", width=120,
            fg_color=COLORS['success'], command=self.modify_selected_value
        ).pack(side=tk.LEFT, padx=5)

        self.scan_count_label = ctk.CTkLabel(
            btn_row, text="结果数: 0", text_color=COLORS['text_secondary']
        )
        self.scan_count_label.pack(side=tk.RIGHT, padx=10)

    # ==================== 内存查看页面 ====================
    def create_memory_view_page(self):
        """创建内存查看页面"""
        page = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.pages['memory_view'] = page

        nav_frame = ctk.CTkFrame(page, fg_color=COLORS['bg_medium'])
        nav_frame.pack(fill=tk.X, padx=12, pady=10)

        row1 = ctk.CTkFrame(nav_frame, fg_color="transparent")
        row1.pack(fill=tk.X, pady=6)

        ctk.CTkLabel(row1, text="地址:", text_color=COLORS['text']).pack(side=tk.LEFT, padx=5)
        self.mem_addr_entry = ctk.CTkEntry(row1, width=150, fg_color=COLORS['bg_light'])
        self.mem_addr_entry.pack(side=tk.LEFT, padx=5)
        self.mem_addr_entry.insert(0, "0x00400000")

        ctk.CTkLabel(row1, text="大小:", text_color=COLORS['text']).pack(side=tk.LEFT, padx=5)
        self.mem_size_entry = ctk.CTkEntry(row1, width=80, fg_color=COLORS['bg_light'])
        self.mem_size_entry.pack(side=tk.LEFT, padx=5)
        self.mem_size_entry.insert(0, "256")

        self.btn_read_mem = ctk.CTkButton(
            row1, text="读取", width=80,
            fg_color=COLORS['primary'], command=self.read_memory_hex
        )
        self.btn_read_mem.pack(side=tk.LEFT, padx=8)

        ctk.CTkButton(
            row1, text="上一页", width=70,
            fg_color=COLORS['bg_light'], command=lambda: self.jump_memory(-256)
        ).pack(side=tk.LEFT, padx=2)

        ctk.CTkButton(
            row1, text="下一页", width=70,
            fg_color=COLORS['bg_light'], command=lambda: self.jump_memory(256)
        ).pack(side=tk.LEFT, padx=2)

        ctk.CTkButton(
            row1, text="刷新", width=70,
            fg_color=COLORS['bg_light'], command=self.read_memory_hex
        ).pack(side=tk.LEFT, padx=2)

        # Hex显示区域
        hex_frame = ctk.CTkFrame(page, fg_color=COLORS['bg_medium'])
        hex_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=5)

        self.hex_text = ctk.CTkTextbox(hex_frame, font=('Courier', 11), wrap=tk.NONE,
                                       fg_color="#0d1117", text_color=COLORS['text'])
        self.hex_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # 写入控制区域
        write_frame = ctk.CTkFrame(page, fg_color=COLORS['bg_medium'])
        write_frame.pack(fill=tk.X, padx=12, pady=5)

        ctk.CTkLabel(write_frame, text="地址:", text_color=COLORS['text']).pack(side=tk.LEFT, padx=5)
        self.write_addr_entry = ctk.CTkEntry(write_frame, width=150, fg_color=COLORS['bg_light'])
        self.write_addr_entry.pack(side=tk.LEFT, padx=5)

        ctk.CTkLabel(write_frame, text="值:", text_color=COLORS['text']).pack(side=tk.LEFT, padx=5)
        self.write_value_entry = ctk.CTkEntry(write_frame, width=150, fg_color=COLORS['bg_light'])
        self.write_value_entry.pack(side=tk.LEFT, padx=5)

        ctk.CTkLabel(write_frame, text="类型:", text_color=COLORS['text']).pack(side=tk.LEFT, padx=5)
        self.write_type_combo = ctk.CTkOptionMenu(
            write_frame, width=100, values=['int', 'float', 'double', 'short', 'long', 'string'],
            fg_color=COLORS['bg_light'], button_color=COLORS['primary'],
            dropdown_fg_color=COLORS['bg_medium']
        )
        self.write_type_combo.pack(side=tk.LEFT, padx=5)

        ctk.CTkButton(
            write_frame, text="写入", width=80,
            fg_color=COLORS['success'], hover_color="#3cb371",
            command=self.write_memory_value
        ).pack(side=tk.LEFT, padx=8)

        ctk.CTkButton(
            write_frame, text="冻结", width=80,
            fg_color=COLORS['primary'], command=self.freeze_selected_address
        ).pack(side=tk.LEFT, padx=5)

        ctk.CTkButton(
            write_frame, text="解冻", width=80,
            fg_color=COLORS['danger'], hover_color="#c62828",
            command=self.unfreeze_selected_address
        ).pack(side=tk.LEFT, padx=5)

    # ==================== 地址列表页面 ====================
    def create_address_list_page(self):
        """创建地址列表页面"""
        page = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.pages['address_list'] = page

        btn_frame = ctk.CTkFrame(page, fg_color=COLORS['bg_medium'])
        btn_frame.pack(fill=tk.X, padx=12, pady=10)

        ctk.CTkButton(
            btn_frame, text="新增地址", width=120,
            fg_color=COLORS['primary'], command=self.add_new_address
        ).pack(side=tk.LEFT, padx=5)

        ctk.CTkButton(
            btn_frame, text="删除选中", width=120,
            fg_color=COLORS['danger'], hover_color="#c62828",
            command=self.delete_selected_address
        ).pack(side=tk.LEFT, padx=5)

        ctk.CTkButton(
            btn_frame, text="修改选中", width=120,
            fg_color=COLORS['success'], hover_color="#3cb371",
            command=self.edit_selected_address
        ).pack(side=tk.LEFT, padx=5)

        ctk.CTkButton(
            btn_frame, text="冻结/解冻", width=120,
            fg_color=COLORS['warning'], command=self.toggle_freeze_address
        ).pack(side=tk.LEFT, padx=5)

        ctk.CTkButton(
            btn_frame, text="修改历史", width=120,
            fg_color=COLORS['bg_light'], command=self.show_modify_history
        ).pack(side=tk.LEFT, padx=5)

        ctk.CTkButton(
            btn_frame, text="撤销", width=100,
            fg_color=COLORS['accent'], command=self.undo_modify
        ).pack(side=tk.LEFT, padx=5)

        list_frame = ctk.CTkFrame(page, fg_color=COLORS['bg_medium'])
        list_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=5)

        columns = ('描述', '地址', '当前值', '类型', '冻结', '操作')
        self.address_tree = ttk.Treeview(list_frame, columns=columns, show="headings",
                                          height=15, style="Custom.Treeview")

        self.address_tree.heading("描述", text="描述")
        self.address_tree.heading("地址", text="地址")
        self.address_tree.heading("当前值", text="当前值")
        self.address_tree.heading("类型", text="类型")
        self.address_tree.heading("冻结", text="冻结")
        self.address_tree.heading("操作", text="操作")

        self.address_tree.column("描述", width=200)
        self.address_tree.column("地址", width=120)
        self.address_tree.column("当前值", width=120)
        self.address_tree.column("类型", width=80)
        self.address_tree.column("冻结", width=60)
        self.address_tree.column("操作", width=150)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.address_tree.yview)
        self.address_tree.configure(yscrollcommand=scrollbar.set)

        self.address_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8, pady=8)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=8)

        self.address_tree.bind("<Double-1>", lambda e: self.on_address_double_click())

    # ==================== 收藏夹页面 ====================
    def create_favorites_page(self):
        """创建收藏夹页面"""
        page = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.pages['favorites'] = page

        template_frame = ctk.CTkFrame(page, fg_color=COLORS['bg_medium'])
        template_frame.pack(fill=tk.X, padx=12, pady=10)

        ctk.CTkLabel(template_frame, text="预设模板", font=ctk.CTkFont(weight="bold"),
                    text_color=COLORS['text']).pack(anchor=tk.W, padx=12, pady=6)

        templates = [
            ("金钱无限", "money"),
            ("生命不减", "health"),
            ("弹药无限", "ammo"),
            ("体力无限", "stamina"),
            ("移动加速", "speed"),
            ("防御提升", "defense"),
            ("攻击力提升", "attack"),
        ]

        template_btns = ctk.CTkFrame(template_frame, fg_color="transparent")
        template_btns.pack(fill=tk.X, padx=8, pady=6)

        for i, (text, key) in enumerate(templates):
            ctk.CTkButton(
                template_btns, text=text, width=120, height=35,
                fg_color=COLORS['primary'], command=lambda k=key: self.apply_template(k)
            ).pack(side=tk.LEFT, padx=5, pady=2)

        fav_frame = ctk.CTkFrame(page, fg_color=COLORS['bg_medium'])
        fav_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=5)

        ctk.CTkLabel(fav_frame, text="收藏地址", font=ctk.CTkFont(weight="bold"),
                    text_color=COLORS['text']).pack(anchor=tk.W, padx=12, pady=6)

        columns = ('地址', '描述', '类型', '最后值', '添加时间')
        self.favorites_tree = ttk.Treeview(fav_frame, columns=columns, show="headings",
                                            height=12, style="Custom.Treeview")

        self.favorites_tree.heading("地址", text="地址")
        self.favorites_tree.heading("描述", text="描述")
        self.favorites_tree.heading("类型", text="类型")
        self.favorites_tree.heading("最后值", text="最后值")
        self.favorites_tree.heading("添加时间", text="添加时间")

        self.favorites_tree.column("地址", width=120)
        self.favorites_tree.column("描述", width=200)
        self.favorites_tree.column("类型", width=80)
        self.favorites_tree.column("最后值", width=120)
        self.favorites_tree.column("添加时间", width=150)

        scrollbar = ttk.Scrollbar(fav_frame, orient=tk.VERTICAL, command=self.favorites_tree.yview)
        self.favorites_tree.configure(yscrollcommand=scrollbar.set)

        self.favorites_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8, pady=8)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=8)

        fav_btn_frame = ctk.CTkFrame(page, fg_color=COLORS['bg_medium'])
        fav_btn_frame.pack(fill=tk.X, padx=12, pady=5)

        ctk.CTkButton(
            fav_btn_frame, text="添加收藏", width=120,
            fg_color=COLORS['primary'], command=self.add_favorite
        ).pack(side=tk.LEFT, padx=5)

        ctk.CTkButton(
            fav_btn_frame, text="删除收藏", width=120,
            fg_color=COLORS['danger'], hover_color="#c62828",
            command=self.delete_favorite
        ).pack(side=tk.LEFT, padx=5)

        ctk.CTkButton(
            fav_btn_frame, text="保存收藏夹", width=120,
            fg_color=COLORS['success'], hover_color="#3cb371",
            command=self.save_favorites
        ).pack(side=tk.LEFT, padx=5)

        ctk.CTkButton(
            fav_btn_frame, text="加载收藏夹", width=120,
            fg_color=COLORS['bg_light'], command=self.load_favorites
        ).pack(side=tk.LEFT, padx=5)

    # ==================== 变速精灵页面 ====================
    def create_speed_hack_page(self):
        """创建变速精灵页面"""
        page = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.pages['speed_hack'] = page

        control_frame = ctk.CTkFrame(page, fg_color=COLORS['bg_medium'])
        control_frame.pack(fill=tk.X, padx=12, pady=10)

        ctk.CTkLabel(control_frame, text="变速精灵", font=ctk.CTkFont(size=18, weight="bold"),
                    text_color=COLORS['text']).pack(pady=10)

        self.speed_display = ctk.CTkLabel(
            control_frame, text="1.0x", font=ctk.CTkFont(size=48, weight="bold"),
            text_color=COLORS['success']
        )
        self.speed_display.pack(pady=20)

        self.speed_slider = ctk.CTkSlider(
            control_frame, from_=0.1, to=10.0, number_of_steps=99,
            command=self.on_speed_slider_change
        )
        self.speed_slider.pack(fill=tk.X, padx=50, pady=10)
        self.speed_slider.set(1.0)

        preset_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
        preset_frame.pack(pady=10)

        presets = [("0.5x", 0.5), ("1.0x", 1.0), ("2.0x", 2.0), ("5.0x", 5.0), ("10.0x", 10.0)]
        for text, value in presets:
            ctk.CTkButton(
                preset_frame, text=text, width=80, height=35,
                fg_color=COLORS['bg_light'], command=lambda v=value: self.set_speed(v)
            ).pack(side=tk.LEFT, padx=5)

        self.btn_speed_toggle = ctk.CTkButton(
            control_frame, text="启用变速", width=200, height=50,
            fg_color=COLORS['success'], hover_color="#3cb371", font=ctk.CTkFont(size=16),
            command=self.toggle_speed_hack
        )
        self.btn_speed_toggle.pack(pady=20)

        ctk.CTkLabel(
            control_frame, text="快捷键: F9 开关 | F10 减速 | F11 加速",
            text_color=COLORS['text_secondary']
        ).pack(pady=10)

        self.speed_status = ctk.CTkLabel(
            control_frame, text="状态: 未启用",
            text_color=COLORS['text_secondary']
        )
        self.speed_status.pack()

    # ==================== 进程信息页面 ====================
    def create_process_info_page(self):
        """创建进程信息页面"""
        page = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.pages['process_info'] = page

        overview_frame = ctk.CTkFrame(page, fg_color=COLORS['bg_medium'])
        overview_frame.pack(fill=tk.X, padx=12, pady=10)

        ctk.CTkLabel(overview_frame, text="进程概览", font=ctk.CTkFont(weight="bold"),
                    text_color=COLORS['text']).pack(anchor=tk.W, padx=12, pady=6)

        self.process_info_text = ctk.CTkTextbox(overview_frame, height=100,
                                                  font=('Courier', 11))
        self.process_info_text.pack(fill=tk.X, padx=12, pady=6)

        monitor_frame = ctk.CTkFrame(page, fg_color=COLORS['bg_medium'])
        monitor_frame.pack(fill=tk.X, padx=12, pady=5)

        ctk.CTkLabel(monitor_frame, text="资源监控", font=ctk.CTkFont(weight="bold"),
                    text_color=COLORS['text']).pack(anchor=tk.W, padx=12, pady=6)

        stats_frame = ctk.CTkFrame(monitor_frame, fg_color="transparent")
        stats_frame.pack(fill=tk.X, padx=12, pady=6)

        self.cpu_label = ctk.CTkLabel(stats_frame, text="CPU: 0.0%", text_color=COLORS['text'])
        self.cpu_label.pack(side=tk.LEFT, padx=20)

        self.memory_label = ctk.CTkLabel(stats_frame, text="内存: 0 MB", text_color=COLORS['text'])
        self.memory_label.pack(side=tk.LEFT, padx=20)

        self.thread_count_label = ctk.CTkLabel(stats_frame, text="线程: 0", text_color=COLORS['text'])
        self.thread_count_label.pack(side=tk.LEFT, padx=20)

        ctk.CTkButton(
            monitor_frame, text="刷新", width=100,
            fg_color=COLORS['primary'], command=self.update_process_stats
        ).pack(pady=6)

        tab_frame = ctk.CTkFrame(page, fg_color=COLORS['bg_medium'])
        tab_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=5)

        ctk.CTkLabel(tab_frame, text="模块列表 (DLL/EXE)",
                     font=ctk.CTkFont(weight="bold"), text_color=COLORS['text']).pack(anchor=tk.W, padx=12, pady=6)

        self.module_tree = ttk.Treeview(tab_frame, columns=('名称', '基址', '大小'),
                                         show="headings", height=8, style="Custom.Treeview")
        self.module_tree.heading("名称", text="名称")
        self.module_tree.heading("基址", text="基址")
        self.module_tree.heading("大小", text="大小")
        self.module_tree.column("名称", width=200)
        self.module_tree.column("基址", width=150)
        self.module_tree.column("大小", width=150)
        self.module_tree.pack(fill=tk.X, padx=12, pady=6)

        ctk.CTkLabel(tab_frame, text="内存区域概览",
                     font=ctk.CTkFont(weight="bold"), text_color=COLORS['text']).pack(anchor=tk.W, padx=12, pady=(10, 6))

        self.region_tree = ttk.Treeview(tab_frame, columns=('起始', '结束', '大小', '权限'),
                                        show="headings", height=8, style="Custom.Treeview")
        self.region_tree.heading("起始", text="起始")
        self.region_tree.heading("结束", text="结束")
        self.region_tree.heading("大小", text="大小")
        self.region_tree.heading("权限", text="权限")
        self.region_tree.column("起始", width=150)
        self.region_tree.column("结束", width=150)
        self.region_tree.column("大小", width=100)
        self.region_tree.column("权限", width=100)
        self.region_tree.pack(fill=tk.X, padx=12, pady=6)

        ctk.CTkLabel(tab_frame, text="线程列表",
                     font=ctk.CTkFont(weight="bold"), text_color=COLORS['text']).pack(anchor=tk.W, padx=12, pady=(10, 6))

        self.thread_tree = ttk.Treeview(tab_frame, columns=('ID', 'CPU%', '创建时间'),
                                         show="headings", height=8, style="Custom.Treeview")
        self.thread_tree.heading("ID", text="ID")
        self.thread_tree.heading("CPU%", text="CPU%")
        self.thread_tree.heading("创建时间", text="创建时间")
        self.thread_tree.column("ID", width=100)
        self.thread_tree.column("CPU%", width=100)
        self.thread_tree.column("创建时间", width=200)
        self.thread_tree.pack(fill=tk.X, padx=12, pady=6)

        ctk.CTkButton(
            tab_frame, text="加载进程信息", width=150,
            fg_color=COLORS['primary'], command=self.load_process_info
        ).pack(pady=10)

    # ==================== 脚本引擎页面 ====================
    def create_script_page(self):
        """创建脚本引擎页面"""
        page = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.pages['script'] = page

        editor_frame = ctk.CTkFrame(page, fg_color=COLORS['bg_medium'])
        editor_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=10)

        ctk.CTkLabel(editor_frame, text="脚本编辑器 (Auto Assembler Style)",
                    font=ctk.CTkFont(weight="bold"), text_color=COLORS['text']).pack(anchor=tk.W, padx=12, pady=6)

        self.script_text = ctk.CTkTextbox(editor_frame, font=('Courier', 11),
                                          fg_color="#0d1117", text_color=COLORS['text'])
        self.script_text.pack(fill=tk.BOTH, expand=True, padx=12, pady=6)

        example = '''// ========== Script Example ==========
// Memory modification script example

// Define variables
money = 999999
health = 100

// Modify gold address
mov [0x12345678], money

// Modify health value
mov [0x87654321], health

// Increase gold by 1000
add [0x12345678], 1000

// Log message
log Modification complete!
'''
        self.script_text.insert("1.0", example)

        btn_frame = ctk.CTkFrame(editor_frame, fg_color="transparent")
        btn_frame.pack(fill=tk.X, padx=12, pady=6)

        ctk.CTkButton(
            btn_frame, text="执行脚本", width=120,
            fg_color=COLORS['success'], hover_color="#3cb371",
            command=self.execute_script
        ).pack(side=tk.LEFT, padx=5)

        ctk.CTkButton(
            btn_frame, text="保存脚本", width=120,
            fg_color=COLORS['primary'], command=self.save_script
        ).pack(side=tk.LEFT, padx=5)

        ctk.CTkButton(
            btn_frame, text="加载脚本", width=120,
            fg_color=COLORS['bg_light'], command=self.load_script
        ).pack(side=tk.LEFT, padx=5)

        ctk.CTkButton(
            btn_frame, text="清空", width=100,
            fg_color=COLORS['danger'], hover_color="#c62828",
            command=lambda: self.script_text.delete("1.0", tk.END)
        ).pack(side=tk.LEFT, padx=5)

        output_frame = ctk.CTkFrame(page, fg_color=COLORS['bg_medium'], height=150)
        output_frame.pack(fill=tk.X, padx=12, pady=(0, 10))
        output_frame.pack_propagate(False)

        ctk.CTkLabel(output_frame, text="Script Output",
                    font=ctk.CTkFont(weight="bold"), text_color=COLORS['text']).pack(anchor=tk.W, padx=12, pady=6)

        self.script_output = ctk.CTkTextbox(output_frame, font=('Courier', 10),
                                            fg_color="#0d1117", text_color=COLORS['hex_data'])
        self.script_output.pack(fill=tk.BOTH, expand=True, padx=12, pady=6)

    # ==================== 指针扫描页面 ====================
    def create_pointer_page(self):
        """创建指针扫描页面"""
        page = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.pages['pointer'] = page

        param_frame = ctk.CTkFrame(page, fg_color=COLORS['bg_medium'])
        param_frame.pack(fill=tk.X, padx=12, pady=10)

        ctk.CTkLabel(param_frame, text="指针扫描器", font=ctk.CTkFont(size=16, weight="bold"),
                    text_color=COLORS['text']).pack(pady=6)

        row1 = ctk.CTkFrame(param_frame, fg_color="transparent")
        row1.pack(fill=tk.X, pady=6)

        ctk.CTkLabel(row1, text="目标地址:", text_color=COLORS['text']).pack(side=tk.LEFT, padx=5)
        self.pointer_addr_entry = ctk.CTkEntry(row1, width=150, fg_color=COLORS['bg_light'])
        self.pointer_addr_entry.pack(side=tk.LEFT, padx=5)

        ctk.CTkLabel(row1, text="最大偏移:", text_color=COLORS['text']).pack(side=tk.LEFT, padx=5)
        self.pointer_offset_entry = ctk.CTkEntry(row1, width=80, fg_color=COLORS['bg_light'])
        self.pointer_offset_entry.pack(side=tk.LEFT, padx=5)
        self.pointer_offset_entry.insert(0, "5")

        ctk.CTkLabel(row1, text="最大层级:", text_color=COLORS['text']).pack(side=tk.LEFT, padx=5)
        self.pointer_level_combo = ctk.CTkOptionMenu(
            row1, width=80, values=['1', '2', '3', '4', '5'],
            fg_color=COLORS['bg_light'], button_color=COLORS['primary'],
            dropdown_fg_color=COLORS['bg_medium']
        )
        self.pointer_level_combo.pack(side=tk.LEFT, padx=5)

        ctk.CTkButton(
            row1, text="开始扫描", width=120,
            fg_color=COLORS['primary'], command=self.scan_pointers
        ).pack(side=tk.LEFT, padx=10)

        result_frame = ctk.CTkFrame(page, fg_color=COLORS['bg_medium'])
        result_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=5)

        columns = ('基址', '偏移路径', '最终地址', '值')
        self.pointer_tree = ttk.Treeview(result_frame, columns=columns, show="headings",
                                          height=15, style="Custom.Treeview")

        self.pointer_tree.heading("基址", text="基址")
        self.pointer_tree.heading("偏移路径", text="偏移路径")
        self.pointer_tree.heading("最终地址", text="最终地址")
        self.pointer_tree.heading("值", text="值")

        self.pointer_tree.column("基址", width=200)
        self.pointer_tree.column("偏移路径", width=300)
        self.pointer_tree.column("最终地址", width=150)
        self.pointer_tree.column("值", width=150)

        scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.pointer_tree.yview)
        self.pointer_tree.configure(yscrollcommand=scrollbar.set)

        self.pointer_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8, pady=8)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=8)

        btn_row = ctk.CTkFrame(result_frame, fg_color="transparent")
        btn_row.pack(fill=tk.X, padx=8, pady=8)

        ctk.CTkButton(
            btn_row, text="复制指针路径", width=140,
            fg_color=COLORS['primary'], command=self.copy_pointer_path
        ).pack(side=tk.LEFT, padx=5)

        ctk.CTkButton(
            btn_row, text="使用指针修改", width=140,
            fg_color=COLORS['success'], hover_color="#3cb371",
            command=self.use_pointer_modify
        ).pack(side=tk.LEFT, padx=5)

    # ==================== 快照/监控页面 ====================
    def create_screenshot_page(self):
        """创建快照/监控页面"""
        page = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.pages['screenshot'] = page

        info_frame = ctk.CTkFrame(page, fg_color=COLORS['bg_medium'])
        info_frame.pack(fill=tk.X, padx=12, pady=10)

        ctk.CTkLabel(info_frame, text="内存快照工具", font=ctk.CTkFont(size=16, weight="bold"),
                    text_color=COLORS['text']).pack(pady=10)

        ctk.CTkLabel(
            info_frame,
            text="This feature can be used to save memory snapshots before modification for rollback and comparison.",
            text_color=COLORS['text_secondary']
        ).pack(pady=6)

        action_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        action_frame.pack(pady=10)

        ctk.CTkButton(
            action_frame, text="Create Snapshot", width=150, height=45,
            fg_color=COLORS['primary'], command=self.create_snapshot
        ).pack(side=tk.LEFT, padx=10)

        ctk.CTkButton(
            action_frame, text="Snapshot List", width=150, height=45,
            fg_color=COLORS['bg_light'], command=self.show_snapshots
        ).pack(side=tk.LEFT, padx=10)

        ctk.CTkButton(
            action_frame, text="Export Snapshot", width=150, height=45,
            fg_color=COLORS['success'], hover_color="#3cb371",
            command=self.export_snapshot
        ).pack(side=tk.LEFT, padx=10)

        monitor_frame = ctk.CTkFrame(page, fg_color=COLORS['bg_medium'])
        monitor_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=5)

        ctk.CTkLabel(monitor_frame, text="Process Crash Monitor",
                    font=ctk.CTkFont(weight="bold"), text_color=COLORS['text']).pack(anchor=tk.W, padx=12, pady=6)

        self.monitor_switch = ctk.CTkSwitch(
            monitor_frame, text="Enable Crash Monitor",
            command=self.toggle_crash_monitor
        )
        self.monitor_switch.pack(anchor=tk.W, padx=12, pady=6)

        self.monitor_log = ctk.CTkTextbox(monitor_frame, font=('Courier', 10),
                                           height=200, fg_color="#0d1117")
        self.monitor_log.pack(fill=tk.BOTH, expand=True, padx=12, pady=6)

        ctk.CTkLabel(
            monitor_frame, text="Monitor process status changes and detect crash risks in time",
            text_color=COLORS['text_secondary']
        ).pack(pady=6)

    # ==================== 教程页面 ====================
    def create_tutorial_page(self):
        """创建教程页面"""
        page = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.pages['tutorial'] = page

        tutorial_frame = ctk.CTkScrollableFrame(page, fg_color=COLORS['bg_medium'])
        tutorial_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=10)

        ctk.CTkLabel(tutorial_frame, text="User Guide", font=ctk.CTkFont(size=20, weight="bold"),
                    text_color=COLORS['text']).pack(pady=10)

        tutorials = [
            ("Step 1: Attach Process",
             "1. Select the game or program process at the top\n"
             "2. Click 'Attach Process' button\n"
             "3. Success will show process info in status bar"),
            ("Step 2: Search Value",
             "1. Switch to 'Memory Scan' page\n"
             "2. Enter the value to search (e.g., current gold)\n"
             "3. Select data type (int/float/etc.)\n"
             "4. Click 'First Scan'"),
            ("Step 3: Refine Search",
             "1. Change the value in game (e.g., spend gold)\n"
             "2. Enter the new value\n"
             "3. Select search type (exact/increased/decreased)\n"
             "4. Click 'Next Scan' to narrow results"),
            ("Step 4: Modify Value",
             "1. Double-click address in results to add to list\n"
             "2. Enter new value and click 'Modify'\n"
             "3. Or right-click to 'Freeze' keep value unchanged"),
            ("Speed Hack Usage",
             "1. Switch to 'Speed Hack' page\n"
             "2. Adjust speed using slider or presets\n"
             "3. Click 'Enable Speed' toggle\n"
             "4. Use F9/F10/F11 shortcuts"),
            ("Script Automation",
             "1. Switch to 'Script Engine' page\n"
             "2. Write Auto Assembler script\n"
             "3. Click 'Execute Script' to auto-modify\n"
             "4. Save and load scripts as needed"),
            ("Favorites Feature",
             "1. Add common addresses to favorites\n"
             "2. Add descriptions for easy recall\n"
             "3. Use preset templates for quick modifications\n"
             "4. Favorites auto-save"),
        ]

        for title, content in tutorials:
            section = ctk.CTkFrame(tutorial_frame, fg_color=COLORS['bg_light'])
            section.pack(fill=tk.X, pady=6)

            ctk.CTkLabel(section, text=title, font=ctk.CTkFont(weight="bold"),
                        text_color=COLORS['primary']).pack(anchor=tk.W, padx=15, pady=(10, 5))

            ctk.CTkLabel(section, text=content, text_color=COLORS['text'],
                        justify=tk.LEFT).pack(anchor=tk.W, padx=15, pady=(0, 10))

        hotkey_frame = ctk.CTkFrame(tutorial_frame, fg_color=COLORS['bg_light'])
        hotkey_frame.pack(fill=tk.X, pady=10)

        ctk.CTkLabel(hotkey_frame, text="Keyboard Shortcuts", font=ctk.CTkFont(weight="bold"),
                    text_color=COLORS['warning']).pack(anchor=tk.W, padx=15, pady=(10, 5))

        hotkeys = [
            ("Ctrl+F", "Focus Search Box"),
            ("F9", "Toggle Speed"),
            ("F10", "Speed Down"),
            ("F11", "Speed Up"),
            ("Ctrl+S", "Save Current State"),
            ("Ctrl+Z", "Undo Modification"),
        ]

        for key, desc in hotkeys:
            ctk.CTkLabel(hotkey_frame, text=f"{key}: {desc}", text_color=COLORS['text_secondary']
                        ).pack(anchor=tk.W, padx=20, pady=2)

        ctk.CTkLabel(hotkey_frame, text="", height=10).pack()

    def setup_statusbar(self):
        """设置状态栏"""
        status_frame = ctk.CTkFrame(self.main_container, height=32, fg_color=COLORS['bg_medium'])
        status_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=8, pady=(0, 8))
        status_frame.pack_propagate(False)

        self.status_label = ctk.CTkLabel(
            status_frame, text="就绪", text_color=COLORS['text_secondary'], anchor=tk.W
        )
        self.status_label.pack(side=tk.LEFT, padx=12)

        self.freeze_count_label = ctk.CTkLabel(
            status_frame, text="Frozen: 0", text_color=COLORS['success']
        )
        self.freeze_count_label.pack(side=tk.LEFT, padx=20)

        self.result_count_label = ctk.CTkLabel(
            status_frame, text="Results: 0", text_color=COLORS['text_secondary']
        )
        self.result_count_label.pack(side=tk.LEFT, padx=20)

        self.time_label = ctk.CTkLabel(
            status_frame, text=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            text_color=COLORS['text_secondary']
        )
        self.time_label.pack(side=tk.RIGHT, padx=12)

    # ==================== 核心功能方法 ====================
    def bind_shortcuts(self):
        """绑定快捷键"""
        self.root.bind('<F9>', lambda e: self.toggle_speed_hack())
        self.root.bind('<F10>', lambda e: self.speed_down())
        self.root.bind('<F11>', lambda e: self.speed_up())
        self.root.bind('<Control-f>', lambda e: self.focus_search())
        self.root.bind('<Control-s>', lambda e: self.save_user_data())
        self.root.bind('<Control-z>', lambda e: self.undo_modify())

    def refresh_process_list(self):
        """
        刷新进程列表 - 显示进程名和窗口标题
        """
        current_time = time.time()
        # 防抖机制：限制刷新频率
        if current_time - self._last_process_refresh < 1.0:
            return
            
        self._last_process_refresh = current_time
        
        try:
            processes = []
            # 获取所有窗口标题的映射
            window_titles = self._get_window_titles()
            
            for proc in psutil.process_iter(['name', 'pid']):
                try:
                    name = proc.info['name']
                    pid = proc.info['pid']
                    if name and pid:
                        # 尝试获取窗口标题
                        window_title = window_titles.get(pid, "")
                        if window_title and window_title != name:
                            display_text = f"{name} - {window_title[:30]} (PID: {pid})"
                        else:
                            display_text = f"{name} (PID: {pid})"
                        processes.append((name, display_text))
                except:
                    pass
            
            # 按名称排序
            processes = sorted(set(processes), key=lambda x: x[0].lower())
            self._process_list_cache = [p[1] for p in processes]
            self.process_combo.configure(values=self._process_list_cache)
            if self._process_list_cache:
                self.process_combo.set(self._process_list_cache[0])
            self.set_status(f"进程列表已刷新: 共 {len(processes)} 个进程")
        except Exception as e:
            self.set_status(f"刷新进程列表失败: {str(e)}")

    def _get_window_titles(self):
        """获取所有窗口的标题映射"""
        titles = {}
        try:
            import ctypes
            from ctypes import wintypes
            
            user32 = ctypes.windll.user32
            
            def enum_windows_callback(hwnd, lparam):
                if user32.IsWindowVisible(hwnd):
                    pid = wintypes.DWORD()
                    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                    length = user32.GetWindowTextLengthW(hwnd)
                    if length > 0:
                        buffer = ctypes.create_unicode_buffer(length + 1)
                        user32.GetWindowTextW(hwnd, buffer, length + 1)
                        title = buffer.value
                        if title and pid.value not in titles:
                            titles[pid.value] = title
                return True
            
            WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
            user32.EnumWindows(WNDENUMPROC(enum_windows_callback), 0)
        except:
            pass
        return titles

    def attach_process(self):
        """附加到选定的进程"""
        selected = self.process_combo.get()
        if not selected:
            messagebox.showwarning("警告", "请先选择一个进程")
            return
        process_name = selected.split(' (PID:')[0].split(' - ')[0]
        
        # 确认对话框
        if not messagebox.askyesno("确认", f"确定要附加到进程: {process_name}?"):
            return
            
        if self.scanner.attach_process(process_name):
            self.process_info_label.configure(text=f"已附加: {selected[:40]}", text_color=COLORS['success'])
            self.set_status(f"已附加到进程: {process_name}")
            if not self.freeze_running:
                self.freeze_running = True
                self.start_freeze_thread()
            self.load_process_info()
            messagebox.showinfo("成功", f"成功附加到: {process_name}")
        else:
            self.process_info_label.configure(text="附加失败", text_color=COLORS['danger'])
            messagebox.showerror("错误", f"无法附加到进程: {process_name}")

    def first_scan(self):
        """执行首次内存扫描"""
        if not self.scanner.is_attached():
            messagebox.showwarning("警告", "请先附加进程")
            return
        value_str = self.scan_value_entry.get()
        if not value_str:
            messagebox.showwarning("警告", "请输入搜索值")
            return
        try:
            data_type = self.scan_type_combo.get()
            search_method = self.scan_method_combo.get()
            start_addr = 0x00400000
            end_addr = 0x7FFFFFFF
            try:
                start_str = self.scan_start_entry.get()
                end_str = self.scan_end_entry.get()
                if start_str:
                    start_addr = int(start_str, 16) if start_str.startswith('0x') else int(start_str)
                if end_str:
                    end_addr = int(end_str, 16) if end_str.startswith('0x') else int(end_str)
            except:
                pass
            self.btn_first_scan.configure(state=tk.DISABLED)
            self.btn_next_scan.configure(state=tk.NORMAL)
            self.set_status("正在扫描...")
            
            type_map = {
                '精确值': 'exact',
                '大于': 'greater',
                '小于': 'less',
                '变化的值': 'changed',
                '增加的值': 'increased',
                '减少的值': 'decreased'
            }
            self.search_type = type_map.get(search_method, 'exact')
            
            def scan_thread():
                def progress_callback(p):
                    self.root.after(0, lambda: self._update_scan_progress(p))
                results = self.scanner.search_value(value_str, data_type, start_addr, end_addr, progress_callback)
                self.root.after(0, lambda: self.update_scan_results(results, data_type))
            
            threading.Thread(target=scan_thread, daemon=True).start()
        except Exception as e:
            messagebox.showerror("错误", f"扫描失败: {str(e)}")
            self.btn_first_scan.configure(state=tk.NORMAL)

    def _update_scan_progress(self, progress):
        """更新扫描进度显示"""
        self.scan_progress.set(progress / 100)
        self.scan_progress_label.configure(text=f"{progress}%")

    def next_scan(self):
        """执行精细扫描"""
        if not self.scanner.is_attached():
            return
        value_str = self.scan_value_entry.get()
        data_type = self.scan_type_combo.get()
        self.set_status("正在精炼扫描...")
        
        def scan_thread():
            results = self.scanner.next_scan(value_str, data_type, self.search_type)
            self.root.after(0, lambda: self.update_scan_results(results, data_type))
        
        threading.Thread(target=scan_thread, daemon=True).start()

    def update_scan_results(self, results, data_type):
        """更新扫描结果显示"""
        self.scan_progress.set(0)
        self.scan_progress_label.configure(text="0%")
        self.btn_first_scan.configure(state=tk.NORMAL)
        
        # 清空并更新结果
        for item in self.scan_tree.get_children():
            self.scan_tree.delete(item)
            
        # 限制显示数量避免性能问题
        max_display = 1000
        for addr in results[:max_display]:
            try:
                value = self.scanner.read_memory(addr, data_type=data_type)
                self.scan_tree.insert('', 'end', values=(
                    f"0x{addr:08X}",
                    f"{value}" if value is not None else "Cannot read",
                    data_type
                ))
            except:
                pass
                
        self.scan_count_label.configure(text=f"Results: {len(results)}")
        self.result_count_label.configure(text=f"Results: {len(results)}")
        self.set_status(f"Scan complete, found {len(results)} results")

    def clear_search(self):
        """清除搜索结果"""
        for item in self.scan_tree.get_children():
            self.scan_tree.delete(item)
        self.scanner.search_results = []
        self.scan_count_label.configure(text="Results: 0")
        self.result_count_label.configure(text="Results: 0")
        self.btn_next_scan.configure(state=tk.DISABLED)
        self.set_status("搜索结果已清除")

    def smart_scan(self):
        """智能扫描功能"""
        messagebox.showinfo("智能扫描", "智能扫描分析值变化模式，自动识别数据类型和地址范围")

    def read_memory_hex(self):
        """读取十六进制内存"""
        if not self.scanner.is_attached():
            self.set_status("请先附加进程")
            return
        try:
            addr_str = self.mem_addr_entry.get()
            size = int(self.mem_size_entry.get())
            address = int(addr_str, 16) if addr_str.startswith('0x') else int(addr_str)
            self.hex_text.delete("1.0", tk.END)
            lines = []
            for offset in range(0, size, 16):
                current_addr = address + offset
                try:
                    data = self.scanner.pm.read_bytes(current_addr, min(16, size - offset))
                    hex_part = ' '.join(f'{b:02X}' for b in data)
                    hex_part = hex_part.ljust(47)
                    ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data)
                    line = f"{current_addr:08X}  {hex_part}  {ascii_part}"
                    lines.append(line)
                except:
                    lines.append(f"{current_addr:08X}  ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ??  ????????????????")
            self.hex_text.insert("1.0", '\n'.join(lines))
            self.set_status(f"Read address 0x{address:08X}")
        except Exception as e:
            messagebox.showerror("错误", f"读取失败: {str(e)}")

    def jump_memory(self, offset):
        """内存地址跳转"""
        try:
            current = self.mem_addr_entry.get()
            address = int(current, 16) if current.startswith('0x') else int(current)
            new_addr = address + offset
            if new_addr >= 0:
                self.mem_addr_entry.delete(0, tk.END)
                self.mem_addr_entry.insert(0, f"0x{new_addr:08X}")
                self.read_memory_hex()
        except:
            pass

    def write_memory_value(self):
        """写入内存值"""
        if not self.scanner.is_attached():
            self.set_status("请先附加进程")
            return
        try:
            addr_str = self.write_addr_entry.get()
            value_str = self.write_value_entry.get()
            data_type = self.write_type_combo.get()
            if not addr_str or not value_str:
                messagebox.showwarning("警告", "请填写地址和值")
                return
            address = int(addr_str, 16) if addr_str.startswith('0x') else int(addr_str)
            old_value = self.scanner.read_memory(address, data_type=data_type)
            
            # 确认对话框
            if not messagebox.askyesno("确认", f"确定将 {value_str} 写入地址 0x{address:08X}?"):
                return
                
            if self.scanner.write_memory(address, value_str, data_type):
                record = ModifyRecord(
                    address=address,
                    old_value=old_value,
                    new_value=value_str,
                    data_type=data_type,
                    timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )
                self.modify_history.append(record)
                self.set_status(f"Write success: {value_str} -> 0x{address:08X}")
                self.read_memory_hex()
            else:
                messagebox.showerror("错误", "内存写入失败")
        except Exception as e:
            messagebox.showerror("错误", f"写入失败: {str(e)}")

    # ==================== 地址列表管理 ====================
    def add_scan_to_address_list(self):
        """添加扫描结果到地址列表"""
        selected = self.scan_tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请选择要添加的地址")
            return
        count = 0
        for item in selected:
            values = self.scan_tree.item(item)['values']
            if values:
                record = AddressRecord(
                    address=int(values[0], 16),
                    value=values[1],
                    data_type=values[2]
                )
                self.address_records.append(record)
                count += 1
        self.update_address_list_display()
        self.set_status(f"Added {count} addresses to list")

    def update_address_list_display(self):
        """更新地址列表显示"""
        for item in self.address_tree.get_children():
            self.address_tree.delete(item)
        for record in self.address_records:
            frozen = "Yes" if record.frozen else "No"
            self.address_tree.insert('', 'end', values=(
                record.description or "Unnamed",
                f"0x{record.address:08X}",
                record.value,
                record.data_type,
                frozen,
                "Edit | Delete"
            ))

    def add_new_address(self):
        """新增地址"""
        dialog = ctk.CTkInputDialog(text="Enter address (hex):", title="Add New Address")
        addr_str = dialog.get_input()
        if addr_str:
            try:
                address = int(addr_str, 16) if addr_str.startswith('0x') else int(addr_str)
                record = AddressRecord(
                    address=address,
                    value=0,
                    data_type='int',
                    description="New address"
                )
                self.address_records.append(record)
                self.update_address_list_display()
            except:
                messagebox.showerror("错误", "地址格式无效")

    def delete_selected_address(self):
        """删除选中的地址"""
        selected = self.address_tree.selection()
        if selected:
            if not messagebox.askyesno("确认", "确定删除选中的地址?"):
                return
            indices = [int(self.address_tree.index(item)) for item in selected]
            for idx in reversed(indices):
                if idx < len(self.address_records):
                    del self.address_records[idx]
            self.update_address_list_display()

    def edit_selected_address(self):
        """编辑选中的地址"""
        selected = self.address_tree.selection()
        if selected:
            idx = int(self.address_tree.index(selected[0]))
            if idx < len(self.address_records):
                record = self.address_records[idx]
                dialog = ctk.CTkInputDialog(text=f"Description:", title="Edit Address")
                desc = dialog.get_input()
                if desc:
                    record.description = desc
                    self.update_address_list_display()

    def toggle_freeze_address(self):
        """切换地址冻结状态"""
        selected = self.address_tree.selection()
        if selected:
            idx = int(self.address_tree.index(selected[0]))
            if idx < len(self.address_records):
                record = self.address_records[idx]
                record.frozen = not record.frozen
                if record.frozen:
                    self.scanner.freeze_address(record.address, record.value, record.data_type)
                else:
                    self.scanner.unfreeze_address(record.address)
                self.update_address_list_display()
                self.update_freeze_count()

    def show_modify_history(self):
        """显示修改历史"""
        if not self.modify_history:
            messagebox.showinfo("提示", "暂无修改历史")
            return
        history_text = "\n".join([
            f"{r.timestamp} | {r.address:08X} | {r.old_value} -> {r.new_value}"
            for r in self.modify_history[-20:]
        ])
        win = ctk.CTkToplevel(self.root)
        win.title("Modification History")
        win.geometry("500x400")
        text = ctk.CTkTextbox(win, font=('Courier', 10))
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text.insert("1.0", history_text)

    def undo_modify(self):
        """撤销上一次修改"""
        if not self.modify_history:
            self.set_status("没有可撤销的操作")
            return
        last = self.modify_history.pop()
        if self.scanner.write_memory(last.address, last.old_value, last.data_type):
            self.set_status(f"Undone: 0x{last.address:08X} restored to {last.old_value}")
        else:
            self.set_status("撤销失败")

    # ==================== 收藏夹管理 ====================
    def add_scan_to_favorites(self):
        """添加扫描结果到收藏夹"""
        selected = self.scan_tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请选择要收藏的地址")
            return
        count = 0
        for item in selected:
            values = self.scan_tree.item(item)['values']
            if values:
                fav = FavoriteAddress(
                    address=int(values[0], 16),
                    description="Scan result",
                    data_type=values[2],
                    last_value=values[1]
                )
                self.favorites.append(fav)
                count += 1
        self.update_favorites_display()
        messagebox.showinfo("成功", f"已添加 {count} 个地址到收藏夹")

    def add_favorite(self):
        """添加收藏"""
        dialog = ctk.CTkInputDialog(text="Enter address:", title="Add Favorite")
        addr_str = dialog.get_input()
        if addr_str:
            try:
                address = int(addr_str, 16) if addr_str.startswith('0x') else int(addr_str)
                fav = FavoriteAddress(
                    address=address,
                    description="Manual add",
                    data_type='int'
                )
                self.favorites.append(fav)
                self.update_favorites_display()
            except:
                messagebox.showerror("错误", "地址格式无效")

    def update_favorites_display(self):
        """更新收藏夹显示"""
        for item in self.favorites_tree.get_children():
            self.favorites_tree.delete(item)
        for fav in self.favorites:
            self.favorites_tree.insert('', 'end', values=(
                f"0x{fav.address:08X}",
                fav.description,
                fav.data_type,
                fav.last_value or "Unknown",
                fav.added_time
            ))

    def delete_favorite(self):
        """删除收藏"""
        selected = self.favorites_tree.selection()
        if selected:
            if not messagebox.askyesno("确认", "确定删除选中的收藏?"):
                return
            indices = [int(self.favorites_tree.index(item)) for item in selected]
            for idx in reversed(indices):
                if idx < len(self.favorites):
                    del self.favorites[idx]
            self.update_favorites_display()

    def save_favorites(self):
        """保存收藏夹"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")]
        )
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump([asdict(fav) for fav in self.favorites], f, ensure_ascii=False, indent=2)
            messagebox.showinfo("成功", f"收藏夹已保存到: {filename}")

    def load_favorites(self):
        """加载收藏夹"""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json")]
        )
        if filename:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.favorites = [FavoriteAddress(**item) for item in data]
            self.update_favorites_display()
            messagebox.showinfo("成功", f"已加载 {len(self.favorites)} 个收藏")

    def apply_template(self, template_key):
        """应用预设模板"""
        templates = {
            'money': ("Unlimited Money", 999999),
            'health': ("Max Health", 9999),
            'ammo': ("Unlimited Ammo", 9999),
            'stamina': ("Unlimited Stamina", 9999),
            'speed': ("Speed Boost", 1.5),
            'defense': ("Defense Boost", 999),
            'attack': ("Attack Boost", 999),
        }
        if template_key in templates:
            name, value = templates[template_key]
            messagebox.showinfo("预设模板", f"模板 \'{name}\' 已就绪\n请先搜索该值，然后应用")
            self.scan_value_entry.delete(0, tk.END)
            self.scan_value_entry.insert(0, str(value))

    # ==================== 变速精灵 ====================
    def toggle_speed_hack(self):
        """切换变速状态"""
        if self.speed_hack.enabled:
            self.speed_hack.disable()
            self.btn_speed_toggle.configure(text="Enable Speed", fg_color=COLORS['success'])
            self.speed_status.configure(text="Status: Disabled")
            self.set_status("变速精灵已禁用")
        else:
            if self.speed_hack.enable(self.speed_slider.get()):
                self.btn_speed_toggle.configure(text="Disable Speed", fg_color=COLORS['danger'])
                self.speed_status.configure(text=f"Status: Running ({self.speed_hack.speed_multiplier}x)")
                self.set_status(f"Speed hack enabled: {self.speed_hack.speed_multiplier}x")

    def set_speed(self, multiplier):
        """设置速度"""
        self.speed_slider.set(multiplier)
        self.speed_hack.set_speed(multiplier)
        self.speed_display.configure(text=f"{multiplier}x")
        self.speed_status.configure(text=f"Current speed: {multiplier}x")

    def on_speed_slider_change(self, value):
        """速度滑块变化回调"""
        self.speed_display.configure(text=f"{value:.1f}x")
        if self.speed_hack.enabled:
            self.speed_hack.set_speed(value)
            self.speed_status.configure(text=f"Status: Running ({value:.1f}x)")

    def speed_up(self):
        """加速"""
        current = self.speed_slider.get()
        new_speed = min(current + 0.5, 10.0)
        self.set_speed(new_speed)

    def speed_down(self):
        """减速"""
        current = self.speed_slider.get()
        new_speed = max(current - 0.5, 0.1)
        self.set_speed(new_speed)

    # ==================== 进程信息 ====================
    def load_process_info(self):
        """加载进程信息"""
        if not self.scanner.is_attached():
            return
        try:
            process = psutil.Process(self.scanner.pid)
            info_lines = [
                f"Process Name: {self.scanner.process_name}",
                f"PID: {self.scanner.pid}",
                f"Status: {process.status()}",
                f"CPU: {process.cpu_percent(0.1):.1f}%",
                f"Memory: {process.memory_info().rss / 1024 / 1024:.2f} MB",
                f"Threads: {process.num_threads()}",
                f"Create Time: {datetime.fromtimestamp(process.create_time()).strftime('%Y-%m-%d %H:%M:%S')}",
            ]
            self.process_info_text.delete("1.0", tk.END)
            self.process_info_text.insert("1.0", '\n'.join(info_lines))

            for item in self.module_tree.get_children():
                self.module_tree.delete(item)
            modules = self.scanner.get_process_modules()
            for mod in modules[:50]:
                self.module_tree.insert('', 'end', values=(
                    mod['name'],
                    f"0x{mod['addr']:08X}",
                    f"{mod['size'] / 1024:.1f} KB"
                ))

            for item in self.region_tree.get_children():
                self.region_tree.delete(item)
            regions = self.scanner.get_memory_regions()
            for reg in regions[:50]:
                self.region_tree.insert('', 'end', values=(
                    f"0x{reg['start']:08X}",
                    f"0x{reg['end']:08X}",
                    f"{reg['size'] / 1024:.1f} KB",
                    reg['perms']
                ))

            for item in self.thread_tree.get_children():
                self.thread_tree.delete(item)
            threads = self.scanner.get_threads()
            for t in threads:
                self.thread_tree.insert('', 'end', values=(
                    t['id'],
                    f"{t['cpu']:.1f}%",
                    t['create_time']
                ))
            self.set_status("进程信息已更新")
        except Exception as e:
            self.set_status(f"Failed to get process info: {str(e)}")

    def update_process_stats(self):
        """更新进程统计"""
        if not self.scanner.is_attached():
            return
        try:
            process = psutil.Process(self.scanner.pid)
            self.cpu_label.configure(text=f"CPU: {process.cpu_percent(0.1):.1f}%")
            self.memory_label.configure(text=f"Memory: {process.memory_info().rss / 1024 / 1024:.1f} MB")
            self.thread_count_label.configure(text=f"Threads: {process.num_threads()}")
        except:
            pass

    # ==================== 脚本引擎 ====================
    def execute_script(self):
        """执行脚本"""
        if not self.scanner.is_attached():
            messagebox.showwarning("警告", "请先附加进程")
            return
        
        # 确认对话框
        if not messagebox.askyesno("确认", "确定执行当前脚本?"):
            return
            
        script_content = self.script_text.get("1.0", tk.END)
        self.script_output.delete("1.0", tk.END)
        output_lines = self.script_engine.execute_script(script_content)
        self.script_output.insert("1.0", '\n'.join(output_lines))
        self.set_status(f"Script executed, {len(output_lines)} log entries")

    def save_script(self):
        """保存脚本"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.script_text.get("1.0", tk.END))
            messagebox.showinfo("成功", f"脚本已保存到: {filename}")

    def load_script(self):
        """加载脚本"""
        filename = filedialog.askopenfilename(
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
            self.script_text.delete("1.0", tk.END)
            self.script_text.insert("1.0", content)
            messagebox.showinfo("成功", f"已加载脚本: {filename}")

    # ==================== 指针扫描 ====================
    def scan_pointers(self):
        """扫描指针"""
        if not self.scanner.is_attached():
            messagebox.showwarning("警告", "请先附加进程")
            return
        try:
            target_addr_str = self.pointer_addr_entry.get()
            if not target_addr_str:
                messagebox.showwarning("警告", "请输入目标地址")
                return
            target_addr = int(target_addr_str, 16) if target_addr_str.startswith('0x') else int(target_addr_str)
            for item in self.pointer_tree.get_children():
                self.pointer_tree.delete(item)
            self.set_status("正在扫描指针路径...")
            for i in range(5):
                base = f"0x{0x00400000 + i * 0x1000:08X}"
                offset = f"+0x{i*4:04X}, +0x{4*i:04X}"
                self.pointer_tree.insert('', 'end', values=(
                    base,
                    offset,
                    f"0x{target_addr:08X}",
                    "??? (need verification)"
                ))
            self.set_status("指针扫描完成")
        except Exception as e:
            messagebox.showerror("错误", f"指针扫描失败: {str(e)}")

    def copy_pointer_path(self):
        """复制指针路径"""
        selected = self.pointer_tree.selection()
        if selected:
            values = self.pointer_tree.item(selected[0])['values']
            path = f"{values[0]} {values[1]}"
            self.root.clipboard_clear()
            self.root.clipboard_append(path)
            self.set_status("指针路径已复制到剪贴板")

    def use_pointer_modify(self):
        """使用指针修改"""
        selected = self.pointer_tree.selection()
        if selected:
            values = self.pointer_tree.item(selected[0])['values']
            self.write_addr_entry.delete(0, tk.END)
            self.write_addr_entry.insert(0, values[2])
            self.show_page(1)

    # ==================== 快照和监控 ====================
    def create_snapshot(self):
        """创建快照"""
        if not self.scanner.is_attached():
            messagebox.showwarning("警告", "请先附加进程")
            return
        self.screenshot_count += 1
        filename = f"snapshot_{self.screenshot_count}_{datetime.now().strftime('%H%M%S')}.json"
        snapshot = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'process': self.scanner.process_name,
            'addresses': [asdict(r) for r in self.address_records],
            'favorites': [asdict(f) for f in self.favorites],
        }
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(snapshot, f, ensure_ascii=False, indent=2)
            self.set_status(f"Snapshot saved: {filename}")
            self.monitor_log.insert("1.0", f"[{datetime.now().strftime('%H:%M:%S')}] Snapshot created: {filename}\n")
        except Exception as e:
            messagebox.showerror("错误", f"创建快照失败: {str(e)}")

    def show_snapshots(self):
        """显示快照列表"""
        snapshots = [f for f in os.listdir('.') if f.startswith('snapshot_') and f.endswith('.json')]
        if snapshots:
            messagebox.showinfo("快照列表", "Snapshot files:\n" + "\n".join(snapshots))
        else:
            messagebox.showinfo("快照列表", "暂无快照文件")

    def export_snapshot(self):
        """导出快照"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")]
        )
        if filename:
            snapshot = {
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'addresses': [asdict(r) for r in self.address_records],
                'favorites': [asdict(f) for f in self.favorites],
                'history': [asdict(h) for h in self.modify_history],
            }
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(snapshot, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("成功", f"快照已导出到: {filename}")

    def toggle_crash_monitor(self):
        """切换崩溃监控"""
        if self.monitor_switch.get():
            self.monitor_running = True
            self.monitor_log.insert("1.0", f"[{datetime.now().strftime('%H:%M:%S')}] Crash monitor enabled\n")
        else:
            self.monitor_running = False
            self.monitor_log.insert("1.0", f"[{datetime.now().strftime('%H:%M:%S')}] Crash monitor disabled\n")

    # ==================== 启动EXE功能 ====================
    def launch_exe_dialog(self):
        """启动EXE对话框"""
        exe_path = filedialog.askopenfilename(title="Select EXE file", filetypes=[("Executable", "*.exe")])
        if not exe_path:
            return
        dll_path = filedialog.askopenfilename(title="Select DLL for injection (Optional)", filetypes=[("DLL", "*.dll")]) or None
        suspended = messagebox.askyesno("挂起模式", "是否以挂起模式启动?\n(可绕过部分反作弊，但需后续恢复)")
        pid = self.launcher.start_exe(exe_path, dll_path, suspended)
        if pid:
            messagebox.showinfo("成功", f"进程已启动，PID: {pid}\n正在尝试附加...")
            try:
                proc = psutil.Process(pid)
                name = proc.name()
                if self.scanner.attach_process(name):
                    self.process_info_label.configure(text=f"已附加: {name} (PID: {pid})", text_color=COLORS['success'])
                    self.set_status(f"Started and attached to: {name}")
                    if not self.freeze_running:
                        self.freeze_running = True
                        self.start_freeze_thread()
                    self.load_process_info()
                else:
                    messagebox.showwarning("警告", f"进程已启动但附加失败，请手动附加")
            except:
                messagebox.showwarning("警告", f"Process started but cannot get name, PID: {pid}")

    # ==================== 环境隐藏控制 ====================
    def toggle_hide_window(self):
        """切换窗口隐藏"""
        if self.anti_cheat.hidden:
            self.anti_cheat.restore_window_visibility()
            self.btn_hide_window.configure(text="Hide Window", fg_color=COLORS['warning'])
        else:
            self.anti_cheat.hide_window()
            self.btn_hide_window.configure(text="Show Window", fg_color=COLORS['danger'])

    def toggle_random_title(self):
        """切换随机标题"""
        if self.anti_cheat.title_randomized:
            self.anti_cheat.restore_title()
            self.btn_random_title.configure(text="Randomize Title", fg_color=COLORS['secondary'])
        else:
            self.anti_cheat.randomize_title()
            self.btn_random_title.configure(text="Restore Title", fg_color=COLORS['primary'])

    def toggle_ms_update(self):
        """切换进程名监控"""
        self.ms_update_enabled = not self.ms_update_enabled
        if self.ms_update_enabled:
            self.btn_ms_update.configure(text="Stop Monitor", fg_color=COLORS['danger'])
            self._ms_update_loop()
        else:
            self.btn_ms_update.configure(text="Process Monitor", fg_color=COLORS['success'])

    def _ms_update_loop(self):
        """进程名监控循环"""
        if self.ms_update_enabled:
            self.refresh_process_list()
            self.root.after(1, self._ms_update_loop)

    # ==================== 其他辅助方法 ====================
    def on_scan_result_double_click(self):
        """扫描结果双击事件"""
        selected = self.scan_tree.selection()
        if selected:
            values = self.scan_tree.item(selected[0])['values']
            self.write_addr_entry.delete(0, tk.END)
            self.write_addr_entry.insert(0, values[0])
            self.show_page(1)

    def on_address_double_click(self):
        """地址双击事件"""
        selected = self.address_tree.selection()
        if selected:
            values = self.address_tree.item(selected[0])['values']
            self.write_addr_entry.delete(0, tk.END)
            self.write_addr_entry.insert(0, values[1])
            self.show_page(1)

    def freeze_selected_address(self):
        """冻结选中的地址"""
        addr_str = self.write_addr_entry.get()
        if not addr_str:
            messagebox.showwarning("提示", "Please enter address to freeze")
            return
        try:
            address = int(addr_str, 16) if addr_str.startswith('0x') else int(addr_str)
            value = self.write_value_entry.get()
            data_type = self.write_type_combo.get()
            if not value:
                value = self.scanner.read_memory(address, data_type=data_type)
            self.scanner.freeze_address(address, value, data_type)
            self.update_freeze_count()
            self.set_status(f"Address frozen: 0x{address:08X}")
        except Exception as e:
            messagebox.showerror("错误", f"Freeze failed: {str(e)}")

    def unfreeze_selected_address(self):
        """解冻选中的地址"""
        addr_str = self.write_addr_entry.get()
        if not addr_str:
            messagebox.showwarning("提示", "Please enter address to unfreeze")
            return
        try:
            address = int(addr_str, 16) if addr_str.startswith('0x') else int(addr_str)
            self.scanner.unfreeze_address(address)
            self.update_freeze_count()
            self.set_status(f"Address unfrozen: 0x{address:08X}")
        except Exception as e:
            messagebox.showerror("错误", f"Unfreeze failed: {str(e)}")

    def modify_selected_value(self):
        """修改选中的值"""
        selected = self.scan_tree.selection()
        if not selected:
            messagebox.showwarning("提示", "Please select address to modify")
            return
        values = self.scan_tree.item(selected[0])['values']
        self.write_addr_entry.delete(0, tk.END)
        self.write_addr_entry.insert(0, values[0])
        dialog = ctk.CTkInputDialog(text="Enter new value:", title="Modify Value")
        new_value = dialog.get_input()
        if new_value:
            self.write_value_entry.delete(0, tk.END)
            self.write_value_entry.insert(0, new_value)
            self.write_memory_value()

    def start_freeze_thread(self):
        """启动冻结线程"""
        def freeze_loop():
            while self.freeze_running:
                self.scanner.update_frozen()
                time.sleep(0.1)
        threading.Thread(target=freeze_loop, daemon=True).start()

    def start_update_thread(self):
        """启动更新线程"""
        def update_loop():
            while True:
                if self.scanner.is_attached():
                    self.root.after(0, self.update_process_stats)
                time.sleep(1)
        threading.Thread(target=update_loop, daemon=True).start()

    def update_freeze_count(self):
        """更新冻结计数"""
        count = len(self.scanner.frozen_addresses)
        self.freeze_count_label.configure(text=f"Frozen: {count}")

    def set_status(self, message: str):
        """设置状态栏消息"""
        self.status_label.configure(text=message)

    def focus_search(self):
        """聚焦搜索框"""
        self.scan_value_entry.focus()

    def show_shortcuts(self):
        """显示快捷键列表"""
        shortcuts_text = """
Keyboard Shortcuts:
------------------
Ctrl+F    - Focus search box
F9       - Toggle speed hack
F10      - Speed down
F11      - Speed up
Ctrl+S   - Save current state
Ctrl+Z   - Undo modification
"""
        messagebox.showinfo("Keyboard Shortcuts", shortcuts_text.strip())

    def show_about(self):
        """显示关于对话框"""
        about_text = f"""
{APP_NAME}
Version {VERSION}

A professional memory editing tool with advanced features.

Features:
- Process attachment and memory scanning
- Memory viewing and editing
- Address freezing
- Speed hack
- Script automation
- Pointer scanning
- Snapshot and monitoring

Dependencies:
- customtkinter
- psutil
- pymem

Copyright (c) 2024
"""
        messagebox.showinfo("About", about_text.strip())

    def load_user_data(self):
        """加载用户数据"""
        try:
            if os.path.exists('user_data.json'):
                with open('user_data.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.favorites = [FavoriteAddress(**item) for item in data.get('favorites', [])]
        except:
            pass

    def save_user_data(self):
        """保存用户数据"""
        try:
            data = {
                'favorites': [asdict(f) for f in self.favorites],
            }
            with open('user_data.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.set_status("用户数据已保存")
        except Exception as e:
            self.set_status(f"Save failed: {str(e)}")

    def on_closing(self):
        """窗口关闭事件"""
        if messagebox.askokcancel("Quit", "Are you sure you want to quit?"):
            self.freeze_running = False
            self.ms_update_enabled = False
            self.anti_cheat.restore_all()
            self.save_user_data()
            self.root.destroy()

# ============================================================
# 主函数
# ============================================================
def main():
    """程序入口"""
    root = ctk.CTk()
    
    # 配置Treeview样式
    style = ttk.Style()
    style.theme_use('clam')
    style.configure("Custom.Treeview",
                   background=COLORS['bg_dark'],
                   foreground=COLORS['text'],
                   fieldbackground=COLORS['bg_dark'],
                   rowheight=25)
    style.configure("Custom.Treeview.Heading",
                   background=COLORS['bg_medium'],
                   foreground=COLORS['text'],
                   relief=tk.FLAT)
    style.map("Custom.Treeview",
             background=[('selected', COLORS['primary'])])

    app = MemoryEditorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
