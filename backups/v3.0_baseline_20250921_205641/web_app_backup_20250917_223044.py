# app/web_app.py
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from werkzeug.utils import secure_filename
import os
import json
import uuid
from datetime import datetime
import logging
from typing import Dict, List, Any, Optional

# 导入核心服务
from app.workflow_service import MaterialWorkflowService
from app.database_connector import DatabaseConnector
from app.data_loader import load_data_from_config, save_data_to_config

# 尝试导入增强功能
try:
    from app.advanced_preprocessor import AdvancedPreprocessor
    ADVANCED_PREPROCESSOR_AVAILABLE = True
except ImportError:
    ADVANCED_PREPROCESSOR_AVAILABLE = False

try:
    from enhanced_config import DATABASE_CONNECTIONS, DATA_LOADING_CONFIGS
    ENHANCED_CONFIG_AVAILABLE = True
except ImportError:
    ENHANCED_CONFIG_AVAILABLE = False

# 获取项目根目录路径
import sys
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 创建Flask应用，指定正确的模板和静态文件路径
app = Flask(__name__, 
           template_folder=os.path.join(project_root, 'templates'),
           static_folder=os.path.join(project_root, 'static'))

# 配置Flask会话
app.secret_key = 'your-secret-key-change-in-production'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_KEY_PREFIX'] = 'mmp_session:'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = False  # 开发环境设为False，生产环境应为True
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1小时过期

# 配置文件上传
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls', 'json'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# 确保上传目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 全局服务实例
workflow_service = None
session_data = {}  # 简单的会话数据存储

def init_service():
    """初始化工作流服务"""
    global workflow_service
    try:
        if ENHANCED_CONFIG_AVAILABLE:
            service_config = {
                'data_source': {
                    'master_data': DATA_LOADING_CONFIGS.get('master_data', {}),
                    'use_database': True
                },
                'processing': {
                    'use_advanced_preprocessor': ADVANCED_PREPROCESSOR_AVAILABLE,
                    'use_advanced_matcher': True
                }
            }
        else:
            service_config = None
        
        workflow_service = MaterialWorkflowService(service_config)
        logging.info("工作流服务初始化成功")
        return True
    except Exception as e:
        logging.error(f"工作流服务初始化失败: {e}")
        return False

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_session_id():
    """获取或创建会话ID"""
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    return session['session_id']

def store_session_data(key: str, data: Any):
    """存储会话数据"""
    session_id = get_session_id()
    if session_id not in session_data:
        session_data[session_id] = {}
    session_data[session_id][key] = data
    logging.info(f"存储会话数据: session_id={session_id}, key={key}, data_type={type(data).__name__}")

def get_session_data(key: str, default=None):
    """获取会话数据"""
    session_id = get_session_id()
    data = session_data.get(session_id, {}).get(key, default)
    logging.info(f"获取会话数据: session_id={session_id}, key={key}, found={'Yes' if data != default else 'No'}")
    return data

# ==================== 路由定义 ====================

@app.route('/')
def index():
    """首页"""
    return render_template('index.html')

