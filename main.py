"""轻量级透明窗口 GIF 循环播放器（PyQt5 版）"""

import ctypes
import ctypes.wintypes
import json
import os
import subprocess
import sys
from pathlib import Path

# 修复虚拟环境下 Qt platform plugin 找不到的问题
if not os.environ.get("QT_QPA_PLATFORM_PLUGIN_PATH"):
    try:
        import PyQt5 as _pyqt5
        _qt_plugins = Path(_pyqt5.__file__).parent / "Qt5" / "plugins"
        if _qt_plugins.is_dir():
            os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = str(_qt_plugins / "platforms")
    except ImportError:
        pass

from PyQt5.QtCore import Qt, QPoint, QTimer
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import QApplication, QLabel, QMenu
from PIL import Image, ImageSequence


def _resource_path(relative: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
    return base / relative


DEFAULT_GIF = _resource_path("ezgif-1d911cbe5d7205e3.gif")
APPDATA = Path(os.environ.get("APPDATA", str(Path.home()))) / "桌面宠物list"
POS_FILE = APPDATA / "position.json"

STARTUP_DIR = (
    Path(os.environ.get("APPDATA", str(Path.home())))
    / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
)
SHORTCUT_PATH = STARTUP_DIR / "桌面宠物.lnk"

user32 = ctypes.windll.user32


def _find_workerw() -> int:
    progman = user32.FindWindowW("Progman", None)
    result = ctypes.c_long(0)
    user32.SendMessageTimeoutW(progman, 0x052C, 0, 0, 0, 1000, ctypes.byref(result))
    workerw = [0]
    def callback(hwnd: int, _lparam: int) -> bool:
        shell_view = user32.FindWindowExW(hwnd, 0, "SHELLDLL_DefView", None)
        if shell_view:
            workerw[0] = user32.FindWindowExW(0, hwnd, "WorkerW", None)
        return True
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
    user32.EnumWindows(WNDENUMPROC(callback), 0)
    return workerw[0]


def _is_frozen() -> bool:
    return getattr(sys, "frozen", False)


def _is_auto_start() -> bool:
    return SHORTCUT_PATH.is_file()


def _set_auto_start(enable: bool) -> None:
    if enable:
        target = str(Path(sys.executable).resolve())
        script = str(Path(__file__).resolve()) if not _is_frozen() else ""
        work_dir = str(Path(target).parent)
        ps = (
            f'$ws = New-Object -ComObject WScript.Shell; '
            f'$sc = $ws.CreateShortcut("{SHORTCUT_PATH}"); '
            f'$sc.TargetPath = "{target}"; '
        )
        if script:
            ps += f"$sc.Arguments = '{script}'; "
        ps += f'$sc.WorkingDirectory = "{work_dir}"; $sc.Save()'
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps],
            check=True, creationflags=subprocess.CREATE_NO_WINDOW,
        )
    else:
        SHORTCUT_PATH.unlink(missing_ok=True)


def _load_gif_frames(gif_path: Path, speed_mult: float = 1.0) -> tuple[list[QPixmap], int]:
    """用 Pillow 加载 GIF 所有帧，返回 (帧列表, 基础间隔ms)。"""
    img = Image.open(str(gif_path))
    frames: list[QPixmap] = []
    durations: list[int] = []

    for frame in ImageSequence.Iterator(img):
        # 转为 RGBA 保证透明通道
        rgba = frame.convert("RGBA")
        data = rgba.tobytes("raw", "RGBA")
        qimg = QImage(data, rgba.width, rgba.height, QImage.Format_RGBA8888)
        frames.append(QPixmap.fromImage(qimg))
        durations.append(frame.info.get("duration", 100))

    # 基础间隔取所有帧的平均 duration，再按速度倍率缩放
    avg_duration = sum(durations) / len(durations) if durations else 100
    interval = max(10, int(avg_duration / speed_mult))
    return frames, interval


