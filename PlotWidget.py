import time
from PySide6.QtWidgets import QMainWindow, QTabWidget, QWidget, QVBoxLayout, QGridLayout, QFileDialog
import pyqtgraph as pg
from pyqtgraph.widgets.FileDialog import FileDialog

original_file_dialog_init = FileDialog.__init__

def patched_init(self, *args, **kwargs):
    """替换FileDialog的__init__方法"""
    original_file_dialog_init(self, *args, **kwargs)

    self.setOption(QFileDialog.Option.DontUseNativeDialog, True)
    self.setStyleSheet('''* {padding: 0px;border: 0px;margin: 0px;}''')
    
FileDialog.__init__ = patched_init

class SensorPlotter(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sensor Data Plotter")
        self.setGeometry(100, 100, 1200, 800)

        self.start_time = time.time()
        self.relative_time = True

        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        # BH1750 Tab
        bh_tab = QWidget()
        bh_layout = QGridLayout()
        self.bh_plots = {}
        self.bh_curves = {}
        self.bh_data = {name: {'x': [], 'y': []} for name in ['LIGHT']}
        for i, name in enumerate(['LIGHT']):
            pw = pg.PlotWidget()
            pw.setTitle(name)
            pw.setLabel('bottom', 'Time (s)')
            pw.setLabel('left', '强度 (lux)')
            curve = pw.plot(pen=pg.mkPen('r'))
            self.bh_plots[name] = pw
            self.bh_curves[name] = curve
            bh_layout.addWidget(pw, i // 3, i % 3)  # 2 rows x 3 columns for better layout
        bh_tab.setLayout(bh_layout)
        self.tab_widget.addTab(bh_tab, "BH1750传感器")

        # Gas Sensor Tab
        gas_tab = QWidget()
        gas_layout = QVBoxLayout()
        self.gas_plots = {}
        self.gas_curves = {}
        self.gas_data = {name: {'x': [], 'y': []} for name in ['CO2', 'TVOC']}
        for name in ['CO2', 'TVOC']:
            pw = pg.PlotWidget()
            pw.setTitle(name)
            pw.setLabel('bottom', 'Time (s)')
            pw.setLabel('left', 'Value')
            curve = pw.plot(pen=pg.mkPen('g'))
            self.gas_plots[name] = pw
            self.gas_curves[name] = curve
            gas_layout.addWidget(pw)
        gas_tab.setLayout(gas_layout)
        self.tab_widget.addTab(gas_tab, "气体传感器")

        # Temp Hum Press Sensor Tab
        thp_tab = QWidget()
        thp_layout = QVBoxLayout()
        self.thp_plots = {}
        self.thp_curves = {}
        self.thp_data = {name: {'x': [], 'y': []} for name in ['温度', '湿度', '压强']}
        for name in ['温度', '湿度', '压强']:
            pw = pg.PlotWidget()
            pw.setTitle(name)
            pw.setLabel('bottom', 'Time (s)')
            pw.setLabel('left', 'Value')
            curve = pw.plot(pen=pg.mkPen('b'))
            self.thp_plots[name] = pw
            self.thp_curves[name] = curve
            thp_layout.addWidget(pw)
        thp_tab.setLayout(thp_layout)
        self.tab_widget.addTab(thp_tab, "温湿压传感器")

        # Max data points to keep (to prevent memory issues)
        self.max_points = 1000

    def _update_plot(self, data_dict, curve, x_list, y_list, value):
        current_time = time.time() - self.start_time
        if not self.relative_time:
            self.use_relative_time_axis()
        x_list.append(current_time)
        y_list.append(value)
        if len(x_list) > self.max_points:
            x_list.pop(0)
            y_list.pop(0)
        curve.setData(x_list, y_list)

    def update_bh(self, data):
        """
        Update BH1750 plots. data should be a dict with keys 'LIGHT'
        """
        for name in ['LIGHT']:
            if name in data:
                self._update_plot(self.bh_data[name], self.bh_curves[name],
                                  self.bh_data[name]['x'], self.bh_data[name]['y'], data[name])

    def update_gas(self, data):
        """
        Update Gas Sensor plots. data should be a dict with keys 'CO2', 'TVOC'
        """
        for name in ['CO2', 'TVOC']:
            if name in data:
                self._update_plot(self.gas_data[name], self.gas_curves[name],
                                  self.gas_data[name]['x'], self.gas_data[name]['y'], data[name])

    def update_thp(self, data):
        """
        Update Temp Hum Press plots. data should be a dict with keys '温度', '湿度', '压强'
        """
        for name in ['温度', '湿度', '压强']:
            if name in data:
                self._update_plot(self.thp_data[name], self.thp_curves[name],
                                  self.thp_data[name]['x'], self.thp_data[name]['y'], data[name])

    def reset(self):
        """
        Clear all plots, data, and reset time to zero.
        """
        self.start_time = time.time()
        self.relative_time = True
        data_groups = [self.bh_data, self.gas_data, self.thp_data]
        curve_groups = [self.bh_curves, self.gas_curves, self.thp_curves]
        for data_dict in data_groups:
            for name in data_dict:
                data_dict[name]['x'] = []
                data_dict[name]['y'] = []
        for curves in curve_groups:
            for curve in curves.values():
                curve.setData([], [])

    def load_bh_history(self, history_data):
        """
        Load historical data for BH1750 with absolute times.
        history_data should be a dict like {'LIGHT': {'times': [t1, t2, ...], 'values': [v1, v2, ...]}, ...}
        """
        if self.relative_time:
            self.relative_time = False

            # 为所有 BH plot 设置日期时间轴（只需设置一次）
            for name in self.bh_plots:
                plot_widget = self.bh_plots[name]
                # 替换默认的 AxisItem 为 DateAxisItem
                plot_widget.setAxisItems({'bottom': pg.DateAxisItem(orientation='bottom')})
                # 可选：调整显示格式（默认已经比较友好）
                # plot_widget.getAxis('bottom').setLabel(text='时间')

        for name in self.bh_data:
            if name in history_data:
                times = history_data[name]['times']
                values = history_data[name]['values']
                if len(times) == len(values):
                    self.bh_data[name]['x'] = times
                    self.bh_data[name]['y'] = values
                    self.bh_curves[name].setData(times, values)

    def load_gas_history(self, history_data):
        """
        Load historical data for Gas Sensor with absolute times.
        history_data should be a dict like {'CO2': {'times': [t1, t2, ...], 'values': [v1, v2, ...]}, ...}
        """
        if self.relative_time:
            self.relative_time = False
            
            # 为所有 Gas plot 设置日期时间轴（只需设置一次）
            for name in self.gas_plots:
                plot_widget = self.gas_plots[name]
                plot_widget.setAxisItems({'bottom': pg.DateAxisItem(orientation='bottom')})

        for name in self.gas_data:
            if name in history_data:
                times = history_data[name]['times']
                values = history_data[name]['values']
                if len(times) == len(values):
                    self.gas_data[name]['x'] = times
                    self.gas_data[name]['y'] = values
                    self.gas_curves[name].setData(times, values)

    def load_thp_history(self, history_data):
        """
        Load historical data for Temp Hum Press Sensor with absolute times.
        history_data should be a dict like {'温度': {'times': [t1, t2, ...], 'values': [v1, v2, ...]}, ...}
        """
        if self.relative_time:
            self.relative_time = False

            # 为所有 THP plot 设置日期时间轴（只需设置一次）
            for name in self.thp_plots:
                plot_widget = self.thp_plots[name]
                plot_widget.setAxisItems({'bottom': pg.DateAxisItem(orientation='bottom')})

        for name in self.thp_data:
            if name in history_data:
                times = history_data[name]['times']
                values = history_data[name]['values']
                if len(times) == len(values):
                    self.thp_data[name]['x'] = times
                    self.thp_data[name]['y'] = values
                    self.thp_curves[name].setData(times, values)

    def use_relative_time_axis(self):
        self.relative_time = True
        for plots in [self.bh_plots, self.gas_plots, self.thp_plots]:
            for pw in plots.values():
                pw.setAxisItems({'bottom': pg.AxisItem(orientation='bottom')})
                pw.setLabel('bottom', 'Time (s)')