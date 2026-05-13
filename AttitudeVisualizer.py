"""
3D姿态可视化器 - 实时绘制带坐标轴的3D立方体和传感器姿态
基于OpenGL的实时3D渲染
"""

from PySide6.QtWidgets import QVBoxLayout, QWidget
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QSurfaceFormat

from OpenGL.GL import *
from OpenGL.GLU import *
import math
import numpy as np
from imu_processor import QuaternionHelper


class AttitudeVisualizer(QOpenGLWidget):
    """3D姿态指示器 - 使用OpenGL实时显示传感器旋转"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 设置OpenGL格式
        fmt = QSurfaceFormat()
        fmt.setVersion(2, 1)
        fmt.setProfile(QSurfaceFormat.CoreProfile)
        self.setFormat(fmt)
        
        # 旋转角度 (欧拉角 - 度)
        self.roll = 0.0      # 绕X轴
        self.pitch = 0.0     # 绕Y轴
        self.yaw = 0.0       # 绕Z轴
        
        # 四元数
        self.quaternion = np.array([1.0, 0.0, 0.0, 0.0])
        
        # 视图参数
        self.camera_distance = 3.0
        self.auto_rotate = False
        self.rotation_speed = 1.0
        
        # 渲染参数
        self.cube_size = 0.8
        self.axis_length = 1.2
        
        # 动画定时器
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update)
        
        # 鼠标交互
        self.last_mouse_x = 0
        self.last_mouse_y = 0
        self.mouse_pressed = False
    
    def initializeGL(self):
        """OpenGL初始化"""
        glClearColor(0.2, 0.2, 0.2, 1.0)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        
        # 设置光源
        light_position = [1.0, 1.0, 2.0, 0.0]
        light_color = [1.0, 1.0, 1.0, 1.0]
        glLight(GL_LIGHT0, GL_POSITION, light_position)
        glLight(GL_LIGHT0, GL_AMBIENT, [0.3, 0.3, 0.3, 1.0])
        glLight(GL_LIGHT0, GL_DIFFUSE, light_color)
        glLight(GL_LIGHT0, GL_SPECULAR, light_color)
    
    def resizeGL(self, w, h):
        """窗口大小改变"""
        if h == 0:
            h = 1
        
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        
        # 透视投影
        gluPerspective(45.0, w / h, 0.1, 50.0)
        glMatrixMode(GL_MODELVIEW)
    
    def paintGL(self):
        """绘制场景"""
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        
        # 设置相机位置
        gluLookAt(
            0, 0, self.camera_distance,  # 相机位置
            0, 0, 0,                      # 看向点
            0, 1, 0                       # 上向量
        )
        
        # 绘制网格
        self._draw_grid()
        
        # 绘制世界坐标轴（固定）
        self._draw_world_axes()
        
        # 应用旋转
        glPushMatrix()
        self._apply_rotation()
        
        # 绘制立方体（传感器体）
        self._draw_cube()
        
        # 绘制传感器坐标轴
        self._draw_sensor_axes()
        
        glPopMatrix()
    
    def _apply_rotation(self):
        """应用旋转变换（基于四元数或欧拉角）"""
        # 使用欧拉角
        glRotatef(self.yaw, 0, 0, 1)      # Z轴旋转 (yaw)
        glRotatef(self.pitch, 0, 1, 0)    # Y轴旋转 (pitch)
        glRotatef(self.roll, 1, 0, 0)     # X轴旋转 (roll)
    
    def _draw_grid(self):
        """绘制参考网格"""
        glDisable(GL_LIGHTING)
        glColor3f(0.5, 0.5, 0.5)
        glBegin(GL_LINES)
        
        size = 2.0
        step = 0.5
        y = -0.8
        
        for i in np.arange(-size, size + step, step):
            glVertex3f(i, y, -size)
            glVertex3f(i, y, size)
            glVertex3f(-size, y, i)
            glVertex3f(size, y, i)
        
        glEnd()
        glEnable(GL_LIGHTING)
    
    def _draw_world_axes(self):
        """绘制世界坐标轴（参考轴）"""
        glDisable(GL_LIGHTING)
        glLineWidth(2.0)
        glBegin(GL_LINES)
        
        axis_len = 1.5
        
        # X轴 - 红色
        glColor3f(1.0, 0.0, 0.0)
        glVertex3f(0, 0, 0)
        glVertex3f(axis_len, 0, 0)
        
        # Y轴 - 绿色
        glColor3f(0.0, 1.0, 0.0)
        glVertex3f(0, 0, 0)
        glVertex3f(0, axis_len, 0)
        
        # Z轴 - 蓝色
        glColor3f(0.0, 0.0, 1.0)
        glVertex3f(0, 0, 0)
        glVertex3f(0, 0, axis_len)
        
        glEnd()
        glLineWidth(1.0)
        glEnable(GL_LIGHTING)
    
    def _draw_cube(self):
        """绘制立方体（传感器体）"""
        glColor3f(0.3, 0.8, 0.3)
        
        # 立方体顶点
        s = self.cube_size
        vertices = [
            [-s, -s, -s], [s, -s, -s],
            [s, s, -s], [-s, s, -s],
            [-s, -s, s], [s, -s, s],
            [s, s, s], [-s, s, s]
        ]
        
        # 立方体面
        faces = [
            [0, 1, 2, 3],  # 后面
            [4, 7, 6, 5],  # 前面
            [0, 4, 5, 1],  # 下面
            [2, 6, 7, 3],  # 上面
            [0, 3, 7, 4],  # 左面
            [1, 5, 6, 2]   # 右面
        ]
        
        # 面的颜色
        colors = [
            [1.0, 0.0, 0.0],  # 红色
            [0.0, 1.0, 0.0],  # 绿色
            [0.0, 0.0, 1.0],  # 蓝色
            [1.0, 1.0, 0.0],  # 黄色
            [1.0, 0.0, 1.0],  # 品红
            [0.0, 1.0, 1.0]   # 青色
        ]
        
        glBegin(GL_QUADS)
        for i, face in enumerate(faces):
            glColor3fv(colors[i])
            for vertex in face:
                glVertex3fv(vertices[vertex])
        glEnd()
        
        # 绘制边框
        glDisable(GL_LIGHTING)
        glColor3f(0.0, 0.0, 0.0)
        glLineWidth(2.0)
        glBegin(GL_LINE_LOOP)
        for face in faces:
            for vertex in face:
                glVertex3fv(vertices[vertex])
        glEnd()
        glLineWidth(1.0)
        glEnable(GL_LIGHTING)
    
    def _draw_sensor_axes(self):
        """绘制传感器坐标轴"""
        glDisable(GL_LIGHTING)
        glLineWidth(2.0)
        glBegin(GL_LINES)
        
        # X轴 - 红色
        glColor3f(1.0, 0.3, 0.3)
        glVertex3f(0, 0, 0)
        glVertex3f(self.axis_length, 0, 0)
        
        # Y轴 - 绿色
        glColor3f(0.3, 1.0, 0.3)
        glVertex3f(0, 0, 0)
        glVertex3f(0, self.axis_length, 0)
        
        # Z轴 - 蓝色
        glColor3f(0.3, 0.3, 1.0)
        glVertex3f(0, 0, 0)
        glVertex3f(0, 0, self.axis_length)
        
        glEnd()
        glLineWidth(1.0)
        glEnable(GL_LIGHTING)
    
    def set_euler_angles(self, roll, pitch, yaw):
        """
        设置欧拉角 (度)
        
        Args:
            roll: 绕X轴旋转 (度)
            pitch: 绕Y轴旋转 (度)
            yaw: 绕Z轴旋转 (度)
        """
        self.roll = roll % 360.0
        self.pitch = pitch % 360.0
        self.yaw = yaw % 360.0
    
    def set_quaternion(self, quaternion):
        """
        设置四元数
        
        Args:
            quaternion: [w, x, y, z]
        """
        self.quaternion = np.array(quaternion)
        # 转换为欧拉角
        roll, pitch, yaw = QuaternionHelper.to_euler(quaternion)
        self.set_euler_angles(
            math.degrees(roll),
            math.degrees(pitch),
            math.degrees(yaw)
        )
    
    def start_animation(self):
        """启动自动旋转动画"""
        if not self.animation_timer.isActive():
            self.animation_timer.start(16)  # 约60fps
    
    def stop_animation(self):
        """停止动画"""
        self.animation_timer.stop()
    
    def set_camera_distance(self, distance):
        """设置相机距离"""
        self.camera_distance = max(1.0, min(10.0, distance))
        self.update()
    
    def reset_view(self):
        """重置视图"""
        self.roll = 0.0
        self.pitch = 0.0
        self.yaw = 0.0
        self.camera_distance = 3.0
        self.update()
    
    def mousePressEvent(self, event):
        """鼠标按下"""
        self.mouse_pressed = True
        self.last_mouse_x = event.position().x()
        self.last_mouse_y = event.position().y()
    
    def mouseMoveEvent(self, event):
        """鼠标移动"""
        if self.mouse_pressed:
            dx = event.position().x() - self.last_mouse_x
            dy = event.position().y() - self.last_mouse_y
            
            self.yaw += dx * 0.5
            self.pitch += dy * 0.5
            
            self.last_mouse_x = event.position().x()
            self.last_mouse_y = event.position().y()
            
            self.update()
    
    def mouseReleaseEvent(self, event):
        """鼠标释放"""
        self.mouse_pressed = False
    
    def wheelEvent(self, event):
        """鼠标滚轮缩放"""
        delta = event.angleDelta().y()
        self.camera_distance -= delta / 120.0 * 0.3
        self.camera_distance = max(1.0, min(10.0, self.camera_distance))
        self.update()


class AttitudePanel(QWidget):
    """姿态指示器面板 - 包含3D可视化和控制面板"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # 创建3D可视化器
        self.visualizer = AttitudeVisualizer()
        layout.addWidget(self.visualizer)
    
    def update_attitude(self, roll, pitch, yaw):
        """更新姿态角度 (度)"""
        self.visualizer.set_euler_angles(roll, pitch, yaw)
        self.visualizer.update()
    
    def update_from_quaternion(self, quaternion):
        """从四元数更新"""
        self.visualizer.set_quaternion(quaternion)
        self.visualizer.update()
