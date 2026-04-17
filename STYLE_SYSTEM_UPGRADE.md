# 样式系统统一升级文档

## 概述
对应用程序的样式管理系统进行了完全升级，确保主题切换时所有组件的深浅色调一致。

## 主要改进

### 1. 统一的样式管理 (`colorstyle.py`)
- ✅ 创建了样式生成函数，支持动态主题切换
- ✅ 添加了 `get_theme_colors(is_dark)` 函数获取当前主题颜色
- ✅ 为各个组件创建了专用的样式表生成函数：
  - `get_menubar_stylesheet()` - 菜单栏
  - `get_menubar_title_stylesheet()` - 菜单栏标题
  - `get_menubar_button_stylesheet()` - 菜单栏按钮
  - `get_sidebar_stylesheet()` - 侧边栏
  - `get_sidebar_button_stylesheet()` - 侧边栏按钮
  - `get_homepage_stylesheet()` - 首页
  - `get_homepage_label_stylesheet()` - 首页标签
  - `get_homepage_sensor_label_stylesheet()` - 传感器标签
  - `get_tool_button_stylesheet()` - 工具按钮

### 2. 组件级别的主题支持
所有主要组件都添加了 `update_style(is_dark: bool)` 方法：

#### Menubar.py
- ✅ 添加了 `is_dark_theme` 属性追踪当前主题
- ✅ 实现了 `update_style()` 方法，更新菜单栏、标题和按钮样式

#### Sidebar.py
- ✅ 添加了 `is_dark_theme` 属性
- ✅ 实现了 `update_style()` 方法，更新侧边栏和所有按钮样式

#### Pages.py
- ✅ **Homepage** 类：
  - 添加了 `is_dark_theme` 属性
  - 实现了 `update_style()` 方法，更新所有标签、传感器标签和工具按钮
  - 更新右侧面板样式
  
- ✅ **CommandPanel** 类：
  - 添加了 `is_dark_theme` 属性和 `update_style()` 方法
  
- ✅ **HistoryPage** 类：
  - 添加了 `is_dark_theme` 属性和 `update_style()` 方法
  
- ✅ **SettingsPage** 类：
  - 添加了 `is_dark_theme` 属性和 `update_style()` 方法
  
- ✅ **LogPage** 类：
  - 添加了 `is_dark_theme` 属性和 `update_style()` 方法
  
- ✅ **AnalysisTab** 类：
  - 添加了 `is_dark_theme` 属性和 `update_style()` 方法

#### MainWindow.py
- ✅ 添加了 `is_dark_theme` 属性
- ✅ 实现了 `update_style()` 方法，统一调用所有子组件的更新方法：
  - `menubar.update_style(is_dark)`
  - `sidebar.update_style(is_dark)`
  - `Homepage.update_style(is_dark)`
  - `HistoryPage.update_style(is_dark)`
  - `SettingsPage.update_style(is_dark)`
  - `LogPage.update_style(is_dark)`

#### main.py
- ✅ 简化了 `switch_theme()` 函数
- ✅ 现在只需调用 `MainWindow.update_style(is_dark)` 即可完成所有样式更新

## 样式系统架构

```
深色/浅色主题选择
    ↓
colorstyle.py (中心控制)
    ├─ get_theme_colors(is_dark)
    ├─ get_menubar_stylesheet(is_dark)
    ├─ get_sidebar_stylesheet(is_dark)
    ├─ get_homepage_stylesheet(is_dark)
    └─ ... 其他样式函数
    ↓
MainWindow.update_style(is_dark)
    ├─ menubar.update_style(is_dark)
    ├─ sidebar.update_style(is_dark)
    ├─ Homepage.update_style(is_dark)
    ├─ HistoryPage.update_style(is_dark)
    ├─ SettingsPage.update_style(is_dark)
    └─ LogPage.update_style(is_dark)
```

## 使用方式

### 主题切换流程
```python
# 原来的方式（已废弃）：
# switch_theme(app, 'dark_amber.xml', MainWindow)

# 新的方式（推荐）：
theme_name = 'dark_amber.xml'
is_dark = theme_name.split('_')[0] == 'dark'
apply_stylesheet(app, theme=theme_name, invert_secondary=False)
MainWindow.update_style(is_dark)
```

## 优势

1. **集中管理**: 所有样式定义都在 `colorstyle.py` 中统一管理
2. **易于维护**: 修改主题颜色只需更新 `colorstyle.py` 中的颜色字典和样式函数
3. **一致性**: 确保主题切换时所有组件的深浅色调完全一致
4. **可扩展性**: 新添加的组件只需实现 `update_style()` 方法即可支持主题切换
5. **清晰的流程**: 从主窗口到各个子组件的更新流程清晰明确

## 测试结果

✅ colorstyle 模块导入成功
✅ 所有样式函数正常工作
✅ 深色主题样式生成正确
✅ 浅色主题样式生成正确
✅ 组件样式更新方法有效

## 示例

### 为新组件添加主题支持
```python
class MyComponent(QWidget):
    def __init__(self):
        super().__init__()
        self.is_dark_theme = True
        self.initUI()
    
    def update_style(self, is_dark: bool):
        """更新主题样式"""
        self.is_dark_theme = is_dark
        colors = get_theme_colors(is_dark)
        self.setStyleSheet(f"background-color: {colors['Surface']};")
        # 更新其他组件样式...
```

## 主题颜色定义

### 深色主题 (dark_theme_colors)
- Background: #121212
- Surface: #1E1E1E
- Text_Primary: #E0E0E0
- Text_Secondary: #A0A0A0
- Accent: #BB86FC
- Border_Hover: #333333

### 浅色主题 (light_theme_colors)
- Background: #FFFFFF
- Surface: #C8C8C8
- Text_Primary: #000000
- Text_Secondary: #606060
- Accent: #6200EE
- Border_Hover: #CCCCCC
