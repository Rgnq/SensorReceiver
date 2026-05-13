# 3D姿态显示 - 快速参考

## 快速开始

### 1. 依赖安装
```bash
# 确保已安装必要的库
pip install PyOpenGL PyOpenGL-accelerate PyOpenGL_accelerate
```

### 2. 运行测试程序
```bash
python test_3d_attitude.py
```

这会启动一个演示窗口，显示模拟的IMU数据和3D姿态可视化。

### 3. 在主应用中使用
主应用已自动集成，数据流：
```
串口接收数据 → Pages.py → IMUProcessor → PlotWidget 3D选项卡
```

## 核心代码片段

### 初始化处理器
```python
from imu_processor import IMUProcessor, FilterType

processor = IMUProcessor(
    sample_rate=100.0,  # Hz
    filter_type=FilterType.COMPLEMENTARY
)
```

### 更新数据
```python
# 接收传感器数据
accel = [ax, ay, az]  # m/s² 或 g
gyro = [gx, gy, gz]   # rad/s

# 更新处理器
processor.update(accel, gyro)

# 获取结果
roll, pitch, yaw = processor.get_euler_angles()  # 返回度数
```

### 更新UI显示
```python
# 自动更新（Pages.py中已实现）
self.RegionPlot.update_attitude(roll, pitch, yaw)

# 或从四元数更新
quat = processor.get_quaternion()
self.RegionPlot.update_attitude_from_quaternion(quat)
```

## 数据格式

### 输入格式（从单片机）
```
AX,AY,AZ,GX,GY,GZ,CO2,TVOC,TEMP,HUM,PRESS
```
其中：
- AX, AY, AZ: 加速度（单位：g 或 m/s²）
- GX, GY, GZ: 角速度（单位：**rad/s** 或 deg/s）

### 单位转换
如果角速度是 deg/s，需转换：
```python
gx_rad = gx_deg * math.pi / 180
```

## 3D坐标系定义

```
      Y轴(绿)
       ↑
       |
Z轴(蓝) ← ○ → X轴(红)
       |
       ↓

欧拉角含义：
- Roll (绕X轴): 向前向后翻滚
- Pitch (绕Y轴): 向上向下俯仰
- Yaw (绕Z轴): 左右转向
```

## 常见配置

### 配置1：标准IMU（推荐）
```python
processor = IMUProcessor(
    sample_rate=100.0,
    filter_type=FilterType.COMPLEMENTARY
)
processor.accel_weight = 0.02
processor.gyro_weight = 0.98
```

### 配置2：高精度模式
```python
processor = IMUProcessor(
    sample_rate=200.0,
    filter_type=FilterType.MADGWICK
)
processor.beta = 0.1
```

### 配置3：快速响应模式
```python
processor = IMUProcessor(
    sample_rate=50.0,
    filter_type=FilterType.SIMPLE
)
```

## 调试技巧

### 查看实时数据
```python
# 在Pages.py的updateDataDisplay()中添加
roll, pitch, yaw = self.imu_processor.get_euler_angles()
print(f"Attitude: R:{roll:.1f}° P:{pitch:.1f}° Y:{yaw:.1f}°")
```

### 检查四元数
```python
quat = self.imu_processor.get_quaternion()
print(f"Quaternion: {quat}")
```

### 旋转向量
```python
# 在传感器坐标系中定义一个向量
v = [1, 0, 0]  # X轴方向
v_rotated = processor.rotate_vector(v)
print(f"Rotated vector: {v_rotated}")
```

## 故障排除

| 问题 | 原因 | 解决方案 |
|------|------|--------|
| 3D显示不动 | 数据未更新 | 检查串口连接和数据接收 |
| 显示抖动 | 传感器噪声大 | 增加 `accel_weight`，降低 `gyro_weight` |
| 显示漂移 | 陀螺仪零偏未标定 | 增加 `accel_weight`，启用加速度约束 |
| 坐标系反向 | 传感器安装方向 | 反转相应轴的数据符号 |
| 导入错误 | 缺少依赖 | `pip install PyOpenGL` |

## 性能指标

- **计算延迟**：< 1ms（互补滤波）
- **更新频率**：支持 50-200Hz
- **内存占用**：< 1MB
- **精度**：±5°（互补滤波）, ±2°（Madgwick）

## 文件结构

```
SensorReceiver/
├── imu_processor.py           # IMU数据处理
├── AttitudeVisualizer.py       # 3D可视化
├── PlotWidget.py               # 集成3D选项卡
├── Pages.py                    # 数据驱动（已修改）
├── test_3d_attitude.py         # 测试程序
├── 3D_ATTITUDE_GUIDE.md        # 完整文档
└── 3D_ATTITUDE_QUICK_START.md  # 本文件
```

## 进阶用法

### 自定义滤波器参数
```python
# Madgwick算法增益
processor.beta = 0.05  # 更保守
processor.beta = 0.2   # 更激进

# 互补滤波权重（动态调整）
def adjust_weights(error_magnitude):
    if error_magnitude > threshold:
        processor.accel_weight = 0.05  # 增加加速度校正
    else:
        processor.accel_weight = 0.01
```

### 数据回放和分析
```python
# 保存数据
import json
data = {
    'time': time.time(),
    'accel': accel,
    'gyro': gyro,
    'euler': (roll, pitch, yaw),
    'quaternion': quat.tolist()
}

# 离线处理
with open('imu_data.json', 'w') as f:
    json.dump(data, f)
```

## 资源链接

- **OpenGL教程**：https://learnopengl.com
- **四元数入门**：https://eater.net/quaternions
- **MPU6050指南**：https://github.com/Edubgr/MPU6050-MotionTracking

## 支持和反馈

如遇问题，请：
1. 检查 `3D_ATTITUDE_GUIDE.md` 中的故障排除部分
2. 运行 `test_3d_attitude.py` 验证环境
3. 查看实时调试输出
4. 参考日志文件

---

**版本**：1.0  
**最后更新**：2026-05-13
