from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QDateTimeEdit,
    QComboBox, QCheckBox, QPushButton, QListWidget, QStackedWidget, QTabWidget,
    QTableWidget, QTableWidgetItem, QTextEdit, QLabel, QScrollArea
)
from PySide6.QtCore import Qt, QDateTime
import pyqtgraph as pg
import sys
from datetime import datetime
from sensor_sql import SensorDB  # 你的数据库模块


class SensorUI(QWidget):
    def __init__(self):
        super().__init__()
        self.db = SensorDB()
        self.setWindowTitle("传感器数据可视化")
        self.resize(1200, 800)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # 上下分割
        splitter = QSplitter(Qt.Vertical)
        main_layout.addWidget(splitter)

        # 上部分：筛选与操作
        top_widget = QWidget()
        top_layout = QHBoxLayout(top_widget)

        # 时间筛选
        self.chk_time = QCheckBox("启用时间筛选")
        self.dt_start = QDateTimeEdit(QDateTime.currentDateTime())
        self.dt_end = QDateTimeEdit(QDateTime.currentDateTime())
        top_layout.addWidget(self.chk_time)
        top_layout.addWidget(QLabel("开始时间:"))
        top_layout.addWidget(self.dt_start)
        top_layout.addWidget(QLabel("结束时间:"))
        top_layout.addWidget(self.dt_end)

        # 数据类型和传感器下拉框
        self.chk_category = QCheckBox("启用传感器类型")
        self.cmb_category = QComboBox()
        self.cmb_category.addItem("所有")
        self.chk_sensor = QCheckBox("启用传感器")
        self.cmb_sensor = QComboBox()
        self.cmb_sensor.addItem("所有")

        top_layout.addWidget(self.chk_category)
        top_layout.addWidget(self.cmb_category)
        top_layout.addWidget(self.chk_sensor)
        top_layout.addWidget(self.cmb_sensor)

        # 查询按钮
        self.btn_latest = QPushButton("查询最新记录")
        self.btn_all = QPushButton("查询所有记录")
        self.btn_filter = QPushButton("查询筛选条件下的记录")

        top_layout.addWidget(self.btn_latest)
        top_layout.addWidget(self.btn_all)
        top_layout.addWidget(self.btn_filter)

        splitter.addWidget(top_widget)

        # 下半部分：TabWidget 查询结果 + 日志
        bottom_tab = QTabWidget()
        splitter.addWidget(bottom_tab)

        # 查询结果Tab
        self.tab_result = QWidget()
        bottom_tab.addTab(self.tab_result, "查询结果")
        bottom_layout = QHBoxLayout(self.tab_result)

        # 左右分割（左传感器列表，右StackWidget）
        self.result_splitter = QSplitter(Qt.Horizontal)
        bottom_layout.addWidget(self.result_splitter)

        self.list_sensors = QListWidget()
        self.result_splitter.addWidget(self.list_sensors)

        self.stack_sensors = QStackedWidget()
        self.result_splitter.addWidget(self.stack_sensors)
        self.result_splitter.setStretchFactor(1, 3)

        # 日志Tab
        self.tab_log = QTextEdit()
        self.tab_log.setReadOnly(True)
        bottom_tab.addTab(self.tab_log, "日志")

        # 事件绑定
        self.btn_latest.clicked.connect(self.query_latest)
        self.btn_all.clicked.connect(self.query_all)
        self.btn_filter.clicked.connect(self.query_filtered)

        # 初始化下拉框
        self.update_comboboxes()

    # ---------------- 工具函数 ----------------
    def log(self, text):
        self.tab_log.append(text)

    def update_comboboxes(self):
        categories = self.db.query_by_time("2000-01-01 00:00:00", "2100-01-01 00:00:00").keys()
        self.cmb_category.clear()
        self.cmb_category.addItem("所有")
        self.cmb_category.addItems(categories)

        sensor_names = set()
        for cat in categories:
            sensor_names.update(self.db.query_by_time("2000-01-01 00:00:00", "2100-01-01 00:00:00", category=cat).get(cat, {}).keys())
        self.cmb_sensor.clear()
        self.cmb_sensor.addItem("所有")
        self.cmb_sensor.addItems(sensor_names)

    def clear_results(self):
        self.list_sensors.clear()
        while self.stack_sensors.count() > 0:
            widget = self.stack_sensors.widget(0)
            self.stack_sensors.removeWidget(widget)
            widget.deleteLater()

    def format_latest_results(self, rows):
        """list -> dict {category: {sensor: [(ts,value)]}}"""
        result = {}
        for cat, sensor_name, unit, value, ts in rows:
            result.setdefault(cat, {}).setdefault(sensor_name, []).append((ts, value))
        return result

    def get_filter_conditions(self):
        category = self.cmb_category.currentText() if self.chk_category.isChecked() and self.cmb_category.currentText() != "所有" else None
        sensor = self.cmb_sensor.currentText() if self.chk_sensor.isChecked() and self.cmb_sensor.currentText() != "所有" else None
        start = self.dt_start.dateTime().toPython() if self.chk_time.isChecked() else None
        end = self.dt_end.dateTime().toPython() if self.chk_time.isChecked() else None
        return category, sensor, start, end

    # ---------------- 查询功能 ----------------
    def query_latest(self):
        self.clear_results()
        category, sensor, start, end = self.get_filter_conditions()
        rows = self.db.query_latest(category=category, sensor_name=sensor)
        self.log(f"【原始数据】{rows}")  # 输出原始结果
        results = self.format_latest_results(rows)
        self.display_results(results)

    def query_all(self):
        self.clear_results()
        category, sensor, start, end = self.get_filter_conditions()
        results = self.db.query_by_time("2000-01-01 00:00:00", "2100-01-01 00:00:00", category=category, sensor_name=sensor)
        self.log(f"【原始数据】{results}")  # 输出原始结果
        self.display_results(results)

    def query_filtered(self):
        self.clear_results()
        category, sensor, start, end = self.get_filter_conditions()
        start = start or datetime(2000,1,1)
        end = end or datetime(2100,1,1)
        results = self.db.query_by_time(start, end, category=category, sensor_name=sensor)
        self.log(f"【原始数据】{results}")  # 输出原始结果
        self.display_results(results)

    # ---------------- 创建美化统计Tab ----------------
    def create_stats_tab(self, stats_dict):
        stats_widget = QWidget()
        layout = QVBoxLayout(stats_widget)
        layout.setSpacing(10)
        stat_translations = {
            "count": "计数",
            "min": "最小值",
            "max": "最大值",
            "sum": "求和",
            "avg": "平均值",
            "median": "中位数",
            "variance": "方差",
            "stddev": "标准差",
            "first": "首值",
            "last": "末值"
        }
        for key, value in stats_dict.items():
            label = QLabel(f"{stat_translations.get(key, key)}: {value}")
            label.setStyleSheet("""
                QLabel {
                    background-color: #2c2c2c;
                    color: #ffffff;
                    border: 1px solid #555;
                    border-radius: 5px;
                    padding: 5px;
                    font-weight: bold;
                }
            """)
            layout.addWidget(label)
        layout.addStretch()
        return stats_widget

    # ---------------- 显示结果 ----------------
    def display_results(self, results):
        self.update_comboboxes()
        for cat, sensors in results.items():
            for sensor_name, data_list in sensors.items():
                self.list_sensors.addItem(sensor_name)

                # 右侧滚动区
                scroll_area = QScrollArea()
                scroll_area.setWidgetResizable(True)
                container = QWidget()
                scroll_layout = QVBoxLayout(container)
                container.setLayout(scroll_layout)
                scroll_area.setWidget(container)

                tab_widget = QTabWidget()
                scroll_layout.addWidget(tab_widget)

                # 图像Tab
                plot_tab = pg.PlotWidget()
                if data_list:
                    ts, vals = zip(*data_list)
                    plot_tab.plot(list(range(len(vals))), vals, pen='r')
                tab_widget.addTab(plot_tab, "图像")

                # 统计信息Tab
                stats = self.db.stats_by_time("2000-01-01 00:00:00","2100-01-01 00:00:00", category=cat, sensor_name=sensor_name)
                stats_tab = self.create_stats_tab(stats.get(cat, {}).get(sensor_name, {}))
                tab_widget.addTab(stats_tab, "统计信息")

                # 表格Tab
                table_tab = QTableWidget()
                table_tab.setRowCount(len(data_list))
                table_tab.setColumnCount(2)
                table_tab.setHorizontalHeaderLabels(["时间", "值"])
                for i, (ts, val) in enumerate(data_list):
                    table_tab.setItem(i, 0, QTableWidgetItem(str(ts)))
                    table_tab.setItem(i, 1, QTableWidgetItem(str(val)))
                tab_widget.addTab(table_tab, "表格")

                self.stack_sensors.addWidget(scroll_area)

        if self.list_sensors.count() > 0:
            self.list_sensors.setCurrentRow(0)
            self.list_sensors.currentRowChanged.connect(lambda idx: self.stack_sensors.setCurrentIndex(idx))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = SensorUI()
    win.show()
    sys.exit(app.exec())