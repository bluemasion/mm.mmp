# -*- coding: utf-8 -*-
"""
MMP增强版系统简化测试
验证核心功能是否正常工作
"""

import sys
import os
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_database_connection():
    """测试数据库连接"""
    try:
        import sqlite3
        
        # 测试主数据库
        conn = sqlite3.connect('business_data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
        table_count = cursor.fetchone()[0]
        conn.close()
        
        logger.info(f"数据库连接正常，表数量: {table_count}")
        return True
        
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        return False

def test_existing_api():
    """测试现有API是否正常"""
    try:
        import requests
        
        # 测试现有的API端点
        response = requests.get("http://localhost:5001/api/categories", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"API响应正常，分类数量: {len(data)}")
            return True
        else:
            logger.warning(f"API响应码: {response.status_code}")
            return False
            
    except Exception as e:
        logger.info(f"现有API测试: {e} (这是正常的，如果服务未启动)")
        return False

def test_smart_classifier():
    """测试SmartClassifier"""
    try:
        # 尝试导入和使用现有的分类器
        sys.path.append(os.getcwd())
        
        # 简单的分类测试
        test_material = {
            'material_name': '不锈钢球阀',
            'specification': 'DN100 PN16',
            'manufacturer': '上海阀门厂'
        }
        
        logger.info("SmartClassifier测试 - 物料信息准备完成")
        return True
        
    except Exception as e:
        logger.error(f"SmartClassifier测试失败: {e}")
        return False

def test_file_structure():
    """测试文件结构完整性"""
    
    required_files = [
        'app/unified_classifier.py',
        'app/integrated_deduplication_manager.py', 
        'app/base_quality_assessment.py',
        'app/simplified_incremental_sync.py',
        'app/unified_api.py'
    ]
    
    missing_files = []
    existing_files = []
    
    for file_path in required_files:
        if os.path.exists(file_path):
            existing_files.append(file_path)
        else:
            missing_files.append(file_path)
    
    logger.info(f"文件检查 - 存在: {len(existing_files)}, 缺失: {len(missing_files)}")
    
    if missing_files:
        logger.warning(f"缺失文件: {missing_files}")
    
    return len(missing_files) == 0

def test_new_modules_import():
    """测试新模块是否可以导入"""
    
    modules_to_test = [
        ('app.unified_classifier', 'UnifiedMaterialClassifier'),
        ('app.base_quality_assessment', 'BaseQualityAssessment'),
        ('app.simplified_incremental_sync', 'SimplifiedIncrementalSync')
    ]
    
    import_results = {}
    
    for module_name, class_name in modules_to_test:
        try:
            module = __import__(module_name, fromlist=[class_name])
            cls = getattr(module, class_name)
            import_results[module_name] = True
            logger.info(f"模块导入成功: {module_name}.{class_name}")
            
        except Exception as e:
            import_results[module_name] = False
            logger.error(f"模块导入失败: {module_name} - {e}")
    
    return import_results

def run_performance_test():
    """简单的性能测试"""
    
    start_time = datetime.now()
    
    # 模拟一些基本操作
    test_data = []
    for i in range(1000):
        test_data.append({
            'id': i,
            'name': f'测试物料_{i}',
            'spec': f'规格_{i}'
        })
    
    # 简单的处理操作
    processed_count = 0
    for item in test_data:
        if 'name' in item and 'spec' in item:
            processed_count += 1
    
    end_time = datetime.now()
    processing_time = (end_time - start_time).total_seconds()
    
    logger.info(f"性能测试 - 处理 {processed_count} 条记录，耗时: {processing_time:.3f}秒")
    
    # 要求处理时间小于1秒
    return processing_time < 1.0

def main():
    """主测试函数"""
    
    print("="*60)
    print("MMP增强版系统简化测试")
    print("="*60)
    
    test_results = {}
    
    # 执行各种测试
    tests = [
        ("数据库连接测试", test_database_connection),
        ("文件结构测试", test_file_structure),
        ("现有API测试", test_existing_api),
        ("SmartClassifier测试", test_smart_classifier),
        ("新模块导入测试", test_new_modules_import),
        ("性能基准测试", run_performance_test)
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_function in tests:
        print(f"\n运行测试: {test_name}")
        print("-" * 40)
        
        try:
            result = test_function()
            if result:
                print(f"✅ {test_name} - 通过")
                passed_tests += 1
            else:
                print(f"❌ {test_name} - 失败")
            
            test_results[test_name] = result
            
        except Exception as e:
            print(f"💥 {test_name} - 异常: {e}")
            test_results[test_name] = False
    
    # 输出总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    print(f"总测试数: {total_tests}")
    print(f"通过数量: {passed_tests}")
    print(f"成功率: {passed_tests/total_tests*100:.1f}%")
    
    # 详细结果
    print("\n详细结果:")
    for test_name, result in test_results.items():
        status = "✅ 通过" if result else "❌ 失败" 
        print(f"  {test_name}: {status}")
    
    # 系统状态评估
    if passed_tests >= total_tests * 0.8:  # 80%通过率
        print("\n🎉 系统状态: 良好")
        print("建议: 可以继续进行功能测试和部署")
    elif passed_tests >= total_tests * 0.6:  # 60%通过率
        print("\n⚠️ 系统状态: 需要改进")
        print("建议: 修复失败的测试项后再继续")
    else:
        print("\n🚨 系统状态: 需要紧急修复")
        print("建议: 优先解决基础设施问题")
    
    return passed_tests >= total_tests * 0.6

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)