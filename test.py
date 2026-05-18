from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QScrollArea, QListWidget, QStackedWidget,
    QGridLayout, QTabWidget, QTextEdit, QLabel, QFrame
)
from PySide6.QtCore import Qt
import sys

class ModernPage(QWidget):
    def __init__(self):
        super().__init__()

        # ----------------- 主布局 -----------------
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # ----------------- 左右可拖拽分隔 -----------------
        horizontal_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(horizontal_splitter)

        # ----------------- 左侧滚动区域（选择传感器） -----------------
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_content = QWidget()
        left_layout = QVBoxLayout(left_content)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(5)

        # 测试：添加一些传感器列表
        sensor_list = QListWidget()
        for i in range(20):
            sensor_list.addItem(f"传感器 {i+1}")

        left_layout.addWidget(sensor_list)
        left_scroll.setWidget(left_content)

        horizontal_splitter.addWidget(left_scroll)
        horizontal_splitter.setStretchFactor(0, 1)  # 左侧占比

        # ----------------- 右侧区域（StackedWidget） -----------------
        right_stack = QStackedWidget()
        horizontal_splitter.addWidget(right_stack)
        horizontal_splitter.setStretchFactor(1, 3)  # 右侧占比

        # ----------------- 每个右侧页面 -----------------
        for i in range(20):  # 假设有20个传感器对应页面
            page = QWidget()
            page_layout = QVBoxLayout(page)
            page_layout.setContentsMargins(0, 0, 0, 0)
            page_layout.setSpacing(5)

            # 右侧上下分割器
            vertical_splitter = QSplitter(Qt.Vertical)
            page_layout.addWidget(vertical_splitter)

            # 上部滚动区 + 网格布局
            top_scroll = QScrollArea()
            top_scroll.setWidgetResizable(True)
            top_content = QWidget()
            top_layout = QGridLayout(top_content)
            top_layout.setContentsMargins(5, 5, 5, 5)
            top_layout.setSpacing(10)

            # 测试网格
            for row in range(3):
                for col in range(3):
                    lbl = QLabel(f"数据 {row},{col}")
                    lbl.setFrameShape(QFrame.Box)
                    lbl.setAlignment(Qt.AlignCenter)
                    top_layout.addWidget(lbl, row, col)

            top_scroll.setWidget(top_content)
            vertical_splitter.addWidget(top_scroll)

            # 下部滚动区 + TabWidget
            bottom_scroll = QScrollArea()
            bottom_scroll.setWidgetResizable(True)
            bottom_content = QWidget()
            bottom_layout = QVBoxLayout(bottom_content)
            bottom_layout.setContentsMargins(0, 0, 0, 0)
            bottom_layout.setSpacing(5)

            tab_widget = QTabWidget()
            # 图像页
            image_page = QLabel("图像区域")
            image_page.setAlignment(Qt.AlignCenter)
            tab_widget.addTab(image_page, "图像")

            # 统计页
            stats_page = QLabel("统计数值区域")
            stats_page.setAlignment(Qt.AlignCenter)
            tab_widget.addTab(stats_page, "统计")

            bottom_layout.addWidget(tab_widget)
            bottom_scroll.setWidget(bottom_content)
            vertical_splitter.addWidget(bottom_scroll)

            right_stack.addWidget(page)

        # ----------------- 连接左侧列表切换右侧StackedWidget -----------------
        def on_sensor_selected(index):
            if index >= 0 and index < right_stack.count():
                right_stack.setCurrentIndex(index)

        sensor_list.currentRowChanged.connect(on_sensor_selected)


# ----------------- 测试运行 -----------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ModernPage()
    window.resize(1200, 800)
    window.show()
    sys.exit(app.exec())