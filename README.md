# WxOcr2Clip - 微信截图OCR到剪贴板

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)](https://www.microsoft.com/windows)
[![License](https://img.shields.io/badge/License-MIT-green)](https://opensource.org/licenses/MIT)

一款基于 Python 制作的 Windows 小工具，它允许您通过全局热键进行截图，然后调用微信PC版**内置的离线OCR引擎**识别图中文字，并将结果**自动复制到剪贴板**。

## 🚀 安装与使用

我们提供两种使用方式，请根据您的需求选择。

### 方式一：为普通用户 (推荐)

如果您不关心代码，只想直接使用，请下载我们为您打包好的 `.exe` 程序。

1.  前往 [Releases 页面](https://github.com/naninoimi/WxOcr2clip/releases) 下载最新的压缩包。
2.  解压后，直接运行 `WxOcr2Clip.exe`。
3.  程序启动后会显示在系统托盘区，请**右键点击托盘图标 -> 设置**，进入配置界面。
4.  请直接跳转到下方的 **[⚙️ 配置说明](#️-配置说明)** 部分，完成配置后即可开始使用。

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
    ```bash
    # 安装 requirements.txt 中的依赖
    pip install -r requirements.txt
    
    # 安装项目附带的本地 OCR 库
    pip install Wechat_ocr/wechat_ocr-0.0.4.tar.gz
    ```

4.  **运行程序**
    ```bash
    python app.py
    ```
    程序启动后，请参考下方的 **[⚙️ 配置说明](#️-配置说明)** 进行设置。

## ⚙️ 配置说明

本工具现在提供图形化的设置界面，配置更简单！

1.  **打开设置**：程序运行后，在电脑右下角的系统托盘区找到程序图标，**右键点击 -> 设置**，即可打开设置窗口。
2.  **自动检测**：点击 **“自动检测路径”** 按钮，程序会自动搜索您电脑上的相关文件并填充路径。这是最推荐的方式！
3.  **手动配置**：如果自动检测失败，您需要手动填写两个路径：
    *   **OCR 引擎可执行文件路径**：通常指向一个名为 `WeChatOCR.exe` 的文件。
    *   **引擎依赖库目录**：指向一个包含 `WeChatExt.exe` 文件的**文件夹**。
4.  **保存并应用**：完成配置后，点击“保存并应用”，程序即可在后台正常工作。

## 🎯 使用流程

1.  启动程序并完成首次配置。
2.  屏幕底部会出现系统通知，提示“服务正在后台运行中”。
3.  在任何界面，按下您设置的热键（默认为 `Ctrl+Alt+A`）。
4.  拖动鼠标进行截图。
5.  松开鼠标后，图片中的文字就已经在您的剪贴板里了，直接去需要的地方按 `Ctrl+V` 粘贴即可！

## 🙏 致谢

本项目的核心OCR调用功能，原理及代码实现主要基于以下优秀项目，感谢原作者的探索与分享！

*   [kanadeblisst00/wechat_ocr](https://github.com/kanadeblisst00/wechat_ocr) - 提供了微信OCR的直接调用接口。
*   [Knighthood2001/wechat_OCR](https://github.com/Knighthood2001/wechat_OCR) - 提供了相关的实现思路。

## 📄 许可协议

本项目采用 [MIT License](https://opensource.org/licenses/MIT) 开源。
