"""
3D姿态显示测试脚本
演示IMUProcessor和AttitudeVisualizer的使用
"""

import sys
import math
import numpy as np
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QSlider, QLabel, QPushButton, 
                               QComboBox, QDoubleSpinBox, QGroupBox, QGridLayout)
from PySide6.QtCore import Qt, QTimer, Signal

from imu_processor import IMUProcessor, FilterType
from AttitudeVisualizer import AttitudeVisualizer


class IMUSimulator:
    """模拟IMU数据的生成器"""
    
    def __init__(self):
        self.time = 0
        self.dt = 0.01  # 采样周期
        self.amplitude = 30.0  # 角度幅度
        
    def get_data(self):
        """获取模拟的加速度和角速度数据"""
        # 模拟缓慢旋转的欧拉角
        roll = self.amplitude * math.sin(self.time * 0.5)
        pitch = self.amplitude * math.sin(self.time * 0.3 + 1.57)
        yaw = self.amplitude * math.sin(self.time * 0.2 + 3.14)
        
        # 计算重力向量（仅基于roll和pitch）
        roll_rad = math.radians(roll)
        pitch_rad = math.radians(pitch)
        
        ax = -math.sin(pitch_rad)
        ay = math.sin(roll_rad) * math.cos(pitch_rad)
        az = math.cos(roll_rad) * math.cos(pitch_rad)
        
        # 添加噪声
        noise_level = 0.02
        ax += np.random.normal(0, noise_level)
        ay += np.random.normal(0, noise_level)
        az += np.random.normal(0, noise_level)
        
        # 规范化
        norm = math.sqrt(ax*ax + ay*ay + az*az)
        if norm > 0:
            ax, ay, az = ax/norm, ay/norm, az/norm
        
        # 角速度（微分）
        gx = math.cos(self.time * 0.5) * 0.5 * 0.017453  # rad/s
        gy = math.cos(self.time * 0.3 + 1.57) * 0.3 * 0.017453
        gz = math.cos(self.time * 0.2 + 3.14) * 0.2 * 0.017453
        
        self.time += self.dt
        
        return [ax, ay, az], [gx, gy, gz]


class IMUTestWindow(QMainWindow):
    """IMU测试窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("3D姿态显示测试")
        self.setGeometry(100, 100, 1400, 900)
        
        # 创建中央widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)
        
        # 左侧：3D可视化
        self.visualizer = AttitudeVisualizer()
        layout.addWidget(self.visualizer, stretch=3)
        
        # 右侧：控制面板
        control_panel = self._create_control_panel()
        layout.addWidget(control_panel, stretch=1)
        
        # 初始化IMU处理器和模拟器
        self.imu_processor = IMUProcessor(sample_rate=100.0, filter_type=FilterType.COMPLEMENTARY)
        self.simulator = IMUSimulator()
        
        # 定时器用于更新数据
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_data)
        self.timer.start(10)  # 10ms更新一次
        
        self.is_running = True
    
    def _create_control_panel(self):
        """创建控制面板"""
        panel = QGroupBox("控制面板")
        layout = QVBoxLayout()
        
        # 滤波器选择
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("滤波器:"))
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["互补滤波", "Madgwick", "简单积分"])
        self.filter_combo.currentIndexChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self.filter_combo)
        layout.addLayout(filter_layout)
        
        # 加速度计权重
        accel_weight_layout = QHBoxLayout()
        accel_weight_layout.addWidget(QLabel("加速度权重:"))
        self.accel_weight_spinbox = QDoubleSpinBox()
        self.accel_weight_spinbox.setRange(0.0, 1.0)
        self.accel_weight_spinbox.setSingleStep(0.01)
        self.accel_weight_spinbox.setValue(0.02)
        self.accel_weight_spinbox.valueChanged.connect(self._on_accel_weight_changed)
        accel_weight_layout.addWidget(self.accel_weight_spinbox)
        layout.addLayout(accel_weight_layout)
        
        # 陀螺仪权重
        gyro_weight_layout = QHBoxLayout()
        gyro_weight_layout.addWidget(QLabel("陀螺仪权重:"))
        self.gyro_weight_spinbox = QDoubleSpinBox()
        self.gyro_weight_spinbox.setRange(0.0, 1.0)
        self.gyro_weight_spinbox.setSingleStep(0.01)
        self.gyro_weight_spinbox.setValue(0.98)
        self.gyro_weight_spinbox.valueChanged.connect(self._on_gyro_weight_changed)
        gyro_weight_layout.addWidget(self.gyro_weight_spinbox)
        layout.addLayout(gyro_weight_layout)
        
        # 欧拉角显示
        layout.addWidget(QLabel("当前欧拉角:"))
        self.roll_label = QLineEdit()
        self.roll_label.setReadOnly(True)
        self.pitch_label = QLineEdit()
        self.pitch_label.setReadOnly(True)
        self.yaw_label = QLineEdit()
        self.yaw_label.setReadOnly(True)
        
        layout.addWidget(QLabel("Roll: "))
        layout.addWidget(self.roll_label)
        layout.addWidget(QLabel("Pitch: "))
        layout.addWidget(self.pitch_label)
        layout.addWidget(QLabel("Yaw: "))
        layout.addWidget(self.yaw_label)
        
        # 按钮
        reset_button = QPushButton("重置视图")
        reset_button.clicked.connect(self.visualizer.reset_view)
        layout.addWidget(reset_button)
        
        pause_button = QPushButton("暂停/继续")
        pause_button.clicked.connect(self._toggle_pause)
        layout.addWidget(pause_button)
        
        layout.addStretch()
        
        panel.setLayout(layout)
        return panel
    
    def _update_data(self):
        """更新IMU数据"""
        if not self.is_running:
            return
        
        # 获取模拟数据
        accel, gyro = self.simulator.get_data()
        
        # 更新IMU处理器
        self.imu_processor.update(accel, gyro)
        
        # 获取欧拉角
        roll, pitch, yaw = self.imu_processor.get_euler_angles()
        
        # 更新3D可视化
        self.visualizer.set_euler_angles(roll, pitch, yaw)
        self.visualizer.update()
        
        # 更新标签
        self.roll_label.setText(f"{roll:.1f}°")
        self.pitch_label.setText(f"{pitch:.1f}°")
        self.yaw_label.setText(f"{yaw:.1f}°")
    
    def _on_filter_changed(self, index):
        """滤波器改变"""
        filter_types = [FilterType.COMPLEMENTARY, FilterType.MADGWICK, FilterType.SIMPLE]
        self.imu_processor.filter_type = filter_types[index]
        self.imu_processor.reset()
    
    def _on_accel_weight_changed(self, value):
        """加速度权重改变"""
        self.imu_processor.accel_weight = value
        self.imu_processor.gyro_weight = 1.0 - value
        self.gyro_weight_spinbox.blockSignals(True)
        self.gyro_weight_spinbox.setValue(1.0 - value)
        self.gyro_weight_spinbox.blockSignals(False)
    
    def _on_gyro_weight_changed(self, value):
        """陀螺仪权重改变"""
        self.imu_processor.gyro_weight = value
        self.imu_processor.accel_weight = 1.0 - value
        self.accel_weight_spinbox.blockSignals(True)
        self.accel_weight_spinbox.setValue(1.0 - value)
        self.accel_weight_spinbox.blockSignals(False)
    
    def _toggle_pause(self):
        """暂停/继续"""
        self.is_running = not self.is_running


def main():
    """主函数"""
    app = QApplication(sys.argv)
    window = IMUTestWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
