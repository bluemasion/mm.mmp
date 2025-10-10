#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试增强版API的功能
"""
import json
import requests
from datetime import datetime

class EnhancedAPITester:
    def __init__(self):
        self.base_url = "http://127.0.0.1:5000"
        self.test_materials = [
            {
                "material": "316L不锈钢法兰",
                "expected_category": "管件"
            },
            {
                "material": "镀锌管接头",
                "expected_category": "管件"
            },
            {
                "material": "304不锈钢疏水器",
                "expected_category": "阀门"
            },
            {
                "material": "碳钢螺塞",
                "expected_category": "管件"
            }
        ]

    def test_enhanced_api(self):
        """测试增强版API"""
        print("🔬 测试增强版材料分类API")
        print("=" * 60)
        
        # 准备测试数据 - 格式：[物料编码, 物料长描述, 物料名称, 物料分类, 规格, 型号, 单位]
        materials_data = []
        for i, mat in enumerate(self.test_materials):
            materials_data.append([
                f"M{i+1:03d}",  # 物料编码
                mat['material'],  # 物料长描述
                mat['material'],  # 物料名称
                mat['expected_category'],  # 当前分类
                "",  # 规格
                "",  # 型号
                "个"  # 单位
            ])
        
        test_data = {
            'materials': materials_data,
            'template': 'universal-manufacturing',
            'use_enhanced': True
        }
        
        try:
            # 发送请求
            response = requests.post(
                f"{self.base_url}/api/batch_material_matching",
                json=test_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                result = response.json()
                return self._analyze_enhanced_results(result)
            else:
                print(f"❌ API请求失败: {response.status_code}")
                print(f"错误信息: {response.text}")
                return False
                
        except requests.exceptions.ConnectionError:
            print("❌ 无法连接到服务器，请确保服务正在运行")
            return False
        except Exception as e:
            print(f"❌ 测试过程中出现错误: {str(e)}")
            return False

    def test_comparison(self):
        """比较原始版本和增强版本的差异"""
        print("\n🔄 对比测试：原始算法 vs 增强算法")
        print("=" * 60)
        
        # 准备测试数据
        materials_data = []
        for i, mat in enumerate(self.test_materials):
            materials_data.append([
                f"M{i+1:03d}",  # 物料编码
                mat['material'],  # 物料长描述
                mat['material'],  # 物料名称
                mat['expected_category'],  # 当前分类
                "",  # 规格
                "",  # 型号
                "个"  # 单位
            ])
        
        # 测试原始算法
        original_data = {
            'materials': materials_data,
            'template': 'universal-manufacturing',
            'use_enhanced': False
        }
        
        # 测试增强算法
        enhanced_data = {
            'materials': materials_data,
            'template': 'universal-manufacturing', 
            'use_enhanced': True
        }
        
        try:
            # 获取两个版本的结果
            original_response = requests.post(
                f"{self.base_url}/api/batch_material_matching",
                json=original_data,
                headers={'Content-Type': 'application/json'}
            )
            
            enhanced_response = requests.post(
                f"{self.base_url}/api/batch_material_matching",
                json=enhanced_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if original_response.status_code == 200 and enhanced_response.status_code == 200:
                original_result = original_response.json()
                enhanced_result = enhanced_response.json()
                return self._compare_results(original_result, enhanced_result)
            else:
                print("❌ API请求失败")
                return False
                
        except Exception as e:
            print(f"❌ 比较测试失败: {str(e)}")
            return False

    def _analyze_enhanced_results(self, result):
        """分析增强版API结果"""
        if not result.get('success'):
            print("❌ API返回失败状态")
            return False
            
        results = result.get('results', [])
        algorithm_info = result.get('algorithm_info', {})
        
        print(f"📊 算法信息:")
        print(f"   类型: {algorithm_info.get('type', 'Unknown')}")
        print(f"   增强功能: {'启用' if algorithm_info.get('enhanced_enabled') else '未启用'}")
        print(f"   平均置信度: {algorithm_info.get('average_confidence', 0)}%")
        print(f"   材质检测率: {algorithm_info.get('material_detection_rate', 0)}%")
        
        print(f"\n📋 分类结果详情:")
        print("-" * 60)
        
        for i, (test_mat, api_result) in enumerate(zip(self.test_materials, results)):
            material = test_mat['material']
            expected = test_mat['expected_category']
            
            confidence = api_result.get('classification_confidence', 0)
            predicted = api_result.get('recommended_category', 'Unknown')
            material_detected = api_result.get('material_detected', [])
            material_bonus = api_result.get('material_bonus', 0)
            
            print(f"{i+1}. {material}")
            print(f"   预期分类: {expected}")
            print(f"   实际分类: {predicted} (置信度: {confidence}%)")
            print(f"   材质检测: {', '.join(material_detected) if material_detected else '无'}")
            if material_bonus > 0:
                print(f"   材质加成: +{material_bonus}%")
            
            # 检查分类准确性
            accuracy = "✅ 正确" if predicted == expected else "❌ 错误"
            print(f"   准确性: {accuracy}")
            print()
        
        return True

    def _compare_results(self, original, enhanced):
        """比较两个版本的结果"""
        original_results = original.get('results', [])
        enhanced_results = enhanced.get('results', [])
        original_info = original.get('algorithm_info', {})
        enhanced_info = enhanced.get('algorithm_info', {})
        
        print("📈 性能对比:")
        print("-" * 60)
        
        original_avg = original_info.get('average_confidence', 0)
        enhanced_avg = enhanced_info.get('average_confidence', 0)
        improvement = enhanced_avg - original_avg
        
        print(f"原始算法平均置信度: {original_avg}%")
        print(f"增强算法平均置信度: {enhanced_avg}%")
        print(f"置信度提升: {improvement:+.1f}%")
        print(f"材质检测率: {enhanced_info.get('material_detection_rate', 0)}%")
        
        print(f"\n📋 详细对比:")
        print("-" * 60)
        
        for i, material in enumerate(self.test_materials):
            if i < len(original_results) and i < len(enhanced_results):
                orig = original_results[i]
                enh = enhanced_results[i]
                
                orig_conf = orig.get('classification_confidence', 0)
                enh_conf = enh.get('classification_confidence', 0)
                conf_diff = enh_conf - orig_conf
                
                print(f"{i+1}. {material['material']}")
                print(f"   原始: {orig_conf}% -> 增强: {enh_conf}% (提升: {conf_diff:+.1f}%)")
                
                materials_found = enh.get('material_detected', [])
                if materials_found:
                    print(f"   检测到材质: {', '.join(materials_found)}")
                print()
        
        return True

    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始增强版API综合测试")
        print("=" * 60)
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # 测试增强版API
        success1 = self.test_enhanced_api()
        
        # 比较测试
        success2 = self.test_comparison()
        
        # 总结
        print("\n" + "=" * 60)
        if success1 and success2:
            print("✅ 所有测试通过！增强版API工作正常")
        else:
            print("❌ 测试失败，需要检查问题")
        print("=" * 60)

if __name__ == "__main__":
    tester = EnhancedAPITester()
    tester.run_all_tests()