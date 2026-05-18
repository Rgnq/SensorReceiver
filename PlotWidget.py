from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QApplication, QScrollArea, QSizePolicy, QFileDialog
)
from PySide6.QtCore import QTimer, Qt
import pyqtgraph as pg
from datetime import datetime
import sys
from pyqtgraph.widgets.FileDialog import FileDialog

original_file_dialog_init = FileDialog.__init__

def patched_init(self, *args, **kwargs):
    """替换FileDialog的__init__方法"""
    original_file_dialog_init(self, *args, **kwargs)

    self.setOption(QFileDialog.Option.DontUseNativeDialog, True)
    self.setStyleSheet('''* {padding: 0px;border: 0px;margin: 0px;}''')
    
FileDialog.__init__ = patched_init

class MultiPlotWidget(QWidget):
    def __init__(self, plot_infos, max_points=100000):
        """
        plot_infos: [{"name": "name1", "unit": "unit1"}, ...]
        max_points: 每条曲线最大点数
        """
        super().__init__()
        self.plot_infos = plot_infos
        self.max_points = max_points  # 最大点数
        self.plots = {}  
        self.curves = {}
        self.data_x = {} # 保存时间戳
        self.data_y = {}

        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5,5,5,5)
        main_layout.setSpacing(5)

        # --- 顶部按钮 ---
        top_layout = QHBoxLayout()
        top_layout.addStretch()
        self.btn_toggle_bg = QPushButton("背景切换")
        self.btn_color_pick = QPushButton("曲线颜色")
        top_layout.addWidget(self.btn_toggle_bg)
        top_layout.addWidget(self.btn_color_pick)
        main_layout.addLayout(top_layout)

        # --- 滚动绘图区域 ---
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(scroll_content)
        self.scroll_layout.setContentsMargins(0,0,0,0)
        self.scroll_layout.setSpacing(10)

        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

        # --- 创建图表 ---
        for info in self.plot_infos:
            pw = pg.PlotWidget(title=info["name"])
            pw.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            pw.setFixedHeight(200)
            pw.showGrid(x=True, y=True)
            pw.setLabel('left', text=info["unit"])
            pw.setLabel('bottom', text="Time")
            curve = pw.plot([], [], pen=pg.mkPen(width=2))

            self.plots[info["name"]] = pw
            self.curves[info["name"]] = curve
            self.data_x[info["name"]] = []
            self.data_y[info["name"]] = []

            self.scroll_layout.addWidget(pw)

        self.scroll_layout.addStretch()

    def update_data(self, data_list, display_count=40):
        """
        data_list: [{'name': '温度', 'value': 25.3}, ...]
        """
        now_ts = datetime.now().timestamp()
        for data in data_list:
            name = data['name']
            value = data['value']
            if name in self.plots:
                # 保存数据
                self.data_x[name].append(now_ts)
                self.data_y[name].append(value)

                # 限制最大点数
                if len(self.data_x[name]) > self.max_points:
                    self.data_x[name] = self.data_x[name][-self.max_points:]
                    self.data_y[name] = self.data_y[name][-self.max_points:]

                # 更新曲线
                self.curves[name].setData(self.data_x[name], self.data_y[name])

                # 横坐标显示格式化时间 & 间隔显示标签
                tick_labels = []
                interval = max(1, display_count // 8)
                for i, ts in enumerate(self.data_x[name]):
                    if i % interval == 0:
                        tick_labels.append((ts, datetime.fromtimestamp(ts).strftime("%H:%M:%S")))
                self.plots[name].getAxis('bottom').setTicks([tick_labels])

                # 自动追随最新点，显示最近40个点
                total_points = len(self.data_x[name])
                if total_points <= display_count:
                    x_min = self.data_x[name][0]
                else:
                    x_min = self.data_x[name][-display_count]
                x_max = self.data_x[name][-1]
                self.plots[name].setXRange(x_min, x_max, padding=0.05)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    infos = [
        {"name": "温度", "unit": "℃"},
        {"name": "湿度", "unit": "%"},
        {"name": "压力", "unit": "Pa"}
    ]
    widget = MultiPlotWidget(infos)
    widget.resize(800, 600)
    widget.show()

    # 模拟动态更新
    import random
    def add_data():
        widget.update_data([
            {"name": "温度", "value": random.uniform(20,30)},
            {"name": "湿度", "value": random.uniform(40,60)},
            {"name": "压力", "value": random.uniform(1000,1100)}
        ])
    timer = QTimer()
    timer.timeout.connect(add_data)
    timer.start(100)

    sys.exit(app.exec())