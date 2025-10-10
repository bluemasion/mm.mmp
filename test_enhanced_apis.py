#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接测试增强API模块
"""

import sys
import os
import json

# 确保当前目录在Python路径中
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def test_unified_api():
    """测试统一API模块"""
    try:
        print("🔍 测试统一API模块导入...")
        from app.unified_api import unified_api_bp, create_enhanced_app
        
        print("✅ 统一API模块导入成功")
        
        # 测试Flask应用创建
        app = create_enhanced_app()
        print("✅ 增强版Flask应用创建成功")
        
        # 检查Blueprint注册
        print(f"📊 API Blueprint: {unified_api_bp.name}")
        
        return True
        
    except ImportError as e:
        print(f"❌ 模块导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ API测试失败: {e}")
        return False

def test_deduplication_api():
    """测试去重API模块"""
    try:
        print("\n🔍 测试去重API模块导入...")
        from app.deduplication_api import deduplication_bp, init_deduplication_manager
        
        print("✅ 去重API模块导入成功")
        
        # 测试管理器初始化
        manager = init_deduplication_manager()
        print("✅ 去重管理器初始化成功")
        
        # 检查Blueprint
        print(f"📊 去重Blueprint: {deduplication_bp.name}")
        
        return True
        
    except ImportError as e:
        print(f"❌ 模块导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 去重API测试失败: {e}")
        return False

def test_quality_api():
    """测试质量评估API模块"""
    try:
        print("\n🔍 测试质量评估API模块导入...")
        from app.quality_api import quality_bp, init_quality_assessment
        
        print("✅ 质量评估API模块导入成功")
        
        # 测试评估系统初始化
        assessor = init_quality_assessment()
        print("✅ 质量评估系统初始化成功")
        
        # 检查Blueprint
        print(f"📊 质量评估Blueprint: {quality_bp.name}")
        
        return True
        
    except ImportError as e:
        print(f"❌ 模块导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 质量评估API测试失败: {e}")
        return False

def test_sync_api():
    """测试同步API模块"""
    try:
        print("\n🔍 测试同步API模块导入...")
        from app.sync_api import sync_bp, init_sync_system
        
        print("✅ 同步API模块导入成功")
        
        # 测试同步系统初始化
        sync_system = init_sync_system()
        print("✅ 同步系统初始化成功")
        
        # 检查Blueprint
        print(f"📊 同步API Blueprint: {sync_bp.name}")
        
        return True
        
    except ImportError as e:
        print(f"❌ 模块导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 同步API测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("  MMP增强API模块测试")
    print("=" * 60)
    
    test_results = []
    
    # 测试各个API模块
    test_results.append(("统一API", test_unified_api()))
    test_results.append(("去重API", test_deduplication_api()))
    test_results.append(("质量评估API", test_quality_api()))
    test_results.append(("同步API", test_sync_api()))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("  测试结果汇总")
    print("=" * 60)
    
    success_count = 0
    for module_name, success in test_results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{module_name:15}: {status}")
        if success:
            success_count += 1
    
    total_tests = len(test_results)
    success_rate = (success_count / total_tests) * 100
    
    print(f"\n📊 测试统计:")
    print(f"   总测试数: {total_tests}")
    print(f"   成功数量: {success_count}")
    print(f"   成功率: {success_rate:.1f}%")
    
    if success_rate == 100:
        print("\n🎉 所有API模块测试通过！")
    elif success_rate >= 75:
        print("\n✨ 大部分API模块可用，系统基本正常")
    else:
        print("\n⚠️  部分API模块存在问题，需要检查")
    
    return success_rate

if __name__ == '__main__':
    main()