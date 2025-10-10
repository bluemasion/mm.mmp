# -*- coding: ut# 导入功能模块
try:
    # 直接从当前目录导入
    from unified_classifier import UnifiedMaterialClassifier, ClassificationRequest
    from integrated_deduplication_manager import IntegratedDeduplicationManager, DeduplicationRequest
    from base_quality_assessment import BaseQualityAssessment
    from simplified_incremental_sync import SimplifiedIncrementalSync
except ImportError as e:
    print(f"导入模块失败: {e}")
    print("请确保在正确的目录中运行此脚本")
    sys.exit(1)"
MMP增强版系统集成测试
验证所有功能模块的协同工作
"""

import sys
import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List

# 添加当前路径到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入功能模块
try:
    from app.unified_classifier import UnifiedMaterialClassifier, ClassificationRequest
    from app.integrated_deduplication_manager import IntegratedDeduplicationManager, DeduplicationRequest
    from app.base_quality_assessment import BaseQualityAssessment
    from app.simplified_incremental_sync import SimplifiedIncrementalSync
except ImportError as e:
    print("导入模块失败: " + str(e))
    print("请确保在正确的目录中运行此脚本")
    sys.exit(1)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

class IntegratedSystemTest:
    """系统集成测试类"""
    
    def __init__(self):
        self.test_results = {
            'start_time': datetime.now().isoformat(),
            'test_cases': [],
            'summary': {
                'total_tests': 0,
                'passed': 0,
                'failed': 0,
                'errors': []
            }
        }
        
        # 初始化系统组件
        self.components = {}
        self._init_components()
    
    def _init_components(self):
        """初始化系统组件"""
        
        logger.info("初始化系统组件...")
        
        try:
            # 统一分类器
            self.components['classifier'] = UnifiedMaterialClassifier({
                'db_path': 'business_data.db'
            })
            logger.info("统一分类器初始化成功")
            
            # 去重管理器
            self.components['deduplication'] = IntegratedDeduplicationManager(
                'business_data.db', 'material_deduplication.db'
            )
            logger.info("去重管理器初始化成功")
            
            # 质量评估器
            self.components['quality'] = BaseQualityAssessment('business_data.db')
            logger.info("质量评估器初始化成功")
            
            # 增量同步系统
            self.components['sync'] = SimplifiedIncrementalSync(
                'business_data.db', 'sync_tracking.db'
            )
            logger.info("增量同步系统初始化成功")
            
        except Exception as e:
            logger.error(f"组件初始化失败: {e}")
            raise
    
    def run_test_case(self, test_name: str, test_function: callable) -> Dict[str, Any]:
        """运行单个测试用例"""
        
        logger.info(f"运行测试: {test_name}")
        
        test_result = {
            'name': test_name,
            'start_time': datetime.now().isoformat(),
            'status': 'running',
            'duration': 0,
            'result': None,
            'error': None
        }
        
        start_time = datetime.now()
        
        try:
            # 执行测试函数
            result = test_function()
            
            test_result['status'] = 'passed'
            test_result['result'] = result
            self.test_results['summary']['passed'] += 1
            
        except Exception as e:
            test_result['status'] = 'failed'
            test_result['error'] = str(e)
            self.test_results['summary']['failed'] += 1
            self.test_results['summary']['errors'].append(f"{test_name}: {e}")
            
            logger.error(f"测试 {test_name} 失败: {e}")
        
        finally:
            end_time = datetime.now()
            test_result['duration'] = (end_time - start_time).total_seconds()
            test_result['end_time'] = end_time.isoformat()
            
            self.test_results['test_cases'].append(test_result)
            self.test_results['summary']['total_tests'] += 1
        
        return test_result
    
    def test_unified_classification(self) -> Dict[str, Any]:
        """测试统一分类功能"""
        
        classifier = self.components['classifier']
        
        # 测试物料
        test_material = ClassificationRequest(
            material_name='不锈钢球阀',
            specification='DN100 PN16 304材质',
            manufacturer='上海阀门制造有限公司',
            material_type='阀门',
            unit='个'
        )
        
        # 执行分类
        result = classifier.classify(test_material)
        
        # 验证结果
        assert result.predicted_category, "分类结果不能为空"
        assert 0 <= result.confidence_score <= 1, "置信度必须在0-1之间"
        assert result.processing_time > 0, "处理时间必须大于0"
        
        return {
            'predicted_category': result.predicted_category,
            'confidence_score': result.confidence_score,
            'classifier_used': result.classifier_used,
            'processing_time': result.processing_time
        }
    
    def test_batch_classification(self) -> Dict[str, Any]:
        """测试批量分类功能"""
        
        classifier = self.components['classifier']
        
        # 测试物料列表
        test_materials = [
            ClassificationRequest(
                material_name='碳钢法兰',
                specification='DN150 PN25',
                manufacturer='北京钢铁公司',
                unit='个'
            ),
            ClassificationRequest(
                material_name='铜管',
                specification='φ25×2mm',
                manufacturer='天津铜业',
                unit='米'
            ),
            ClassificationRequest(
                material_name='橡胶密封圈',
                specification='内径100mm 外径120mm',
                manufacturer='青岛橡胶厂',
                unit='个'
            )
        ]
        
        # 执行批量分类
        results = classifier.classify_batch(test_materials)
        
        # 验证结果
        assert len(results) == len(test_materials), "批量分类结果数量不匹配"
        
        batch_stats = {
            'total_materials': len(test_materials),
            'successful_classifications': sum(1 for r in results if r.predicted_category),
            'average_confidence': sum(r.confidence_score for r in results) / len(results),
            'total_processing_time': sum(r.processing_time for r in results)
        }
        
        return batch_stats
    
    def test_quality_assessment(self) -> Dict[str, Any]:
        """测试质量评估功能"""
        
        quality_assessor = self.components['quality']
        
        # 测试物料数据
        test_material = {
            'material_code': 'TEST_M001',
            'material_name': '不锈钢球阀',
            'specification': 'DN100 PN16 304不锈钢材质 法兰连接 手动操作',
            'manufacturer': '上海阀门制造有限公司',
            'material_type': '阀门',
            'unit': '个',
            'source_system': 'ERP',
            'last_updated': '2024-01-15T10:00:00'
        }
        
        # 执行质量评估
        quality_result = quality_assessor.assess_material_quality(test_material)
        
        # 验证结果
        assert 0 <= quality_result.overall_score <= 100, "总分必须在0-100之间"
        assert quality_result.quality_grade in ['A', 'B', 'C', 'D'], "质量等级必须为A/B/C/D"
        assert len(quality_result.dimension_scores) == 5, "必须有5个维度的评分"
        
        return {
            'overall_score': quality_result.overall_score,
            'quality_grade': quality_result.quality_grade,
            'dimension_scores': quality_result.dimension_scores,
            'quality_issues_count': len(quality_result.quality_issues),
            'improvement_suggestions_count': len(quality_result.improvement_suggestions)
        }
    
    def test_deduplication_analysis(self) -> Dict[str, Any]:
        """测试去重分析功能"""
        
        dedup_manager = self.components['deduplication']
        
        # 测试物料（模拟相似物料）
        test_materials = [
            {
                'material_code': 'ERP_M001',
                'material_name': '不锈钢球阀',
                'specification': 'DN100 PN16',
                'manufacturer': '上海阀门厂',
                'unit': '个'
            },
            {
                'material_code': 'PLM_M001',
                'material_name': '304不锈钢球阀',
                'specification': 'DN100 压力16bar',
                'manufacturer': '上海阀门制造有限公司',
                'unit': '个'
            },
            {
                'material_code': 'WMS_M001',
                'material_name': '铜管',
                'specification': 'φ25×2mm',
                'manufacturer': '天津铜业',
                'unit': '米'
            }
        ]
        
        # 创建去重请求
        dedup_request = DeduplicationRequest(
            materials=test_materials,
            source_systems=['ERP', 'PLM', 'WMS'],
            confidence_threshold=0.75
        )
        
        # 执行去重分析
        dedup_result = dedup_manager.analyze_material_duplicates(dedup_request)
        
        # 验证结果
        assert dedup_result.statistics['total_materials'] == len(test_materials), "总物料数量不匹配"
        
        return {
            'total_materials': dedup_result.statistics['total_materials'],
            'duplicate_groups_found': len(dedup_result.duplicate_groups),
            'duplication_rate': dedup_result.statistics.get('duplication_rate', 0),
            'recommendations_count': len(dedup_result.recommendations)
        }
    
    def test_incremental_sync(self) -> Dict[str, Any]:
        """测试增量同步功能"""
        
        sync_system = self.components['sync']
        
        # 模拟ERP系统数据
        erp_data = [
            {
                'material_code': 'SYNC_TEST_001',
                'material_name': '测试物料1',
                'specification': '测试规格1',
                'manufacturer': '测试厂商1',
                'unit': '个',
                'last_modified': '2024-01-15T10:30:00'
            },
            {
                'material_code': 'SYNC_TEST_002',
                'material_name': '测试物料2',
                'specification': '测试规格2',
                'manufacturer': '测试厂商2',
                'unit': '套',
                'last_modified': '2024-01-15T11:00:00'
            }
        ]
        
        # 执行同步
        sync_result = sync_system.sync_from_source('TEST_ERP', erp_data)
        
        # 验证结果
        assert sync_result.total_records == len(erp_data), "同步记录数量不匹配"
        assert sync_result.processing_time > 0, "处理时间必须大于0"
        
        return {
            'total_records': sync_result.total_records,
            'new_records': sync_result.new_records,
            'updated_records': sync_result.updated_records,
            'conflicts': sync_result.conflicts,
            'errors': sync_result.errors,
            'processing_time': sync_result.processing_time
        }
    
    def test_integrated_workflow(self) -> Dict[str, Any]:
        """测试集成工作流"""
        
        # 模拟完整的物料处理流程
        test_material_data = {
            'material_code': 'WORKFLOW_TEST_001',
            'material_name': '集成测试阀门',
            'specification': 'DN80 PN20 316L不锈钢',
            'manufacturer': '集成测试阀门公司',
            'material_type': '阀门',
            'unit': '个',
            'source_system': 'integration_test'
        }
        
        workflow_results = {}
        
        # 1. 分类
        classifier = self.components['classifier']
        classification_request = ClassificationRequest(
            material_name=test_material_data['material_name'],
            specification=test_material_data['specification'],
            manufacturer=test_material_data['manufacturer'],
            material_type=test_material_data['material_type'],
            unit=test_material_data['unit']
        )
        
        classification_result = classifier.classify(classification_request)
        workflow_results['classification'] = {
            'category': classification_result.predicted_category,
            'confidence': classification_result.confidence_score
        }
        
        # 2. 质量评估
        quality_assessor = self.components['quality']
        quality_result = quality_assessor.assess_material_quality(test_material_data)
        workflow_results['quality'] = {
            'score': quality_result.overall_score,
            'grade': quality_result.quality_grade
        }
        
        # 3. 去重检测
        dedup_manager = self.components['deduplication']
        dedup_request = DeduplicationRequest(
            materials=[test_material_data],
            source_systems=['integration_test']
        )
        dedup_result = dedup_manager.analyze_material_duplicates(dedup_request)
        workflow_results['deduplication'] = {
            'duplicates_found': len(dedup_result.duplicate_groups) > 0
        }
        
        # 4. 同步存储
        sync_system = self.components['sync']
        sync_result = sync_system.sync_from_source('integration_test', [test_material_data])
        workflow_results['sync'] = {
            'records_processed': sync_result.total_records,
            'processing_time': sync_result.processing_time
        }
        
        return workflow_results
    
    def run_all_tests(self):
        """运行所有测试用例"""
        
        logger.info("开始运行系统集成测试...")
        
        # 定义测试用例
        test_cases = [
            ('统一分类功能测试', self.test_unified_classification),
            ('批量分类功能测试', self.test_batch_classification),
            ('质量评估功能测试', self.test_quality_assessment),
            ('去重分析功能测试', self.test_deduplication_analysis),
            ('增量同步功能测试', self.test_incremental_sync),
            ('集成工作流测试', self.test_integrated_workflow)
        ]
        
        # 执行所有测试
        for test_name, test_function in test_cases:
            self.run_test_case(test_name, test_function)
        
        # 完成测试
        self.test_results['end_time'] = datetime.now().isoformat()
        self.test_results['total_duration'] = (
            datetime.fromisoformat(self.test_results['end_time']) - 
            datetime.fromisoformat(self.test_results['start_time'])
        ).total_seconds()
        
        # 输出测试报告
        self._generate_test_report()
    
    def _generate_test_report(self):
        """生成测试报告"""
        
        print("\n" + "="*80)
        print("MMP增强版系统集成测试报告")
        print("="*80)
        
        # 总体统计
        summary = self.test_results['summary']
        print(f"\n📊 测试统计:")
        print(f"   总测试数: {summary['total_tests']}")
        print(f"   通过数量: {summary['passed']}")
        print(f"   失败数量: {summary['failed']}")
        print(f"   成功率: {summary['passed']/summary['total_tests']*100:.1f}%")
        print(f"   总耗时: {self.test_results['total_duration']:.2f}秒")
        
        # 详细结果
        print(f"\n📋 详细测试结果:")
        for i, test_case in enumerate(self.test_results['test_cases'], 1):
            status_icon = "✅" if test_case['status'] == 'passed' else "❌"
            print(f"   {i}. {status_icon} {test_case['name']} ({test_case['duration']:.2f}s)")
            
            if test_case['status'] == 'failed':
                print(f"      错误: {test_case['error']}")
            elif test_case['result']:
                # 显示部分关键结果
                result = test_case['result']
                if isinstance(result, dict):
                    key_items = list(result.items())[:3]  # 只显示前3项
                    for key, value in key_items:
                        print(f"      {key}: {value}")
        
        # 错误总结
        if summary['errors']:
            print(f"\n❌ 错误总结:")
            for error in summary['errors']:
                print(f"   - {error}")
        
        # 系统组件状态
        print(f"\n🔧 系统组件状态:")
        for component_name, component in self.components.items():
            status = "正常" if component else "异常"
            print(f"   {component_name}: {status}")
        
        print("\n" + "="*80)
        
        # 保存测试结果到文件
        with open(f'integration_test_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json', 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)
        
        print(f"详细测试结果已保存到 integration_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")

def main():
    """主函数"""
    
    print("MMP增强版系统集成测试")
    print("正在初始化测试环境...")
    
    try:
        # 创建测试实例
        test_runner = IntegratedSystemTest()
        
        # 运行所有测试
        test_runner.run_all_tests()
        
        # 检查是否有测试失败
        if test_runner.test_results['summary']['failed'] > 0:
            print("\n⚠️ 有测试失败，请检查错误信息并修复问题")
            return 1
        else:
            print("\n🎉 所有测试通过！系统集成成功！")
            return 0
            
    except Exception as e:
        print(f"\n💥 测试运行失败: {e}")
        logger.error(f"测试运行失败: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)