"""
IMU数据处理模块 - 处理MPU6050传感器数据，计算四元数和欧拉角
支持9轴数据融合（加速度+角速度）
"""
import math
import numpy as np
from collections import deque
from enum import Enum


class FilterType(Enum):
    """滤波器类型"""
    COMPLEMENTARY = "complementary"  # 互补滤波
    MADGWICK = "madgwick"  # Madgwick滤波
    SIMPLE = "simple"  # 简单积分


class IMUProcessor:
    """IMU数据处理器 - 融合加速度计和陀螺仪数据"""
    
    def __init__(self, sample_rate=100.0, filter_type=FilterType.COMPLEMENTARY):
        """
        初始化IMU处理器
        
        Args:
            sample_rate: 采样频率 (Hz)
            filter_type: 滤波器类型
        """
        self.sample_rate = sample_rate
        self.dt = 1.0 / sample_rate
        self.filter_type = filter_type
        
        # 四元数状态 (w, x, y, z)
        self.quaternion = np.array([1.0, 0.0, 0.0, 0.0])
        
        # 欧拉角 (roll, pitch, yaw) - 单位：弧度
        self.roll = 0.0
        self.pitch = 0.0
        self.yaw = 0.0
        
        # 互补滤波系数
        self.gyro_weight = 0.98  # 陀螺仪权重
        self.accel_weight = 0.02  # 加速度计权重
        
        # Madgwick滤波参数
        self.beta = 0.1  # 算法增益
        
        # 数据历史（用于滤波）
        self.history_size = 10
        self.accel_history = deque(maxlen=self.history_size)
        self.gyro_history = deque(maxlen=self.history_size)
        
        # 初始化缓存
        self.last_accel = np.array([0.0, 0.0, 1.0])
        self.last_gyro = np.array([0.0, 0.0, 0.0])
    
    def update(self, accel, gyro):
        """
        更新IMU状态
        
        Args:
            accel: 加速度 [ax, ay, az] (m/s² 或 g)
            gyro: 角速度 [gx, gy, gz] (rad/s 或 deg/s)
        """
        accel = np.array(accel, dtype=float)
        gyro = np.array(gyro, dtype=float)
        
        # 保存历史数据
        self.accel_history.append(accel.copy())
        self.gyro_history.append(gyro.copy())
        
        # 应用滤波选择
        if self.filter_type == FilterType.COMPLEMENTARY:
            self._update_complementary(accel, gyro)
        elif self.filter_type == FilterType.MADGWICK:
            self._update_madgwick(accel, gyro)
        else:
            self._update_simple(accel, gyro)
        
        # 更新欧拉角
        self._quaternion_to_euler()
        
        self.last_accel = accel.copy()
        self.last_gyro = gyro.copy()
    
    def _update_complementary(self, accel, gyro):
        """互补滤波 - 结合加速度计和陀螺仪"""
        # 规范化加速度
        accel_norm = np.linalg.norm(accel)
        if accel_norm > 0:
            accel = accel / accel_norm
        else:
            return
        
        # 从加速度计计算四元数（仅用于倾斜）
        accel_quat = self._accel_to_quaternion(accel)
        
        # 陀螺仪积分
        gyro_quat = self._gyro_integration(gyro)
        
        # 线性插值融合
        self.quaternion = self.gyro_weight * self._quaternion_multiply(self.quaternion, gyro_quat) + \
                         self.accel_weight * accel_quat
        
        # 规范化四元数
        self._normalize_quaternion()
    
    def _update_madgwick(self, accel, gyro):
        """Madgwick算法 - 更高级的融合滤波"""
        # 规范化加速度
        accel_norm = np.linalg.norm(accel)
        if accel_norm == 0:
            return
        accel = accel / accel_norm

        # 提取四元数分量
        q0, q1, q2, q3 = self.quaternion

        # 陀螺仪数据
        gx, gy, gz = gyro

        # 辅助变量 (用于雅可比和梯度下降)
        q0q0 = q0 * q0
        q1q1 = q1 * q1
        q2q2 = q2 * q2
        q3q3 = q3 * q3

        # 目标函数 f = [f0, f1, f2]^T
        f0 = 2.0 * (q1 * q3 - q0 * q2) - accel[0]   # 原代码中的 f0 有误，此处更正为标准形式
        f1 = 2.0 * (q0 * q1 + q2 * q3) - accel[1]
        f2 = 2.0 * (0.5 - q1q1 - q2q2) - accel[2]

        # 雅可比矩阵 J (3x4)
        J_00 = -2.0 * q2
        J_01 =  2.0 * q3
        J_02 = -2.0 * q0
        J_03 =  2.0 * q1

        J_10 =  2.0 * q1
        J_11 =  2.0 * q0
        J_12 =  2.0 * q3
        J_13 =  2.0 * q2

        J_20 = -4.0 * q1
        J_21 = -4.0 * q2
        J_22 =  0.0
        J_23 =  0.0

        # 梯度步长 step = J^T * f
        step0 = J_00 * f0 + J_10 * f1 + J_20 * f2
        step1 = J_01 * f0 + J_11 * f1 + J_21 * f2
        step2 = J_02 * f0 + J_12 * f1 + J_22 * f2
        step3 = J_03 * f0 + J_13 * f1 + J_23 * f2

        # 规范化步长
        step_norm = math.sqrt(step0*step0 + step1*step1 + step2*step2 + step3*step3)
        if step_norm > 0:
            step0 /= step_norm
            step1 /= step_norm
            step2 /= step_norm
            step3 /= step_norm

        # 梯度下降更新四元数
        q0 -= self.beta * step0
        q1 -= self.beta * step1
        q2 -= self.beta * step2
        q3 -= self.beta * step3

        # 陀螺仪积分 (四元数微分方程)
        q0 += 0.5 * (-q1 * gx - q2 * gy - q3 * gz) * self.dt
        q1 += 0.5 * ( q0 * gx + q2 * gz - q3 * gy) * self.dt
        q2 += 0.5 * ( q0 * gy - q1 * gz + q3 * gx) * self.dt
        q3 += 0.5 * ( q0 * gz + q1 * gy - q2 * gx) * self.dt

        # 规范化四元数
        norm = math.sqrt(q0*q0 + q1*q1 + q2*q2 + q3*q3)
        if norm > 0:
            self.quaternion = np.array([q0/norm, q1/norm, q2/norm, q3/norm])
    
    def _update_simple(self, accel, gyro):
        """简单积分方法"""
        # 规范化加速度
        accel_norm = np.linalg.norm(accel)
        if accel_norm > 0:
            accel = accel / accel_norm
        
        # 陀螺仪积分
        gyro_quat = self._gyro_integration(gyro)
        self.quaternion = self._quaternion_multiply(self.quaternion, gyro_quat)
        
        # 规范化
        self._normalize_quaternion()
    
    def _accel_to_quaternion(self, accel):
        """从加速度向量计算四元数（仅用于倾斜）"""
        ax, ay, az = accel
        
        # 计算pitch和roll
        pitch = math.atan2(-ax, math.sqrt(ay*ay + az*az))
        roll = math.atan2(ay, az)
        yaw = 0.0  # 加速度无法确定yaw
        
        # 欧拉角转四元数
        cy = math.cos(yaw * 0.5)
        sy = math.sin(yaw * 0.5)
        cp = math.cos(pitch * 0.5)
        sp = math.sin(pitch * 0.5)
        cr = math.cos(roll * 0.5)
        sr = math.sin(roll * 0.5)
        
        w = cy * cp * cr + sy * sp * sr
        x = cy * sp * cr + sy * cp * sr
        y = sy * cp * cr - cy * sp * sr
        z = cy * cp * sr - sy * sp * cr
        
        return np.array([w, x, y, z])
    
    def _gyro_integration(self, gyro):
        """陀螺仪角速度积分为四元数"""
        gx, gy, gz = gyro
        
        # 计算旋转量
        theta = math.sqrt(gx*gx + gy*gy + gz*gz) * self.dt
        
        if theta > 0:
            half_theta = theta * 0.5
            factor = math.sin(half_theta) / theta
            
            w = math.cos(half_theta)
            x = gx * factor
            y = gy * factor
            z = gz * factor
        else:
            w, x, y, z = 1.0, 0.0, 0.0, 0.0
        
        return np.array([w, x, y, z])
    
    def _quaternion_multiply(self, q1, q2):
        """四元数乘法"""
        w1, x1, y1, z1 = q1
        w2, x2, y2, z2 = q2
        
        w = w1*w2 - x1*x2 - y1*y2 - z1*z2
        x = w1*x2 + x1*w2 + y1*z2 - z1*y2
        y = w1*y2 - x1*z2 + y1*w2 + z1*x2
        z = w1*z2 + x1*y2 - y1*x2 + z1*w2
        
        return np.array([w, x, y, z])
    
    def _normalize_quaternion(self):
        """规范化四元数"""
        norm = np.linalg.norm(self.quaternion)
        if norm > 0:
            self.quaternion = self.quaternion / norm
    
    def _quaternion_to_euler(self):
        """四元数转欧拉角"""
        w, x, y, z = self.quaternion
        
        # Roll (φ) - 绕X轴旋转
        sinr_cosp = 2 * (w * x + y * z)
        cosr_cosp = 1 - 2 * (x*x + y*y)
        self.roll = math.atan2(sinr_cosp, cosr_cosp)
        
        # Pitch (θ) - 绕Y轴旋转
        sinp = 2 * (w * y - z * x)
        if abs(sinp) >= 1:
            self.pitch = math.copysign(math.pi / 2, sinp)
        else:
            self.pitch = math.asin(sinp)
        
        # Yaw (ψ) - 绕Z轴旋转
        siny_cosp = 2 * (w * z + x * y)
        cosy_cosp = 1 - 2 * (y*y + z*z)
        self.yaw = math.atan2(siny_cosp, cosy_cosp)
    
    def get_quaternion(self):
        """获取四元数 (w, x, y, z)"""
        return self.quaternion.copy()
    
    def get_euler_angles(self):
        """获取欧拉角 (roll, pitch, yaw) - 单位：度"""
        return (
            math.degrees(self.roll),
            math.degrees(self.pitch),
            math.degrees(self.yaw)
        )
    
    def get_euler_angles_rad(self):
        """获取欧拉角 (roll, pitch, yaw) - 单位：弧度"""
        return (self.roll, self.pitch, self.yaw)
    
    def rotate_vector(self, v):
        """使用四元数旋转向量"""
        v = np.array(v)
        
        # 构造纯四元数 (0, v)
        q_v = np.array([0, v[0], v[1], v[2]])
        
        # q * v * q^*
        q_conj = np.array([self.quaternion[0], -self.quaternion[1], -self.quaternion[2], -self.quaternion[3]])
        
        q_v_q = self._quaternion_multiply(self._quaternion_multiply(self.quaternion, q_v), q_conj)
        
        return q_v_q[1:4]
    
    def reset(self):
        """重置处理器"""
        self.quaternion = np.array([1.0, 0.0, 0.0, 0.0])
        self.roll = 0.0
        self.pitch = 0.0
        self.yaw = 0.0
        self.accel_history.clear()
        self.gyro_history.clear()


