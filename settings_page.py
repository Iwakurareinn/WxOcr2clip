import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import winreg
import threading
import logging

class SettingsPage(ttk.Frame):
    def __init__(self, master, config_path, logger, on_save_callback=None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.config_path = config_path
        self.on_save_callback = on_save_callback
        self.logger = logger

        # --- 加载当前配置 ---
        self.config = self._load_config()

        # --- UI 变量 ---
        self.ocr_exe_path_var = tk.StringVar(value=self.config.get("ocr_engine_path", ""))
        self.engine_lib_path_var = tk.StringVar(value=self.config.get("engine_lib_path", ""))
        self.hotkey_var = tk.StringVar(value=self.config.get("hotkey", "ctrl+alt+a"))
        self.delay_var = tk.StringVar(value=self.config.get("screenshot_delay", 0.1))
        self.verbose_log_var = tk.BooleanVar(value=self.config.get("verbose_log", False))

        # --- 构建界面 ---
        self._setup_ui()

        # --- 绑定事件 ---
        self.verbose_log_var.trace_add("write", self._on_verbose_log_change)

    def _on_verbose_log_change(self, *args):
        """当'显示完整日志'复选框状态改变时调用，立即生效"""
        is_verbose = self.verbose_log_var.get()
        if self.logger:
            self.logger.set_verbose(is_verbose)

    def _load_config(self):
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _setup_ui(self):
        # --- OCR引擎路径 ---
        ttk.Label(self, text="OCR 引擎可执行文件路径:").grid(row=0, column=0, sticky="w", pady=5)
        ocr_entry = ttk.Entry(self, textvariable=self.ocr_exe_path_var, width=60)
        ocr_entry.grid(row=1, column=0, columnspan=2, sticky="ew")

        # --- 引擎依赖库路径 ---
        ttk.Label(self, text="引擎依赖库目录:").grid(row=2, column=0, sticky="w", pady=5)
        wechat_entry = ttk.Entry(self, textvariable=self.engine_lib_path_var, width=60)
        wechat_entry.grid(row=3, column=0, columnspan=2, sticky="ew")

        # --- 热键设置 ---
        ttk.Label(self, text="截图热键:").grid(row=4, column=0, sticky="w", pady=5)
        hotkey_entry = ttk.Entry(self, textvariable=self.hotkey_var, width=20)
        hotkey_entry.grid(row=5, column=0, sticky="w")
        ttk.Label(self, text="(格式: ctrl+alt+a)").grid(row=5, column=1, sticky="w", padx=10)

        # --- 截图延迟 ---
        ttk.Label(self, text="截图延迟(秒):").grid(row=6, column=0, sticky="w", pady=5)
        delay_entry = ttk.Entry(self, textvariable=self.delay_var, width=20)
        delay_entry.grid(row=7, column=0, sticky="w")

        # --- 日志级别 ---
        log_check = ttk.Checkbutton(self, text="显示完整日志 (用于调试)", variable=self.verbose_log_var)
        log_check.grid(row=8, column=0, columnspan=2, sticky="w", pady=(10, 0))

        # --- 按钮区域 ---
        button_frame = ttk.Frame(self)
        button_frame.grid(row=9, column=0, columnspan=2, pady=(20, 0), sticky="e")

        self.detect_button = ttk.Button(button_frame, text="自动检测路径", command=self._auto_detect_paths_thread)
        self.detect_button.pack(side="left", padx=10)

        self.save_button = ttk.Button(button_frame, text="保存并应用", command=self._save_settings)
        self.save_button.pack(side="left")
        
        self.grid_columnconfigure(0, weight=1)

    def _auto_detect_paths_thread(self):
        self.detect_button.config(state="disabled", text="检测中...")
        threading.Thread(target=self._auto_detect_paths, daemon=True).start()

    def _auto_detect_paths(self):
        logging.info("开始独立检测两个关键路径...")
        
        # 清空现有路径，确保从干净的状态开始检测
        self.ocr_exe_path_var.set("")
        self.engine_lib_path_var.set("")

        # 1. 检测引擎依赖库目录
        found_lib_path = self._find_engine_dependency_path()
        if found_lib_path:
            logging.info(f"成功检测到引擎依赖库目录: {found_lib_path}")
            self.engine_lib_path_var.set(found_lib_path)
        else:
            logging.warning("未能通过注册表找到引擎依赖库目录。")

        # 2. 检测 OCR 引擎可执行文件
        found_ocr_path = ""
        # 首先在 AppData 中寻找
        appdata_path = os.getenv('APPDATA')
        if appdata_path:
            ocr_search_path_appdata = os.path.join(appdata_path, "Tencent", "WeChat", "XPlugin", "Plugins", "WeChatOCR")
            found_ocr_path = self._find_ocr_engine_exe(ocr_search_path_appdata)
        
        # 如果 AppData 中没有，再尝试从已找到的依赖库目录的父目录中寻找
        if not found_ocr_path and found_lib_path:
            # 假设依赖库目录是版本号文件夹，其父目录是主安装目录
            base_install_dir = os.path.dirname(found_lib_path)
            ocr_search_path_install = os.path.join(base_install_dir, "XPlugin", "Plugins", "WeChatOCR")
            found_ocr_path = self._find_ocr_engine_exe(ocr_search_path_install)

        if found_ocr_path:
            logging.info(f"成功检测到 OCR 引擎路径: {found_ocr_path}")
            self.ocr_exe_path_var.set(found_ocr_path)
        else:
            logging.warning("未能在常规位置找到 WeChatOCR.exe。")

        # 3. 在UI线程中显示最终的检测结果
        self.after(0, self._on_detection_complete, bool(found_lib_path), bool(found_ocr_path))

    def _on_detection_complete(self, found_lib_path, found_ocr_path):
        self.detect_button.config(state="normal", text="自动检测路径")
        
        if found_lib_path and found_ocr_path:
            messagebox.showinfo("成功", "已成功自动检测到所有必需路径！", parent=self)
        elif found_lib_path or found_ocr_path:
            messagebox.showwarning("部分成功", "仅检测到部分路径，请检查并手动补全。", parent=self)
        else:
            messagebox.showerror("检测失败", "未能自动检测到任何相关路径，请手动填写。", parent=self)
        
        logging.info("路径检测完成。")

    def _find_engine_dependency_path(self):
        """
        全面搜索注册表以找到依赖库的根目录，然后递归查找所需的 .exe 文件，
        并返回其所在的文件夹路径。
        """
        # 1. 定义所有可能的注册表项和根键来寻找主程序目录
        registry_paths = [
            (winreg.HKEY_CURRENT_USER, r"Software\Tencent\WeChat"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Tencent\WeChat"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\WOW6432Node\Tencent\WeChat"),
            (winreg.HKEY_CURRENT_USER, r"Software\WOW6432Node\Tencent\WeChat"),
        ]

        dependency_search_base = None
        for hkey, path in registry_paths:
            try:
                with winreg.OpenKey(hkey, path, 0, winreg.KEY_READ) as key:
                    install_path, _ = winreg.QueryValueEx(key, "InstallPath")
                    if install_path and os.path.exists(install_path):
                        logging.info(f"在注册表中找到依赖库搜索根目录: {install_path}")
                        dependency_search_base = install_path
                        break 
            except (FileNotFoundError, OSError):
                continue
        
        if not dependency_search_base:
            logging.warning("未能在注册表中找到依赖库的搜索根目录。")
            return None

        # 2. 在找到的根目录下递归搜索 WeChatExt.exe
        logging.info(f"开始在 {dependency_search_base} 中搜索依赖文件...")
        for root, _, files in os.walk(dependency_search_base):
            if "WeChatExt.exe" in files:
                ext_dir = root
                logging.info(f"成功找到依赖文件所在目录: {ext_dir}")
                return ext_dir
        
        logging.warning(f"在 {dependency_search_base} 及其子目录中未能找到所需的依赖文件。")
        return None

    def _find_ocr_engine_exe(self, search_dir):
        """在指定目录下递归查找OCR引擎主程序"""
        if not os.path.isdir(search_dir): return ""
        for root, _, files in os.walk(search_dir):
            # 使用更通用的名称，同时兼容旧名称
            for engine_name in ["WeChatOCR.exe", "OcrEngine.exe"]:
                if engine_name in files:
                    return os.path.join(root, engine_name)
        return ""

    def _save_settings(self):
        try:
            delay = float(self.delay_var.get())
        except ValueError:
            messagebox.showwarning("输入错误", "截图延迟必须是一个数字！", parent=self)
            return

        new_config = {
            "ocr_engine_path": self.ocr_exe_path_var.get().strip(),
            "engine_lib_path": self.engine_lib_path_var.get().strip(),
            "hotkey": self.hotkey_var.get().strip().lower(),
            "screenshot_delay": delay,
            "verbose_log": self.verbose_log_var.get()
        }

        # 验证必填字段
        if not new_config["ocr_engine_path"] or not new_config["engine_lib_path"] or not new_config["hotkey"]:
            messagebox.showwarning("输入错误", "OCR引擎路径、依赖库目录和热键均不能为空！", parent=self)
            return

        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(new_config, f, indent=4)
            
            messagebox.showinfo("保存成功", "配置已保存，正在应用新设置...", parent=self)
            
            if self.on_save_callback:
                # 将新的热键值传递给回调函数
                self._reload_services_thread(new_config["hotkey"])

        except Exception as e:
            messagebox.showerror("保存失败", f"无法写入配置文件: {e}", parent=self)
            logging.error(f"保存配置失败: {e}")

    def _reload_services_thread(self, new_hotkey):
        """在后台线程中执行服务重载，避免UI卡死"""
        # 将新热键作为参数传递
        threading.Thread(target=self.on_save_callback, args=(new_hotkey,), daemon=True).start()