class GifLabel(QLabel):
    """用 QLabel 作为窗口，Pillow 解码帧，QTimer 驱动播放。"""

    def __init__(self, gif_path: Path) -> None:
        super().__init__()
        self._drag_pos: QPoint | None = None
        self._is_on_top = True
        self._is_embedded = False

        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )

        # Pillow 加载帧
        self._frames, self._interval = _load_gif_frames(gif_path, speed_mult=5.0)
        self._frame_index = 0

        if self._frames:
            self.setFixedSize(self._frames[0].size())
            self.setPixmap(self._frames[0])

        # QTimer 驱动逐帧播放
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._next_frame)
        self._timer.start(self._interval)

    def _next_frame(self) -> None:
        self._frame_index = (self._frame_index + 1) % len(self._frames)
        self.setPixmap(self._frames[self._frame_index])

    # ── 鼠标交互 ──────────────────────────────────────────────────

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.pos()

    def mouseMoveEvent(self, event) -> None:
        if self._drag_pos is not None:
            self.move(event.globalPos() - self._drag_pos)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self._drag_pos = None

    def mouseDoubleClickEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.close()

    def contextMenuEvent(self, event) -> None:
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #1e1e1e;
                color: #e0e0e0;
                border: 1px solid #444;
                padding: 4px 0px;
            }
            QMenu::item { padding: 6px 24px; font-size: 13px; }
            QMenu::item:selected { background-color: #3a3a3a; }
        """)

        pin_text = "取消置顶" if self._is_on_top else "恢复置顶"
        pin_action = menu.addAction(pin_text)
        pin_action.triggered.connect(self._toggle_pin)

        auto_text = "☑ 开机自启动" if _is_auto_start() else "☐ 开机自启动"
        auto_action = menu.addAction(auto_text)
        auto_action.triggered.connect(self._toggle_auto_start)

        menu.addSeparator()
        quit_action = menu.addAction("退出")
        quit_action.triggered.connect(self.close)

        menu.exec_(event.globalPos())

    # ── 置顶 / 嵌入桌面 ──────────────────────────────────────────

    def _toggle_pin(self) -> None:
        self._is_on_top = not self._is_on_top
        if self._is_on_top:
            if self._is_embedded:
                user32.SetParent(int(self.winId()), 0)
                self._is_embedded = False
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
            self.show()
        else:
            workerw = _find_workerw()
            if workerw:
                user32.SetParent(int(self.winId()), workerw)
                self._is_embedded = True
            else:
                self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool)
                self.show()

    # ── 开机自启动 ────────────────────────────────────────────────

    def _toggle_auto_start(self) -> None:
        enable = not _is_auto_start()
        try:
            _set_auto_start(enable)
        except (subprocess.CalledProcessError, PermissionError) as e:
            print(f"{'开启' if enable else '关闭'}开机自启动失败：{e}")

    # ── 位置持久化 ────────────────────────────────────────────────

    def _restore_position(self) -> None:
        if not POS_FILE.is_file():
            return
        try:
            data = json.loads(POS_FILE.read_text(encoding="utf-8"))
            self.move(data["x"], data["y"])
        except (json.JSONDecodeError, KeyError):
            pass

    def _save_position(self) -> None:
        APPDATA.mkdir(parents=True, exist_ok=True)
        pos = self.pos()
        POS_FILE.write_text(
            json.dumps({"x": pos.x(), "y": pos.y()}),
            encoding="utf-8",
        )

    def closeEvent(self, event) -> None:
        self._timer.stop()
        self._save_position()
        super().closeEvent(event)
        QApplication.quit()


def main() -> None:
    gif_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_GIF
    if not gif_path.is_file():
        print(f"GIF 文件不存在：{gif_path}")
        sys.exit(1)

    app = QApplication(sys.argv)
    widget = GifLabel(gif_path)
    widget._restore_position()
    widget.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
