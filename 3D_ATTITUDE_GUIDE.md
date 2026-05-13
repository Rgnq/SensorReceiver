# 3D姿态实时显示功能使用指南

## 功能概述

本功能基于MPU6050传感器的加速度和角速度数据，实现了实时3D姿态可视化。系统采用互补滤波算法融合加速度计和陀螺仪数据，计算四元数和欧拉角，并以3D立方体的形式实时显示传感器的旋转姿态。

## 新增文件

### 1. **imu_processor.py** - IMU数据处理模块
处理MPU6050传感器数据的核心模块，包含：
- **IMUProcessor 类** - 主要的数据融合处理器
  - `update(accel, gyro)` - 更新加速度和角速度数据
  - `get_euler_angles()` - 获取欧拉角（度）
  - `get_quaternion()` - 获取四元数
  - `rotate_vector(v)` - 使用四元数旋转向量
  - `reset()` - 重置处理器状态

- **QuaternionHelper 类** - 四元数辅助函数
  - `from_euler(roll, pitch, yaw)` - 从欧拉角创建四元数
  - `to_euler(q)` - 四元数转欧拉角
  - `to_rotation_matrix(q)` - 四元数转旋转矩阵

- **FilterType 枚举** - 支持的滤波器类型
  - `COMPLEMENTARY` - 互补滤波（推荐）
  - `MADGWICK` - Madgwick算法
  - `SIMPLE` - 简单积分

### 2. **AttitudeVisualizer.py** - 3D可视化模块
基于OpenGL的实时3D渲染模块，包含：
- **AttitudeVisualizer 类** - OpenGL 3D可视化窗口
  - `set_euler_angles(roll, pitch, yaw)` - 设置欧拉角
  - `set_quaternion(quaternion)` - 设置四元数
  - `set_camera_distance(distance)` - 调整视距
  - `reset_view()` - 重置视图

- **AttitudePanel 类** - 姿态指示器面板
  - `update_attitude(roll, pitch, yaw)` - 更新姿态显示

### 3. **修改的文件**

#### PlotWidget.py
- 添加了3D姿态选项卡
- 新增方法：
  - `update_attitude(roll, pitch, yaw)` - 更新3D姿态
  - `update_attitude_from_quaternion(quaternion)` - 从四元数更新

#### Pages.py
- 集成了IMUProcessor处理器
- 在 `updateDataDisplay()` 方法中添加IMU数据处理
- 自动计算并显示3D姿态

## 工作原理

```
传感器数据 (AX, AY, AZ, GX, GY, GZ)
    ↓
IMUProcessor.update(accel, gyro)
    ↓
    ├─ 加速度计数据 → 计算倾斜角
    ├─ 陀螺仪数据 → 角速度积分
    └─ 互补滤波融合 → 四元数
    ↓
计算欧拉角 (roll, pitch, yaw)
    ↓
AttitudeVisualizer 3D显示
```

## 数据单位说明

### 输入数据单位
- **加速度 (AX, AY, AZ)**：
  - 如果传感器输出为 g（重力加速度）：保持原样
  - 如果传感器输出为 m/s²：使用原值
  
- **角速度 (GX, GY, GZ)**：
  - 推荐单位：**rad/s**（弧度/秒）
  - 如果单位是 deg/s（度/秒），需要转换：`gyro_rad = gyro_deg * π / 180`

### 输出数据
- **欧拉角 (Roll, Pitch, Yaw)**：度数（0-360°）
- **四元数 (w, x, y, z)**：单位四元数

## 使用示例

### 基本使用

```python
from imu_processor import IMUProcessor, FilterType

# 创建处理器
processor = IMUProcessor(sample_rate=100.0, filter_type=FilterType.COMPLEMENTARY)

# 连续更新传感器数据
while True:
    accel = [ax, ay, az]  # 加速度
    gyro = [gx, gy, gz]   # 角速度（rad/s）
    
    # 更新处理器
    processor.update(accel, gyro)
    
    # 获取结果
    roll, pitch, yaw = processor.get_euler_angles()  # 度数
    quaternion = processor.get_quaternion()  # [w, x, y, z]
    
    print(f"Roll: {roll:.1f}°, Pitch: {pitch:.1f}°, Yaw: {yaw:.1f}°")
```

### 在UI中使用

