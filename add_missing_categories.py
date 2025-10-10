#!/usr/bin/env python3
# add_missing_categories.py
"""添加缺失的分类到数据库"""
from app.master_data_manager import master_data_manager

def add_missing_categories():
    """添加缺失的分类"""
    
    # 需要添加的分类
    categories_to_add = [
        {
            'category_id': 'CAT007',
            'category_name': '电子设备',
            'parent_id': None,
            'level': 1,
            'description': '各类电子设备和电气设备',
            'features': {'keywords': ['电子', '电路', '传感器', '控制器']}
        },
        {
            'category_id': 'CAT008', 
            'category_name': '电气设备',
            'parent_id': 'CAT007',
            'level': 2,
            'description': '电气控制设备',
            'features': {'keywords': ['电气', '控制', '开关', '继电器']}
        },
        {
            'category_id': 'CAT009',
            'category_name': '化工材料',
            'parent_id': None, 
            'level': 1,
            'description': '各类化工材料和试剂',
            'features': {'keywords': ['化学', '溶液', '试剂', '材料']}
        },
        {
            'category_id': 'CAT010',
            'category_name': '建筑材料',
            'parent_id': None,
            'level': 1, 
            'description': '各类建筑材料',
            'features': {'keywords': ['钢材', '水泥', '砂石', '管材']}
        },
        {
            'category_id': 'CAT011',
            'category_name': '钢材',
            'parent_id': 'CAT010',
            'level': 2,
            'description': '各种钢材制品',
            'features': {'keywords': ['钢材', '不锈钢', '钢板', '钢管']}
        },
        {
            'category_id': 'CAT012',
            'category_name': '手术器械',
            'parent_id': 'CAT003',
            'level': 2,
            'description': '外科手术器械',
            'features': {'keywords': ['手术', '外科', '器械', '电极']}
        },
        {
            'category_id': 'CAT013',
            'category_name': '治疗设备',
            'parent_id': 'CAT003', 
            'level': 2,
            'description': '治疗用医疗设备',
            'features': {'keywords': ['治疗', '激光', '射频', '等离子']}
        }
    ]
    
    print("📋 添加缺失的分类到数据库...")
    
    for category in categories_to_add:
        try:
            # 直接尝试添加分类（忽略重复错误）
            pass
            
            # 添加分类
            success = master_data_manager.add_material_category(
                category_id=category['category_id'],
                category_name=category['category_name'],
                parent_id=category['parent_id'],
                level=category['level'],
                description=category['description'],
                features=category['features']
            )
            
            if success:
                print(f"  ✅ 已添加分类: {category['category_name']} ({category['category_id']})")
            else:
                print(f"  ❌ 添加分类失败: {category['category_name']}")
                
        except Exception as e:
            print(f"  ❌ 添加分类失败: {category['category_name']}, 错误: {e}")
    
    print("🎉 分类添加完成!")
    
    # 显示最新的分类统计
    categories = master_data_manager.get_material_categories()
    print(f"📊 当前分类总数: {len(categories)}")

if __name__ == "__main__":
    add_missing_categories()