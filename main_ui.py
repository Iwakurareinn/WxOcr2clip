import tkinter as tk
from tkinter import ttk, scrolledtext

class MainUI(tk.Tk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.withdraw()  # 初始隐藏主窗口
        self.title("Ocr2Clip 控制面板")
        self.geometry("600x450")
        self.resizable(False, False)
        
        self.protocol("WM_DELETE_WINDOW", self.hide_window)

        self._create_widgets()

    def _create_widgets(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill="both", padx=10, pady=10)

        # --- 状态页面 ---
        self.status_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.status_frame, text="  状态  ")
        self._create_status_page()

        # --- 设置页面 ---
        # 这个 Frame 将由外部代码填充
        self.settings_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.settings_frame, text="  设置  ")

    def _create_status_page(self):
        # 状态标签
        status_label_frame = ttk.LabelFrame(self.status_frame, text="服务状态", padding="10")
        status_label_frame.pack(fill="x", pady=5)
        
        self.status_var = tk.StringVar(value="初始化中...")
        status_display = ttk.Label(status_label_frame, textvariable=self.status_var, font=("Microsoft YaHei", 12, "bold"))
        status_display.pack()

        # 日志区域
        log_frame = ttk.LabelFrame(self.status_frame, text="运行日志", padding="10")
        log_frame.pack(expand=True, fill="both", pady=5)

        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, state='disabled', font=("Consolas", 9))
        self.log_text.pack(expand=True, fill="both")

    def show_window(self):
        """显示并置顶窗口"""
        self.deiconify()
        self.lift()
        self.focus_force()

    def hide_window(self):
        """隐藏窗口"""
        self.withdraw()

    def update_status(self, message, color="black"):
        """更新状态标签的文本和颜色"""
        self.status_var.set(message)
        # 更加健壮地找到Label
        try:
            status_label = self.status_frame.winfo_children()[0].winfo_children()[0]
            status_label.config(foreground=color)
        except (IndexError, AttributeError):
            logging.warning("更新状态标签失败，UI组件可能尚未完全创建。")

    def log(self, message):
        """向日志框中添加一条日志"""
        if not hasattr(self, 'log_text') or not self.log_text.winfo_exists():
            return
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, message)
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')

    def show_toast(self, message):
        """显示一个屏幕底部的浮动提示条。"""
        try:
            toast = tk.Toplevel(self)
            toast.overrideredirect(True)
            toast.attributes('-alpha', 0.85)
            toast.attributes('-topmost', True)

            label = tk.Label(toast, text=message, bg="#333", fg="white", font=("Microsoft YaHei", 12), padx=20, pady=10)
            label.pack()

            toast.update_idletasks()
            screen_width = self.winfo_screenwidth()
            screen_height = self.winfo_screenheight()
            toast_width = toast.winfo_width()
            x = (screen_width // 2) - (toast_width // 2)
            y = screen_height - 100
            toast.geometry(f'+{x}+{y}')

            toast.after(2000, toast.destroy)
        except Exception as e:
            # 使用logging记录错误，而不是print
            if 'logging' in globals():
                logging.error(f"显示提示条失败: {e}")

if __name__ == '__main__':
    # 用于独立测试UI
    app = MainUI()
    app.show_window()
    app.update_status("服务运行中", "green")
    app.log("这是一条测试日志。\n")
    app.log("这是另一条测试日志。\n")
    app.mainloop()
