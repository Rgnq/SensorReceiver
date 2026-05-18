from PySide6.QtWidgets import (QWidget, QTabWidget, QListWidget, QVBoxLayout, QTableWidget, QHBoxLayout, QLabel, 
                            QToolButton, QSpacerItem, QSizePolicy, QGridLayout, QComboBox, QPushButton, 
                            QLineEdit, QTextEdit, QCheckBox, QFileDialog, QMessageBox, QCalendarWidget, 
                            QDialog, QStyle, QTableWidgetItem, QSplitter, QInputDialog, QScrollArea, QFrame,
                            QStackedWidget, QMenu, QDateTimeEdit,QHeaderView)
from PySide6.QtCore import Qt, QPropertyAnimation, Signal, QDateTime, Slot
from serial.tools import list_ports
import os, json, datetime
import pyqtgraph as pg

from Serial import SerialThread
from PlotWidget import MultiPlotWidget
from components import SensorDisplayWidget, DataModifyDialog, DataReceiverParse
import styles
from sensor_sql import SensorDB

class Homepage(QWidget):
    sendTextSignal = Signal(str)
    sendErrorSignal = Signal(str)
    sensor_config = {}  # 用于存储传感器配置数据

    def __init__(self, parent=None):
        super().__init__(parent)
        #self.setStyleSheet(HOMEPAGE_STYLE)

        self.dataBuffer = []
        self.db = SensorDB()
        self.data_cards: dict[str, dict[str, SensorDisplayWidget]] = {}  # 存储传感器数据卡片的字典，格式: {"传感器名称": {"name": data_card, ...}, ...}
        self.plot_widgets: dict[str, MultiPlotWidget] = {}  # 存储传感器对应的绘图组件，格式: {"传感器名称": plot_widget, ...}
        self.parse = DataReceiverParse(data_format="csv")  # 创建数据解析器实例
        self.pathSave = "history"
        self.anims: dict[str, QPropertyAnimation | None] = {"Sensor":None}  # 用于存储动画对象
        self.settingExpanded = False  # 记录设置面板的展开状态
        self.sensorDisplay = True
        self.runtimeSave = None

        self.initUI()

        self.command_panel.serDataSignal.connect(self.updateDataDisplay)
        self.command_panel.stopSignal.connect(self.clearData)

    def initUI(self):
        # ----------------- 主布局 -----------------
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # ----------------- 左侧监测部分 -------------------
        left_main_vertical = QVBoxLayout()
        main_layout.addLayout(left_main_vertical, stretch=4)
        # ----------------- 左右可拖拽分隔 -----------------
        horizontal_splitter = QSplitter(Qt.Horizontal)
        left_main_vertical.addWidget(horizontal_splitter, 1)

        # ----------------- 左侧滚动区域（选择传感器） -----------------
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_content = QWidget()
        left_layout = QVBoxLayout(left_content)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(5)

        # 传感器列表
        self.sensor_list = QListWidget()
        self.sensor_list.currentRowChanged.connect(self._on_sensor_selection_changed)

        left_layout.addWidget(self.sensor_list)
        left_scroll.setWidget(left_content)

        horizontal_splitter.addWidget(left_scroll)
        horizontal_splitter.setStretchFactor(0, 3)  # 左侧占比

        # ----------------- 右侧区域（StackedWidget） -----------------
        self.right_stack = QStackedWidget()
        horizontal_splitter.addWidget(self.right_stack)
        horizontal_splitter.setStretchFactor(1, 10)  # 右侧占比

        # 左侧监测部分--最下方命令输入行
        leftdown_horizontal = QHBoxLayout()
        self.sendline = QLineEdit()
        self.sendline.setPlaceholderText("输入命令并按回车发送")
        self.sendlineButton = QPushButton("发送")
        self.sendline.returnPressed.connect(self.sendText)
        self.sendlineButton.clicked.connect(self.sendText)
        leftdown_horizontal.addWidget(self.sendline)
        leftdown_horizontal.addWidget(self.sendlineButton)
        left_main_vertical.addLayout(leftdown_horizontal)

        # 设置面板
        self.command_panel = CommandPanel()  # 直接使用 SettingsPage 作为右侧设置面板
        self.command_panel.setFixedWidth(0)  # 初始宽度为0，表示收起状态
        main_layout.addWidget(self.command_panel)

        # 工具按钮
        self.toolButton = QToolButton(self)
        self.toolButton.setObjectName("toolButton")
        self.toolButton.setStyleSheet("* {background-color: #404040}")
        self.toolButton.setText("设\n置")
        self.toolButton.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.toolButton.setArrowType(Qt.DownArrow)
        sp = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.toolButton.setSizePolicy(sp)
        self.toolButton.clicked.connect(self._toggleSettingPanel)
        main_layout.addWidget(self.toolButton)

        if os.path.exists("sensor_config.json"):
            with open("sensor_config.json", "r", encoding="utf-8") as f:
                self.sensor_config = json.load(f)
                self.update_sensor_config(self.sensor_config)

    def sendText(self):
        try:
            if self.command_panel.serState:
                data = self.sendline.text()
                self.sendTextSignal.emit(f"发送: {data}")
                if self.command_panel.sendMode.isChecked():
                    if all(c in "0123456789abcdefABCDEF " for c in data):
                        data_bytes = bytes.fromhex(data)
                        self.command_panel.serThread.serial.write(data_bytes)
                    else:
                        raise Exception("非十六进制字符串")
                else:
                    self.command_panel.serThread.serial.write(data.encode('utf-8'))
                #self.sendline.setText("")
            else:
                self.sendTextSignal.emit("尚未连接")
                self.sendline.setText("")
        except Exception as e:
            self.sendErrorSignal.emit(f"发送错误: {e}")

    def updateDataDisplay(self,dataText:str):
        try:
            receive_data = self.parse.parse_csv_data(dataText)
            # 处理解析后的数据
            for sensor, data_list in receive_data.items():
                if sensor in self.data_cards:
                    for data_info in data_list:
                        card = self.data_cards[sensor].get(data_info["name"])
                        if card:
                            card.set_value(data_info["value"])
                if sensor in self.plot_widgets:
                    self.plot_widgets[sensor].update_data(data_list)
            self.db.insert_data(receive_data)

        except Exception as e:
            self.command_panel.serLogSignal.emit(f"错误：{e}")


    def clearData(self):
        for sensor_cards in self.data_cards.values():
            for card in sensor_cards.values():
                card.set_value(0)

    def _toggleSettingPanel(self):
        startWidth = self.command_panel.width()
        if self.settingExpanded:
            # 收起设置面板
            self._animateWidgetDisplay("Command", startWidth,0,self.command_panel,"maximumWidth")
            self.toolButton.setArrowType(Qt.DownArrow)
        else:
            # 展开设置面板
            self._animateWidgetDisplay("Command", startWidth,300,self.command_panel,"maximumWidth")
            self.toolButton.setArrowType(Qt.LeftArrow)
        self.settingExpanded = not self.settingExpanded

    def _animateWidgetDisplay(self, anime, start, end, widget, property, duration=200):
        self.anims[anime] = QPropertyAnimation(widget, bytes(property,encoding='utf-8'))
        self.anims[anime].setDuration(duration)
        self.anims[anime].setStartValue(start)
        self.anims[anime].setEndValue(end)
        self.anims[anime].start()

    def update_sensor_config(self, sensor_config: dict):
        self.sensor_config = sensor_config
         # 清空左侧列表和右侧Stack
        self.sensor_list.clear()
        self._clear_stacked_widget()
        self.data_cards.clear()
        
        for idx,(sensor, data_list) in enumerate(sensor_config.items()):
            self.sensor_list.addItem(f"{sensor}")
            page = self._create_sensor_page(data_list,sensor)
            self.right_stack.addWidget(page)

    def on_sensor_config_updated(self):
        if os.path.exists("sensor_config.json"):
            with open("sensor_config.json", "r", encoding="utf-8") as f:
                self.sensor_config = json.load(f)
                self.update_sensor_config(self.sensor_config)
    
    def _create_sensor_page(self, data_list: list, sensor_name: str = "传感器") -> QWidget:
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
        data_cards = self._add_data_grid(data_list, top_layout)
        self.data_cards[sensor_name] = {}
        for data_info, card in zip(data_list, data_cards):
            self.data_cards[sensor_name][data_info["name"]] = card
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
        image_page = MultiPlotWidget(data_list)
        self.plot_widgets[sensor_name] = image_page  # 存储绘图组件以便后续更新数据
        tab_widget.addTab(image_page, "图像")

        # 统计页(废弃)

        bottom_layout.addWidget(tab_widget)
        bottom_scroll.setWidget(bottom_content)
        vertical_splitter.addWidget(bottom_scroll)
        vertical_splitter.setStretchFactor(0, 2)
        vertical_splitter.setStretchFactor(1, 3)

        return page

    def _add_data_grid(self, data_list: list, layout: QGridLayout):
        data_cards = []
        for i, data in enumerate(data_list):
            data_card = SensorDisplayWidget(data)
            data_cards.append(data_card)
            row = i // 3
            col = i % 3
            layout.addWidget(data_card, row, col)
        return data_cards

    def _clear_stacked_widget(self):
        while self.right_stack.count() > 0:
            widget = self.right_stack.widget(0)
            self.right_stack.removeWidget(widget)
            widget.deleteLater()

    @Slot(int)
    def _on_sensor_selection_changed(self, current_row):
        if current_row >= 0 and current_row < self.right_stack.count():
            self.right_stack.setCurrentIndex(current_row)
    
