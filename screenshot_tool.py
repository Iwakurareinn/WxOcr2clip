import tkinter as tk
from PIL import ImageGrab, ImageTk, ImageEnhance


class _Box:
    """内部辅助类，用于管理坐标"""

    def __init__(self):
        self.start_x, self.start_y = None, None
        self.end_x, self.end_y = None, None

    def is_none(self):
        return self.start_x is None or self.end_x is None

    def set_start(self, x, y):
        self.start_x, self.start_y = x, y

    def set_end(self, x, y):
        self.end_x, self.end_y = x, y

    def get_box(self):
        if self.is_none(): return None
        return (min(self.start_x, self.end_x), min(self.start_y, self.end_y),
                max(self.start_x, self.end_x), max(self.start_y, self.end_y))


class Screenshotter:
    def __init__(self, master):
        self.master = master
        self.win = tk.Toplevel(master)

        # --- 创建一个无边框、置顶的全屏窗口 ---
        width = self.win.winfo_screenwidth()
        height = self.win.winfo_screenheight()
        self.win.geometry(f"{width}x{height}+0+0")
        self.win.overrideredirect(True)
        self.win.attributes('-topmost', True)

        self.captured_image = None
        self.selection_box = _Box()

        # 程序启动时，立即截取一次全屏图像，保存在内存中。
        self.full_screen_image = ImageGrab.grab()

        # 基于上面的全屏图，创建一个变暗的版本作为背景。
        enhancer = ImageEnhance.Brightness(self.full_screen_image)
        self.darkened_image = enhancer.enhance(0.5)  # 50%的亮度

        # 将变暗的图像显示在Canvas上
        self.dark_photo = ImageTk.PhotoImage(self.darkened_image)
        self.canvas = tk.Canvas(self.win, cursor='tcross')
        self.canvas.pack(fill="both", expand=True)
        self.canvas.create_image(0, 0, image=self.dark_photo, anchor=tk.NW)
        self.selection_photo = None

        # 绑定事件
        self.win.bind('<KeyPress-Escape>', self._on_cancel)
        self.win.bind('<Button-3>', self._on_cancel)
        self.win.bind('<ButtonPress-1>', self._on_mouse_press)
        self.win.bind('<B1-Motion>', self._on_mouse_drag)
        self.win.bind('<ButtonRelease-1>', self._on_mouse_release)

    def _on_cancel(self, event=None):
        self.captured_image = None
        self.win.destroy()

    def _on_mouse_press(self, event):
        self.selection_box.set_start(event.x, event.y)

    def _on_mouse_drag(self, event):
        self.selection_box.set_end(event.x, event.y)
        box = self.selection_box.get_box()

        if box:
            # 删除上一次绘制的高亮区域和边框
            self.canvas.delete("selection_area")

            # 从原始全屏图中裁剪出选区
            bright_crop = self.full_screen_image.crop(box)
            self.selection_photo = ImageTk.PhotoImage(bright_crop)

            # 明亮区域
            self.canvas.create_image(box[0], box[1], image=self.selection_photo, anchor=tk.NW, tags="selection_area")

            # 绘制您喜欢的绿色边框
            self.canvas.create_rectangle(box, outline='green', width=2, tags="selection_area")

    def _on_mouse_release(self, event):
        box_coords = self.selection_box.get_box()

        # 检查选区是否有效
        if box_coords and (box_coords[2] - box_coords[0] > 5) and (box_coords[3] - box_coords[1] > 5):
            # 直接从内存中的全屏图裁剪，无需再次截图
            self.captured_image = self.full_screen_image.crop(box_coords)
            print(f'截图坐标: {box_coords}')
        else:
            self.captured_image = None

        self.win.destroy()

    def capture(self):
        """主入口：显示窗口并等待其关闭，然后返回截图结果"""
        self.win.focus_force()
        self.win.wait_window(self.win)
        return self.captured_image

