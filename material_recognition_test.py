# material_recognition_test.py - 材质识别测试工具
import os
import sys
import json
import logging
from typing import List, Dict, Any
import time
from datetime import datetime

# 添加app模块路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.smart_classifier import SmartClassifier, MaterialFeature
from app.enhanced_smart_classifier import EnhancedSmartClassifier

class MaterialRecognitionTester:
    """材质识别测试工具"""
    
    def __init__(self):
        self.setup_logging()
        
        # 数据库路径
        self.db_path = 'master_data.db'
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"数据库文件未找到: {self.db_path}")
            
        # 初始化分类器
        self.original_classifier = SmartClassifier(self.db_path)
        self.enhanced_classifier = EnhancedSmartClassifier(self.db_path)
        
    def setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
    def create_test_dataset(self) -> List[Dict[str, Any]]:
        """创建全面的测试数据集"""
        return [
            # 不锈钢系列测试
            {
                'name': '304不锈钢疏水器',
                'spec': 'DN25 PN16',
                'expected_materials': ['304', '不锈钢'],
                'expected_category': '疏水阀',
                'difficulty': 'medium'
            },
            {
                'name': '316L不锈钢法兰',
                'spec': 'DN100 PN16',
                'expected_materials': ['316L'],
                'expected_category': '法兰',
                'difficulty': 'medium'
            },
            {
                'name': '321不锈钢三通',
                'spec': 'DN50×40×50',
                'expected_materials': ['321'],
                'expected_category': '三通',
                'difficulty': 'hard'
            },
            
            # 碳钢系列测试
            {
                'name': '碳钢螺塞',
                'spec': 'M20×2.5',
                'expected_materials': ['碳钢'],
                'expected_category': '紧固件',
                'difficulty': 'easy'
            },
            {
                'name': '20#钢管道',
                'spec': 'DN80 PN25',
                'expected_materials': ['20#'],
                'expected_category': '管道',
                'difficulty': 'medium'
            },
            {
                'name': 'Q235法兰',
                'spec': 'DN150 PN16',
                'expected_materials': ['Q235'],
                'expected_category': '法兰',
                'difficulty': 'medium'
            },
            
            # 有色金属测试
            {
                'name': '黄铜球阀',
                'spec': 'DN50 PN16',
                'expected_materials': ['黄铜'],
                'expected_category': '球阀',
                'difficulty': 'easy'
            },
            {
                'name': '紫铜管接头',
                'spec': '1/2"NPT',
                'expected_materials': ['紫铜'],
                'expected_category': '接头',
                'difficulty': 'medium'
            },
            
            # 表面处理测试
            {
                'name': '镀锌管接头',
                'spec': '1/2寸',
                'expected_materials': ['镀锌'],
                'expected_category': '接头',
                'difficulty': 'medium'
            },
            {
                'name': '镀镍螺栓',
                'spec': 'M16×50',
                'expected_materials': ['镀镍'],
                'expected_category': '螺栓',
                'difficulty': 'hard'
            },
            
            # 复合材质测试（难度高）
            {
                'name': '304不锈钢镀锌法兰',
                'spec': 'DN80 PN16',
                'expected_materials': ['304', '镀锌'],
                'expected_category': '法兰',
                'difficulty': 'hard'
            },
            
            # 无材质信息测试（对照组）
            {
                'name': '疏水器',
                'spec': 'DN25',
                'expected_materials': [],
                'expected_category': '疏水阀',
                'difficulty': 'easy'
            },
            {
                'name': '球阀',
                'spec': 'DN50',
                'expected_materials': [],
                'expected_category': '球阀',
                'difficulty': 'easy'
            }
        ]
        
    def test_single_material(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """测试单个物料的识别效果"""
        
        material = MaterialFeature(
            name=test_case['name'],
            spec=test_case['spec'],
            unit='个'
        )
        
        start_time = time.time()
        
        # 原始分类器测试
        original_results = self.original_classifier.classify_material(material)
        original_time = time.time() - start_time
        
        start_time = time.time()
        
        # 增强分类器测试  
        enhanced_results = self.enhanced_classifier.classify_material(material)
        enhanced_time = time.time() - start_time
        
        # 分析结果
        result = {
            'input': {
                'name': test_case['name'],
                'spec': test_case['spec'],
                'difficulty': test_case['difficulty']
            },
            'expected': {
                'materials': test_case['expected_materials'],
                'category': test_case['expected_category']
            },
            'original': {
                'category': original_results[0]['category'] if original_results else 'N/A',
                'confidence': original_results[0]['confidence'] if original_results else 0,
                'time_ms': round(original_time * 1000, 2)
            },
            'enhanced': {
                'category': enhanced_results[0]['category'] if enhanced_results else 'N/A',
                'confidence': enhanced_results[0]['confidence'] if enhanced_results else 0,
                'materials_detected': enhanced_results[0].get('material_info', []) if enhanced_results else [],
                'time_ms': round(enhanced_time * 1000, 2)
            }
        }
        
        # 计算改进效果
        if original_results and enhanced_results:
            result['improvement'] = {
                'confidence_delta': enhanced_results[0]['confidence'] - original_results[0]['confidence'],
                'category_match': enhanced_results[0]['category'] == test_case['expected_category'],
                'material_detection_success': len(enhanced_results[0].get('material_info', [])) > 0 and len(test_case['expected_materials']) > 0
            }
            
        return result
        
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """运行全面测试"""
        
        print("🔬 开始材质识别全面测试...")
        print("=" * 60)
        
        test_dataset = self.create_test_dataset()
        results = []
        
        for i, test_case in enumerate(test_dataset, 1):
            print(f"\n测试 {i}/{len(test_dataset)}: {test_case['name']}")
            result = self.test_single_material(test_case)
            results.append(result)
            
            # 打印测试结果
            self._print_test_result(result)
            
        # 统计分析
        stats = self._calculate_statistics(results)
        
        # 生成报告
        report = {
            'test_time': datetime.now().isoformat(),
            'total_tests': len(results),
            'results': results,
            'statistics': stats
        }
        
        return report
        
    def _print_test_result(self, result: Dict[str, Any]):
        """打印单个测试结果"""
        
        input_info = result['input']
        original = result['original']
        enhanced = result['enhanced']
        
        print(f"  📝 输入: {input_info['name']} ({input_info['spec']})")
        print(f"  📊 原始: {original['category']} ({original['confidence']}%) - {original['time_ms']}ms")
        print(f"  ✨ 增强: {enhanced['category']} ({enhanced['confidence']}%) - {enhanced['time_ms']}ms")
        
        if 'improvement' in result:
            improvement = result['improvement']
            delta = improvement['confidence_delta']
            print(f"  🎯 改进: {delta:+.1f}% | 分类正确: {'✅' if improvement['category_match'] else '❌'} | 材质检测: {'✅' if improvement['material_detection_success'] else '❌'}")
        else:
            print("  ⚠️  无法比较结果")
            
    def _calculate_statistics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """计算统计信息"""
        
        stats = {
            'total_tests': len(results),
            'original_algorithm': {
                'avg_confidence': 0,
                'correct_classifications': 0,
                'avg_time_ms': 0
            },
            'enhanced_algorithm': {
                'avg_confidence': 0, 
                'correct_classifications': 0,
                'material_detections': 0,
                'avg_time_ms': 0
            },
            'improvements': {
                'avg_confidence_gain': 0,
                'accuracy_improvement': 0,
                'tests_with_gains': 0
            },
            'difficulty_analysis': {
                'easy': {'total': 0, 'improved': 0},
                'medium': {'total': 0, 'improved': 0},
                'hard': {'total': 0, 'improved': 0}
            }
        }
        
        valid_comparisons = [r for r in results if 'improvement' in r]
        
        if not valid_comparisons:
            return stats
            
        # 原始算法统计
        original_confidences = [r['original']['confidence'] for r in valid_comparisons]
        original_times = [r['original']['time_ms'] for r in valid_comparisons]
        original_correct = sum(1 for r in valid_comparisons if r['original']['category'] == r['expected']['category'])
        
        stats['original_algorithm']['avg_confidence'] = round(sum(original_confidences) / len(original_confidences), 1)
        stats['original_algorithm']['correct_classifications'] = original_correct
        stats['original_algorithm']['avg_time_ms'] = round(sum(original_times) / len(original_times), 2)
        
        # 增强算法统计
        enhanced_confidences = [r['enhanced']['confidence'] for r in valid_comparisons]
        enhanced_times = [r['enhanced']['time_ms'] for r in valid_comparisons]
        enhanced_correct = sum(1 for r in valid_comparisons if r['improvement']['category_match'])
        material_detections = sum(1 for r in valid_comparisons if r['improvement']['material_detection_success'])
        
        stats['enhanced_algorithm']['avg_confidence'] = round(sum(enhanced_confidences) / len(enhanced_confidences), 1)
        stats['enhanced_algorithm']['correct_classifications'] = enhanced_correct
        stats['enhanced_algorithm']['material_detections'] = material_detections
        stats['enhanced_algorithm']['avg_time_ms'] = round(sum(enhanced_times) / len(enhanced_times), 2)
        
        # 改进统计
        confidence_gains = [r['improvement']['confidence_delta'] for r in valid_comparisons]
        tests_with_gains = sum(1 for gain in confidence_gains if gain > 0)
        
        stats['improvements']['avg_confidence_gain'] = round(sum(confidence_gains) / len(confidence_gains), 1)
        stats['improvements']['accuracy_improvement'] = enhanced_correct - original_correct
        stats['improvements']['tests_with_gains'] = tests_with_gains
        
        # 难度分析
        for result in valid_comparisons:
            difficulty = result['input']['difficulty']
            stats['difficulty_analysis'][difficulty]['total'] += 1
            if result['improvement']['confidence_delta'] > 5:  # 5%以上改进
                stats['difficulty_analysis'][difficulty]['improved'] += 1
                
        return stats
        
    def print_summary_report(self, report: Dict[str, Any]):
        """打印总结报告"""
        
        stats = report['statistics']
        
        print("\n" + "=" * 60)
        print("📊 材质识别测试总结报告")
        print("=" * 60)
        
        print(f"\n🧪 测试概况:")
        print(f"  总测试数: {stats['total_tests']}")
        print(f"  测试时间: {report['test_time']}")
        
        print(f"\n📈 原始算法表现:")
        print(f"  平均置信度: {stats['original_algorithm']['avg_confidence']}%")
        print(f"  正确分类数: {stats['original_algorithm']['correct_classifications']}/{stats['total_tests']}")
        print(f"  平均响应时间: {stats['original_algorithm']['avg_time_ms']}ms")
        
        print(f"\n✨ 增强算法表现:")
        print(f"  平均置信度: {stats['enhanced_algorithm']['avg_confidence']}%")
        print(f"  正确分类数: {stats['enhanced_algorithm']['correct_classifications']}/{stats['total_tests']}")
        print(f"  材质检测数: {stats['enhanced_algorithm']['material_detections']}")
        print(f"  平均响应时间: {stats['enhanced_algorithm']['avg_time_ms']}ms")
        
        print(f"\n🎯 改进效果:")
        print(f"  平均置信度提升: {stats['improvements']['avg_confidence_gain']:+.1f}%")
        print(f"  分类准确度提升: {stats['improvements']['accuracy_improvement']:+d}")
        print(f"  有改进的测试数: {stats['improvements']['tests_with_gains']}/{stats['total_tests']}")
        
        print(f"\n🔍 难度分析:")
        for difficulty, data in stats['difficulty_analysis'].items():
            if data['total'] > 0:
                improvement_rate = (data['improved'] / data['total']) * 100
                print(f"  {difficulty.title()}: {data['improved']}/{data['total']} ({improvement_rate:.1f}%改进)")
                
    def save_detailed_report(self, report: Dict[str, Any], filename: str = None):
        """保存详细报告到JSON文件"""
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"material_recognition_test_report_{timestamp}.json"
            
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
            
        print(f"\n📄 详细报告已保存到: {filename}")

if __name__ == "__main__":
    # 运行测试
    tester = MaterialRecognitionTester()
    
    try:
        report = tester.run_comprehensive_test()
        tester.print_summary_report(report)
        tester.save_detailed_report(report)
        
        print("\n🎉 材质识别测试完成！")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()