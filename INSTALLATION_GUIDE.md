# 3D姿态显示功能 - 安装和验证指南

## 🔧 安装步骤

### 方法1：自动安装（推荐）

如果你已经设置了虚拟环境并使用了 `uv` 或 `pip`：

```bash
# 使用 uv（如果已安装）
uv sync

# 或使用 pip
pip install -e .
```

这会自动安装所有依赖，包括新添加的：
- PyOpenGL>=3.1.5
- numpy>=1.20.0
- scipy>=1.7.0

### 方法2：手动安装

如果上述方法不适用，手动安装依赖：

```bash
# 激活虚拟环境
.venv\Scripts\activate.ps1

# 安装新增的库
pip install PyOpenGL numpy scipy

# 验证安装
pip list | grep -E "(PyOpenGL|numpy|scipy)"
```

### 方法3：仅安装3D功能依赖

如果只想使用3D功能，最少需要：

```bash
pip install PyOpenGL numpy scipy
```

## ✅ 验证安装

### 快速验证

运行以下命令验证所有组件是否正确安装：

```bash
# 1. 验证IMU处理器
python -c "from imu_processor import IMUProcessor, FilterType; print('✓ IMU处理器就绪')"

# 2. 验证3D可视化（需要完整环境）
python -c "from AttitudeVisualizer import AttitudeVisualizer; print('✓ 3D可视化器就绪')"

# 3. 运行完整测试
python test_3d_attitude.py
```

### 完整验证脚本

保存为 `verify_installation.py`：

```python
#!/usr/bin/env python3
"""验证3D姿态显示功能安装"""

import sys

def verify_imports():
    """验证所有必要的导入"""
    print("🔍 验证依赖库...")
    
    required_modules = {
        'numpy': '数值计算',
        'scipy': '科学计算',
        'OpenGL': '3D渲染',
        'PySide6': '图形界面',
        'pyqtgraph': '数据绘图',
    }
    
    failed = []
    for module, description in required_modules.items():
        try:
            __import__(module)
            print(f"  ✓ {module:15} - {description}")
        except ImportError as e:
            print(f"  ✗ {module:15} - {description} [缺失]")
            failed.append(module)
    
    return len(failed) == 0

def verify_project_modules():
    """验证项目模块"""
    print("\n🔍 验证项目模块...")
    
    modules = [
        ('imu_processor', 'IMU处理器'),
        ('AttitudeVisualizer', '3D可视化'),
        ('PlotWidget', '绘图窗口'),
        ('Serial', '串口通信'),
    ]
    
    failed = []
    for module_name, description in modules:
        try:
            __import__(module_name)
            print(f"  ✓ {module_name:20} - {description}")
        except ImportError as e:
            print(f"  ✗ {module_name:20} - {description}")
            print(f"    错误: {e}")
            failed.append(module_name)
    
    return len(failed) == 0

def verify_functionality():
    """验证基本功能"""
    print("\n🔍 验证功能...")
    
    try:
        from imu_processor import IMUProcessor, FilterType
        processor = IMUProcessor()
        
        # 测试更新
        processor.update([0, 0, 1], [0, 0, 0])
        roll, pitch, yaw = processor.get_euler_angles()
        print(f"  ✓ IMU处理 - 欧拉角计算成功")
        print(f"    样本输出: Roll={roll:.1f}°, Pitch={pitch:.1f}°, Yaw={yaw:.1f}°")
        
        # 测试四元数
        quat = processor.get_quaternion()
        print(f"  ✓ 四元数 - {quat[:2]}...")
        
        return True
    except Exception as e:
        print(f"  ✗ 功能验证失败: {e}")
        return False

def main():
    """主验证流程"""
    print("=" * 60)
    print("3D姿态显示功能 - 安装验证")
    print("=" * 60)
    
    results = []
    
    # 验证导入
    results.append(("依赖库", verify_imports()))
    
    # 验证项目模块
    results.append(("项目模块", verify_project_modules()))
    
    # 验证功能
    results.append(("功能验证", verify_functionality()))
    
    # 总结
    print("\n" + "=" * 60)
    print("验证总结:")
    all_pass = True
    for name, passed in results:
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"  {status} - {name}")
        all_pass = all_pass and passed
    
    if all_pass:
        print("\n✅ 所有验证通过！可以开始使用3D姿态功能。")
        print("\n下一步:")
        print("  1. 运行测试: python test_3d_attitude.py")
        print("  2. 启动应用: python main.py")
        print("  3. 连接传感器并切换到'3D姿态'选项卡")
        return 0
    else:
        print("\n❌ 验证失败。请检查上面的错误信息。")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

运行验证：
```bash
python verify_installation.py
```

## 📋 依赖清单

### 必需的依赖（已在pyproject.toml中）

| 库 | 版本 | 用途 | 状态 |
|----|------|------|------|
| PySide6 | >=6.10.2 | GUI框架 | ✓ 原有 |
| pyqtgraph | >=0.14.0 | 2D图表 | ✓ 原有 |
| pyserial | >=3.5 | 串口通信 | ✓ 原有 |
| qt-material | >=2.17 | 主题 | ✓ 原有 |
| **PyOpenGL** | >=3.1.5 | 3D渲染 | ✨ 新增 |
| **numpy** | >=1.20.0 | 数值计算 | ✨ 新增 |
| **scipy** | >=1.7.0 | 科学计算 | ✨ 新增 |

### 可选依赖

```bash
# GPU加速（推荐，如果显卡支持）
pip install PyOpenGL_accelerate

