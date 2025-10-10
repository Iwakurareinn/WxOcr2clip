import os
import sys
import pyperclip
import threading
import queue
from wechat_ocr.ocr_manager import OcrManager

ocr_manager_instance = None
result_queue = queue.Queue()


def get_resource_path(relative_path):
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def ocr_result_callback(img_path: str, results: dict):
    """当OCR完成时，wechat-ocr库会调用此函数"""
    print(f"识别回调触发: {img_path}")
    if results and results.get('ocrResult'):
        ocr_text = "\n".join([item['text'] for item in results['ocrResult']])
        result_queue.put(ocr_text)
    else:
        result_queue.put("")


def setup_ocr_manager(wechat_ocr_exe_path: str, wechat_dir: str) -> bool:
    """初始化并启动OCR服务"""
    global ocr_manager_instance
    if ocr_manager_instance: return True
    try:
        print("正在初始化 OcrManager...")
        ocr_manager_instance = OcrManager(wechat_dir)
        ocr_manager_instance.SetExePath(wechat_ocr_exe_path)
        ocr_manager_instance.SetUsrLibDir(wechat_dir)
        ocr_manager_instance.SetOcrResultCallback(ocr_result_callback)
        threading.Thread(target=ocr_manager_instance.StartWeChatOCR, daemon=True).start()
        print("OcrManager 初始化成功！")
        return True
    except Exception as e:
        print(f"OcrManager 初始化失败: {e}")
        ocr_manager_instance = None
        return False


def shutdown_ocr_manager():
    """关闭OCR服务"""
    global ocr_manager_instance
    if ocr_manager_instance:
        print("正在关闭 OcrManager...")
        ocr_manager_instance.KillWeChatOCR()
        ocr_manager_instance = None
        print("OcrManager 已关闭。")


def perform_ocr_on_image(image):
    """在一个后台线程中对给定的图像执行OCR"""
    if not ocr_manager_instance or not image:
        print("错误：OcrManager未运行或图像无效。")
        return

    # --- 关键修改 ---
    # 使用 get_resource_path 来确保临时文件路径的正确性
    temp_path = get_resource_path("temp_screenshot.png")

    try:
        image.save(temp_path)
        # 此时 temp_path 已经是绝对路径，可以直接使用
        screenshot_file = temp_path
    except Exception as e:
        print(f"保存临时截图文件失败: {e}")
        return

    # 清空可能存在的旧结果
    while not result_queue.empty(): result_queue.get_nowait()

    print(f"正在提交OCR任务: {screenshot_file}")
    ocr_manager_instance.DoOCRTask(screenshot_file)

    try:
        # 等待最多10秒获取结果
        ocr_text = result_queue.get(timeout=10)
        if ocr_text:
            pyperclip.copy(ocr_text)
            print("\n" + "=" * 20 + " OCR 结果已复制到剪贴板 " + "=" * 20)
            print(ocr_text)
            print("=" * 64 + "\n")
        else:
            pyperclip.copy("")
            print("未识别到任何文字。")
    except queue.Empty:
        print("OCR 任务超时！未在10秒内收到回调结果。")
    finally:
        # 确保能删除临时文件
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError as e:
                print(f"删除临时文件失败: {e}")