class QuaternionHelper:
    """四元数辅助函数"""
    
    @staticmethod
    def from_euler(roll, pitch, yaw):
        """从欧拉角创建四元数 (角度单位：弧度)"""
        cy = math.cos(yaw * 0.5)
        sy = math.sin(yaw * 0.5)
        cp = math.cos(pitch * 0.5)
        sp = math.sin(pitch * 0.5)
        cr = math.cos(roll * 0.5)
        sr = math.sin(roll * 0.5)
        
        w = cy * cp * cr + sy * sp * sr
        x = cy * sp * cr + sy * cp * sr
        y = sy * cp * cr - cy * sp * sr
        z = cy * cp * sr - sy * sp * cr
        
        return np.array([w, x, y, z])
    
    @staticmethod
    def to_euler(q):
        """四元数转欧拉角"""
        w, x, y, z = q
        
        sinr_cosp = 2 * (w * x + y * z)
        cosr_cosp = 1 - 2 * (x*x + y*y)
        roll = math.atan2(sinr_cosp, cosr_cosp)
        
        sinp = 2 * (w * y - z * x)
        if abs(sinp) >= 1:
            pitch = math.copysign(math.pi / 2, sinp)
        else:
            pitch = math.asin(sinp)
        
        siny_cosp = 2 * (w * z + x * y)
        cosy_cosp = 1 - 2 * (y*y + z*z)
        yaw = math.atan2(siny_cosp, cosy_cosp)
        
        return roll, pitch, yaw
    
    @staticmethod
    def to_rotation_matrix(q):
        """四元数转旋转矩阵 (3x3)"""
        w, x, y, z = q
        
        xx = x*x
        yy = y*y
        zz = z*z
        xy = x*y
        xz = x*z
        yz = y*z
        wx = w*x
        wy = w*y
        wz = w*z
        
        matrix = np.array([
            [1-2*(yy+zz), 2*(xy-wz), 2*(xz+wy)],
            [2*(xy+wz), 1-2*(xx+zz), 2*(yz-wx)],
            [2*(xz-wy), 2*(yz+wx), 1-2*(xx+yy)]
        ])
        
        return matrix