# 用于运行测试
pip install pytest
```

## 🔐 环境检查清单

使用以下检查列表确保环境正确：

```bash
# ✓ Python版本 >= 3.12
python --version

# ✓ 虚拟环境已激活
which python  # Linux/Mac
where python  # Windows

# ✓ pip已更新
python -m pip --version

# ✓ 所有依赖已安装
pip list

# ✓ OpenGL驱动可用
python -c "import OpenGL; print(OpenGL.GL.glGetString(OpenGL.GL.GL_VERSION))"
```

## 🚀 快速测试

安装完成后，快速测试功能：

```bash
# 1. 测试IMU处理器（无图形界面）
python -c "
from imu_processor import IMUProcessor
p = IMUProcessor()
p.update([0, 0, 1], [0.1, 0, 0])
roll, pitch, yaw = p.get_euler_angles()
print(f'IMU正常工作: Roll={roll:.1f}°')
"

# 2. 运行完整演示（需要显示器）
python test_3d_attitude.py

# 3. 启动主应用
python main.py
```

## 🐛 常见安装问题

### 问题1：`ModuleNotFoundError: No module named 'PyOpenGL'`

**原因**：PyOpenGL未安装  
**解决**：
```bash
pip install PyOpenGL
```

### 问题2：`ModuleNotFoundError: No module named 'numpy'`

**原因**：numpy未安装  
**解决**：
```bash
pip install numpy scipy
```

### 问题3：OpenGL错误：`OpenGL is not available`

**原因**：显卡驱动问题或OpenGL不可用  
**解决**：
1. 更新显卡驱动
2. 检查OpenGL支持：
```bash
python -c "from OpenGL.GL import *; print('OpenGL可用')"
```

### 问题4：虚拟环境中的包冲突

**原因**：依赖版本冲突  
**解决**：
```bash
# 清理并重新安装
pip uninstall -y PyOpenGL numpy scipy
pip install PyOpenGL numpy scipy --upgrade
```

## 📊 验证输出示例

成功安装应该看到：

```
✓ numpy        - 数值计算
✓ scipy        - 科学计算
✓ OpenGL       - 3D渲染
✓ PySide6      - 图形界面
✓ pyqtgraph    - 数据绘图

✓ imu_processor      - IMU处理器
✓ AttitudeVisualizer - 3D可视化
✓ PlotWidget         - 绘图窗口
✓ Serial             - 串口通信

✓ IMU处理 - 欧拉角计算成功
  样本输出: Roll=0.0°, Pitch=0.0°, Yaw=0.0°

✅ 所有验证通过！
```

## 📚 后续步骤

1. **运行测试程序**：`python test_3d_attitude.py`
2. **查看文档**：`3D_ATTITUDE_QUICK_START.md`
3. **启动应用**：`python main.py`
4. **连接传感器**：按照主应用指引操作
5. **查看3D显示**：切换到"3D姿态"选项卡

## 🔧 常见配置

### 开发环境
```bash
# 安装开发依赖
pip install pytest black mypy
```

### 性能优化
```bash
# 启用OpenGL加速
pip install PyOpenGL_accelerate
```

### 调试模式
```bash
# 设置环境变量启用调试
export PYOPENGL_PLATFORM=egl  # Linux
set PYOPENGL_PLATFORM=wgl     # Windows
```

---

**需要帮助？**

1. 查看 `3D_ATTITUDE_GUIDE.md` 中的故障排除部分
2. 运行 `python verify_installation.py` 获取详细报告
3. 检查日志文件（如果有）

---

*最后更新：2026年5月13日*
