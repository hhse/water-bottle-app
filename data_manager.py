import os
import json
import time
from datetime import datetime, date, timedelta
from pathlib import Path

class DataManager:
    def __init__(self):
        """初始化数据管理器"""
        self.data_dir = os.path.join(os.path.expanduser("~"), ".water_bottle")
        self.data_file = os.path.join(self.data_dir, "water_data.json")
        self.backup_file = os.path.join(self.data_dir, "water_data_backup.json")
        
        # 确保数据目录存在
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        
        # 加载数据或创建空数据结构
        self.data = self.load_data()
    
    def load_data(self):
        """加载饮水数据，如果不存在则创建新数据结构"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                # 如果数据文件损坏，尝试加载备份
                if os.path.exists(self.backup_file):
                    try:
                        with open(self.backup_file, 'r', encoding='utf-8') as f:
                            return json.load(f)
                    except:
                        pass
        
        # 创建新的数据结构
        return {
            "user_info": {
                "weight": 65,
                "gender": "male",
                "activity_level": 0
            },
            "daily_goal": 1700,
            "records": {}
        }
    
    def save_data(self):
        """保存饮水数据到JSON文件"""
        try:
            # 保存当前数据
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            
            # 判断是否需要创建备份
            # 每天23:59或数据变更超过10次后创建备份
            today = date.today().strftime("%Y-%m-%d")
            if today not in self.data.get("backup_info", {}):
                self.data.setdefault("backup_info", {})[today] = 0
            
            self.data["backup_info"][today] += 1
            if self.data["backup_info"][today] >= 10:
                # 创建备份
                with open(self.backup_file, 'w', encoding='utf-8') as f:
                    json.dump(self.data, f, ensure_ascii=False, indent=2)
                self.data["backup_info"][today] = 0
        except Exception as e:
            print(f"保存数据时出错: {str(e)}")
    
    def add_water_record(self, amount):
        """添加饮水记录"""
        today = date.today().strftime("%Y-%m-%d")
        now = datetime.now().strftime("%H:%M")
        
        # 确保记录字典中有今天的记录列表
        if "records" not in self.data:
            self.data["records"] = {}
        
        if today not in self.data["records"]:
            self.data["records"][today] = []
        
        # 添加记录
        self.data["records"][today].append({
            "time": now,
            "amount": amount
        })
        
        # 保存数据
        self.save_data()
    
    def get_today_total(self):
        """获取今天的总饮水量"""
        today = date.today().strftime("%Y-%m-%d")
        total = 0
        
        if today in self.data.get("records", {}):
            for record in self.data["records"][today]:
                total += record["amount"]
        
        return total
    
    def get_daily_goal(self):
        """获取每日饮水目标"""
        return self.data.get("daily_goal", 1700)
    
    def set_daily_goal(self, goal):
        """设置每日饮水目标"""
        self.data["daily_goal"] = goal
        self.save_data()
    
    def get_user_info(self):
        """获取用户信息"""
        return self.data.get("user_info", {
            "weight": 65,
            "gender": "male",
            "activity_level": 0
        })
    
    def set_user_info(self, user_info):
        """设置用户信息"""
        self.data["user_info"] = user_info
        self.save_data()
    
    def get_weekly_stats(self):
        """获取最近一周的饮水统计"""
        stats = []
        today = date.today()
        
        # 获取过去7天的数据
        for i in range(6, -1, -1):
            day = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            total = 0
            
            if day in self.data.get("records", {}):
                for record in self.data["records"][day]:
                    total += record["amount"]
            
            stats.append({
                "date": day,
                "total": total,
                "goal": self.data.get("daily_goal", 1700)
            })
        
        return stats
    
    def reset_today_records(self):
        """重置今天的饮水记录（仅用于测试）"""
        today = date.today().strftime("%Y-%m-%d")
        if "records" in self.data and today in self.data["records"]:
            self.data["records"][today] = []
            self.save_data()
    
    def cleanup_old_records(self, days=30):
        """清理旧记录，默认保留最近30天的数据"""
        if "records" not in self.data:
            return
            
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        records_to_keep = {}
        
        for day, records in self.data["records"].items():
            if day >= cutoff_date:
                records_to_keep[day] = records
        
        self.data["records"] = records_to_keep
        self.save_data() 