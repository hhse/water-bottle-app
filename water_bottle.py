import sys
import os
import json
import math
import time
from datetime import datetime, date
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, 
                            QSystemTrayIcon, QMenu, QAction, QGraphicsDropShadowEffect,
                            QMessageBox, QStyleFactory, QGraphicsBlurEffect)
from PyQt5.QtCore import Qt, QPropertyAnimation, QPoint, QTimer, pyqtProperty, QRect, QSize, QEasingCurve
from PyQt5.QtGui import (QPainter, QColor, QPen, QBrush, QPainterPath, QFont, QIcon, QPixmap, 
                        QLinearGradient, QRadialGradient, QPalette, QFontDatabase)

from settings_dialog import SettingsDialog
from data_manager import DataManager

# 尝试导入图标生成模块
try:
    from create_icon import create_water_bottle_icon
except ImportError:
    create_water_bottle_icon = None

class WaterBottle(QWidget):
    def __init__(self):
        super().__init__()
        
        # 检查是否有图形界面环境
        if not QApplication.instance().testAttribute(Qt.AA_UseDesktopOpenGL) and \
           not QApplication.instance().testAttribute(Qt.AA_UseSoftwareOpenGL) and \
           not QApplication.instance().testAttribute(Qt.AA_UseOpenGLES):
            if os.environ.get('DISPLAY') is None and os.environ.get('WAYLAND_DISPLAY') is None and os.name != 'nt':
                print("错误: 未检测到图形显示环境，请在桌面环境中运行")
                sys.exit(1)
                
        # 初始化数据管理器
        self.data_manager = DataManager()
                
        # 基本属性设置
        self.setWindowTitle("水瓶提醒")
        
        # 解决透明窗口问题的关键：先设置无边框窗口
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        
        # 创建一个白色背景，而不是完全透明，避免UpdateLayeredWindowIndirect错误
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 设置美观的字体
        try:
            # 尝试加载微软雅黑字体
            font_id = QFontDatabase.addApplicationFont("msyh.ttc")
            if font_id != -1:
                font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
                self.font = QFont(font_family, 10)
            else:
                self.font = QFont("微软雅黑", 10)
        except:
            self.font = QFont("微软雅黑", 10)
            
        self.setFont(self.font)
        
        # 窗口大小 - 调整为更适合卡通风格（将被设置覆盖）
        self.resize(160, 320)
        
        # 饮水数据
        self.daily_goal = self.data_manager.get_daily_goal()  # 获取目标
        self.current_amount = self.data_manager.get_today_total()  # 获取今日饮水量
        self.water_percentage = self.calculate_percentage()  # 计算水位百分比
        
        # 卡通视觉样式 - 使用更活泼的颜色
        self.bottle_color = QColor(65, 180, 255)      # 明亮的天蓝色
        self.water_color = QColor(30, 150, 255, 220)  # 鲜艳的蓝色
        self.text_color = QColor(50, 50, 80)          # 深色文字
        self.face_color = QColor(255, 255, 255)       # 白色表情
        self.cheek_color = QColor(255, 182, 193, 180) # 粉色脸颊
        
        # 动画相关变量
        self._water_offset = 0
        self._bounce_offset = 0  # 弹跳偏移
        self._blink_state = 0    # 眨眼状态
        self._expression_state = "happy"  # 表情状态
        
        # 提醒相关
        self.reminder_interval = 60  # 默认60分钟提醒一次
        self.default_water_amount = 200  # 默认每次200ml
        
        # 加载设置（包括水瓶大小）- 在设置动画之前加载
        self.load_settings()
        
        # 设置多重动画
        self.setup_animations()
        
        # 鼠标拖动相关
        self.old_pos = None
        self.is_dragging = False
        
        # 初始化UI
        self.init_ui()
        
        # 不再在这里设置位置，因为apply_bottle_size会处理位置
        
        # 设置提醒定时器
        self.reminder_timer = QTimer(self)
        self.reminder_timer.timeout.connect(self.show_reminder)
        self.reminder_timer.start(self.reminder_interval * 60 * 1000)  # 转换为毫秒
        
        # 设置系统托盘
        self.setup_tray_icon()
        
        # 修复UpdateLayeredWindowIndirect错误：增加额外边距
        self.setContentsMargins(25, 25, 25, 25)
        
    def setup_animations(self):
        """设置多重动画效果"""
        # 水波动画 - 调慢速度
        self.water_animation = QPropertyAnimation(self, b"waterOffset")
        self.water_animation.setDuration(4000)  # 从2500ms增加到4000ms，让水波更慢更优雅
        self.water_animation.setLoopCount(-1)
        self.water_animation.setStartValue(0)
        self.water_animation.setEndValue(2 * math.pi)
        self.water_animation.start()
        
        # 弹跳动画 - 也稍微调慢
        self.bounce_animation = QPropertyAnimation(self, b"bounceOffset")
        self.bounce_animation.setDuration(4500)  # 从3000ms增加到4500ms
        self.bounce_animation.setLoopCount(-1)
        self.bounce_animation.setStartValue(0)
        self.bounce_animation.setEndValue(2 * math.pi)
        self.bounce_animation.setEasingCurve(QEasingCurve.InOutSine)
        self.bounce_animation.start()
        
        # 眨眼动画定时器
        self.blink_timer = QTimer(self)
        self.blink_timer.timeout.connect(self.blink)
        self.blink_timer.start(3000)  # 每3秒眨一次眼
        
        # 创建一个定时器来限制更新频率
        self.update_timer = QTimer(self)
        self.update_timer.setInterval(60)  # 从50ms增加到60ms，稍微降低刷新率
        self.update_timer.timeout.connect(self.update)
        self.update_timer.start()
        
    def blink(self):
        """眨眼动画"""
        self._blink_state = 1
        QTimer.singleShot(150, lambda: setattr(self, '_blink_state', 0))
        
    def update_expression(self):
        """根据水位更新表情"""
        if self.water_percentage < 0.2:
            self._expression_state = "thirsty"
        elif self.water_percentage < 0.5:
            self._expression_state = "normal"
        elif self.water_percentage < 0.8:
            self._expression_state = "happy"
        else:
            self._expression_state = "excited"
        
    @pyqtProperty(float)
    def waterOffset(self):
        return self._water_offset
    
    @waterOffset.setter
    def waterOffset(self, value):
        self._water_offset = value
        
    @pyqtProperty(float)
    def bounceOffset(self):
        return self._bounce_offset
    
    @bounceOffset.setter
    def bounceOffset(self, value):
        self._bounce_offset = value
        
    def init_ui(self):
        # 布局
        layout = QVBoxLayout()
        layout.setContentsMargins(25, 25, 25, 25)
        self.setLayout(layout)
        
    def create_cartoon_bottle_path(self, rect):
        """创建卡通水瓶轮廓路径"""
        width = rect.width()
        height = rect.height()
        x_offset = rect.x()
        y_offset = rect.y()
        
        # 添加轻微的弹跳效果
        bounce_y = int(3 * math.sin(self._bounce_offset))
        y_offset += bounce_y
        
        bottle_path = QPainterPath()
        
        # 卡通瓶盖 - 更可爱的设计
        cap_height = height * 0.08
        cap_width = width * 0.4
        bottle_path.addRoundedRect(
            x_offset + width/2 - cap_width/2, y_offset - cap_height/2,
            cap_width, cap_height, cap_width/4, cap_width/4
        )
        
        # 瓶颈 - 更短更可爱
        neck_width = width * 0.32
        neck_height = height * 0.12
        bottle_path.addRoundedRect(
            x_offset + width/2 - neck_width/2, y_offset,
            neck_width, neck_height, neck_width/6, neck_width/6
        )
        
        # 主瓶身 - 圆润的卡通形状
        body_path = QPainterPath()
        body_width = width * 0.85
        body_height = height * 0.8
        body_y = y_offset + neck_height
        
        # 使用椭圆形作为主体，然后在顶部做一些调整
        body_path.addEllipse(
            x_offset + width/2 - body_width/2, body_y,
            body_width, body_height
        )
        
        # 瓶身与瓶颈的平滑连接
        connect_path = QPainterPath()
        connect_width = width * 0.6
        connect_height = height * 0.08
        connect_path.addRoundedRect(
            x_offset + width/2 - connect_width/2, body_y - connect_height/2,
            connect_width, connect_height, connect_height/2, connect_height/2
        )
        
        # 合并所有路径
        bottle_path = bottle_path.united(connect_path)
        bottle_path = bottle_path.united(body_path)
        
        return bottle_path
        
    def draw_cartoon_face(self, painter, rect):
        """绘制卡通表情"""
        width = rect.width()
        height = rect.height()
        x_offset = rect.x()
        y_offset = rect.y()
        
        # 添加弹跳效果
        bounce_y = int(3 * math.sin(self._bounce_offset))
        y_offset += bounce_y
        
        # 脸部区域
        face_y = y_offset + height * 0.25
        face_height = height * 0.35
        
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制脸颊（可选，当开心时显示）
        if self._expression_state in ["happy", "excited"]:
            cheek_size = width * 0.08
            # 左脸颊
            painter.setBrush(self.cheek_color)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(
                int(x_offset + width * 0.15), int(face_y + face_height * 0.6),
                int(cheek_size), int(cheek_size)
            )
            # 右脸颊
            painter.drawEllipse(
                int(x_offset + width * 0.77), int(face_y + face_height * 0.6),
                int(cheek_size), int(cheek_size)
            )
        
        # 绘制眼睛
        eye_size = width * 0.06
        eye_y = face_y + face_height * 0.3
        left_eye_x = x_offset + width * 0.32
        right_eye_x = x_offset + width * 0.6
        
        painter.setBrush(QColor(50, 50, 50))  # 深色眼睛
        
        if self._blink_state == 0:
            # 正常眼睛
            if self._expression_state == "thirsty":
                # 疲惫的眼神（小一点）
                painter.drawEllipse(int(left_eye_x), int(eye_y + eye_size*0.2), 
                                  int(eye_size), int(eye_size*0.6))
                painter.drawEllipse(int(right_eye_x), int(eye_y + eye_size*0.2), 
                                  int(eye_size), int(eye_size*0.6))
            elif self._expression_state == "excited":
                # 兴奋的大眼睛
                painter.drawEllipse(int(left_eye_x - eye_size*0.1), int(eye_y - eye_size*0.1), 
                                  int(eye_size*1.2), int(eye_size*1.2))
                painter.drawEllipse(int(right_eye_x - eye_size*0.1), int(eye_y - eye_size*0.1), 
                                  int(eye_size*1.2), int(eye_size*1.2))
                # 兴奋的高光
                painter.setBrush(QColor(255, 255, 255))
                painter.drawEllipse(int(left_eye_x + eye_size*0.2), int(eye_y + eye_size*0.1), 
                                  int(eye_size*0.3), int(eye_size*0.3))
                painter.drawEllipse(int(right_eye_x + eye_size*0.2), int(eye_y + eye_size*0.1), 
                                  int(eye_size*0.3), int(eye_size*0.3))
            else:
                # 普通圆眼睛
                painter.drawEllipse(int(left_eye_x), int(eye_y), int(eye_size), int(eye_size))
                painter.drawEllipse(int(right_eye_x), int(eye_y), int(eye_size), int(eye_size))
                
                # 眼睛高光
                painter.setBrush(QColor(255, 255, 255, 200))
                highlight_size = eye_size * 0.25
                painter.drawEllipse(int(left_eye_x + eye_size*0.6), int(eye_y + eye_size*0.2), 
                                  int(highlight_size), int(highlight_size))
                painter.drawEllipse(int(right_eye_x + eye_size*0.6), int(eye_y + eye_size*0.2), 
                                  int(highlight_size), int(highlight_size))
        else:
            # 眨眼状态 - 画线条
            painter.setPen(QPen(QColor(50, 50, 50), 3))
            painter.drawLine(int(left_eye_x), int(eye_y + eye_size/2), 
                           int(left_eye_x + eye_size), int(eye_y + eye_size/2))
            painter.drawLine(int(right_eye_x), int(eye_y + eye_size/2), 
                           int(right_eye_x + eye_size), int(eye_y + eye_size/2))
        
        # 绘制嘴巴
        mouth_y = face_y + face_height * 0.7
        mouth_width = width * 0.15
        mouth_x = x_offset + width/2 - mouth_width/2
        
        painter.setPen(QPen(QColor(50, 50, 50), 2))
        painter.setBrush(Qt.NoBrush)
        
        if self._expression_state == "thirsty":
            # 渴望的小嘴
            painter.drawEllipse(int(mouth_x + mouth_width*0.3), int(mouth_y), 
                              int(mouth_width*0.4), int(mouth_width*0.3))
        elif self._expression_state == "excited":
            # 兴奋的大笑
            smile_path = QPainterPath()
            smile_path.moveTo(mouth_x, mouth_y)
            smile_path.quadTo(mouth_x + mouth_width/2, mouth_y + mouth_width*0.4,
                            mouth_x + mouth_width, mouth_y)
            painter.drawPath(smile_path)
            # 画牙齿
            painter.setBrush(QColor(255, 255, 255))
            painter.drawRect(int(mouth_x + mouth_width*0.4), int(mouth_y + mouth_width*0.1),
                           int(mouth_width*0.2), int(mouth_width*0.15))
        elif self._expression_state == "happy":
            # 开心的微笑
            smile_path = QPainterPath()
            smile_path.moveTo(mouth_x, mouth_y)
            smile_path.quadTo(mouth_x + mouth_width/2, mouth_y + mouth_width*0.3,
                            mouth_x + mouth_width, mouth_y)
            painter.drawPath(smile_path)
        else:
            # 普通表情
            painter.drawLine(int(mouth_x), int(mouth_y), 
                           int(mouth_x + mouth_width), int(mouth_y))
        
    def paintEvent(self, event):
        """绘制卡通水瓶"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        # 获取有效绘制区域
        draw_rect = self.rect().adjusted(
            self.contentsMargins().left(),
            self.contentsMargins().top(),
            -self.contentsMargins().right(),
            -self.contentsMargins().bottom()
        )
        
        # 更新表情状态
        self.update_expression()
        
        # 创建阴影
        shadow_path = self.create_cartoon_bottle_path(draw_rect.adjusted(-8, -8, 8, 8))
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(0, 0, 0, 20))
        painter.drawPath(shadow_path.translated(8, 8))
        
        # 绘制瓶身
        bottle_path = self.create_cartoon_bottle_path(draw_rect)
        
        # 卡通风格的渐变
        gradient = QRadialGradient(
            draw_rect.x() + draw_rect.width() * 0.3,
            draw_rect.y() + draw_rect.height() * 0.2,
            draw_rect.width() * 0.8
        )
        gradient.setColorAt(0, QColor(255, 255, 255, 200))
        gradient.setColorAt(0.7, QColor(230, 245, 255, 180))
        gradient.setColorAt(1, QColor(200, 230, 255, 160))
        
        painter.setPen(QPen(self.bottle_color, 2.5))
        painter.setBrush(gradient)
        painter.drawPath(bottle_path)
        
        # 绘制水
        if self.water_percentage > 0:
            water_height = draw_rect.height() * (1 - self.water_percentage * 0.7)
            self.draw_cartoon_water(painter, water_height, draw_rect, bottle_path)
        
        # 绘制表情
        self.draw_cartoon_face(painter, draw_rect)
        
        # 绘制可爱的装饰
        self.draw_decorations(painter, draw_rect)
        
        # 绘制文字
        self.draw_text(painter, draw_rect)
        
    def draw_cartoon_water(self, painter, water_height, rect, bottle_path):
        """绘制卡通风格的水"""
        width = rect.width()
        bottom = rect.height() + rect.y()
        x_offset = rect.x()
        
        # 添加弹跳效果
        bounce_y = int(3 * math.sin(self._bounce_offset))
        water_height += bounce_y
        
        water_path = QPainterPath()
        water_height = int(water_height)
        water_path.moveTo(x_offset, water_height)
        
        # 创建更优雅的卡通波浪 - 调整波浪参数
        wave_height = 8  # 从10减少到8，波浪幅度稍小
        wave_count = 2   # 从2.5减少到2，波浪数量更少，更优雅
        
        for x in range(width + 1):
            # 使用更平缓的波浪函数
            offset = int(wave_height * math.sin((x / width * wave_count * math.pi) + self._water_offset) * 
                          (0.6 + 0.4 * math.sin(self._water_offset * 0.3)))  # 调整振幅变化
            water_path.lineTo(x_offset + x, water_height + offset)
        
        water_path.lineTo(x_offset + width, bottom)
        water_path.lineTo(x_offset, bottom)
        water_path.closeSubpath()
        
        # 裁剪到瓶身内部
        water_path = bottle_path.intersected(water_path)
        
        # 卡通风格的水渐变
        water_gradient = QLinearGradient(x_offset, water_height, x_offset, bottom)
        water_gradient.setColorAt(0, QColor(120, 200, 255, 160))
        water_gradient.setColorAt(0.4, QColor(80, 180, 255, 180))
        water_gradient.setColorAt(1, QColor(40, 160, 255, 200))
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(water_gradient)
        painter.drawPath(water_path)
        
        # 添加可爱的水泡
        if self.water_percentage > 0.1:
            self.draw_bubbles(painter, water_height, rect, bottle_path)
            
    def draw_bubbles(self, painter, water_height, rect, bottle_path):
        """绘制可爱的气泡 - 调整气泡速度"""
        bubble_count = int(self.water_percentage * 6) + 2  # 从8减少到6，气泡数量稍少
        
        painter.setBrush(QColor(255, 255, 255, 120))
        painter.setPen(Qt.NoPen)
        
        for i in range(bubble_count):
            # 气泡位置计算 - 使用更慢的动画偏移
            bubble_x = rect.x() + rect.width() * (0.2 + 0.6 * (i / bubble_count))
            # 气泡上升速度减慢
            bubble_y = water_height + (rect.height() - water_height) * (0.2 + 0.6 * ((i + self._water_offset * 0.3) % 1))
            
            # 气泡大小随机，变化更温和
            bubble_size = 3 + (i % 3) * 1.5 + int(1.5 * math.sin(self._water_offset * 0.5 + i))
            
            # 创建气泡路径并裁剪
            bubble_path = QPainterPath()
            bubble_path.addEllipse(bubble_x - bubble_size/2, bubble_y - bubble_size/2, 
                                 bubble_size, bubble_size)
            bubble_path = bottle_path.intersected(bubble_path)
            
            painter.drawPath(bubble_path)
            
    def draw_decorations(self, painter, rect):
        """绘制可爱的装饰元素"""
        # 在瓶身上画一些小星星或心形装饰
        if self._expression_state == "excited":
            # 兴奋时显示小星星
            star_positions = [
                (0.15, 0.4), (0.85, 0.5), (0.2, 0.7), (0.8, 0.75)
            ]
            
            painter.setBrush(QColor(255, 255, 100, 150))
            painter.setPen(Qt.NoPen)
            
            for pos_x, pos_y in star_positions:
                star_x = rect.x() + rect.width() * pos_x
                star_y = rect.y() + rect.height() * pos_y
                star_size = 6
                
                # 简单的星形
                star_path = QPainterPath()
                for i in range(5):
                    angle = i * 2 * math.pi / 5
                    x = star_x + star_size * math.cos(angle)
                    y = star_y + star_size * math.sin(angle)
                    if i == 0:
                        star_path.moveTo(x, y)
                    else:
                        star_path.lineTo(x, y)
                star_path.closeSubpath()
                
                painter.drawPath(star_path)
                
    def draw_text(self, painter, rect):
        """绘制文字信息"""
        # 绘制百分比
        percentage_text = f"{int(self.water_percentage * 100)}%"
        font = QFont(self.font)
        font.setPointSize(16)
        font.setBold(True)
        painter.setFont(font)
        
        # 根据表情改变文字颜色
        if self._expression_state == "thirsty":
            painter.setPen(QColor(255, 100, 100))  # 红色，表示需要喝水
        elif self._expression_state == "excited":
            painter.setPen(QColor(50, 200, 50))    # 绿色，表示完成目标
        else:
            painter.setPen(self.text_color)
        
        text_rect = QRect(
            rect.x(), 
            int(rect.y() + rect.height() * 0.75), 
            rect.width(), 
            int(rect.height() * 0.15)
        )
        painter.drawText(text_rect, Qt.AlignCenter, percentage_text)
        
        # 绘制状态文字
        status_texts = {
            "thirsty": "渴了~",
            "normal": "还行",
            "happy": "不错!",
            "excited": "棒极了!"
        }
        
        status_text = status_texts.get(self._expression_state, "")
        font.setPointSize(10)
        font.setBold(False)
        painter.setFont(font)
        painter.setPen(QColor(100, 100, 120))
        
        status_rect = QRect(
            rect.x(), 
            int(rect.y() + rect.height() * 0.88), 
            rect.width(), 
            int(rect.height() * 0.1)
        )
        painter.drawText(status_rect, Qt.AlignCenter, status_text)
        
    def add_water(self, amount):
        """添加饮水量 - 增加动画效果"""
        old_percentage = self.water_percentage
        self.current_amount += amount
        if self.current_amount > self.daily_goal:
            self.show_styled_message("恭喜", "您今天的饮水目标已达成！🎉", QMessageBox.Information)
        
        # 更新数据库
        self.data_manager.add_water_record(amount)
        
        # 更新显示
        self.update_water_percentage()
        
        # 如果水位有显著增加，触发开心动画
        if self.water_percentage - old_percentage > 0.1:
            self.trigger_happy_animation()
            
    def trigger_happy_animation(self):
        """触发开心动画"""
        # 暂时设置为兴奋状态
        old_state = self._expression_state
        self._expression_state = "excited"
        
        # 2秒后恢复正常状态
        QTimer.singleShot(2000, lambda: setattr(self, '_expression_state', old_state))
        
        # 触发额外的弹跳
        bounce_anim = QPropertyAnimation(self, b"bounceOffset")
        bounce_anim.setDuration(500)
        bounce_anim.setStartValue(self._bounce_offset)
        bounce_anim.setEndValue(self._bounce_offset + math.pi)
        bounce_anim.setEasingCurve(QEasingCurve.OutBounce)
        bounce_anim.start(QPropertyAnimation.DeleteWhenStopped)
    
    def load_settings(self):
        """从QSettings加载设置"""
        from PyQt5.QtCore import QSettings
        settings = QSettings("WaterBottleApp", "WaterReminder")
        
        # 提醒间隔
        self.reminder_interval = int(settings.value("reminder_interval", 60))
        
        # 每次饮水量
        self.default_water_amount = int(settings.value("water_amount", 200))
        
        # 水瓶大小设置 - 默认为"中等"
        bottle_size = settings.value("bottle_size", "中等")
        self.apply_bottle_size(bottle_size)
        
    def apply_bottle_size(self, size_name):
        """应用水瓶大小设置"""
        size_configs = {
            "小": (120, 240),
            "中等": (160, 320),
            "大": (200, 400),
            "超大": (240, 480)
        }
        
        if size_name in size_configs:
            width, height = size_configs[size_name]
            self.resize(width, height)
            
            # 重新定位到屏幕右下角
            desktop = QApplication.desktop()
            screen_rect = desktop.availableGeometry()
            self.move(screen_rect.width() - self.width() - 20, 
                     screen_rect.height() - self.height() - 20)
        else:
            # 如果设置值无效，使用默认的"中等"大小
            self.resize(160, 320)
            desktop = QApplication.desktop()
            screen_rect = desktop.availableGeometry()
            self.move(screen_rect.width() - self.width() - 20, 
                     screen_rect.height() - self.height() - 20)
            
    def setup_tray_icon(self):
        """设置系统托盘图标"""
        # 托盘菜单
        self.tray_menu = QMenu()
        self.tray_menu.setStyleSheet("""
            QMenu {
                background-color: rgba(255, 255, 255, 0.85);
                border: 1px solid rgba(200, 200, 200, 0.5);
                border-radius: 10px;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 30px 8px 30px;
                border-radius: 6px;
            }
            QMenu::item:selected {
                background-color: rgba(52, 152, 219, 0.8);
                color: white;
            }
            QMenu::separator {
                height: 1px;
                background-color: rgba(200, 200, 200, 0.5);
                margin: 5px 15px;
            }
        """)
        
        # 添加菜单项
        self.show_action = QAction("显示", self)
        self.show_action.triggered.connect(self.show)
        
        self.settings_action = QAction("设置", self)
        self.settings_action.triggered.connect(self.open_settings)
        
        self.exit_action = QAction("退出", self)
        self.exit_action.triggered.connect(self.close_application)
        
        self.tray_menu.addAction(self.show_action)
        self.tray_menu.addAction(self.settings_action)
        self.tray_menu.addSeparator()
        self.tray_menu.addAction(self.exit_action)
        
        # 创建图标
        try:
            icon = None
            
            # 1. 尝试从资源目录加载图标
            icon_path = os.path.join("resources", "water_bottle_64.png")
            if os.path.exists(icon_path):
                icon = QIcon(icon_path)
            
            # 2. 尝试生成图标
            elif create_water_bottle_icon:
                try:
                    icon_path = create_water_bottle_icon()
                    if os.path.exists(icon_path):
                        icon = QIcon(icon_path)
                except Exception as e:
                    print(f"生成图标失败: {str(e)}")
            
            # 3. 如果前两种方式失败，创建一个简单的默认图标
            if not icon:
                icon_pixmap = QPixmap(32, 32)
                icon_pixmap.fill(self.bottle_color)
                icon = QIcon(icon_pixmap)
            
            # 设置系统托盘图标
            self.tray_icon = QSystemTrayIcon(self)
            self.tray_icon.setIcon(icon)
            self.tray_icon.setToolTip("水瓶提醒")
            self.tray_icon.setContextMenu(self.tray_menu)
            self.tray_icon.activated.connect(self.tray_icon_activated)
            self.tray_icon.show()
        except Exception as e:
            print(f"无法创建系统托盘图标: {str(e)}")
            
    def tray_icon_activated(self, reason):
        """托盘图标被激活"""
        if reason == QSystemTrayIcon.DoubleClick:
            if self.isHidden():
                self.show()
            else:
                self.hide()
        
    def update_water_percentage(self):
        """更新水位百分比"""
        self.water_percentage = self.calculate_percentage()
        
    def calculate_percentage(self):
        """计算当前饮水百分比"""
        if self.daily_goal > 0:
            return min(1.0, self.current_amount / self.daily_goal)
        return 0
        
    def mousePressEvent(self, event):
        """鼠标按下事件，用于拖动窗口"""
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPos()
            self.is_dragging = True
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件，用于拖动窗口"""
        if self.is_dragging:
            delta = QPoint(event.globalPos() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件，结束拖动"""
        if event.button() == Qt.LeftButton:
            self.is_dragging = False
    
    def mouseDoubleClickEvent(self, event):
        """鼠标双击事件，记录饮水"""
        self.add_water(self.default_water_amount)
        
    def contextMenuEvent(self, event):
        """右键菜单 - 卡通风格"""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: rgba(255, 255, 255, 0.9);
                border: 2px solid rgba(65, 180, 255, 0.7);
                border-radius: 12px;
                padding: 8px;
            }
            QMenu::item {
                padding: 10px 35px 10px 35px;
                border-radius: 8px;
                color: #333;
            }
            QMenu::item:selected {
                background-color: rgba(65, 180, 255, 0.8);
                color: white;
            }
            QMenu::separator {
                height: 2px;
                background-color: rgba(65, 180, 255, 0.3);
                margin: 8px 15px;
            }
        """)
        
        # 添加饮水量动作
        add_menu = menu.addMenu("💧 添加饮水量")
        add_menu.setStyleSheet("QMenu::item {padding: 8px 25px;}")
        
        amounts = [100, 200, 300, 500]
        for amount in amounts:
            action = add_menu.addAction(f"{amount}ml")
            action.triggered.connect(lambda checked, a=amount: self.add_water(a))
        
        # 其他动作
        menu.addSeparator()
        settings_action = menu.addAction("⚙️ 设置")
        settings_action.triggered.connect(self.open_settings)
        
        reset_action = menu.addAction("🔄 重置今日记录")
        reset_action.triggered.connect(self.reset_today)
        
        menu.addSeparator()
        exit_action = menu.addAction("❌ 退出")
        exit_action.triggered.connect(self.close_application)
        
        menu.exec_(event.globalPos())
        
    def open_settings(self):
        """打开设置对话框"""
        dialog = SettingsDialog(self)
        if dialog.exec_():
            # 更新设置
            self.load_settings()
            
            # 更新每日目标
            new_goal = dialog.calculate_daily_goal()
            self.daily_goal = new_goal
            self.data_manager.set_daily_goal(new_goal)
            
            # 更新用户信息
            user_info = {
                "gender": "male" if dialog.male_radio.isChecked() else "female",
                "weight": dialog.weight_input.value(),
                "activity_level": dialog.activity_combo.currentIndex()
            }
            self.data_manager.set_user_info(user_info)
            
            # 更新显示
            self.update_water_percentage()
            
            # 重置提醒定时器
            self.reminder_timer.stop()
            self.reminder_timer.start(self.reminder_interval * 60 * 1000)
    
    def reset_today(self):
        """重置今天的饮水记录"""
        reply = self.show_styled_message("确认重置", 
                                "确定要重置今天的饮水记录吗？",
                                QMessageBox.Question,
                                QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.data_manager.reset_today_records()
            self.current_amount = 0
            self.update_water_percentage()
            
    def show_styled_message(self, title, text, icon_type=QMessageBox.Information, buttons=QMessageBox.Ok):
        """显示自定义样式的消息框 - 卡通风格"""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(text)
        msg_box.setIcon(icon_type)
        msg_box.setStandardButtons(buttons)
        
        # 设置样式表 - 卡通风格
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: rgba(245, 250, 255, 0.95);
                color: #2c3e50;
                border-radius: 15px;
                border: 2px solid rgba(65, 180, 255, 0.7);
            }
            QPushButton {
                background-color: rgba(65, 180, 255, 0.9);
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px 18px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: rgba(30, 150, 255, 0.9);
            }
            QPushButton:pressed {
                background-color: rgba(20, 120, 200, 0.9);
                padding-top: 11px;
                padding-left: 19px;
                padding-bottom: 9px;
                padding-right: 17px;
            }
            QLabel {
                color: #2c3e50;
                font-size: 12pt;
            }
        """)
        
        # 应用字体
        font = QFont("微软雅黑", 9)
        msg_box.setFont(font)
        
        # 返回结果
        return msg_box.exec_()
    
    def show_reminder(self):
        """显示饮水提醒"""
        # 如果已经达成目标，就不再提醒
        if self.water_percentage >= 1.0:
            return
            
        # 创建提醒动画
        self.reminder_animation()
        
        # 显示消息
        if hasattr(self, 'tray_icon') and self.tray_icon:
            self.tray_icon.showMessage("该喝水了! 💧", 
                                      f"距离上次喝水已经过去 {self.reminder_interval} 分钟了！\n来喝点水吧~",
                                      QSystemTrayIcon.Information, 
                                      4000)
            
            # 同时显示一个更美观的提醒对话框
            self.show_styled_message("喝水提醒 🥤", 
                                    f"已经 {self.reminder_interval} 分钟没有喝水了\n该补充水分啦！",
                                    QMessageBox.Information)
    
    def reminder_animation(self):
        """提醒动画效果"""
        # 保存原始位置
        original_pos = self.pos()
        
        # 创建抖动动画 - 修改为更安全的实现方式
        try:
            # 停止update_timer，避免过多重绘
            self.update_timer.stop()
            
            # 使用QPropertyAnimation代替直接移动
            pos_anim = QPropertyAnimation(self, b"pos")
            pos_anim.setDuration(800)  # 总时长800ms
            pos_anim.setLoopCount(2)   # 循环2次
            
            # 设置关键帧
            pos_anim.setKeyValueAt(0, original_pos)
            pos_anim.setKeyValueAt(0.25, original_pos + QPoint(-15, 0))
            pos_anim.setKeyValueAt(0.5, original_pos)
            pos_anim.setKeyValueAt(0.75, original_pos + QPoint(15, 0))
            pos_anim.setKeyValueAt(1, original_pos)
            
            # 动画结束后重新启动update_timer
            def resume_update():
                self.update_timer.start()
                # 触发开心表情，因为用户注意到了提醒
                self._expression_state = "happy"
                QTimer.singleShot(3000, lambda: setattr(self, '_expression_state', "normal"))
                
            pos_anim.finished.connect(resume_update)
            
            # 启动动画
            pos_anim.start(QPropertyAnimation.DeleteWhenStopped)
            
        except Exception as e:
            print(f"提醒动画出错: {str(e)}")
            # 确保update_timer能继续
            self.update_timer.start()
    
    def close_application(self):
        """关闭应用程序"""
        # 停止所有计时器和动画
        if hasattr(self, 'update_timer') and self.update_timer:
            self.update_timer.stop()
            
        if hasattr(self, 'water_animation') and self.water_animation:
            self.water_animation.stop()
            
        if hasattr(self, 'bounce_animation') and self.bounce_animation:
            self.bounce_animation.stop()
            
        if hasattr(self, 'blink_timer') and self.blink_timer:
            self.blink_timer.stop()
            
        if hasattr(self, 'reminder_timer') and self.reminder_timer:
            self.reminder_timer.stop()
        
        # 清理系统托盘图标
        if hasattr(self, 'tray_icon') and self.tray_icon:
            self.tray_icon.hide()
        
        # 退出应用
        QApplication.quit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 检查运行环境
    try:
        window = WaterBottle()
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        print(f"启动错误: {str(e)}")
        sys.exit(1) 