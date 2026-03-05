from PySide6.QtCore import QThread, Signal
import serial as ser

class SerialThread(QThread):
    data_signal = Signal(str)  # 定义一个信号，用于发送数据到主线程

    def __init__(self, port, baudrate=9600, timeout=1):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.running = True

    def run(self):
        errorTimes = 0
        while self.running:
            try:
                with ser.Serial(self.port, self.baudrate, timeout=self.timeout) as ser_port:
                    if ser_port.in_waiting > 0:
                        data = ser_port.readline().decode('utf-8').strip()
                        self.data_signal.emit(data)  # 发送数据到主线程
            except Exception as e:
                errorTimes += 1
                print(f"Serial error: {e}")
                if errorTimes > 10:
                    print("重试失败！请重新连接")

    def stop(self):
        self.running = False