class CommandPanel(QWidget):
    serDataSignal = Signal(str)  # 定义一个信号，用于接收串口数据
    serLogSignal = Signal(str)
    stopSignal = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.autoSaveStatus = True
        self.autoSaveInterval = 60

        self.serThread = None  # 用于存储串口线程
        self.serState = False

        self.initUI()

    def initUI(self):
        self.gridlayout = QGridLayout(self)

        self.selectPortComboBox = QComboBox()
        self.refreshPortsButton = QPushButton("刷新")
        self.connectButton = QPushButton("连/断")
        self.BaudrateLineEdit = QLineEdit()
        self.autosaveCheckBox = QCheckBox("启用")
        # self.autosaveIntervalLineEdit = QLineEdit()
        self.autosaveIntervalButton = QPushButton("设置")
        self.sendMode = QCheckBox("发送Bytes")
        self.debugmode = QCheckBox("调试模式")
        self.TextCopy = QTextEdit()
        self.TextCopy.setReadOnly(True)
        

        self.gridlayout.addWidget(QLabel("选择端口"), 0, 0)
        self.gridlayout.addWidget(self.refreshPortsButton, 0, 1)
        self.gridlayout.addWidget(self.selectPortComboBox, 1, 0)
        self.gridlayout.addWidget(self.connectButton, 1, 1)
        self.FillcomboxPorts()  # 初始化时填充可用串口列表
        self.refreshPortsButton.clicked.connect(self.FillcomboxPorts)  # 刷新按钮连接槽函数
        self.connectButton.clicked.connect(self.toggleSerialIO)


        self.gridlayout.addWidget(QLabel("波特率"), 2, 0)
        self.gridlayout.addWidget(self.debugmode, 2, 1)
        self.debugmode.stateChanged.connect(self.toggleDEBUG)
        self.gridlayout.addWidget(self.BaudrateLineEdit, 3, 0)
        self.BaudrateLineEdit.setText("9600")  # 默认波特率

        self.gridlayout.addWidget(QLabel("自动保存"), 4, 0)
        self.gridlayout.addWidget(self.autosaveCheckBox, 4, 1)
        self.autosaveCheckBox.setChecked(True)  # 默认启用自动保存

        self.gridlayout.addWidget(self.sendMode, 3, 1)
        self.sendMode.setChecked(True)

        self.gridlayout.addWidget(self.TextCopy,6,0,1,2)

        self.gridlayout.setColumnStretch(0, 4)
        self.gridlayout.setColumnStretch(1, 0)
        self.gridlayout.setColumnStretch(2, 0)
        self.gridlayout.setRowStretch(6, 1)  # 添加伸缩项，推送内容到顶部

    def FillcomboxPorts(self):
        self.selectPortComboBox.clear()
        ports = list_ports.comports()
        if ports:
            for port in ports:
                self.selectPortComboBox.addItem(port.device)
        else:
            self.selectPortComboBox.addItem("无可用串口")

    def toggleSerialIO(self):
        if self.serState:
            self.stopSerialThread()
            self.stopSignal.emit()
        else:
            self.startSerialThread()


    def startSerialThread(self):
        try:
            self.stopSerialThread()
            currentPort = self.selectPortComboBox.currentText()
            baudrate = int(self.BaudrateLineEdit.text())
            self.serThread = SerialThread(currentPort,baudrate,timeout=1)
            self.serThread.data_signal.connect(self.serDataSignal.emit)
            self.serThread.status_signal.connect(self.serLogSignal.emit)
            self.serThread.stop_signal.connect(self.stopSerialThread)
            self.serThread.start()
            self.serState = True
        except Exception as e:
            self.serDataSignal.emit(f"Error: {e}")

    def toggleDEBUG(self, state):
        if state:
            SerialThread.DEBUG = True
            self.serLogSignal.emit("调试模式已启用")
        else:
            SerialThread.DEBUG = False
            self.serLogSignal.emit("调试模式已禁用")
        
    def stopSerialThread(self):
        if self.serState:
            self.serThread.stop()
            self.serState = False
            
    
    def LogText(self,text):
        self.serDataSignal.emit(text)



