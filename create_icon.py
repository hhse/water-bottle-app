from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QPainterPath, QPixmap, QIcon
from PyQt5.QtCore import Qt, QSize
import sys
import os

def create_water_bottle_icon():
    """创建一个水瓶图标并保存为文件"""
    # 创建应用程序实例（必须在创建QPixmap之前）
    app = QApplication.instance() or QApplication(sys.argv)
    
    # 创建不同尺寸的图标
    sizes = [16, 32, 48, 64, 128]
    icons = []
    
    for size in sizes:
        # 创建一个透明的pixmap
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        
        # 创建画家
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 计算水瓶路径
        bottle_path = QPainterPath()
        width, height = size, size
        
        # 瓶颈
        neck_width = width * 0.4
        bottle_path.moveTo(width/2 - neck_width/2, 0)
        bottle_path.lineTo(width/2 + neck_width/2, 0)
        bottle_path.lineTo(width/2 + width*0.4, height*0.2)
        bottle_path.lineTo(width*0.9, height*0.25)
        # 瓶身
        bottle_path.lineTo(width*0.9, height*0.85)
        bottle_path.quadTo(width*0.9, height, width/2, height)
        bottle_path.quadTo(width*0.1, height, width*0.1, height*0.85)
        bottle_path.lineTo(width*0.1, height*0.25)
        bottle_path.lineTo(width/2 - width*0.4, height*0.2)
        bottle_path.closeSubpath()
        
        # 绘制瓶身轮廓
        painter.setPen(QPen(QColor(70, 130, 180), 2))
        painter.setBrush(QColor(255, 255, 255, 200))
        painter.drawPath(bottle_path)
        
        # 绘制水
        water_path = QPainterPath()
        water_height = int(height * 0.6)  # 水位高度
        water_path.moveTo(0, water_height)
        
        # 简单的波浪线
        for x in range(width + 1):
            offset = int(3 * (1 + (x % 2) * 0.5))  # 简单波浪，不使用正弦函数
            water_path.lineTo(x, water_height + offset)
        
        water_path.lineTo(width, height)
        water_path.lineTo(0, height)
        water_path.closeSubpath()
        
        # 裁剪到瓶身内部
        water_path = bottle_path.intersected(water_path)
        
        # 绘制水
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(90, 170, 220, 180))
        painter.drawPath(water_path)
        
        # 结束绘制
        painter.end()
        
        # 添加到图标列表
        icons.append((size, pixmap))
    
    # 创建QIcon并添加各种尺寸
    icon = QIcon()
    for size, pixmap in icons:
        icon.addPixmap(pixmap)
    
    # 保存图标到文件
    icon_dir = "resources"
    if not os.path.exists(icon_dir):
        os.makedirs(icon_dir)
    
    # 保存PNG格式
    for size, pixmap in icons:
        pixmap.save(os.path.join(icon_dir, f"water_bottle_{size}.png"))
    
    print(f"图标已保存到 {icon_dir} 目录")
    return os.path.join(icon_dir, "water_bottle_64.png")

if __name__ == "__main__":
    path = create_water_bottle_icon()
    print(f"主图标路径: {path}")
    sys.exit(0) 