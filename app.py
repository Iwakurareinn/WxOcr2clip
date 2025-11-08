import json
import logging
import os
import sys
import threading
import tkinter as tk
from PIL import Image
import pystray

from hotkey_manager import hotkey_manager
from log_handler import setup_logging
from main_ui import MainUI
from ocr_tool import (perform_ocr_on_image, setup_ocr_manager,
                      shutdown_ocr_manager)
from screenshot_tool import Screenshotter
from settings_page import SettingsPage


def get_resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    if os.path.basename(relative_path) in ['config.json', 'icon.ico']:
        if hasattr(sys, 'frozen'):
            return os.path.join(os.path.dirname(sys.executable), relative_path)
        else:
            return os.path.join(base_path, relative_path)
    return os.path.join(base_path, relative_path)

CONFIG_FILE = get_resource_path("config.json")
ICON_FILE = get_resource_path("icon.ico")

class Application:
    def __init__(self):
        self.main_ui = MainUI()
        self.logger = setup_logging(self.main_ui.log)
        
        self.config = None
        self.is_service_running = False
        self.tray_icon = None
        self.screenshot_after_id = None
        self.active_screenshotter = None

        # 将设置页面嵌入到主UI中
        self.settings_page = SettingsPage(self.main_ui.settings_frame, CONFIG_FILE, self.logger, on_save_callback=self.apply_new_hotkey)
        self.settings_page.pack(expand=True, fill="both")

    def apply_new_hotkey(self, new_hotkey):
        """应用新的热键配置"""
        logging.info(f"接收到新的热键配置: {new_hotkey}")
        # 重新加载配置以确保所有设置都是最新的
        self.load_config()
        self.config['hotkey'] = new_hotkey # 确保内存中的配置也更新
        
        hotkey_manager.reregister_hotkeys(new_hotkey, self.trigger_screenshot)
        self.main_ui.show_toast(f"热键已更新为: {new_hotkey}")

    def initialize_services(self):
        """加载配置、启动OCR和注册热键"""
        # 首次运行的特殊处理
        if not os.path.exists(CONFIG_FILE):
            logging.info("首次运行，开始自动检测和创建默认配置...")
            # 直接调用，同步执行路径检测，确保在写配置前完成
            self.settings_page._auto_detect_paths() 
            
            # 创建默认配置文件
            default_config = {
                "ocr_engine_path": self.settings_page.ocr_exe_path_var.get(),
                "engine_lib_path": self.settings_page.engine_lib_path_var.get(),
                "hotkey": "ctrl+alt+q",
                "screenshot_delay": 0.15,
                "verbose_log": False
            }
            try:
                with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, indent=4)
                logging.info(f"已创建默认配置文件: {CONFIG_FILE}")
                # 更新UI上的显示
                self.settings_page.hotkey_var.set(default_config["hotkey"])
                self.settings_page.delay_var.set(default_config["screenshot_delay"])
                self.settings_page.verbose_log_var.set(default_config["verbose_log"])
            except Exception as e:
                logging.error(f"创建默认配置文件失败: {e}")

        if not self.load_config() or not self.is_config_valid():
            logging.warning("配置无效或不完整，请在'设置'页面中完成配置。")
            self.main_ui.update_status("配置无效", "orange")
            self.main_ui.show_window()
            self.main_ui.notebook.select(self.main_ui.settings_frame) # 自动切换到设置页
            return
        
        # 应用日志级别设置
        self.logger.set_verbose(self.config.get("verbose_log", False))

        logging.debug("正在初始化OCR服务...")
        if not setup_ocr_manager(self.config.get("ocr_engine_path", ""), self.config.get("engine_lib_path", "")):
            logging.error("无法启动外部OCR引擎，请检查配置路径。")
            self.main_ui.update_status("OCR启动失败", "red")
            self.main_ui.show_window()
            return
        logging.info("OCR服务初始化成功。")

        try:
            hotkey = self.config["hotkey"]
            logging.info(f"正在注册热键: {hotkey}")
            # 清理旧的热键（如果存在）
            hotkey_manager.hotkeys.clear()
            if hotkey_manager.register(hotkey, self.trigger_screenshot):
                hotkey_manager.start()
                self.is_service_running = True
                logging.info(f"服务启动成功！热键 '{hotkey}' 已激活。")
                self.main_ui.update_status("运行中", "green")
                self.main_ui.show_toast(f"Ocr2Clip 开始运行\n热键: {hotkey}")
            else:
                raise ValueError("热键注册失败")
        except Exception as e:
            logging.error(f"无法注册热键 '{self.config.get('hotkey', '')}': {e}")
            self.main_ui.update_status("热键注册失败", "red")
            self.shutdown()

    def load_config(self):
        try:
            if not os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                    json.dump({}, f)
                self.config = {}
                return True
            
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            return True
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logging.error(f"加载或创建配置失败: {e}")
            self.config = {}
            return False

    def is_config_valid(self):
        required_keys = ["ocr_engine_path", "engine_lib_path", "hotkey"]
        return self.config and all(key in self.config and self.config[key] for key in required_keys)

    def trigger_screenshot(self):
        if self.screenshot_after_id:
            self.main_ui.after_cancel(self.screenshot_after_id)
            logging.debug("取消了上一个待执行的截图计划。")

        delay_seconds = self.config.get("screenshot_delay", 0.1)
        delay_ms = int(delay_seconds * 1000)

        logging.info(f"热键触发，将在 {delay_seconds} 秒后开始截图...")
        self.screenshot_after_id = self.main_ui.after(delay_ms, self._execute_screenshot_flow)

    def _execute_screenshot_flow(self):
        self.screenshot_after_id = None

        if self.active_screenshotter and self.active_screenshotter.win.winfo_exists():
            logging.debug("检测到已存在的截图窗口，正在关闭...")
            self.active_screenshotter.destroy()

        logging.debug("正式开始截图流程...")
        self.active_screenshotter = Screenshotter(self.main_ui)
        image = self.active_screenshotter.capture()
        self.active_screenshotter = None

        if image:
            logging.info("截图成功，提交OCR任务...")
            threading.Thread(target=perform_ocr_on_image, args=(image,), daemon=True).start()
        else:
            logging.info("截图已取消。")

    def shutdown(self):
        logging.info("正在关闭应用程序...")
        if self.tray_icon:
            self.tray_icon.stop()
        
        if self.is_service_running:
            hotkey_manager.stop()
            shutdown_ocr_manager()
        
        self.logger.stop()
        self.main_ui.quit()
        logging.info("应用程序已退出。")

    def run(self):
        self.initialize_services()
        
        # 创建系统托盘图标
        icon_image = Image.open(ICON_FILE)
        menu = (
            pystray.MenuItem('显示菜单', self.toggle_main_window, default=True),
            pystray.MenuItem('退出', self.shutdown)
        )
        self.tray_icon = pystray.Icon("Ocr2Clip", icon_image, "Ocr2Clip", menu)
        
        # 在后台线程中运行托盘图标
        tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
        tray_thread.start()

        self.main_ui.mainloop()
        
        # mainloop结束后，确保所有资源被清理
        self.shutdown()

    def toggle_main_window(self):
        if self.main_ui.state() == 'withdrawn':
            self.main_ui.show_window()
        else:
            self.main_ui.hide_window()

if __name__ == "__main__":
    app = Application()
    app.run()
