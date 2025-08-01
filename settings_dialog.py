from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                           QPushButton, QComboBox, QSpinBox, QFormLayout, QGroupBox,
                           QRadioButton, QButtonGroup, QApplication, QStyleFactory, QFrame, QGraphicsBlurEffect, QStyleOptionButton, QStyle)
from PyQt5.QtCore import Qt, QSettings, QSize, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QIcon, QFont, QColor, QPalette, QCursor, QBrush, QLinearGradient

class StyledSpinBox(QSpinBox):
    """自定义样式的SpinBox"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setButtonSymbols(QSpinBox.NoButtons)  # 移除上下按钮，使用更简洁的样式

class StyledRadioButton(QRadioButton):
    """自定义iPhone风格的单选按钮"""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        # 自定义样式
        self.setStyleSheet("""
            QRadioButton {
                spacing: 8px;
                color: #2c3e50;
                padding: 4px 0px;
                margin-right: 15px;
            }
            QRadioButton::indicator {
                width: 22px;
                height: 22px;
                border-radius: 11px;
            }
            QRadioButton::indicator:unchecked {
                border: 2px solid #bdc3c7;
                background-color: transparent;
            }
            QRadioButton::indicator:hover {
                border: 2px solid #3498db;
            }
            QRadioButton::indicator:checked {
                border: none;
                background-color: #3498db;
            }
            QRadioButton::indicator:checked:hover {
                background-color: #2980b9;
            }
        """)
        
    def paintEvent(self, event):
        """自定义绘制以添加选中时的勾选标志"""
        super().paintEvent(event)
        
        if self.isChecked():
            from PyQt5.QtGui import QPainter, QPen, QColor
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # 获取正确的指示器位置
            opt = QStyleOptionButton()
            opt.initFrom(self)
            rect = self.style().subElementRect(QStyle.SE_RadioButtonIndicator, opt, self)
            
            # 绘制勾选标志 (白色小对勾)
            painter.setPen(QPen(QColor(255, 255, 255), 2))
            center_x = rect.x() + rect.width() / 2
            center_y = rect.y() + rect.height() / 2
            
            # 绘制简单的对勾线条
            painter.drawLine(int(center_x - 5), int(center_y), int(center_x - 1), int(center_y + 4))
            painter.drawLine(int(center_x - 1), int(center_y + 4), int(center_x + 5), int(center_y - 4))
            
            painter.end()

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("水瓶设置--作者（木木iOS分享）")
        self.resize(450, 650)  # 从580增加到650，为新的外观设置组腾出空间
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        self.settings = QSettings("WaterBottleApp", "WaterReminder")
        
        # 设置字体
        self.font = QFont("微软雅黑", 9)
        QApplication.setFont(self.font)
        
        # 应用样式表
        self.apply_stylesheet()
        
        self.init_ui()
        self.load_settings()
        
        # 设置动画效果
        self.setup_animations()
        
    def setup_animations(self):
        """设置各种控件的动画效果"""
        # 按钮动画
        for button in self.findChildren(QPushButton):
            button.setGraphicsEffect(None)  # 清除之前的效果
            button.setProperty("hovered", False)
            button.enterEvent = lambda e, b=button: self.button_enter_event(e, b)
            button.leaveEvent = lambda e, b=button: self.button_leave_event(e, b)
        
        # 输入框动画
        for spinbox in self.findChildren(QSpinBox):
            spinbox.setProperty("focused", False)
            spinbox.focusInEvent = lambda e, s=spinbox: self.spinbox_focus_in(e, s)
            spinbox.focusOutEvent = lambda e, s=spinbox: self.spinbox_focus_out(e, s)
            
        # ComboBox动画
        for combo in self.findChildren(QComboBox):
            combo.setProperty("focused", False)
            combo.focusInEvent = lambda e, c=combo: self.combo_focus_in(e, c)
            combo.focusOutEvent = lambda e, c=combo: self.combo_focus_out(e, c)
    
    def button_enter_event(self, event, button):
        """按钮鼠标进入事件"""
        button.setProperty("hovered", True)
        button.setStyleSheet("""
            QPushButton {
                background-color: #2980b9;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                min-width: 80px;
                margin: 1px;
            }
        """)
        
    def button_leave_event(self, event, button):
        """按钮鼠标离开事件"""
        button.setProperty("hovered", False)
        button.setStyleSheet("")
        self.style().unpolish(button)
        self.style().polish(button)
        
    def spinbox_focus_in(self, event, spinbox):
        """输入框获取焦点事件"""
        spinbox.setProperty("focused", True)
        spinbox.setStyleSheet("""
            QSpinBox {
                border: 2px solid #3498db;
                border-radius: 6px;
                padding: 4px;
                background-color: rgba(255, 255, 255, 0.8);
            }
        """)
        
    def spinbox_focus_out(self, event, spinbox):
        """输入框失去焦点事件"""
        spinbox.setProperty("focused", False)
        spinbox.setStyleSheet("")
        self.style().unpolish(spinbox)
        self.style().polish(spinbox)
        
    def combo_focus_in(self, event, combo):
        """下拉框获取焦点事件"""
        combo.setProperty("focused", True)
        combo.setStyleSheet("""
            QComboBox {
                border: 2px solid #3498db;
                border-radius: 6px;
                padding: 4px;
                background-color: rgba(255, 255, 255, 0.8);
            }
        """)
        
    def combo_focus_out(self, event, combo):
        """下拉框失去焦点事件"""
        combo.setProperty("focused", False)
        combo.setStyleSheet("")
        self.style().unpolish(combo)
        self.style().polish(combo)
        
    def apply_stylesheet(self):
        """应用自定义样式表"""
        stylesheet = """
        /* 整体样式 - 液态玻璃效果 */
        QDialog {
            background-color: rgba(245, 247, 250, 0.85);
            color: #2c3e50;
        }
        
        /* 分组框样式 - 液态玻璃效果 */
        QGroupBox {
            font-weight: bold;
            border: 1px solid rgba(189, 195, 199, 0.6);
            border-radius: 16px;
            margin-top: 16px;
            padding-top: 16px;
            background-color: rgba(255, 255, 255, 0.7);
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 15px;
            padding: 0 8px;
            color: #3498db;
        }
        
        /* 按钮样式 */
        QPushButton {
            background-color: #3498db;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 8px 16px;
            font-weight: bold;
            min-width: 80px;
            margin: 1px;
        }
        
        QPushButton:hover {
            background-color: #2980b9;
            margin: 0px;
            border: 1px solid #1c6ea4;
        }
        
        QPushButton:pressed {
            background-color: #1c6ea4;
            margin: 2px 0px 0px 2px;
        }
        
        /* 输入框样式 */
        QSpinBox, QComboBox {
            border: 1px solid rgba(189, 195, 199, 0.8);
            border-radius: 8px;
            padding: 6px;
            background-color: rgba(255, 255, 255, 0.7);
            min-height: 24px;
        }
        
        QSpinBox:focus, QComboBox:focus, QSpinBox:hover, QComboBox:hover {
            border: 2px solid #3498db;
            background-color: rgba(255, 255, 255, 0.9);
        }
        
        QComboBox::drop-down {
            border: none;
            width: 24px;
        }
        
        QComboBox::down-arrow {
            image: url(none);
            width: 14px;
            height: 14px;
        }
        
        /* 标签样式 */
        QLabel {
            color: #2c3e50;
        }
        
        /* 表单样式 */
        QFormLayout Label {
            min-width: 80px;
        }
        """
        
        self.setStyleSheet(stylesheet)
        
    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(25, 25, 25, 25)
        self.setLayout(main_layout)
        
        # 创建欢迎标签
        welcome_label = QLabel("个性化您的饮水方案")
        welcome_label.setAlignment(Qt.AlignCenter)
        welcome_label.setFont(QFont("微软雅黑", 14, QFont.Bold))
        welcome_label.setStyleSheet("color: #3498db; margin-bottom: 15px;")
        main_layout.addWidget(welcome_label)
        
        # 个人信息组
        personal_group = QGroupBox("个人信息")
        personal_layout = QFormLayout()
        personal_layout.setSpacing(15)
        personal_layout.setContentsMargins(25, 25, 25, 25)
        personal_group.setLayout(personal_layout)
        
        # 性别选择 - 修复显示问题，使用自定义单选按钮
        gender_layout = QHBoxLayout()
        gender_layout.setSpacing(25)  # 增加间距
        gender_frame = QFrame()
        gender_frame.setMinimumHeight(40)  # 增加高度
        gender_frame.setLayout(gender_layout)
        
        self.male_radio = StyledRadioButton("男")  # 使用自定义单选按钮
        self.female_radio = StyledRadioButton("女")  # 使用自定义单选按钮
        self.male_radio.setMinimumWidth(60)  # 设置最小宽度
        self.female_radio.setMinimumWidth(60)
        
        gender_layout.addWidget(self.male_radio)
        gender_layout.addWidget(self.female_radio)
        gender_layout.addStretch()
        personal_layout.addRow("性别:", gender_frame)  # 使用QFrame容器
        
        # 体重输入
        self.weight_input = StyledSpinBox()
        self.weight_input.setRange(30, 200)
        self.weight_input.setSuffix(" kg")
        self.weight_input.setMinimumHeight(36)  # 增加高度
        personal_layout.addRow("体重:", self.weight_input)
        
        # 活动水平
        self.activity_combo = QComboBox()
        self.activity_combo.addItems(["久坐不动", "轻度活动", "中度活动", "高度活动"])
        self.activity_combo.setFixedHeight(36)  # 增加高度
        personal_layout.addRow("活动水平:", self.activity_combo)
        
        main_layout.addWidget(personal_group)
        
        # 饮水目标组
        goal_group = QGroupBox("饮水目标")
        goal_layout = QVBoxLayout()
        goal_layout.setSpacing(15)
        goal_layout.setContentsMargins(25, 25, 25, 25)
        goal_group.setLayout(goal_layout)
        
        # 计算模式选择 - 使用自定义单选按钮
        self.standard_radio = StyledRadioButton("标准模式 (男1700ml/女1500ml)")
        self.formula_radio = StyledRadioButton("公式模式 (体重×35ml)")
        
        self.goal_button_group = QButtonGroup(self)
        self.goal_button_group.addButton(self.standard_radio)
        self.goal_button_group.addButton(self.formula_radio)
        
        goal_layout.addWidget(self.standard_radio)
        goal_layout.addWidget(self.formula_radio)
        
        # 自定义目标
        custom_layout = QHBoxLayout()
        custom_layout.setSpacing(15)  # 增加间距
        self.custom_radio = StyledRadioButton("自定义:")  # 使用自定义单选按钮
        self.goal_button_group.addButton(self.custom_radio)
        
        self.custom_goal = StyledSpinBox()
        self.custom_goal.setRange(500, 5000)
        self.custom_goal.setSingleStep(100)
        self.custom_goal.setSuffix(" ml")
        self.custom_goal.setMinimumHeight(36)  # 增加高度
        
        custom_layout.addWidget(self.custom_radio)
        custom_layout.addWidget(self.custom_goal)
        custom_layout.addStretch()
        goal_layout.addLayout(custom_layout)
        
        main_layout.addWidget(goal_group)
        
        # 提醒设置组
        reminder_group = QGroupBox("提醒设置")
        reminder_layout = QFormLayout()
        reminder_layout.setSpacing(15)
        reminder_layout.setContentsMargins(25, 25, 25, 25)
        reminder_group.setLayout(reminder_layout)
        
        # 提醒间隔
        self.interval_spin = StyledSpinBox()
        self.interval_spin.setRange(15, 120)
        self.interval_spin.setSingleStep(5)
        self.interval_spin.setSuffix(" 分钟")
        self.interval_spin.setValue(60)
        self.interval_spin.setMinimumHeight(36)  # 增加高度
        reminder_layout.addRow("提醒间隔:", self.interval_spin)
        
        # 每次饮水量
        self.amount_spin = StyledSpinBox()
        self.amount_spin.setRange(50, 500)
        self.amount_spin.setSingleStep(50)
        self.amount_spin.setSuffix(" ml")
        self.amount_spin.setValue(200)
        self.amount_spin.setMinimumHeight(36)  # 增加高度
        reminder_layout.addRow("每次饮水量:", self.amount_spin)
        
        main_layout.addWidget(reminder_group)
        
        # 外观设置组
        appearance_group = QGroupBox("外观设置")
        appearance_layout = QFormLayout()
        appearance_layout.setSpacing(15)
        appearance_layout.setContentsMargins(25, 25, 25, 25)
        appearance_group.setLayout(appearance_layout)
        
        # 水瓶大小设置
        self.size_combo = QComboBox()
        self.size_combo.addItems(["小", "中等", "大", "超大"])
        self.size_combo.setFixedHeight(36)
        appearance_layout.addRow("水瓶大小:", self.size_combo)
        
        main_layout.addWidget(appearance_group)
        
        # 按钮
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        self.save_button = QPushButton("保存")
        self.cancel_button = QPushButton("取消")
        self.cancel_button.setStyleSheet("""
            background-color: #e74c3c;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 8px 16px;
            font-weight: bold;
            min-width: 80px;
        """)
        
        self.save_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.cancel_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.save_button.setMinimumHeight(36)  # 增加高度
        self.cancel_button.setMinimumHeight(36)  # 增加高度
        
        self.save_button.clicked.connect(self.save_settings)
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        
        main_layout.addLayout(button_layout)
        
    def load_settings(self):
        """从QSettings加载设置"""
        # 性别
        if self.settings.value("gender", "male") == "male":
            self.male_radio.setChecked(True)
        else:
            self.female_radio.setChecked(True)
        
        # 体重
        self.weight_input.setValue(int(self.settings.value("weight", 65)))
        
        # 活动水平
        activity_index = self.settings.value("activity_level", 0, int)
        self.activity_combo.setCurrentIndex(activity_index)
        
        # 计算模式
        goal_mode = self.settings.value("goal_mode", "standard")
        if goal_mode == "standard":
            self.standard_radio.setChecked(True)
        elif goal_mode == "formula":
            self.formula_radio.setChecked(True)
        else:
            self.custom_radio.setChecked(True)
        
        # 自定义目标
        self.custom_goal.setValue(int(self.settings.value("custom_goal", 1700)))
        
        # 提醒间隔
        self.interval_spin.setValue(int(self.settings.value("reminder_interval", 60)))
        
        # 每次饮水量
        self.amount_spin.setValue(int(self.settings.value("water_amount", 200)))
        
        # 水瓶大小
        bottle_size = self.settings.value("bottle_size", "中等")
        size_index = ["小", "中等", "大", "超大"].index(bottle_size) if bottle_size in ["小", "中等", "大", "超大"] else 1
        self.size_combo.setCurrentIndex(size_index)
    
    def save_settings(self):
        """保存设置到QSettings"""
        # 性别
        self.settings.setValue("gender", "male" if self.male_radio.isChecked() else "female")
        
        # 体重
        self.settings.setValue("weight", self.weight_input.value())
        
        # 活动水平
        self.settings.setValue("activity_level", self.activity_combo.currentIndex())
        
        # 计算模式
        if self.standard_radio.isChecked():
            self.settings.setValue("goal_mode", "standard")
        elif self.formula_radio.isChecked():
            self.settings.setValue("goal_mode", "formula")
        else:
            self.settings.setValue("goal_mode", "custom")
        
        # 自定义目标
        self.settings.setValue("custom_goal", self.custom_goal.value())
        
        # 提醒间隔
        self.settings.setValue("reminder_interval", self.interval_spin.value())
        
        # 每次饮水量
        self.settings.setValue("water_amount", self.amount_spin.value())
        
        # 水瓶大小
        bottle_sizes = ["小", "中等", "大", "超大"]
        self.settings.setValue("bottle_size", bottle_sizes[self.size_combo.currentIndex()])
        
        # 计算每日目标并返回
        self.accept()
    
    def calculate_daily_goal(self):
        """根据设置计算每日饮水目标"""
        if self.standard_radio.isChecked():
            # 标准模式
            if self.male_radio.isChecked():
                return 1700
            else:
                return 1500
        elif self.formula_radio.isChecked():
            # 公式模式
            weight = self.weight_input.value()
            return weight * 35
        else:
            # 自定义模式
            return self.custom_goal.value() 