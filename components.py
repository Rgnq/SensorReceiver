from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame
from PySide6.QtCore import Qt

class SensorDisplayWidget(QFrame):
    def __init__(self, sensor_info: dict, parent=None):
        """
        sensor_info 示例: {"name": "温度", "unit": "℃"}
        """
        super().__init__(parent)

        self.sensor_name = sensor_info.get("name", "未知传感器")
        self.sensor_unit = sensor_info.get("unit", "")
        self.sensor_value = 0  # 初始值

        # 设置 QFrame 样式，类似卡片风格
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setStyleSheet("""
            QFrame {
                background-color: #1e1e2f;
                border-radius: 10px;
                border: 1px solid #444;
            }
            QLabel {
                color: #ffffff;
            }
            QLabel#valueLabel {
                font-size: 24px;
                font-weight: bold;
            }
            QLabel#unitLabel {
                font-size: 14px;
                color: #aaa;
            }
        """)

        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 10, 15, 10)
        main_layout.setSpacing(5)

        # 传感器名称
        self.name_label = QLabel(self.sensor_name)
        self.name_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.name_label)

        # 水平布局: 数值 + 单位
        value_layout = QHBoxLayout()
        value_layout.setAlignment(Qt.AlignCenter)

        self.value_label = QLabel(str(self.sensor_value))
        self.value_label.setObjectName("valueLabel")
        self.unit_label = QLabel(self.sensor_unit)
        self.unit_label.setObjectName("unitLabel")

        value_layout.addWidget(self.value_label)
        value_layout.addWidget(self.unit_label)

        main_layout.addLayout(value_layout)
        self.setLayout(main_layout)

    def set_value(self, value):
        """更新传感器数值"""
        self.sensor_value = value
        self.value_label.setText(str(value))


# ------------------- 测试 -------------------
if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget
    import sys
    import random

    app = QApplication(sys.argv)

    window = QWidget()
    layout = QVBoxLayout()
    window.setLayout(layout)

    sensors = [
        {"name": "温度", "unit": "℃"},
        {"name": "湿度", "unit": "%"},
        {"name": "电流", "unit": "A"},
    ]

    sensor_widgets = []
    for s in sensors:
        w = SensorDisplayWidget(s)
        layout.addWidget(w)
        sensor_widgets.append(w)

    window.show()

    # 模拟数据更新
    from PySide6.QtCore import QTimer
    def update_values():
        for w in sensor_widgets:
            w.set_value(round(random.uniform(0, 100), 1))

    timer = QTimer()
    timer.timeout.connect(update_values)
    timer.start(1000)  # 每秒更新一次

    sys.exit(app.exec())