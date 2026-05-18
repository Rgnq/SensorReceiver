from PySide6.QtCore import QThread, Signal
import serial as ser
import time
import random

class SerialThread(QThread):
    data_signal = Signal(str)  # 定义一个信号，用于发送数据到主线程
    status_signal = Signal(str)
    stop_signal = Signal()

    DEBUG = False

    def __init__(self, port, baudrate=9600, timeout=1):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial = None
        self.serialState = False
        self.running = True


    def run(self):
        errorTimes = 0
        self.status_signal.emit("开始线程")
        while self.running:
            if not self.serialState:
                try:
                    if errorTimes:
                        self.status_signal.emit(f"尝试第{errorTimes}次重连")
                    self.serial = ser.Serial(port=self.port, baudrate=self.baudrate, timeout= self.timeout)
                    self.serialState = True
                    self.status_signal.emit(f"连接至{self.port}")
                    errorTimes = 0
                except Exception as e:
                    self.status_signal.emit(f"连接失败:{e}")
                    errorTimes += 1
                    if errorTimes > 5:
                        self.status_signal.emit(f"请断开后重新设置")
                        self.stop_signal.emit()
                        self.stop()
                    time.sleep(1)
                    continue
            try:
                if self.serial.in_waiting > 0:
                    line = self.serial.readline().decode('utf-8', errors='replace').strip()
                    if line:
                        self.data_signal.emit(line)
                if self.DEBUG:
                    self.data_signal.emit(self.simulate_data())  # 模拟数据发送
                        
            except Exception as e:
                self.status_signal.emit(f"错误:{e}")


    def stop(self):
        self.running = False
        self.stopSerial()
        self.status_signal.emit("线程终止")
        self.wait()
    
    def stopSerial(self):
        if self.serial or self.serialState:
            try:
                self.serial.close()
                self.serialState = False
                self.status_signal.emit(f"断开{self.port}")
            except:
                pass

    def toggleDebug(self, debug):
        self.DEBUG = debug

    def simulate_data(self, mode='gauss'):
        """模拟数据生成函数，供测试使用"""
        time.sleep(0.1)  # 模拟数据生成的时间间隔
        if mode == "uniform":
            return f'''{random.uniform(20, 30):.2f},{random.uniform(40, 60):.2f},{random.uniform(1000, 1020):.2f},
                        {random.uniform(0, 1000):.2f},
                        {random.uniform(400, 600):.2f},{random.uniform(0, 1):.2f}\r\n'''
        elif mode == "gauss":
            return f'''{random.gauss(25, 2):.2f},{random.gauss(50, 5):.2f},{random.gauss(1013, 10):.2f},
                        {random.gauss(500, 200):.2f},
                        {random.gauss(500, 50):.2f},{random.gauss(0.5, 0.1):.2f}\r\n'''