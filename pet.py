"""DesktopPet — 桌面宠物窗口"""
import os
from ctypes import windll

from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QMenu
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QMovie, QCursor

SIT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sit.gif")
PICK_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pick.gif")

MENU_STYLE = """
    QMenu {
        background-color: #2d2d2d;
        color: #000000;
        border: 1px solid #444444;
        padding: 4px;
    }
    QMenu::item {
        padding: 6px 24px;
    }
    QMenu::item:selected {
        background-color: #444444;
    }
"""


class DesktopPet(QWidget):
    def __init__(self):
        super().__init__()
        self._always_on_top = True
        self._setup_window()
        self._setup_gif()
        self._setup_drag_state()

    # ── 窗口 ──────────────────────────────────
    def _setup_window(self):
        self.setWindowTitle("AuraPet")
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

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
            self._drag_pos = None
        elif event.button() == Qt.RightButton:
            if self._hit_test(event.pos()):
                self._show_context_menu()

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

        top_action = menu.addAction("置顶")
        top_action.setCheckable(True)
        top_action.setChecked(self._always_on_top)

        menu.addSeparator()
        exit_action = menu.addAction("退出")

        action = menu.exec_(QCursor.pos())
        if action == top_action:
            self._toggle_always_on_top()
        elif action == exit_action:
            self._current.stop()
            from PyQt5.QtWidgets import QApplication
            QApplication.quit()

    def _toggle_always_on_top(self):
        self._always_on_top = not self._always_on_top
        flag = Qt.WindowStaysOnTopHint if self._always_on_top else 0
        self.setWindowFlags(
            Qt.FramelessWindowHint | flag | Qt.Tool
        )
        self.show()
        if not self._always_on_top:
            windll.user32.SetWindowPos(
                int(self.winId()), 1, 0, 0, 0, 0, 0x0003
            )
