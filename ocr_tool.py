import logging
import os
import sys
import pyperclip
import threading
import queue

# 动态导入，避免硬编码
try:
    from wechat_ocr.ocr_manager import OcrManager
except ImportError:
    OcrManager = None

ocr_manager_instance = None
result_queue = queue.Queue()


def get_resource_path(relative_path):
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def ocr_result_callback(img_path: str, results: dict):
    """当OCR完成时，外部引擎会调用此函数"""
    logging.debug(f"OCR回调触发: {img_path}")
    if results and results.get('ocrResult'):
        ocr_text = "\n".join([item['text'] for item in results['ocrResult']])
        result_queue.put(ocr_text)
    else:
        result_queue.put("")


def setup_ocr_manager(engine_exe_path: str, lib_dir: str) -> bool:
    """初始化并启动外部OCR引擎服务"""
    global ocr_manager_instance
    if ocr_manager_instance: return True
    
    if not OcrManager:
        logging.error("OCR依赖库 'wechat_ocr' 未安装。请参考项目说明进行安装。")
        return False

    try:
        logging.debug("正在初始化 OcrManager...")
        ocr_manager_instance = OcrManager(lib_dir)
        ocr_manager_instance.SetExePath(engine_exe_path)
        ocr_manager_instance.SetUsrLibDir(lib_dir)
        ocr_manager_instance.SetOcrResultCallback(ocr_result_callback)
        # StartWeChatOCR 是 wechat_ocr 库中的硬编码方法名，这里无法更改
        threading.Thread(target=ocr_manager_instance.StartWeChatOCR, daemon=True).start()
        logging.debug("OcrManager 初始化线程已启动。")
        return True
    except Exception as e:
        logging.error(f"OcrManager 初始化失败: {e}", exc_info=True)
        ocr_manager_instance = None
        return False


def shutdown_ocr_manager():
    """关闭外部OCR引擎服务"""
    global ocr_manager_instance
    if ocr_manager_instance:
        logging.debug("正在关闭 OcrManager...")
        # KillWeChatOCR 是 wechat_ocr 库中的硬编码方法名，这里无法更改
        ocr_manager_instance.KillWeChatOCR()
        ocr_manager_instance = None
        logging.debug("OcrManager 已关闭。")


def perform_ocr_on_image(image):
    """在一个后台线程中对给定的图像执行OCR"""
    if not ocr_manager_instance or not image:
        logging.error("OCR引擎未运行或图像无效，无法执行识别。")
        return

    temp_path = get_resource_path("temp_screenshot.png")

    try:
        image.save(temp_path)
        screenshot_file = temp_path
    except Exception as e:
        logging.error(f"保存临时截图文件失败: {e}", exc_info=True)
        return

    while not result_queue.empty():
        result_queue.get_nowait()

    logging.debug(f"正在提交OCR任务: {screenshot_file}")
    ocr_manager_instance.DoOCRTask(screenshot_file)

    try:
        # 等待最多10秒获取结果
        ocr_text = result_queue.get(timeout=10)
        if ocr_text:
            pyperclip.copy(ocr_text)
            logging.info("OCR 结果已复制到剪贴板。")
            # 将识别内容记录在DEBUG级别，只有在详细模式下显示
            logging.debug(f"识别内容:\n---\n{ocr_text}\n---")
        else:
            logging.info("未识别到任何文字。")
    except queue.Empty:
        logging.warning("OCR 任务超时！未在10秒内收到回调结果。")
    finally:
        # 确保能删除临时文件
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError as e:
                print(f"删除临时文件失败: {e}")
