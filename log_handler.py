import logging
import queue
import sys
import threading

class QueueHandler(logging.Handler):
    """将日志记录发送到队列的处理器"""
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue
        self.is_verbose = False

    def emit(self, record):
        # 在非详细模式下，只记录INFO级别及以上的日志
        if not self.is_verbose and record.levelno < logging.INFO:
            return
        self.log_queue.put(self.format(record))

class UILogger:
    def __init__(self, ui_log_callback):
        self.log_queue = queue.Queue()
        self.ui_log_callback = ui_log_callback
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self.poll_log_queue, daemon=True)
        self.queue_handler = None # 将在 setup_logging 中设置
        self.print_redirector = None # 将在 setup_logging 中设置

    def poll_log_queue(self):
        """从队列中获取日志并更新UI"""
        while not self._stop_event.is_set():
            try:
                record = self.log_queue.get(block=True, timeout=0.1)
                self.ui_log_callback(record + '\n')
            except queue.Empty:
                continue

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop_event.set()

    def set_verbose(self, is_verbose):
        """动态设置日志详细程度"""
        if self.queue_handler:
            self.queue_handler.is_verbose = is_verbose
        if self.print_redirector:
            self.print_redirector.is_verbose = is_verbose
        logging.info(f"日志级别已切换为 {'详细模式' if is_verbose else '简洁模式'}.")

def setup_logging(ui_log_callback):
    """配置日志系统，将日志重定向到UI"""
    logger = UILogger(ui_log_callback)
    
    # 配置根 logger
    root_logger = logging.getLogger()
    # 设置最低捕获级别为DEBUG，由Handler决定是否发送
    root_logger.setLevel(logging.DEBUG)
    
    # 移除所有现有的处理器，避免重复输出
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 添加队列处理器
    logger.queue_handler = QueueHandler(logger.log_queue)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    logger.queue_handler.setFormatter(formatter)
    root_logger.addHandler(logger.queue_handler)
    
    # 重定向 stdout 和 stderr
    logger.print_redirector = PrintRedirector(logger.log_queue)
    sys.stdout = logger.print_redirector
    sys.stderr = logger.print_redirector
    
    logger.start()
    return logger

class PrintRedirector:
    """一个伪文件对象，用于将print语句重定向到日志队列"""
    def __init__(self, log_queue):
        self.log_queue = log_queue
        self.is_verbose = False

    def write(self, text):
        # 在非详细模式下，不记录print输出
        if not self.is_verbose:
            return
        if not text.strip():
            return
        record = f"PRINT: {text.strip()}"
        self.log_queue.put(record)

    def flush(self):
        # 在这个上下文中，flush是无操作的
        pass

if __name__ == '__main__':
    # --- 用于独立测试 ---
    import time
    import tkinter as tk
    from tkinter import scrolledtext

    class TestApp(tk.Tk):
        def __init__(self):
            super().__init__()
            self.title("日志测试")
            self.log_text = scrolledtext.ScrolledText(self, wrap=tk.WORD)
            self.log_text.pack(expand=True, fill="both")
            
            self.logger = setup_logging(self.log_to_ui)

        def log_to_ui(self, message):
            self.log_text.insert(tk.END, message)
            self.log_text.see(tk.END)

        def test_logging(self):
            logging.info("这是一条来自 logging.info 的消息。")
            print("这是一条来自 print 的消息。")
            logging.warning("这是一条警告信息。")
            try:
                1 / 0
            except ZeroDivisionError:
                logging.error("这是一个错误信息。", exc_info=True)
                # exc_info=True 会自动添加异常信息
            
            # 模拟后台线程日志
            threading.Thread(target=self.background_task, daemon=True).start()

        def background_task(self):
            for i in range(5):
                logging.info(f"后台任务正在运行... {i+1}/5")
                time.sleep(1)
            print("后台任务完成。")

        def on_closing(self):
            self.logger.stop()
            self.destroy()

    app = TestApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.after(1000, app.test_logging) # 延迟1秒执行测试
    app.mainloop()
