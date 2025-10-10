# WxOcr2Clip - 微信截图OCR到剪贴板

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)](https://www.microsoft.com/windows)
[![License](https://img.shields.io/badge/License-MIT-green)](https://opensource.org/licenses/MIT)

一款基于 Python 制作的 Windows 小工具，它允许您通过全局热键进行截图，然后调用微信PC版**内置的离线OCR引擎**识别图中文字，并将结果**自动复制到剪贴板**。

## 🚀 安装与使用

我们提供两种使用方式，请根据您的需求选择。

### 方式一：为普通用户 (推荐)

如果您不关心代码，只想直接使用，请下载我们为您打包好的 `.exe` 程序。

1.  前往 [Releases 页面](https://github.com/naninoimi/WxOcr2clip/releases) 
2.  下载压缩包。
3.  解压后，您会得到一个文件夹，里面包含了主程序 `app.exe` 和一个配置文件 `config.json`。
4.  请直接跳转到下方的 **[⚙️ 配置说明](#️-配置说明)** 部分，完成配置后即可双击 `app.exe` 运行。

### 方式二：为开发者 (从源码运行)

如果您希望自行修改代码或从源码开始设置，请按以下步骤操作。

1.  **克隆或下载项目**
    ```bash
    git clone https://github.com/naninoimi/WxOcr2clip.git
    cd WxOcr2clip
    ```

2.  **创建并激活Python虚拟环境**
    ```bash
    # 创建虚拟环境
    python -m venv .venv
    
    # 激活虚拟环境 (Windows)
    .\.venv\Scripts\activate
    ```

3.  **安装所有依赖**
    这些命令会更新pip，安装`requirements.txt`中的库，并安装项目所需的本地`wechat_ocr`包。
    ```bash
    # 升级pip
    python -m pip install --upgrade pip
    
    # 安装依赖
    pip install -r requirements.txt
    
    # 安装本地的wechat_ocr包
    pip install wechat_ocr-0.0.4.tar.gz
    ```

4.  **配置**
    请参考下方的 **[⚙️ 配置说明](#️-配置说明)** 创建并修改 `config.json` 文件。

5.  **运行程序**
    ```bash
    python app.py
    ```

## ⚙️ 配置说明

在使用前，您**必须**在项目根目录（与`app.py`或`app.exe`同级）下找到 `config.json` 文件（如果从源码运行，请手动创建），并根据您电脑的实际情况修改其中的路径。

```json
{
  "wechat_ocr_exe_path": "填写你的WeChatOCR.exe路径",
  "wechat_path": "填写你的微信安装路径",
  "hotkey": "ctrl+alt+q",
  "screenshot_delay": 0.1
}
```

**如何找到正确的路径？**


*   `"wechat_ocr_exe_path"`:
    1.  使用Everything软件搜索 WeChatOCR.exe。
    2.  例如在我的电脑上填写的是 "C:/Users/Alucard/AppData/Roaming/Tencent/WeChat/XPlugin/Plugins/WeChatOCR/7079/extracted/WeChatOCR.exe"

*   `"wechat_path"`:
    1.  你的微信安装路径。
    2.  例如在我的电脑上填写的为"E:\WeChat\[3.9.12.55]"。

*   `"hotkey"`: 您可以自定义喜欢的截图热键，如 `"ctrl+shift+x"`。

*   `"screenshot_delay"`:为可选的截图延迟，一般无需更改。

## 🎯 使用流程

1.  启动 `app.py` 或 `app.exe`。
2.  屏幕底部会出现系统通知，提示“服务正在后台运行中”。
3.  在任何界面，按下您设置的热键（默认为 `Ctrl+Alt+Q`）。
4.  拖动鼠标进行截图。
5.  松开鼠标后，图片中的文字就已经在您的剪贴板里了，直接去需要的地方按 `Ctrl+V` 粘贴即可！

## 🙏 致谢

本项目的核心OCR调用功能，原理及代码实现主要基于以下优秀项目，感谢原作者的探索与分享！

*   [kanadeblisst00/wechat_ocr](https://github.com/kanadeblisst00/wechat_ocr) - 提供了微信OCR的直接调用接口。
*   [Knighthood2001/wechat_OCR](https://github.com/Knighthood2001/wechat_OCR) - 提供了相关的实现思路。

## 📄 许可协议

本项目采用 [MIT License](https://opensource.org/licenses/MIT) 开源。