```python
# 在Pages.py的updateDataDisplay()方法中已自动集成
# 数据会自动更新到3D显示选项卡

# 手动更新3D显示（如果需要）
self.RegionPlot.update_attitude(roll, pitch, yaw)
```

## 3D可视化详解

### 坐标轴说明
- **红色轴（X轴）** - Roll（横滚）轴
- **绿色轴（Y轴）** - Pitch（俯仰）轴
- **蓝色轴（Z轴）** - Yaw（偏航）轴

### 立方体显示
- 多色立方体代表传感器本体
- 立方体的旋转反映实时的姿态变化
- 背景网格用于参考

### 交互操作
- **鼠标拖动** - 手动旋转视图
- **鼠标滚轮** - 缩放（调整相机距离）
- **双击重置** - 回到初始视角（需在代码中实现）

## 参数调整

### 采样率
```python
processor = IMUProcessor(sample_rate=100.0)  # Hz
```
- 与实际数据接收频率一致
- 影响陀螺仪积分精度

### 滤波器选择
```python
# 互补滤波（推荐，性能好）
processor = IMUProcessor(filter_type=FilterType.COMPLEMENTARY)

# Madgwick算法（精度高，计算量大）
processor = IMUProcessor(filter_type=FilterType.MADGWICK)

# 简单积分（最快，精度最低）
processor = IMUProcessor(filter_type=FilterType.SIMPLE)
```

### 权重调整（互补滤波）
```python
# 增加加速度计权重（去漂移快，但容易振荡）
processor.accel_weight = 0.05
processor.gyro_weight = 0.95

# 增加陀螺仪权重（平稳，但会漂移）
processor.accel_weight = 0.01
processor.gyro_weight = 0.99
```

## 常见问题

### Q1: 3D显示抖动明显
**A:** 
- 增加加速度计权重：`processor.accel_weight = 0.05`
- 或切换到Madgwick算法
- 检查传感器数据质量

### Q2: 显示漂移
**A:**
- 减少加速度计权重：`processor.accel_weight = 0.01`
- 增加陀螺仪权重：`processor.gyro_weight = 0.99`
- 确保陀螺仪零偏标定

### Q3: 显示不动或响应缓慢
**A:**
- 检查串口数据是否正确接收
- 确认采样率设置与实际数据频率一致
- 查看日志输出是否有错误

### Q4: 坐标系方向不对
**A:**
- 调整欧拉角的符号或顺序
- 参考MPU6050-MotionTracking项目的标定方法

## 数据融合算法详解

### 互补滤波（推荐）
将加速度计和陀螺仪进行线性加权融合：
```
q_result = gyro_weight * q_gyro + accel_weight * q_accel
```

**优点：**
- 计算量小，响应快
- 实时性好
- 参数调整灵活

**缺点：**
- 精度有限
- 需要手动调参

### Madgwick算法
利用梯度下降法最小化目标函数：
```
J = ||a × f||² 
```
其中 f 是预测的加速度方向

**优点：**
- 精度高
- 自适应性好
- 有理论基础

**缺点：**
- 计算量较大
- 参数调整复杂

## 扩展功能建议

1. **磁力计融合** - 加入磁力计改进yaw角
   ```python
   imu.update(accel, gyro, mag)  # 需修改update方法
   ```

2. **零偏标定** - 自动标定陀螺仪零偏
   ```python
   processor.calibrate()
   ```

3. **动作识别** - 基于欧拉角检测特定姿态
4. **数据记录** - 保存标准的四元数数据用于离线分析
5. **多传感器融合** - 支持多个IMU数据的同步处理

## 性能优化

1. **减少计算频率**
   ```python
   if frame_count % 2 == 0:  # 每2帧更新一次
       processor.update(accel, gyro)
   ```

2. **启用OpenGL硬件加速**
   - 确保显卡驱动最新
   - 在AttitudeVisualizer中已配置

3. **降低3D渲染精度**
   ```python
   visualizer.cube_size = 0.6  # 降低立方体复杂度
   ```

## 参考资源

- MPU6050规格书：https://invensense.tdk.com/products/motion-tracking/6-axis/
- 四元数理论：https://en.wikipedia.org/wiki/Quaternion
- Madgwick算法：https://www.x-io.co.uk/open-source-imu-and-ahrs-algorithms/
- 本项目参考：MPU6050-MotionTracking 项目

## 许可证

与主项目相同