@app.route('/upload')
def upload_page():
    """数据上传页面"""
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """处理文件上传"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': '没有选择文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '没有选择文件'}), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # 预览数据
            try:
                file_config = {
                    'source_type': 'file',
                    'path': filepath,
                    'type': filename.split('.')[-1].lower()
                }
                
                preview_df = load_data_from_config(file_config)
                
                # 限制预览行数
                preview_rows = preview_df.head(10).to_dict('records')
                
                # 存储文件信息到会话
                file_info = {
                    'filename': filename,
                    'filepath': filepath,
                    'total_rows': len(preview_df),
                    'columns': list(preview_df.columns),
                    'config': file_config
                }
                store_session_data('uploaded_file', file_info)
                
                return jsonify({
                    'success': True,
                    'filename': filename,
                    'total_rows': len(preview_df),
                    'columns': list(preview_df.columns),
                    'preview_data': preview_rows
                })
                
            except Exception as e:
                os.remove(filepath)  # 删除无效文件
                return jsonify({'error': f'文件格式错误: {str(e)}'}), 400
        
        return jsonify({'error': '不支持的文件类型'}), 400
        
    except Exception as e:
        logging.error(f"文件上传失败: {e}")
        return jsonify({'error': '文件上传失败'}), 500

@app.route('/extract_parameters')
def extract_parameters_page():
    """参数提取页面"""
    file_info = get_session_data('uploaded_file')
    if not file_info:
        flash('请先上传文件', 'error')
        return redirect(url_for('upload_page'))
    
    return render_template('extract_parameters.html', file_info=file_info)

@app.route('/extract_parameters', methods=['POST'])
def extract_parameters():
    """执行参数提取"""
    try:
        file_info = get_session_data('uploaded_file')
        if not file_info:
            return jsonify({'error': '没有找到上传的文件'}), 400
        
        # 获取用户选择的字段映射
        field_mapping = request.json.get('field_mapping', {})
        
        # 加载数据
        df = load_data_from_config(file_info['config'])
        
        # 处理每一行数据，提取参数
        extraction_results = []
        
        for index, row in df.head(50).iterrows():  # 限制处理数量以避免超时
            row_data = {}
            for target_field, source_field in field_mapping.items():
                if source_field in row:
                    row_data[target_field] = row[source_field]
            
            # 使用预处理器提取参数
            if ADVANCED_PREPROCESSOR_AVAILABLE:
                preprocessor = AdvancedPreprocessor()
                text_parts = []
                for field in ['asset_name', 'spec_model']:
                    if field in row_data:
                        text_parts.append(str(row_data[field]))
                
                full_text = ' '.join(text_parts)
                extracted_params = preprocessor.extract_comprehensive_parameters(full_text)
                category_recommendations = preprocessor.recommend_category_advanced(full_text, extracted_params)
                
                result = {
                    'row_index': index,
                    'input_data': row_data,
                    'extracted_params': extracted_params,
                    'category_recommendations': category_recommendations[:3],  # Top 3
                    'full_text': full_text
                }
            else:
                # 基础提取逻辑
                result = {
                    'row_index': index,
                    'input_data': row_data,
                    'extracted_params': {'raw_text': ' '.join(str(v) for v in row_data.values())},
                    'category_recommendations': [('未分类', 0.1)],
                    'full_text': ' '.join(str(v) for v in row_data.values())
                }
            
            extraction_results.append(result)
        
        # 存储提取结果
        store_session_data('extraction_results', extraction_results)
        store_session_data('field_mapping', field_mapping)
        
        return jsonify({
            'success': True,
            'results': extraction_results,
            'total_processed': len(extraction_results)
        })
        
    except Exception as e:
        logging.error(f"参数提取失败: {e}")
        return jsonify({'error': f'参数提取失败: {str(e)}'}), 500

@app.route('/category_selection')
def category_selection_page():
    """分类选择页面"""
    session_id = get_session_id()
    extraction_results = get_session_data('extraction_results')
    
    logging.info(f"分类选择页面访问 - Session ID: {session_id}")
    logging.info(f"提取结果: {extraction_results is not None} (类型: {type(extraction_results).__name__ if extraction_results else 'None'})")
    
    if not extraction_results:
        # 检查是否有上传文件但没有提取结果
        uploaded_file = get_session_data('uploaded_file')
        if uploaded_file:
            flash('检测到已上传文件但未完成参数提取，请先完成参数提取', 'warning')
        else:
            flash('请先上传文件并完成参数提取', 'error')
        return redirect(url_for('extract_parameters_page'))
    
    logging.info(f"显示分类选择页面，共 {len(extraction_results)} 条提取结果")
    return render_template('categorize.html', results=extraction_results)

@app.route('/category_selection', methods=['POST'])
def save_category_selection():
    """保存分类选择"""
    try:
        category_selections = request.json.get('selections', {})
        
        # 更新提取结果中的分类选择
        extraction_results = get_session_data('extraction_results', [])
        
        for result in extraction_results:
            row_index = str(result['row_index'])
            if row_index in category_selections:
                result['selected_category'] = category_selections[row_index]
        
        # 保存更新后的结果
        store_session_data('extraction_results', extraction_results)
        
        return jsonify({'success': True, 'message': '分类选择已保存'})
        
    except Exception as e:
        logging.error(f"保存分类选择失败: {e}")
        return jsonify({'error': '保存失败'}), 500

@app.route('/form_generation')
def form_generation_page():
    """表单生成页面"""
    extraction_results = get_session_data('extraction_results')
    if not extraction_results:
        flash('请先完成分类选择', 'error')
        return redirect(url_for('category_selection_page'))
    
    # 检查是否有分类选择
    has_category_selection = any('selected_category' in result for result in extraction_results)
    if not has_category_selection:
        flash('请先选择物料分类', 'error')
        return redirect(url_for('category_selection_page'))
    
    return render_template('form_generation.html', results=extraction_results)

@app.route('/generate_forms', methods=['POST'])
def generate_forms():
    """生成动态表单"""
    try:
        extraction_results = get_session_data('extraction_results', [])
        
        # 为每个物料生成表单
        form_data = []
        
        for result in extraction_results:
            if 'selected_category' not in result:
                continue
            
            category = result['selected_category']
            
            # 根据分类生成表单字段（这里是示例逻辑）
            form_fields = generate_form_fields_for_category(category)
            
            # 自动填充已提取的参数
            auto_filled_form = auto_fill_form(form_fields, result)
            
            form_data.append({
                'row_index': result['row_index'],
                'category': category,
                'form_fields': auto_filled_form,
                'input_data': result['input_data']
            })
        
        store_session_data('form_data', form_data)
        
        return jsonify({
            'success': True,
            'forms': form_data
        })
        
    except Exception as e:
        logging.error(f"表单生成失败: {e}")
        return jsonify({'error': '表单生成失败'}), 500

def generate_form_fields_for_category(category: str) -> List[Dict]:
    """根据分类生成表单字段"""
    # 示例表单字段定义
    base_fields = [
        {'name': 'product_name', 'label': '产品名称', 'type': 'text', 'required': True},
        {'name': 'specification', 'label': '规格型号', 'type': 'text', 'required': True},
        {'name': 'manufacturer', 'label': '生产厂家', 'type': 'text', 'required': True},
        {'name': 'brand', 'label': '品牌', 'type': 'text', 'required': False},
        {'name': 'model', 'label': '型号', 'type': 'text', 'required': False},
        {'name': 'unit', 'label': '单位', 'type': 'select', 'required': True, 
         'options': ['个', '台', '套', '件', 'kg', 'g', 'L', 'ml']},
        {'name': 'description', 'label': '描述', 'type': 'textarea', 'required': False}
    ]
    
    # 根据分类添加特定字段
    if '药品' in category:
        base_fields.extend([
            {'name': 'dosage_form', 'label': '剂型', 'type': 'select', 'required': True,
             'options': ['片剂', '胶囊', '注射剂', '口服液', '软膏']},
            {'name': 'approval_number', 'label': '批准文号', 'type': 'text', 'required': True}
        ])
    elif '医疗器械' in category:
        base_fields.extend([
            {'name': 'device_class', 'label': '器械分类', 'type': 'select', 'required': True,
             'options': ['I类', 'II类', 'III类']},
            {'name': 'registration_number', 'label': '注册证号', 'type': 'text', 'required': True}
        ])
    elif '工业' in category:
        base_fields.extend([
            {'name': 'material', 'label': '材质', 'type': 'text', 'required': False},
            {'name': 'technical_params', 'label': '技术参数', 'type': 'textarea', 'required': False}
        ])
    
    return base_fields

def auto_fill_form(form_fields: List[Dict], extraction_result: Dict) -> List[Dict]:
    """自动填充表单"""
    filled_fields = []
    
    input_data = extraction_result.get('input_data', {})
    extracted_params = extraction_result.get('extracted_params', {})
    
    for field in form_fields:
        field_copy = field.copy()
        field_copy['value'] = ''
        
        # 尝试从输入数据中匹配
        if field['name'] == 'product_name' and 'asset_name' in input_data:
            field_copy['value'] = input_data['asset_name']
        elif field['name'] == 'specification' and 'spec_model' in input_data:
            field_copy['value'] = input_data['spec_model']
        elif field['name'] == 'manufacturer' and 'manufacturer_name' in input_data:
            field_copy['value'] = input_data['manufacturer_name']
        
        # 尝试从提取的参数中匹配
        elif field['name'] == 'brand' and 'brand' in extracted_params:
            if extracted_params['brand']:
                field_copy['value'] = extracted_params['brand'][0]
        elif field['name'] == 'model' and 'model' in extracted_params:
            if extracted_params['model']:
                field_copy['value'] = extracted_params['model'][0]
        
        filled_fields.append(field_copy)
    
    return filled_fields

@app.route('/matching')
def matching_page():
    """匹配结果页面"""
    form_data = get_session_data('form_data')
    if not form_data:
        flash('请先完成表单生成', 'error')
        return redirect(url_for('form_generation_page'))
    
    return render_template('matching.html', form_data=form_data)

@app.route('/perform_matching', methods=['POST'])
def perform_matching():
    """执行匹配"""
    try:
        updated_forms = request.json.get('forms', [])
        
        # 使用工作流服务进行匹配
        if not workflow_service:
            return jsonify({'error': '工作流服务未初始化'}), 500
        
        matching_results = []
        
        for form in updated_forms:
            # 构建匹配用的数据
            form_values = {field['name']: field['value'] for field in form['form_fields']}
            
            # 执行匹配
            result = workflow_service.process_single_item(form_values)
            
            matching_results.append({
                'row_index': form['row_index'],
                'form_data': form_values,
                'matches': result['matches'],
                'processing_info': result['processing_info']
            })
        
        store_session_data('matching_results', matching_results)
        
        return jsonify({
            'success': True,
            'results': matching_results
        })
        
    except Exception as e:
        logging.error(f"匹配执行失败: {e}")
        return jsonify({'error': f'匹配失败: {str(e)}'}), 500

@app.route('/decision')
def decision_page():
    """决策确认页面"""
    matching_results = get_session_data('matching_results')
    if not matching_results:
        flash('请先完成匹配', 'error')
        return redirect(url_for('matching_page'))
    
    return render_template('decision.html', results=matching_results)

@app.route('/save_decisions', methods=['POST'])
def save_decisions():
    """保存用户决策"""
    try:
        decisions = request.json.get('decisions', {})
        
        matching_results = get_session_data('matching_results', [])
        
        # 应用用户决策
        final_results = []
        for result in matching_results:
            row_index = str(result['row_index'])
            if row_index in decisions:
                decision = decisions[row_index]
                result['user_decision'] = decision
                result['decision_timestamp'] = datetime.now().isoformat()
                
                final_results.append({
                    'row_index': result['row_index'],
                    'form_data': result['form_data'],
                    'best_match': result['matches'][0] if result['matches'] else None,
                    'match_count': len(result['matches']),
                    'user_decision': decision,
                    'decision_timestamp': result['decision_timestamp']
                })
        
        store_session_data('final_results', final_results)
        
        # 可以在这里集成审批工作流
        # workflow_integration.submit_for_approval(final_results)
        
        return jsonify({
            'success': True,
            'message': f'已保存 {len(final_results)} 个决策',
            'results': final_results
        })
        
    except Exception as e:
        logging.error(f"保存决策失败: {e}")
        return jsonify({'error': '保存决策失败'}), 500

@app.route('/results')
def results_page():
    """最终结果页面"""
    final_results = get_session_data('final_results')
    if not final_results:
        flash('没有找到处理结果', 'info')
        return redirect(url_for('index'))
    
    return render_template('results.html', results=final_results)

@app.route('/export_results')
def export_results():
    """导出结果"""
    try:
        final_results = get_session_data('final_results')
        if not final_results:
            return jsonify({'error': '没有结果可导出'}), 400
        
        # 转换为DataFrame并保存
        import pandas as pd
        
        export_data = []
        for result in final_results:
            row = result['form_data'].copy()
            row['user_decision'] = result['user_decision']
            row['match_count'] = result['match_count']
            row['decision_timestamp'] = result['decision_timestamp']
            
            if result['best_match']:
                row['best_match_similarity'] = result['best_match'].get('similarity', 0)
                row['best_match_id'] = result['best_match'].get('id')
            
            export_data.append(row)
        
        df = pd.DataFrame(export_data)
        
        # 保存到文件
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'material_processing_results_{timestamp}.xlsx'
        filepath = os.path.join('exports', filename)
        
        os.makedirs('exports', exist_ok=True)
        df.to_excel(filepath, index=False)
        
        return jsonify({
            'success': True,
            'filename': filename,
            'filepath': filepath
        })
        
    except Exception as e:
        logging.error(f"导出结果失败: {e}")
        return jsonify({'error': '导出失败'}), 500

@app.route('/batch_management')
def batch_management_page():
    """批量处理管理页面"""
    return render_template('batch_management.html')

@app.route('/api/status')
def api_status():
    """API状态检查"""
    return jsonify({
        'status': 'running',
        'workflow_service_initialized': workflow_service is not None,
        'advanced_preprocessor_available': ADVANCED_PREPROCESSOR_AVAILABLE,
        'enhanced_config_available': ENHANCED_CONFIG_AVAILABLE,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/debug/session')
def debug_session():
    """调试会话数据"""
    session_id = get_session_id()
    current_session_data = session_data.get(session_id, {})
    
    return jsonify({
        'session_id': session_id,
        'session_keys': list(current_session_data.keys()),
        'has_uploaded_file': 'uploaded_file' in current_session_data,
        'has_extraction_results': 'extraction_results' in current_session_data,
        'extraction_results_count': len(current_session_data.get('extraction_results', [])),
        'all_sessions': list(session_data.keys()),
        'session_data_summary': {k: type(v).__name__ for k, v in current_session_data.items()}
    })

# URL重定向处理（处理常见的错误URL）
@app.route('/categorize')
def categorize_redirect():
    """重定向到正确的分类选择页面"""
    return redirect(url_for('category_selection_page'))

@app.route('/category')
def category_redirect():
    """重定向到正确的分类选择页面"""
    return redirect(url_for('category_selection_page'))

# 错误处理
@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', 
                         error_code=404, 
                         error_message='页面未找到'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', 
                         error_code=500, 
                         error_message='服务器内部错误'), 500

if __name__ == '__main__':
    # 初始化服务
    if init_service():
        app.run(host='0.0.0.0', port=5001, debug=True)
    else:
        print("服务初始化失败，请检查配置")
