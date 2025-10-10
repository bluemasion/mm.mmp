#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MMP数据库初始化和集成脚本
创建默认数据表结构，初始化系统数据
"""

import os
import sys
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 确保当前目录在Python路径中
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

Base = declarative_base()

class Material(Base):
    """物料主数据表"""
    __tablename__ = 'materials'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, comment='物料名称')
    category = Column(String(100), comment='物料分类')
    specification = Column(String(255), comment='规格型号')
    manufacturer = Column(String(200), comment='生产厂家')
    unit = Column(String(50), comment='计量单位')
    price = Column(Float, comment='参考价格')
    description = Column(Text, comment='详细描述')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    is_active = Column(Boolean, default=True, comment='是否激活')

class MatchingRecord(Base):
    """匹配记录表"""
    __tablename__ = 'matching_records'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(100), nullable=False, comment='会话ID')
    input_material = Column(String(255), nullable=False, comment='输入物料名称')
    matched_material_id = Column(Integer, comment='匹配到的物料ID')
    similarity_score = Column(Float, comment='相似度评分')
    match_type = Column(String(50), comment='匹配类型：exact/similar/fuzzy/unmatched')
    status = Column(String(50), default='pending', comment='状态：pending/confirmed/rejected')
    user_feedback = Column(Text, comment='用户反馈')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')

class ProcessingSession(Base):
    """处理会话表"""
    __tablename__ = 'processing_sessions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(100), unique=True, nullable=False, comment='会话ID')
    filename = Column(String(255), comment='上传文件名')
    total_records = Column(Integer, comment='总记录数')
    processed_records = Column(Integer, default=0, comment='已处理记录数')
    matched_records = Column(Integer, default=0, comment='已匹配记录数')
    status = Column(String(50), default='processing', comment='处理状态')
    start_time = Column(DateTime, default=datetime.now, comment='开始时间')
    end_time = Column(DateTime, comment='结束时间')
    error_message = Column(Text, comment='错误信息')

class SystemLog(Base):
    """系统日志表"""
    __tablename__ = 'system_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    level = Column(String(20), nullable=False, comment='日志级别')
    message = Column(Text, nullable=False, comment='日志消息')
    module = Column(String(100), comment='模块名称')
    function = Column(String(100), comment='函数名称')
    session_id = Column(String(100), comment='相关会话ID')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

def init_database(db_path='mmp_database.db'):
    """初始化数据库"""
    try:
        print("🚀 开始初始化MMP数据库...")
        
        # 创建数据库引擎
        engine = create_engine(f'sqlite:///{db_path}', echo=True)
        
        # 创建所有表
        print("📋 创建数据表结构...")
        Base.metadata.create_all(engine)
        
        # 创建会话
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # 插入初始数据
        print("📝 插入初始物料数据...")
        
        initial_materials = [
            {
                'name': '一次性医用外科口罩',
                'category': '医疗防护用品',
                'specification': '17.5cm×9.5cm',
                'manufacturer': '3M医疗',
                'unit': '个',
                'price': 0.5,
                'description': '三层无纺布，符合YY0469-2011标准'
            },
            {
                'name': '医用检查手套',
                'category': '医疗防护用品', 
                'specification': 'M码，乳胶材质',
                'manufacturer': '强生医疗',
                'unit': '双',
                'price': 0.8,
                'description': '一次性使用，无粉，符合GB7543标准'
            },
            {
                'name': '一次性注射器',
                'category': '医疗器械',
                'specification': '5ml，三件套',
                'manufacturer': '迈瑞医疗',
                'unit': '支',
                'price': 0.3,
                'description': '无毒无菌，符合GB15810标准'
            },
            {
                'name': '医用纱布块',
                'category': '医用耗材',
                'specification': '5cm×5cm，8层',
                'manufacturer': '稳健医疗',
                'unit': '片',
                'price': 0.2,
                'description': '100%纯棉，无菌包装'
            },
            {
                'name': '输液器',
                'category': '医疗器械',
                'specification': '一次性使用',
                'manufacturer': '山东威高',
                'unit': '套',
                'price': 1.5,
                'description': '精密过滤，流速可调'
            }
        ]
        
        for material_data in initial_materials:
            material = Material(**material_data)
            session.add(material)
        
        # 提交事务
        session.commit()
        
        print(f"✅ 数据库初始化完成！")
        print(f"📁 数据库文件: {db_path}")
        print(f"📊 初始物料数据: {len(initial_materials)}条")
        
        # 验证数据
        material_count = session.query(Material).count()
        print(f"🔍 验证：数据库中共有 {material_count} 条物料记录")
        
        session.close()
        return True
        
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        return False

def create_database_config():
    """创建数据库配置文件"""
    config_content = '''# MMP数据库配置文件
# Database Configuration for MMP System

[database]
# 默认SQLite数据库配置
default_engine = sqlite
sqlite_path = mmp_database.db
sqlite_url = sqlite:///mmp_database.db

# PostgreSQL配置 (可选)
postgresql_host = localhost
postgresql_port = 5432
postgresql_user = mmp_user
postgresql_password = mmp_password
postgresql_database = mmp_db
postgresql_url = postgresql://mmp_user:mmp_password@localhost:5432/mmp_db

# MySQL配置 (可选)
mysql_host = localhost
mysql_port = 3306
mysql_user = mmp_user
mysql_password = mmp_password
mysql_database = mmp_db
mysql_url = mysql+pymysql://mmp_user:mmp_password@localhost:3306/mmp_db

# MongoDB配置 (可选)
mongodb_host = localhost
mongodb_port = 27017
mongodb_database = mmp_db
mongodb_url = mongodb://localhost:27017/mmp_db

[settings]
# 数据库设置
echo_sql = false
pool_size = 5
max_overflow = 10
pool_timeout = 30
pool_recycle = 3600

# 日志设置
enable_logging = true
log_level = INFO
'''
    
    config_path = 'database_config.ini'
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(config_content)
        print(f"✅ 数据库配置文件创建成功: {config_path}")
        return True
    except Exception as e:
        print(f"❌ 配置文件创建失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("MMP系统数据库初始化工具")
    print("=" * 60)
    
    # 检查数据库文件是否存在
    db_path = 'mmp_database.db'
    if os.path.exists(db_path):
        print(f"⚠️  数据库文件 {db_path} 已存在")
        response = input("是否覆盖现有数据库? (y/N): ").strip().lower()
        if response != 'y':
            print("❌ 取消初始化")
            return False
    
    # 初始化数据库
    if init_database(db_path):
        print("✅ 数据库初始化成功")
    else:
        print("❌ 数据库初始化失败")
        return False
    
    # 创建配置文件
    if create_database_config():
        print("✅ 配置文件创建成功")
    else:
        print("❌ 配置文件创建失败")
    
    print("\n" + "=" * 60)
    print("🎉 MMP数据库初始化完成！")
    print("=" * 60)
    print("下一步:")
    print("1. 重启MMP服务以加载数据库配置")
    print("2. 访问 http://localhost:5001 测试功能")
    print("3. 使用数据库管理工具查看数据")
    print("=" * 60)
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)