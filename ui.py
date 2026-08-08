"""UI 模块 — 桌宠窗口、右键菜单、配色与样式"""
import os

import win32con
import win32gui
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QCursor, QMovie
from PyQt5.QtWidgets import QApplication, QLabel, QMenu, QVBoxLayout, QWidget

import settings

SIT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sit.gif")
PICK_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pick.gif")

# ── AuraPet 五色配色 ────────────────────────
COLOR_BG = '#1A1A1E'      # 背景
COLOR_CARD = '#222227'    # 卡片
COLOR_TEXT = '#ECECEF'    # 主文字
COLOR_SUB = '#9A9AA0'     # 次级文字
COLOR_ACCENT = '#4DA3FF'  # 强调
COLOR_HOVER = '#2A2A30'   # 悬停
COLOR_BORDER = '#3A3A40'  # 描边 / 分隔

MENU_STYLE = f"""
QMenu {{
    background-color: {COLOR_CARD};
    color: {COLOR_TEXT};
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    padding: 6px;
    font-family: 'Microsoft YaHei';
    font-size: 12px;
}}
QMenu::item {{
    padding: 6px 28px 6px 12px;
    border-radius: 6px;
    background: transparent;
    color: {COLOR_TEXT};
}}
QMenu::item:selected {{
    background-color: {COLOR_HOVER};
}}
QMenu::item:checked {{
    color: {COLOR_ACCENT};
}}
QMenu::indicator {{
    width: 8px;
    height: 8px;
    border: 1px solid {COLOR_BORDER};
    border-radius: 4px;
    background: transparent;
    margin-left: 8px;
}}
QMenu::indicator:checked {{
    background-color: {COLOR_ACCENT};
    border-color: {COLOR_ACCENT};
}}
QMenu::separator {{
    height: 1px;
    background: {COLOR_BORDER};
    margin: 4px 8px;
}}
"""


class DesktopPet(QWidget):
    def __init__(self):
        super().__init__()
        st = settings.load()
        self._always_on_top = st['topmost']
        self._setup_window()
        self._setup_gif()
        self._setup_drag_state()
        self._restore_pos(st['pos'])

    # ── 窗口 ──────────────────────────────────
    def _setup_window(self):
        self.setWindowTitle("AuraPet")
        # 置顶交由 win32 控制，切换时不重建窗口
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def showEvent(self, event):
        super().showEvent(event)
        if self._always_on_top:
            self._apply_topmost(True)

    # ── 置顶（pywin32）────────────────────────
    def _apply_topmost(self, on):
        win32gui.SetWindowPos(
            int(self.winId()),
            win32con.HWND_TOPMOST if on else win32con.HWND_NOTOPMOST,
            0, 0, 0, 0,
            win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE,
        )

    def _toggle_always_on_top(self):
        self._always_on_top = not self._always_on_top
        self._apply_topmost(self._always_on_top)
        settings.save(topmost=self._always_on_top)

    # ── GIF ───────────────────────────────────
    def _setup_gif(self):
        self.label = QLabel(self)
        self.label.setStyleSheet("background: transparent;")
        self.layout().addWidget(self.label)

        self.movie_sit = QMovie(SIT_PATH)
        self.movie_sit.setCacheMode(QMovie.CacheAll)
        self.movie_pick = QMovie(PICK_PATH)
        self.movie_pick.setCacheMode(QMovie.CacheAll)

        self._current = self.movie_sit
        self.label.setMovie(self._current)

        self._current.jumpToFrame(0)
        QTimer.singleShot(100, self._fit_to_gif)
        self._current.start()

    def _fit_to_gif(self):
        size = self._current.currentImage().size()
        if size.width() > 0:
            self.setFixedSize(size)
        else:
            QTimer.singleShot(100, self._fit_to_gif)

    def _switch_movie(self, target):
        """切换 GIF，同名跳过"""
        if target is self._current:
            return
        self._current.stop()
        self._current = target
        self.label.setMovie(self._current)
        self._current.start()

    # ── 鼠标事件 ──────────────────────────────
    def _setup_drag_state(self):
        self._drag_pos = None
        self._dragging = False

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            self._dragging = False

    def mouseMoveEvent(self, event):
        if self._drag_pos is None:
            return
        if event.buttons() == Qt.LeftButton:
            if not self._dragging:
                self._dragging = True
                self._switch_movie(self.movie_pick)
            self.move(event.globalPos() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self._dragging:
                self._switch_movie(self.movie_sit)
                self._dragging = False
                settings.save(pos=[self.x(), self.y()])
            self._drag_pos = None
        elif event.button() == Qt.RightButton:
            if self._hit_test(event.pos()):
                self._show_context_menu()

    # ── 位置持久化 ────────────────────────────
    def _restore_pos(self, pos):
        if not pos:
            return
        geo = QApplication.primaryScreen().availableGeometry()
        self.move(
            min(max(pos[0], geo.left()), geo.right()),
            min(max(pos[1], geo.top()), geo.bottom()),
        )

    # ── 右键菜单 ──────────────────────────────
    def _hit_test(self, pos):
        """检测点击是否在有色像素上"""
        img = self._current.currentImage()
        if img.isNull():
            return False
        x, y = pos.x(), pos.y()
        if x < 0 or y < 0 or x >= img.width() or y >= img.height():
            return False
        return img.pixelColor(x, y).alpha() > 0

    def _show_context_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet(MENU_STYLE)

        top_action = menu.addAction("取消置顶" if self._always_on_top else "置顶")
        top_action.setCheckable(True)
        top_action.setChecked(self._always_on_top)

        menu.addSeparator()
        exit_action = menu.addAction("退出")

        action = menu.exec_(QCursor.pos())
        if action == top_action:
            self._toggle_always_on_top()
        elif action == exit_action:
            self._current.stop()
            QApplication.quit()
