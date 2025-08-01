import os
import sys
import shutil
import subprocess

def check_dependencies():
    """检查必要的依赖是否安装"""
    try:
        import PyInstaller
        print("PyInstaller已安装，版本：", PyInstaller.__version__)
    except ImportError:
        print("安装PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        
    try:
        import PyQt5
        print("PyQt5已安装，版本：", PyQt5.QtCore.QT_VERSION_STR)
    except ImportError:
        print("安装PyQt5...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "PyQt5"])

def ensure_icon_exists():
    """确保图标文件存在"""
    icon_path = os.path.join("resources", "water_bottle_64.png")
    if not os.path.exists(icon_path):
        print("未找到图标文件，正在生成...")
        try:
            from create_icon import create_water_bottle_icon
            icon_path = create_water_bottle_icon()
            print(f"图标已生成：{icon_path}")
            return icon_path
        except Exception as e:
            print(f"生成图标失败: {str(e)}")
            return None
    else:
        print(f"使用现有图标: {icon_path}")
        return icon_path

def cleanup():
    """清理之前的构建目录"""
    dirs_to_remove = ["build", "dist"]
    for directory in dirs_to_remove:
        if os.path.exists(directory):
            shutil.rmtree(directory)
    
    if os.path.exists("水瓶助手.spec"):
        os.remove("水瓶助手.spec")

def build_exe():
    """使用PyInstaller打包应用程序"""
    print("开始打包应用程序...")
    
    # 确保图标文件存在
    icon_path = ensure_icon_exists()
    
    # PyInstaller命令参数
    cmd = [
        "pyinstaller",
        "--name=水瓶助手",
        "--windowed",  # 不显示控制台窗口
        "--onefile",   # 打包成单个EXE
        "--clean",     # 清理临时文件
        "--noconfirm", # 不询问确认
    ]
    
    # 添加图标
    if icon_path:
        cmd.append(f"--icon={icon_path}")
    
    # 添加数据文件
    cmd.extend([
        "--add-data=README.md;.",
    ])
    
    # 如果resources目录存在，添加所有资源
    if os.path.exists("resources"):
        cmd.append("--add-data=resources;resources")
    
    # 主脚本
    cmd.append("water_bottle.py")
    
    # 执行打包命令
    subprocess.check_call(cmd)
    
    print("打包完成！")
    print(f"可执行文件位于: {os.path.join('dist', '水瓶助手.exe')}")

def check_upx():
    """检查是否安装了UPX压缩工具"""
    try:
        result = subprocess.run(["upx", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print("检测到UPX，将用于压缩可执行文件")
            return True
    except FileNotFoundError:
        pass
    
    print("未检测到UPX，建议安装以减小EXE文件大小")
    print("UPX官网：https://upx.github.io/")
    return False

if __name__ == "__main__":
    print("===== 水瓶助手应用打包工具 =====")
    print("此脚本将把Python应用打包为单个EXE文件")
    
    # 检查依赖
    check_dependencies()
    
    # 检查UPX
    has_upx = check_upx()
    
    # 清理旧的构建文件
    cleanup()
    
    # 构建EXE
    build_exe()
    
    print("\n===== 打包过程完成 =====")
    if not has_upx:
        print("提示: 安装UPX可以减小生成的EXE文件大小")
        print("      请访问: https://upx.github.io/")
    
    input("按Enter键退出...") 