class HistoryPage(QWidget):
    def __init__(self):
        super().__init__()
        self.db = SensorDB()
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # 上下分割
        splitter = QSplitter(Qt.Vertical)
        main_layout.addWidget(splitter)

        # 上部分：筛选与操作
        top_widget = QWidget()
        top_layout = QGridLayout(top_widget)

        # 时间筛选
        self.chk_time = QCheckBox("启用时间筛选")
        self.dt_start = QDateTimeEdit(QDateTime.currentDateTime())
        self.dt_end = QDateTimeEdit(QDateTime.currentDateTime())
        top_layout.addWidget(self.chk_time, 0, 0)
        top_layout.addWidget(QLabel("开始时间:"), 0, 1)
        top_layout.addWidget(self.dt_start, 0, 2)
        top_layout.addWidget(QLabel("结束时间:"), 0, 3)
        top_layout.addWidget(self.dt_end, 0, 4)

        # 数据类型和传感器下拉框
        self.chk_category = QCheckBox("启用传感器类型")
        self.cmb_category = QComboBox()
        self.cmb_category.addItem("所有")
        self.chk_sensor = QCheckBox("启用传感器")
        self.cmb_sensor = QComboBox()
        self.cmb_sensor.addItem("所有")

        top_layout.addWidget(self.chk_category, 2, 0)
        top_layout.addWidget(self.cmb_category, 2, 1)
        top_layout.addWidget(self.chk_sensor, 2, 3)
        top_layout.addWidget(self.cmb_sensor, 2, 4)

        # 查询按钮
        self.btn_latest = QPushButton("查询最新记录")
        self.btn_all = QPushButton("查询所有记录")
        self.btn_filter = QPushButton("查询筛选条件下的记录")

        top_layout.addWidget(self.btn_latest, 3, 0)
        top_layout.addWidget(self.btn_all, 3, 1)
        top_layout.addWidget(self.btn_filter, 3, 2)

        splitter.addWidget(top_widget)

        # 下半部分：TabWidget 查询结果 + 日志
        bottom_tab = QTabWidget()
        splitter.addWidget(bottom_tab)
        splitter.setStretchFactor(1, 1)
        
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
                table_tab.setSizeAdjustPolicy(QTableWidget.AdjustToContents)  # 自动调整大小
                table_tab.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)         # 第一列自适应拉伸
                table_tab.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)  # 第二列自适应内容
                table_tab.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)  # 第三列自适应内容
                table_tab.horizontalHeader().setStretchLastSection(True)  # 最后一列填充剩余空间
                table_tab.verticalHeader().setVisible(False)  # 可选：隐藏行号
                tab_widget.addTab(table_tab, "表格")

                self.stack_sensors.addWidget(scroll_area)

        if self.list_sensors.count() > 0:
            self.list_sensors.setCurrentRow(0)
            self.list_sensors.currentRowChanged.connect(lambda idx: self.stack_sensors.setCurrentIndex(idx))
 

