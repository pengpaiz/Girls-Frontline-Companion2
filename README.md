# 桌面宠物 🐾

一个轻量级的透明窗口 GIF 播放器，可以让 GIF 动画像桌面宠物一样显示在屏幕上。

## ✨ 功能特性

- 🖼️ **透明窗口**：无边框、背景透明，GIF 悬浮在桌面上
- 📌 **窗口置顶**：始终显示在最前面，或嵌入桌面层级
- 🖱️ **自由拖拽**：左键拖拽移动位置
- 🔄 **循环播放**：自动循环播放 GIF 动画
- ⚡ **5 倍速播放**：加速播放 GIF
- 💾 **位置记忆**：自动保存窗口位置，下次启动恢复
- 🚀 **开机自启**：可选开机自动启动
- 📋 **右键菜单**：黑色主题右键菜单，支持：
  - 取消置顶 / 恢复置顶
  - 开启 / 关闭开机自启动
  - 退出程序
- 🖱️ **双击退出**：双击窗口快速退出

## 📦 安装

### 方式一：直接使用 exe（推荐）

下载 Releases 中的 `桌面宠物.exe`，双击运行即可。

### 方式二：从源码运行

```bash
# 1. 克隆仓库
git clone https://github.com/你的用户名/桌面宠物.git
cd 桌面宠物

# 2. 安装依赖
pip install -r requirements.txt

# 3. 运行
python main.py
```

## 🎮 使用说明

| 操作 | 效果 |
|------|------|
| **左键拖拽** | 移动窗口 |
| **双击** | 退出程序 |
| **右键单击** | 打开菜单 |

### 右键菜单

- **取消置顶 / 恢复置顶**：切换窗口是悬浮在最前面还是嵌入桌面
- **☐ 开机自启动 / ☑ 开机自启动**：切换开机自动启动
- **退出**：关闭程序

## 🔧 打包

如需自行打包为 exe：

```bash
pip install pyinstaller

pyinstaller --onefile --noconsole --clean \
  --icon="your_icon.ico" \
  --add-data "ezgif-1d911cbe5d7205e3.gif;." \
  --name "桌面宠物" \
  main.py
```

## 📁 文件说明

```
├── main.py                          # 主程序源代码
├── ezgif-1d911cbe5d7205e3.gif       # 示例 GIF 动画
├── requirements.txt                 # Python 依赖
└── README.md                        # 本文件
```

## 🛠️ 技术栈

- **Python 3.9+**
- **PyQt5**：GUI 框架
- **Pillow**：GIF 帧解码
- **ctypes**：Windows API 调用（桌面嵌入）

## 📝 数据存储

程序会在以下位置存储配置：

- **位置记录**：`%APPDATA%\桌面宠物list\position.json`
- **开机自启动**：`%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\桌面宠物.lnk`

## 📄 许可证

MIT License
