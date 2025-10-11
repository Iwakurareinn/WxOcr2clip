import tkinter as tk
from tkinter import messagebox
import json
import os
import sys
import threading
from PIL import Image
import pystray

from screenshot_tool import Screenshotter
from ocr_tool import setup_ocr_manager, shutdown_ocr_manager, perform_ocr_on_image
from hotkey_manager import hotkey_manager


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


# 使用函数定义文件路径
CONFIG_FILE = get_resource_path("config.json")
ICON_FILE = get_resource_path("icon.ico")


def show_toast_notification(root_or_none, message):
    """显示一个屏幕底部的浮动提示条。"""
    try:
        toast = tk.Toplevel()
        toast.overrideredirect(True)
        toast.attributes('-alpha', 0.85)
        toast.attributes('-topmost', True)

        label = tk.Label(toast, text=message, bg="#333", fg="white", font=("Microsoft YaHei", 12), padx=20, pady=10)
        label.pack()

        toast.update_idletasks()
        screen_width = toast.winfo_screenwidth()
        screen_height = toast.winfo_screenheight()
        toast_width = toast.winfo_width()
        x = (screen_width // 2) - (toast_width // 2)
        y = screen_height - 100
        toast.geometry(f'+{x}+{y}')

        toast.after(1500, toast.destroy)
    except Exception as e:
        print(f"显示提示条失败: {e}")


class Application:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()  # 隐藏主窗口

        self.root.title("WxOcr2Clip 服务")
        self.root.geometry("0x0")

        self.config = None
        self.is_service_running = False
        self.tray_icon = None

        # --- 【关键修改】 ---
        # 1. 初始化状态变量
        self.screenshot_after_id = None  # 用于存储 after() 方法返回的ID
        self.active_screenshotter = None # 用于引用当前的截图工具实例

        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)

    def initialize_services(self):
        """加载配置、启动OCR和注册热键"""
        if not self.load_config():
            messagebox.showerror("配置错误", f"请检查 {CONFIG_FILE} 文件是否存在且配置正确。")
            self.root.destroy()
            return

        if not setup_ocr_manager(self.config["wechat_ocr_exe_path"], self.config["wechat_path"]):
            messagebox.showerror("OCR错误", "无法启动WeChatOCR服务，请检查配置路径。")
            self.root.destroy()
            return

        try:
            hotkey = self.config["hotkey"]
            if hotkey_manager.register(hotkey, self.trigger_screenshot):
                hotkey_manager.start()
                self.is_service_running = True
                print(f"服务启动成功！原生热键 '{hotkey}' 已激活。")
                show_toast_notification(None, f"WxOcr2Clip 开始运行\n热键: {hotkey}")
            else:
                raise ValueError("热键注册失败，请检查热键字符串格式或确认是否已被其他程序占用。")
        except Exception as e:
            messagebox.showerror("热键错误", f"无法注册热键 '{self.config['hotkey']}'.\n错误: {e}")
            self.shutdown(from_error=True)

    def load_config(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                return True
            print(f"配置文件未找到: {CONFIG_FILE}")
            return False
        except Exception as e:
            print(f"加载配置失败: {e}")
            return False

    def trigger_screenshot(self):
        """
        热键触发的入口点。由 hotkey_manager 在后台线程调用。
        使用 root.after 将任务安全地调度到主UI线程执行。
        """
        # --- 【关键修改】 ---
        # 2. 在调度新的截图任务前，先取消上一个未执行的
        if self.screenshot_after_id:
            self.root.after_cancel(self.screenshot_after_id)
            print("取消了上一个待执行的截图计划。")

        delay_seconds = self.config.get("screenshot_delay", 0.1)
        delay_ms = int(delay_seconds * 1000)

        print(f"热键触发，将在 {delay_seconds} 秒后开始截图...")

        # 3. 保存新的调度ID
        self.screenshot_after_id = self.root.after(delay_ms, self._execute_screenshot_flow)

    def _execute_screenshot_flow(self):
        """
        这个函数包含实际的截图和OCR流程。
        它由 trigger_screenshot 通过延迟调用来执行，确保在主UI线程运行。
        """
        # --- 【关键修改】 ---
        # 4. 任务开始执行，清空调度ID
        self.screenshot_after_id = None

        # 5. 检查并销毁已存在的截图窗口
        if self.active_screenshotter and self.active_screenshotter.win.winfo_exists():
            print("检测到已存在的截图窗口，正在关闭...")
            self.active_screenshotter.destroy()
            # self.active_screenshotter 在 destroy 后会自动在 capture() 返回后被清理

        print("延迟结束，正式开始截图流程...")
        # 6. 创建新实例并保存引用
        self.active_screenshotter = Screenshotter(self.root)
        image = self.active_screenshotter.capture()  # 这是一个阻塞操作

        # 7. 截图流程结束后（无论成功或取消），清理引用
        self.active_screenshotter = None

        if image:
            print("截图成功，正在提交OCR任务...")
            threading.Thread(target=perform_ocr_on_image, args=(image,), daemon=True).start()
        else:
            print("截图已取消。")

    def show_window(self):
        messagebox.showinfo("WxOcr2Clip", "服务正在后台运行中。")

    def hide_window(self):
        self.root.withdraw()

    def shutdown(self, from_error=False):
        """核心退出逻辑，确保能被托盘图标和错误处理调用"""
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.quit()  # 结束 tkinter 的 mainloop

    def final_cleanup(self):
        """程序退出前的最终清理工作"""
        print("正在关闭服务...")
        if self.is_service_running:
            hotkey_manager.stop()
            shutdown_ocr_manager()
        print("程序已退出。")

    def run(self):
        self.initialize_services()
        if not self.is_service_running:
            self.final_cleanup()
            return

        self.root.mainloop()
        self.final_cleanup()


def setup_tray_icon(app_instance):
    """创建并配置系统托盘图标"""
    icon_image = Image.open(ICON_FILE)
    def notify_status(icon, item):
        icon.notify("服务正在后台运行中。", "WxOcr2Clip")
    menu = (
        pystray.MenuItem('显示信息', notify_status),
        pystray.MenuItem('退出', app_instance.shutdown)
    )

    icon = pystray.Icon("WxOcr2Clip", icon_image, "WxOcr2Clip OCR", menu)
    app_instance.tray_icon = icon
    return icon

if __name__ == "__main__":
    app = Application()
    tray_thread = threading.Thread(target=setup_tray_icon(app).run, daemon=True)
    tray_thread.start()
    app.run()
