# SettingsPage 颜色调色盘功能说明

## 功能概述
为 SettingsPage 添加了可视化的颜色调色盘功能，允许用户自定义深色/浅色主题的各个颜色元素。

## 新增功能

### 1. 颜色管理模块 (`colorstyle.py`)
新增的函数和功能：

- **`save_theme_colors(is_dark, colors)`** - 保存主题颜色到JSON文件
  ```python
  save_theme_colors(True, {"Background": "#121212", ...})  # 保存深色主题
  ```

- **`load_theme_colors()`** - 从JSON文件加载主题颜色
  ```python
  load_theme_colors()  # 加载已保存的颜色，不存在则使用默认值
  ```

- **`reset_theme_colors(is_dark)`** - 重置主题颜色为默认值
  ```python
  reset_theme_colors(True)  # 重置深色主题
  ```

### 2. 配置文件存储
颜色配置文件保存在：
```
config/
├── dark_theme_colors.json      # 深色主题颜色配置
└── light_theme_colors.json     # 浅色主题颜色配置
```

每个配置文件包含 6 种可自定义的颜色：
- **Background** - 背景色
- **Surface** - 表面色（主要组件背景）
- **Text_Primary** - 主文本色
- **Text_Secondary** - 副文本色
- **Accent** - 强调色
- **Border_Hover** - 悬停边框色

### 3. SettingsPage UI 改进

#### 界面结构
```
┌─────────────────────────────────────────┐
│  数据保存目录                           │
│  ├─ 路径输入框 [浏览...] [设置]        │
│                                         │
│  Material主题                           │
│  ├─ 主题选择 [应用]                    │
│                                         │
│  自定义主题颜色                         │
│  ├─ 编辑主题: [深色/浅色▼]              │
│                                         │
│  颜色选择面板:                          │
│  ├─ 背景色        [■] #121212          │
│  ├─ 表面色        [■] #1E1E1E          │
│  ├─ 主文本色      [■] #E0E0E0          │
│  ├─ 副文本色      [■] #A0A0A0          │
│  ├─ 强调色        [■] #BB86FC          │
│  └─ 悬停边框色    [■] #333333          │
│                                         │
│                      [重置为默认颜色]   │
└─────────────────────────────────────────┘
```

#### 关键UI组件

1. **颜色编辑选择框** - 选择要编辑的主题（深色/浅色）
2. **颜色按钮** - 显示当前颜色，点击打开颜色对话框
3. **颜色值显示** - 显示HEX颜色码（只读）
4. **重置按钮** - 重置为默认颜色

### 4. 使用流程

#### 修改颜色
1. 在"编辑主题"下拉框选择要编辑的主题（深色或浅色）
2. 点击要修改的颜色按钮（例如"背景色"按钮）
3. 在打开的调色盘中选择新颜色
4. 颜色自动保存并应用到整个应用程序
5. 右侧显示HEX颜色码

#### 重置颜色
1. 在"编辑主题"选择要重置的主题
2. 点击"重置为默认颜色"按钮
3. 该主题的所有颜色将恢复为默认值

### 5. 技术实现

#### 信号连接（MainWindow）
```python
# 颜色改变时自动更新UI
self.SettingsPage.themeColorsChangedSignal.connect(self.on_theme_colors_changed)
```

#### 颜色更新流程
```
用户点击颜色按钮
    ↓
打开QColorDialog选择颜色
    ↓
保存到JSON文件
    ↓
更新全局变量(dark_theme_colors/light_theme_colors)
    ↓
发出themeColorsChangedSignal信号
    ↓
MainWindow.on_theme_colors_changed()
    ↓
MainWindow.update_style()更新所有组件
```

### 6. 自定义颜色示例

#### JSON配置文件格式
```json
{
    "Background": "#121212",
    "Surface": "#1E1E1E",
    "Text_Primary": "#E0E0E0",
    "Text_Secondary": "#A0A0A0",
    "Accent": "#BB86FC",
    "Border_Hover": "#333333"
}
```

### 7. 新增信号

#### `themeColorsChangedSignal(is_dark: bool)`
当用户修改或重置主题颜色时发出

参数：
- `is_dark` (bool) - True表示修改深色主题，False表示修改浅色主题

### 8. 相关文件变更

**修改文件：**
- `colorstyle.py` - 添加颜色管理函数
- `Pages.py` - 增强SettingsPage UI和逻辑
- `MainWindow.py` - 添加颜色变化信号处理

**新增文件：**
- `config/dark_theme_colors.json` - 深色主题配置（用户自定义）
- `config/light_theme_colors.json` - 浅色主题配置（用户自定义）

### 9. 代码示例

```python
# 在需要使用自定义颜色的地方
from colorstyle import *

# 获取当前主题颜色
colors = get_theme_colors(is_dark=True)  # 返回深色主题颜色字典

# 应用样式
stylesheet = get_menubar_stylesheet(is_dark=True)

# 颜色会自动从JSON文件加载
# 如果用户修改了颜色，会立即生效
```

### 10. 特性亮点

✅ **实时预览** - 修改颜色后立即应用到整个应用
✅ **持久化存储** - 用户自定义的颜色保存在JSON文件中
✅ **双主题支持** - 分别管理深色和浅色主题的颜色
✅ **直观操作** - 使用系统颜色对话框，符合用户习惯
✅ **一键重置** - 轻松恢复到默认颜色
✅ **HEX值显示** - 显示具体的颜色值便于参考

## 使用建议

1. **初次使用** - 应用会自动使用内置的默认颜色
2. **自定义颜色** - 用户可以根据个人偏好修改颜色
3. **团队使用** - 可以将config目录下的JSON文件共享以保持统一风格
4. **备份配置** - 在进行大量修改前可以备份config目录

