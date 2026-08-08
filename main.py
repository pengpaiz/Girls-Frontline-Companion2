"""AuraPet — 桌面宠物入口"""
import sys
from PyQt5.QtWidgets import QApplication
from ui import DesktopPet


def main():
    app = QApplication(sys.argv)
    pet = DesktopPet()
    pet.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