class SettingsPage(QWidget):
    pathSaveSignal = Signal(str)
    styleSignal = Signal(str)
    sensor_config_changed = Signal()

    tmpConfig = {}  # 临时配置字典，用于存储当前设置
    sensor_config = {}  # 存储传感器配置的字典

    def __init__(self, parent=None):
        super().__init__(parent)

        

        self.dialog = QFileDialog()
        self.dialog.setWindowTitle("请选择文件夹")
        self.dialog.setFileMode(QFileDialog.FileMode.Directory)
        self.dialog.setStyleSheet('''
                    * {
                        padding: 0px;
                        border: 0px;
                        margin: 0px;
                        }    
                    ''')
        self.dialog.setOption(QFileDialog.DontUseNativeDialog, True)
        self.dialog.setWindowIcon(self.style().standardIcon(QStyle.SP_DirHomeIcon))
        
        self.initUI()

    def initUI(self):

        self.main_layout = QVBoxLayout(self)
        self.tabWidget = QTabWidget()
        self.main_layout.addWidget(self.tabWidget)
    
        tab_sensor = QWidget()
        tab_sensor_layout = QGridLayout(tab_sensor)
        tab_custom = QWidget()
        tab_custom_layout = QGridLayout(tab_custom)

        self.tabWidget.addTab(tab_sensor,"数据设置")
        self.tabWidget.addTab(tab_custom,"界面设置")
        
        #############
        # 数据设置页 #
        #############
        pathLabel = QLabel("数据保存目录")
        self.pathLineEdit = QLineEdit()
        nowDir = os.getcwd()
        self.pathLineEdit.setText(f"{nowDir}\\history")
        self.browserFileBtn = QPushButton()
        self.browserFileBtn.setText("浏览...")
        self.browserFileBtn.clicked.connect(self.select_folder)
        self.pathBtn = QPushButton()
        self.pathBtn.setText("设置")
        self.pathBtn.clicked.connect(self.on_pathBtn_click)
        tab_sensor_layout.addWidget(pathLabel,0,0)
        tab_sensor_layout.addWidget(self.pathLineEdit,1,0)
        tab_sensor_layout.addWidget(self.browserFileBtn,1,1)
        tab_sensor_layout.addWidget(self.pathBtn,1,2)
        
        # 配置传感器类型和数据格式等设置项（可扩展）
        self.action_hbox = QHBoxLayout()
        self.action_add_btn = QPushButton("添加传感器")
        self.action_remove_btn = QPushButton("移除当前传感器")
        self.action_add_data_btn = QPushButton("添加数据项")
        self.action_remove_data_btn = QPushButton("移除当前数据项")
        self.action_reset_btn = QPushButton("重置配置")
        self.action_clear_btn = QPushButton("清除配置")
        self.action_hbox.addWidget(self.action_add_btn)
        self.action_hbox.addWidget(self.action_remove_btn)
        self.action_hbox.addWidget(self.action_add_data_btn)
        self.action_hbox.addWidget(self.action_remove_data_btn)
        self.action_hbox.addWidget(self.action_reset_btn)
        self.action_hbox.addWidget(self.action_clear_btn)
        tab_sensor_layout.addLayout(self.action_hbox,2,0,1,3)

        self.splitter = QSplitter(Qt.Horizontal)
        self.sensor_list = QListWidget()
        self.data_list = QListWidget()
        self.splitter.addWidget(self.sensor_list)
        self.splitter.addWidget(self.data_list)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 4)
        tab_sensor_layout.addWidget(self.splitter,3,0,1,3)
        # ------------------------ 在初始化 UI 中添加右键菜单 ------------------------
        self.sensor_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.sensor_list.customContextMenuRequested.connect(self.show_sensor_context_menu)
        self.sensor_list.setDragDropMode(QListWidget.InternalMove)  # 支持拖动排序
        self.sensor_list.setDefaultDropAction(Qt.MoveAction)
        self.sensor_list.model().rowsMoved.connect(self.sensor_rows_moved)

        self.action_apply_btn = QPushButton("应用配置")
        tab_sensor_layout.addWidget(self.action_apply_btn,4,0,1,3)

        tab_sensor_layout.setRowStretch(3,8)
        tab_sensor_layout.setRowStretch(6,1)

        # 信号绑定
        self.action_add_btn.clicked.connect(self.add_sensor)
        self.action_remove_btn.clicked.connect(self.del_sensor)
        self.action_add_data_btn.clicked.connect(self.add_data)
        self.action_remove_data_btn.clicked.connect(self.del_data)
        self.action_reset_btn.clicked.connect(self.reset_config)
        self.action_clear_btn.clicked.connect(self.clear_config)
        self.action_apply_btn.clicked.connect(self.save_config)

        if os.path.exists("sensor_config.json"):
            with open("sensor_config.json", "r", encoding="utf-8") as f:
                self.sensor_config = json.load(f)
                self.tmpConfig = self.sensor_config.copy()
                self.update_display()

        #############
        # 界面设置页 #
        #############
        self.styleCombobox = QComboBox()
        style_dict = styles.material_styles_dict
        self.styleCombobox.addItems(style_dict.keys())
        self.styleApply = QPushButton("应用")
        self.styleApply.clicked.connect(lambda:self.styleSignal.emit(style_dict[self.styleCombobox.currentText()]))
        tab_custom_layout.addWidget(self.styleCombobox,2,0)
        tab_custom_layout.addWidget(self.styleApply,2,1)
        
        tab_custom_layout.setColumnStretch(0,1)
        tab_custom_layout.setRowStretch(3,1)

    def on_pathBtn_click(self):
        directory = self.pathLineEdit.text().strip()
        self.pathSaveSignal.emit(directory)

    ############ 动态传感器配置 ##################
    # ------------------------ 功能实现 ------------------------
    def add_sensor(self):
        name, ok = QInputDialog.getText(self, "增加传感器", "输入传感器名称:")
        if ok and name.strip():
            if name in self.tmpConfig:
                QMessageBox.warning(self, "错误", "传感器已存在")
                return
            self.tmpConfig[name] = []
            self.update_display()

    def del_sensor(self):
        if not self.tmpConfig:
            QMessageBox.warning(self, "提示", "没有传感器可删除")
            return
        sensor, ok = QInputDialog.getItem(self, "删除传感器", "选择传感器:", list(self.tmpConfig.keys()), 0, False)
        if ok:
            self.tmpConfig.pop(sensor)
            self.update_display()

    def add_data(self):
        if not self.tmpConfig:
            QMessageBox.warning(self, "提示", "请先添加传感器")
            return
        # 选择传感器
        sensor, ok = QInputDialog.getItem(self, "选择传感器", "选择传感器:", list(self.tmpConfig.keys()), 0, False)
        if ok:
            # 输入数据名字
            data_name, ok_name = QInputDialog.getText(self, "数据名字", "输入数据名称:")
            if ok_name and data_name.strip():
                # 输入单位
                unit, ok_unit = QInputDialog.getText(self, "数据单位", "输入单位:")
                if ok_unit:
                    entry = {"name": data_name, "unit": unit}
                    self.tmpConfig[sensor].append(entry)
                    self.update_display()

    def del_data(self):
        if not self.tmpConfig:
            QMessageBox.warning(self, "提示", "没有数据可删除")
            return
        # 选择传感器
        sensor, ok = QInputDialog.getItem(self, "选择传感器", "选择传感器:", list(self.tmpConfig.keys()), 0, False)
        if ok:
            if not self.tmpConfig[sensor]:
                QMessageBox.warning(self, "提示", "该传感器没有数据可删除")
                return
            # 选择数据
            data, ok_data = QInputDialog.getItem(self, "删除数据", "选择数据:", [f"{d['name']} ({d['unit']})" for d in self.tmpConfig[sensor]], 0, False)
            if ok_data:
                data = {"name": data.split(" (")[0], "unit": data.split(" (")[1][:-1]}  # 解析出名字和单位
                self.tmpConfig[sensor].remove(data)
                self.update_display()

    def reset_config(self):
        self.tmpConfig = self.sensor_config.copy()
        self.update_display()

    def clear_config(self):
        self.tmpConfig.clear()
        self.update_display()

    def save_config(self):
        self.sensor_config = {k: v.copy() for k, v in self.tmpConfig.items()}
        with open("sensor_config.json", "w", encoding="utf-8") as f:
            json.dump(self.sensor_config, f, ensure_ascii=False, indent=4)
        self.sensor_config_changed.emit()
        QMessageBox.information(self, "保存成功", "配置已保存")
    
    # ------------------------ 右键菜单实现 ------------------------
    # ------------------------ 新增方法 ------------------------
    def show_sensor_context_menu(self, pos):
        item = self.sensor_list.itemAt(pos)
        if item is None:
            return

        menu = QMenu()
        rename_action = menu.addAction("重命名传感器")
        delete_action = menu.addAction("删除传感器")
        modify_action = menu.addAction("修改数据")  # 修改为批量修改
        action = menu.exec(self.sensor_list.mapToGlobal(pos))

        if action == rename_action:
            self.rename_sensor(item)
        elif action == delete_action:
            self.delete_sensor(item)
        elif action == modify_action:
            self.modify_data_dialog()

    def rename_sensor(self, item):
        old_name = item.text()
        new_name, ok = QInputDialog.getText(self, "重命名传感器", "输入新名称:", text=old_name)
        if ok and new_name.strip():
            if new_name in self.tmpConfig:
                QMessageBox.warning(self, "错误", "该名称已存在")
                return
            # 先保存顺序
            keys = list(self.tmpConfig.keys())
            values = list(self.tmpConfig.values())
            index = keys.index(old_name)
            # 修改键名
            keys[index] = new_name
            # 重建字典
            self.tmpConfig = dict(zip(keys, values))
            self.update_display()

    def delete_sensor(self, item):
        name = item.text()
        reply = QMessageBox.question(self, "确认删除", f"确定删除传感器 {name} 吗？",
                                    QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.tmpConfig.pop(name)
            self.update_display()
    
    def modify_data_dialog(self):
        # 找到当前传感器
        sensor_row = self.sensor_list.currentRow()
        if sensor_row < 0:
            QMessageBox.warning(self, "提示", "请选择一个传感器")
            return
        sensor = self.sensor_list.item(sensor_row).text()
        dialog = DataModifyDialog(self, sensor, self.tmpConfig[sensor])
        if dialog.exec() == QDialog.Accepted:
            # 更新 tmpConfig
            self.tmpConfig[sensor] = dialog.data_list
            self.update_display()

    # ------------------------ 拖动排序实现 ------------------------
    def sensor_rows_moved(self, parent, start, end, destination, row):
        # 根据 QListWidget 的顺序重新排列 tmpConfig
        new_order = [self.sensor_list.item(i).text() for i in range(self.sensor_list.count())]
        # 用列表重建 tmpConfig 顺序
        self.tmpConfig = {k: self.tmpConfig[k] for k in new_order}
        self.update_display()

    # ------------------------ 更新显示 ------------------------
    def update_display(self):
        self.sensor_list.clear()
        self.data_list.clear()
        for sensor, data_list in self.tmpConfig.items():
            self.sensor_list.addItem(sensor)
            self.data_list.addItem(", ".join([f"{data['name']} ({data['unit']})" for data in data_list]))



    #############################################
    
    def select_folder(self):
        last_path = self.pathLineEdit.text() if self.pathLineEdit.text() else os.getcwd()
        # 弹出文件夹选择对话框
        folder_path = QFileDialog.getExistingDirectory(
            self.dialog,                    # 父窗口
            "请选择文件夹",           # 标题
            last_path,    # 默认打开的路径（上一次选择的路径）
            QFileDialog.DontUseNativeDialog
        )

        if folder_path:
            self.pathLineEdit.setText(folder_path)
            self.on_pathBtn_click()
        
class AnalysisTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        self.main_layout = QVBoxLayout(self)

        dataNames = ["温度","湿度","压强","LIGHT","CO2","TVOC",]
        valueNames = ['平均值','中位数','标准差']
        self.dataTable = QTableWidget()
        self.dataTable.setRowCount(30)
        self.dataTable.setColumnCount(30)
        self.dataTable.setHorizontalHeaderLabels([*valueNames,*['' for i in range(27)]])
        self.dataTable.setVerticalHeaderLabels([*dataNames,*['' for i in range(19)]])
        self.dataTable.resizeColumnsToContents()
        self.dataTable.setEditTriggers(self.dataTable.editTriggers().NoEditTriggers)
        self.main_layout.addWidget(self.dataTable)

    # def updateCurrent(self,dataList):
    #     for i,data in enumerate(dataList):
    #             self.currentTable.setItem(i,1,QTableWidgetItem(str(data)))

    def analysisData(self,dataList):
        if dataList:
            #data_mean = list(map(lambda x: "{:.2f}".format(sum(x)/len(x)), dataList))
            data_mean = ["{:.2f}".format(sum(x)/len(x)) for x in dataList]
            #data_median = list(map(lambda x: "{:.2f}".format((x[len(x)//2-1]+x[len(x)//2])/2) if len(x)%2==0 else "{:.2f}".format(x[(len(x)-1)//2]),list(map(sorted, dataList))))
            dataListSort = [sorted(data) for data in dataList]
            data_median = ['{:.2f}'.format((x[len(x)//2-1]+x[len(x)//2])/2) if len(x)%2==0 else '{:.2f}'.format(x[(len(x)-1)//2]) for x in dataListSort]
            #data_std = list(map(lambda mean,data: "{:.2f}".format((sum((x-eval(mean))**2 for x in data)/len(data))**(1/2)), data_mean, dataList))
            data_std = ["{:.2f}".format((sum([(x-float(mean))**2 for x in data])/len(data))**(1/2)) for mean,data in zip(data_mean,dataList)]
            data_result = [data_mean,data_median,data_std]
            for column,value in enumerate(data_result):
                for row,data in enumerate(value):
                    self.dataTable.setItem(row,column,QTableWidgetItem(data))
        else:
            self.dataTable.clearContents()

    # def analysisHistoryData(self,dataList):
    #     dataList.pop(0)
    #     data_average = list(map(lambda x: sum(x)/len(x), dataList))

class LogPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.LogLevel = 0 # 0-Error 1-Warning 2-Info
        self.levelNames = ["Error","Warning","Info"]

        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        self.LogLevelLabel = QLabel()
        self.LogLevelLabel.setText(f'日志报告等级：{self.levelNames[self.LogLevel]}')
        self.LogLevelToggleBtn = QPushButton()
        self.LogLevelToggleBtn.setText("切换")
        self.LogLevelToggleBtn.setToolTip("切换日志过滤等级")
        self.LogLevelToggleBtn.clicked.connect(self.on_LogBtn_click)

        self.clearBtn = QPushButton()
        self.clearBtn.setText("清空")
        self.clearBtn.clicked.connect(self.clearText)

        self.textedit = QTextEdit()
        self.textedit.setReadOnly(True)
        self.textedit.textChanged.connect(self.textedit.ensureCursorVisible)

        layout.addWidget(self.LogLevelLabel)
        layout.addWidget(self.LogLevelToggleBtn)
        layout.addWidget(self.clearBtn)
        layout.addWidget(self.textedit,1)
    
    def on_LogBtn_click(self):
        self.LogLevel = (self.LogLevel + 1) % 3
        self.LogLevelLabel.setText(f'日志报告等级：{self.levelNames[self.LogLevel]}')

    def clearText(self):
        self.textedit.clear()

    def append_log(self, log: str, level: int):
        if level <= self.LogLevel:
            self.textedit.append(log)