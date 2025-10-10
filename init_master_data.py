# init_master_data.py
"""
初始化主数据库脚本
为主数据管理器创建表结构并导入基础数据
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.master_data_manager import MasterDataManager

def init_sample_data():
    """初始化示例数据"""
    print("🚀 开始初始化主数据...")
    
    try:
        manager = MasterDataManager()
        
        # 初始化物料分类数据
        sample_categories = [
            {
                'category_id': 'CAT001',
                'category_name': '电子元器件',
                'parent_id': None,
                'level': 1,
                'description': '各类电子元器件',
                'features': {'common_attributes': ['品牌', '型号', '规格']}
            },
            {
                'category_id': 'CAT001001',
                'category_name': '电阻器',
                'parent_id': 'CAT001',
                'level': 2,
                'description': '各种电阻器',
                'features': {'specific_attributes': ['阻值', '功率', '精度']}
            },
            {
                'category_id': 'CAT001002',
                'category_name': '电容器',
                'parent_id': 'CAT001',
                'level': 2,
                'description': '各种电容器',
                'features': {'specific_attributes': ['容量', '电压', '温度系数']}
            },
            {
                'category_id': 'CAT002',
                'category_name': '机械零件',
                'parent_id': None,
                'level': 1,
                'description': '各类机械零件',
                'features': {'common_attributes': ['材质', '尺寸', '表面处理']}
            },
            {
                'category_id': 'CAT002001',
                'category_name': '标准件',
                'parent_id': 'CAT002',
                'level': 2,
                'description': '螺丝、螺母等标准件',
                'features': {'specific_attributes': ['螺纹规格', '长度', '材质']}
            },
            {
                'category_id': 'CAT003',
                'category_name': '原材料',
                'parent_id': None,
                'level': 1,
                'description': '各类原材料',
                'features': {'common_attributes': ['成分', '纯度', '包装规格']}
            }
        ]
        
        manager.store_material_categories(sample_categories)
        print(f"✅ 已导入 {len(sample_categories)} 个物料分类")
        
        # 初始化物料主数据
        sample_materials = [
            {
                'material_code': 'M001001',
                'material_name': '1/4W碳膜电阻 1KΩ',
                'category_id': 'CAT001001',
                'brand': 'KOA',
                'model': 'CF14JT1K00',
                'specification': '1KΩ ±5% 1/4W',
                'unit': '个',
                'attributes': {'阻值': '1KΩ', '功率': '1/4W', '精度': '±5%'}
            },
            {
                'material_code': 'M001002',
                'material_name': '陶瓷电容 100nF',
                'category_id': 'CAT001002',
                'brand': 'MURATA',
                'model': 'GCM188R71C104KA57',
                'specification': '100nF 16V X7R 0603',
                'unit': '个',
                'attributes': {'容量': '100nF', '电压': '16V', '温度系数': 'X7R'}
            },
            {
                'material_code': 'M002001',
                'material_name': '十字盘头螺丝 M3x8',
                'category_id': 'CAT002001',
                'brand': '东明',
                'model': 'DIN7985-M3x8',
                'specification': 'M3x8 304不锈钢',
                'unit': '个',
                'attributes': {'螺纹规格': 'M3', '长度': '8mm', '材质': '304不锈钢'}
            },
            {
                'material_code': 'M003001',
                'material_name': '304不锈钢板 2mm',
                'category_id': 'CAT003',
                'brand': '宝钢',
                'model': '304-2B-2.0',
                'specification': '1000x2000x2.0mm 2B表面',
                'unit': '张',
                'attributes': {'成分': '304不锈钢', '厚度': '2.0mm', '表面': '2B'}
            }
        ]
        
        manager.store_materials(sample_materials)
        print(f"✅ 已导入 {len(sample_materials)} 个物料主数据")
        
        # 初始化分类特征模板
        resistance_features = [
            {'name': '阻值', 'type': 'text', 'required': True},
            {'name': '功率', 'type': 'select', 'options': ['1/8W', '1/4W', '1/2W', '1W', '2W'], 'required': True},
            {'name': '精度', 'type': 'select', 'options': ['±1%', '±5%', '±10%'], 'required': True},
            {'name': '温度系数', 'type': 'text', 'required': False}
        ]
        
        capacitor_features = [
            {'name': '容量', 'type': 'text', 'required': True},
            {'name': '电压', 'type': 'text', 'required': True},
            {'name': '温度系数', 'type': 'select', 'options': ['X7R', 'X5R', 'C0G', 'Y5V'], 'required': False},
            {'name': '封装', 'type': 'select', 'options': ['0603', '0805', '1206', '1210'], 'required': False}
        ]
        
        screw_features = [
            {'name': '螺纹规格', 'type': 'select', 'options': ['M2', 'M2.5', 'M3', 'M4', 'M5', 'M6'], 'required': True},
            {'name': '长度', 'type': 'text', 'required': True},
            {'name': '材质', 'type': 'select', 'options': ['304不锈钢', '316不锈钢', '碳钢镀锌', '黄铜'], 'required': True},
            {'name': '头型', 'type': 'select', 'options': ['十字盘头', '内六角', '外六角', '一字'], 'required': False}
        ]
        
        manager.store_category_features('CAT001001', resistance_features)
        manager.store_category_features('CAT001002', capacitor_features)
        manager.store_category_features('CAT002001', screw_features)
        
        print("✅ 已导入分类特征模板")
        
        # 设置一些缓存数据
        popular_categories = [
            {'id': 'CAT001001', 'name': '电阻器', 'count': 156},
            {'id': 'CAT001002', 'name': '电容器', 'count': 298},
            {'id': 'CAT002001', 'name': '标准件', 'count': 523}
        ]
        
        manager.set_cache('popular_categories', popular_categories, 72)  # 缓存72小时
        print("✅ 已设置热门分类缓存")
        
        # 测试数据查询
        print("\n📊 数据查询测试:")
        categories = manager.get_material_categories()
        print(f"共有 {len(categories)} 个分类")
        
        materials = manager.search_materials('电阻')
        print(f"搜索'电阻'找到 {len(materials)} 个物料")
        
        features = manager.get_category_features('CAT001001')
        print(f"电阻器分类有 {len(features)} 个特征字段")
        
        cache_data = manager.get_cache('popular_categories')
        print(f"热门分类缓存: {len(cache_data) if cache_data else 0} 项")
        
        print("\n🎉 主数据初始化完成！")
        print(f"数据库文件位置: {manager.db_path}")
        
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        raise

if __name__ == "__main__":
    init_sample_data()