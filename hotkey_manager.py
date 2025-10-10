import threading
import ctypes
from ctypes import wintypes
import win32con
import win32gui


class HotkeyManager:
    def __init__(self):
        self._thread = None
        self._stop_event = threading.Event()
        self.hotkeys = {}  # {hotkey_id: (modifiers, vk, callback)}
        self.next_hotkey_id = 1

    def _parse_hotkey(self, hotkey_str):
        """将 'ctrl+alt+a' 这样的字符串解析为 Windows API 需要的修饰符和虚拟键码"""
        parts = hotkey_str.lower().split('+')
        modifiers = 0
        vk = 0

        key_map = {
            'ctrl': win32con.MOD_CONTROL, 'alt': win32con.MOD_ALT,
            'shift': win32con.MOD_SHIFT, 'win': win32con.MOD_WIN
        }

        # 提取修饰符
        for part in parts[:-1]:
            part = part.strip()
            if part not in key_map:
                raise ValueError(f"无法识别的热键修饰符: {part}")
            modifiers |= key_map[part]

        # 提取主键
        main_key = parts[-1].strip()
        if len(main_key) == 1 and 'a' <= main_key <= 'z':
            vk = ord(main_key.upper())
        elif 'f1' <= main_key <= 'f12':
            vk = getattr(win32con, f'VK_F{int(main_key[1:])}')
        else:
            # 可以根据需要扩展更多按键
            raise ValueError(f"不支持的热键主键: {main_key}")

        return modifiers, vk

    def register(self, hotkey_str, callback):
        """注册一个热键"""
        try:
            modifiers, vk = self._parse_hotkey(hotkey_str)
        except ValueError as e:
            print(f"热键注册失败: {e}")
            return False

        hotkey_id = self.next_hotkey_id
        self.hotkeys[hotkey_id] = (modifiers, vk, callback)
        self.next_hotkey_id += 1

        if self._thread and self._thread.is_alive():
            if not win32gui.RegisterHotKey(None, hotkey_id, modifiers, vk):
                print(f"警告: 重新注册热键 '{hotkey_str}' 失败。可能已被其他程序占用。")
                return False
        return True

    def _run(self):
        """在后台线程中运行的消息循环"""
        # 首次注册所有已定义的热键
        for hotkey_id, (modifiers, vk, _) in self.hotkeys.items():
            if not win32gui.RegisterHotKey(None, hotkey_id, modifiers, vk):
                print(f"何意味？")

        print("热键监听服务已启动...")

        try:
            # 开始Windows消息泵
            while not self._stop_event.is_set():
                msg = win32gui.GetMessage(None, 0, 0)
                if msg[1][1] == win32con.WM_HOTKEY:
                    hotkey_id = msg[1][2]
                    if hotkey_id in self.hotkeys:
                        _, _, callback = self.hotkeys[hotkey_id]
                        if callback:
                            callback()
        finally:
            # 清理：注销所有热键
            for hotkey_id in self.hotkeys.keys():
                win32gui.UnregisterHotKey(None, hotkey_id)
            print("热键监听服务已停止。")

    def start(self):
        """启动热键监听线程"""
        if self._thread is None or not self._thread.is_alive():
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()

    def stop(self):
        """停止热键监听线程"""
        if self._thread and self._thread.is_alive():
            self._stop_event.set()
            # 需要向消息循环线程发送一个消息来唤醒 GetMessage
            # PostThreadMessage 是线程安全的
            thread_id = self._thread.ident
            win32gui.PostThreadMessage(thread_id, win32con.WM_QUIT, 0, 0)
            self._thread.join(timeout=2)  # 等待线程结束


# 创建一个全局单例
hotkey_manager = HotkeyManager()
