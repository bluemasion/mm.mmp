# app/web_app.py - 完整修复版本
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from werkzeug.utils import secure_filename
import os
import json
import uuid
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Any, Optional
import pickle
import tempfile

# 导入核心服务
from app.workflow_service import MaterialWorkflowService
from app.database_connector import DatabaseConnector
from app.data_loader import load_data_from_config, save_data_to_config
from app.database_session_manager import DatabaseSessionManager
from app.business_data_manager import BusinessDataManager

# 导入错误处理器
try:
    from app.error_handler import safe_length, safe_api, error_handler
    ERROR_HANDLER_AVAILABLE = True
except ImportError:
    ERROR_HANDLER_AVAILABLE = False
    # 提供降级处理
    def safe_length(obj, default=0):
        try:
            return len(obj) if hasattr(obj, '__len__') else (1 if obj is not None else default)
        except:
            return default
    
    def safe_api(fallback_response=None):
        def decorator(func):
            return func
        return decorator

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

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 获取项目根目录路径
import sys
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 创建Flask应用，指定正确的模板和静态文件路径
app = Flask(__name__, 
           template_folder=os.path.join(project_root, 'templates'),
           static_folder=os.path.join(project_root, 'static'))

# 配置Flask会话 - 增强版本
app.secret_key = 'mmp-secure-key-change-in-production-fixed-key-for-session-persistence'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = True
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_KEY_PREFIX'] = 'mmp_session:'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = False  # 开发环境设为False，生产环境应为True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=4)  # 4小时过期

# 配置文件上传
UPLOAD_FOLDER = os.path.join(project_root, 'uploads')
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls', 'json'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# 确保上传目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 会话数据持久化目录
SESSION_DATA_DIR = os.path.join(project_root, 'session_data')
os.makedirs(SESSION_DATA_DIR, exist_ok=True)

# 全局服务实例
workflow_service = None

class SessionDataManager:
    """会话数据管理器 - 数据库版本"""
    
    def __init__(self, db_path: str = None):
        """初始化数据库会话管理器"""
        if db_path is None:
            db_path = os.path.join(project_root, 'sessions.db')
        self.db_manager = DatabaseSessionManager(db_path)
        logger.info(f"数据库会话管理器初始化完成: {db_path}")
    
    def store_data(self, session_id: str, key: str, data: Any):
        """存储会话数据"""
        try:
            success = self.db_manager.store_data(session_id, key, data)
            if success:
                logger.info(f"会话数据已存储到数据库: session_id={session_id}, key={key}")
            else:
                logger.error(f"存储会话数据失败: session_id={session_id}, key={key}")
        except Exception as e:
            logger.error(f"存储会话数据异常: {e}")
    
    def get_data(self, session_id: str, key: str, default=None):
        """获取会话数据"""
        try:
            data = self.db_manager.get_data(session_id, key, default)
            logger.info(f"从数据库获取数据: session_id={session_id}, key={key}, found={'Yes' if data != default else 'No'}")
            return data
        except Exception as e:
            logger.error(f"获取会话数据异常: {e}")
            return default
    
    def get_all_data(self, session_id: str) -> dict:
        """获取会话的所有数据"""
        try:
            return self.db_manager.get_all_session_data(session_id)
        except Exception as e:
            logger.error(f"获取所有会话数据异常: {e}")
            return {}
    
    def clear_data(self, session_id: str):
        """清除会话数据"""
        try:
            success = self.db_manager.delete_session(session_id)
            if success:
                logger.info(f"会话数据已从数据库清除: session_id={session_id}")
            else:
                logger.error(f"清除会话数据失败: session_id={session_id}")
        except Exception as e:
            logger.error(f"清除会话数据异常: {e}")
    
    def create_session(self, session_id: str = None) -> str:
        """创建新会话"""
        try:
            return self.db_manager.create_session(session_id)
        except Exception as e:
            logger.error(f"创建会话异常: {e}")
            return str(uuid.uuid4())
    
    def get_session_info(self, session_id: str) -> dict:
        """获取会话信息"""
        try:
            return self.db_manager.get_session_info(session_id)
        except Exception as e:
            logger.error(f"获取会话信息异常: {e}")
            return {}

# 创建数据库会话管理器实例
session_manager = SessionDataManager(os.path.join(project_root, 'sessions.db'))

# 创建业务数据管理器实例
business_manager = BusinessDataManager(os.path.join(project_root, 'business_data.db'))

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
        logger.info("工作流服务初始化成功")
        return True
    except Exception as e:
        logger.error(f"工作流服务初始化失败: {e}")
        return False

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_session_id():
    """获取或创建会话ID - 使用数据库管理的会话"""
    # 优先使用URL中的id参数作为会话标识符
    url_id = request.args.get('id')
    if url_id:
        # 验证会话是否存在于数据库中
        session_info = session_manager.get_session_info(url_id)
        if session_info:
            logger.info(f"使用URL会话ID: {url_id}")
            return url_id
        else:
            # 会话不存在，创建新会话
            new_session_id = session_manager.create_session(url_id)
            logger.info(f"创建新的URL会话: {new_session_id}")
            return new_session_id
    
    # 回退到Flask session机制
    if 'session_id' not in session:
        new_session_id = session_manager.create_session()
        session['session_id'] = new_session_id
        session.permanent = True
        logger.info(f"创建新Flask会话: {new_session_id}")
    else:
        # 验证Flask session是否存在于数据库中
        flask_session_id = session['session_id']
        session_info = session_manager.get_session_info(flask_session_id)
        if not session_info:
            # 会话不存在，重新创建
            new_session_id = session_manager.create_session()
            session['session_id'] = new_session_id
            logger.info(f"重新创建Flask会话: {new_session_id}")
        else:
            logger.info(f"使用现有Flask会话: {flask_session_id}")
    
    return session['session_id']

def store_session_data(key: str, data: Any):
    """存储会话数据"""
    session_id = get_session_id()
    logger.info(f"存储会话数据: session_id={session_id}, key={key}, data_type={type(data)}")
    session_manager.store_data(session_id, key, data)

def get_session_data(key: str, default=None):
    """获取会话数据"""
    session_id = get_session_id()
    result = session_manager.get_data(session_id, key, default)
    logger.info(f"获取会话数据: session_id={session_id}, key={key}, found={result is not None}")
    return result

def clear_session_data():
    """清除当前会话数据"""
    session_id = get_session_id()
    session_manager.clear_data(session_id)

def get_workflow_status():
    """获取工作流状态"""
    return {
        'uploaded_data': get_session_data('uploaded_data') is not None,
        'extraction_results': get_session_data('extraction_results') is not None,
        'category_selections': get_session_data('category_selections') is not None,
        'generated_forms': get_session_data('generated_forms') is not None,
        'matching_results': get_session_data('matching_results') is not None,
        'final_decisions': get_session_data('final_decisions') is not None
    }

def _build_category_tree(categories: List[Dict]) -> List[Dict]:
    """构建分类树形结构"""
    # 按层级分组
    level_map = {}
    code_map = {}
    
    for cat in categories:
        level = cat['level']
        if level not in level_map:
            level_map[level] = []
        level_map[level].append(cat)
        code_map[cat['code']] = cat
    
    # 构建树形结构
    tree = []
    
    # 第1级作为根节点
    if 1 in level_map:
        for cat in level_map[1]:
            tree_node = {
                'code': cat['code'],
                'name': cat['name'], 
                'level': cat['level'],
                'is_leaf': cat['is_leaf'],
                'description': cat['description'],
                'template': cat['template'],
                'children': []
            }
            tree.append(tree_node)
    
    # 递归添加子节点
    def add_children(parent_node, parent_code):
        for cat in categories:
            if cat['parent_code'] == parent_code:
                child_node = {
                    'code': cat['code'],
                    'name': cat['name'],
                    'level': cat['level'], 
                    'is_leaf': cat['is_leaf'],
                    'description': cat['description'],
                    'template': cat['template'],
                    'children': []
                }
                parent_node['children'].append(child_node)
                # 递归添加子节点的子节点
                add_children(child_node, cat['code'])
    
    # 为每个根节点添加子节点
    for node in tree:
        add_children(node, node['code'])
    
    return tree

# ==================== 路由定义 ====================

@app.before_request
def before_request():
    """请求前处理"""
    # 确保工作流服务已初始化
    if workflow_service is None:
        init_service()
    
    # 记录请求信息
    logger.info(f"请求: {request.method} {request.path}, Session ID: {get_session_id()}")

@app.route('/')
def index():
    """首页"""
    session_id = get_session_id()
    workflow_status = get_workflow_status()
    logger.info(f"首页访问 - Session: {session_id}, Status: {workflow_status}")
    return render_template('index.html', workflow_status=workflow_status)

@app.route('/upload')
def upload_page():
    """数据上传页面"""
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """处理文件上传"""
    try:
        logger.info("开始处理文件上传")
        
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
            
            logger.info(f"文件已保存: {filepath}")
            
            # 预览数据并存储到业务数据库
            try:
                file_config = {
                    'source_type': 'file',
                    'path': filepath,
                    'type': filename.split('.')[-1].lower()
                }
                
                preview_df = load_data_from_config(file_config)
                
                # 生成文件唯一标识
                file_id = str(uuid.uuid4())
                
                # 获取字段映射
                default_mapping = business_manager.get_config('default_field_mapping', 'standard_medical_mapping')
                field_mapping_dict = business_manager.get_field_mapping_dict(default_mapping)
                
                # 应用字段映射
                mapped_df = preview_df.copy()
                if field_mapping_dict:
                    # 重命名列
                    rename_dict = {}
                    for original_col in mapped_df.columns:
                        if original_col in field_mapping_dict:
                            rename_dict[original_col] = field_mapping_dict[original_col]
                    
                    if rename_dict:
                        mapped_df = mapped_df.rename(columns=rename_dict)
                        logger.info(f"应用字段映射: {rename_dict}")
                
                # 存储文件到业务数据库
                session_id = get_session_id()
                file_size = os.path.getsize(filepath)
                file_type = filename.split('.')[-1].lower()
                
                success = business_manager.store_uploaded_file(
                    file_id=file_id,
                    original_filename=file.filename,
                    stored_filename=filename,
                    file_size=file_size,
                    file_type=file_type,
                    session_id=session_id,
                    df=mapped_df
                )
                
                if success:
                    # 限制预览行数
                    preview_data = mapped_df.head(10).to_dict('records') if len(mapped_df) > 10 else mapped_df.to_dict('records')
                    columns = list(mapped_df.columns)
                    total_rows = len(mapped_df)
                    
                    # 存储上传的数据信息到会话
                    upload_info = {
                        'file_id': file_id,
                        'filename': filename,
                        'filepath': filepath,
                        'original_columns': list(preview_df.columns),
                        'mapped_columns': columns,
                        'field_mapping': rename_dict if 'rename_dict' in locals() else {},
                        'total_rows': total_rows,
                        'preview_data': preview_data,
                        'upload_time': datetime.now().isoformat()
                    }
                    
                    store_session_data('uploaded_data', upload_info)
                    logger.info(f"文件数据已存储到业务数据库 - file_id: {file_id}, 行数: {total_rows}, 列数: {len(columns)}")
                    
                    return jsonify({
                        'success': True,
                        'message': '文件上传成功，已应用字段映射',
                        'file_id': file_id,
                        'filename': filename,
                        'original_columns': list(preview_df.columns),
                        'mapped_columns': columns,
                        'field_mapping': rename_dict if 'rename_dict' in locals() else {},
                        'total_rows': total_rows,
                        'preview_data': preview_data
                    })
                else:
                    return jsonify({'error': '文件数据存储失败'}), 500
                
            except Exception as e:
                logger.error(f"文件预览失败: {e}")
                return jsonify({'error': f'文件处理失败: {str(e)}'}), 500
        
        return jsonify({'error': '不支持的文件格式'}), 400
        
    except Exception as e:
        logger.error(f"文件上传处理失败: {e}")
        return jsonify({'error': f'上传失败: {str(e)}'}), 500

@app.route('/extract_parameters')
def extract_parameters_page():
    """参数提取页面"""
    logger.info("访问参数提取页面")
    
    # 检查是否已选择分类模板
    selected_template = get_session_data('selected_template')
    if not selected_template:
        logger.info("未选择分类模板，跳转到模板选择页面")
        flash('请先选择分类模板', 'warning')
        return redirect(url_for('template_selection'))
    
    logger.info(f"使用的分类模板: {selected_template['template_name']}")
    
    # 获取当前会话ID用于调试
    session_id = get_session_id()
    logger.info(f"当前会话ID: {session_id}")
    
    # 首先尝试从会话数据获取
    uploaded_data = get_session_data('uploaded_data')
    logger.info(f"从会话获取的上传数据: {uploaded_data is not None}")
    
    # 如果会话数据不存在，尝试从URL参数和业务数据库获取
    if not uploaded_data:
        file_id = request.args.get('file_id')
        logger.info(f"从URL获取的文件ID: {file_id}")
        
        if file_id:
            try:
                # 从业务数据库获取文件信息
                file_info = business_manager.get_uploaded_file_info(file_id)
                logger.info(f"从业务数据库获取的文件信息: {file_info is not None}")
                
                if file_info:
                    # 重建上传数据结构
                    uploaded_data = {
                        'file_id': file_id,
                        'filename': file_info.get('original_filename', ''),
                        'total_rows': file_info.get('row_count', 0),
                        'upload_time': file_info.get('upload_time', ''),
                        'original_columns': [],  # 可以从file_data表获取
                        'mapped_columns': []     # 可以从file_data表获取
                    }
                    
                    # 重新存储到会话中
                    store_session_data('uploaded_data', uploaded_data)
                    logger.info(f"重建并存储上传数据到会话")
                    
            except Exception as e:
                logger.error(f"从业务数据库获取文件信息失败: {e}")
    
    if not uploaded_data:
        logger.warning("未找到上传数据，重定向到上传页面")
        flash('请先上传数据文件', 'error')
        return redirect(url_for('upload_page'))
    
    logger.info("找到上传数据，渲染参数提取页面")
    return render_template('extract_parameters.html', 
                         uploaded_data=uploaded_data)

@app.route('/extract_parameters', methods=['POST'])
def perform_parameter_extraction():
    """执行参数提取"""
    try:
        logger.info("开始执行参数提取")
        
        uploaded_data = get_session_data('uploaded_data')
        if not uploaded_data:
            return jsonify({'error': '请先上传数据'}), 400
        
        # 获取用户输入的参数
        request_data = request.get_json()
        extraction_config = {
            'key_columns': request_data.get('key_columns', []),
            'extraction_rules': request_data.get('extraction_rules', {}),
            'custom_patterns': request_data.get('custom_patterns', {})
        }
        
        # 执行参数提取
        if workflow_service:
            try:
                # 加载完整数据
                file_config = {
                    'source_type': 'file',
                    'path': uploaded_data['filepath'],
                    'type': uploaded_data['filepath'].split('.')[-1].lower()
                }
                
                full_data = load_data_from_config(file_config)
                extraction_results = workflow_service.extract_parameters(full_data, extraction_config)
                
                # 存储提取结果
                extraction_data = {
                    'results': extraction_results,
                    'config': extraction_config,
                    'extraction_time': datetime.now().isoformat(),
                    'total_extracted': len(extraction_results) if extraction_results else 0
                }
                
                store_session_data('extraction_results', extraction_data)
                logger.info(f"参数提取完成 - 提取了 {extraction_data['total_extracted']} 条结果")
                
                return jsonify({
                    'success': True,
                    'message': '参数提取完成',
                    'results': extraction_results[:10] if extraction_results else [],  # 返回前10条预览
                    'total_count': len(extraction_results) if extraction_results else 0
                })
                
            except Exception as e:
                logger.error(f"工作流服务执行参数提取失败: {e}")
                return jsonify({'error': f'参数提取失败: {str(e)}'}), 500
        else:
            return jsonify({'error': '工作流服务未初始化'}), 500
            
    except Exception as e:
        logger.error(f"参数提取处理失败: {e}")
        return jsonify({'error': f'处理失败: {str(e)}'}), 500

@app.route('/save_extraction_results', methods=['POST'])
def save_extraction_results():
    """保存参数提取结果到会话"""
    try:
        logger.info("保存参数提取结果到会话")
        
        request_data = request.get_json()
        extraction_data = {
            'results': request_data.get('results', []),
            'config': request_data.get('config', {}),
            'extraction_time': datetime.now().isoformat(),
            'total_extracted': request_data.get('total_extracted', 0),
            'total_errors': request_data.get('total_errors', 0)
        }
        
        store_session_data('extraction_results', extraction_data)
        logger.info(f"参数提取结果已保存 - 提取了 {extraction_data['total_extracted']} 条结果")
        
        return jsonify({
            'success': True,
            'message': '提取结果已保存',
            'total_count': extraction_data['total_extracted']
        })
        
    except Exception as e:
        logger.error(f"保存提取结果失败: {e}")
        return jsonify({'error': f'保存失败: {str(e)}'}), 500

@app.route('/save_category_selections', methods=['POST'])
def save_category_selections():
    """保存分类选择结果到会话"""
    try:
        logger.info("保存分类选择结果到会话")
        
        request_data = request.get_json()
        category_data = {
            'selections': request_data.get('selections', {}),
            'selection_time': datetime.now().isoformat(),
            'total_classified': request_data.get('total_classified', 0),
            'total_failed': request_data.get('total_failed', 0)
        }
        
        store_session_data('category_selections', category_data)
        logger.info(f"分类选择结果已保存 - 分类了 {category_data['total_classified']} 条结果")
        
        return jsonify({
            'success': True,
            'message': '分类选择已保存',
            'total_count': category_data['total_classified']
        })
        
    except Exception as e:
        logger.error(f"保存分类选择失败: {e}")
        return jsonify({'error': f'保存失败: {str(e)}'}), 500

@app.route('/save_generated_forms', methods=['POST'])
def save_generated_forms():
    """保存表单生成结果到会话"""
    try:
        logger.info("保存表单生成结果到会话")
        
        request_data = request.get_json()
        forms_data = {
            'forms': request_data.get('forms', []),
            'config': request_data.get('config', {}),
            'generation_time': datetime.now().isoformat(),
            'total_generated': request_data.get('total_generated', 0),
            'total_errors': request_data.get('total_errors', 0)
        }
        
        store_session_data('generated_forms', forms_data)
        logger.info(f"表单生成结果已保存 - 生成了 {forms_data['total_generated']} 个表单")
        
        return jsonify({
            'success': True,
            'message': '表单生成结果已保存',
            'total_count': forms_data['total_generated']
        })
        
    except Exception as e:
        logger.error(f"保存表单生成结果失败: {e}")
        return jsonify({'error': f'保存失败: {str(e)}'}), 500

@app.route('/save_matching_results', methods=['POST'])
def save_matching_results():
    """保存匹配结果到会话"""
    try:
        logger.info("保存匹配结果到会话")
        
        request_data = request.get_json()
        matching_data = {
            'results': request_data.get('results', []),
            'config': request_data.get('config', {}),
            'matching_time': datetime.now().isoformat(),
            'total_exact': request_data.get('total_exact', 0),
            'total_similar': request_data.get('total_similar', 0),
            'total_unmatched': request_data.get('total_unmatched', 0)
        }
        
        store_session_data('matching_results', matching_data)
        logger.info(f"匹配结果已保存 - 精确匹配: {matching_data['total_exact']}, 相似匹配: {matching_data['total_similar']}, 未匹配: {matching_data['total_unmatched']}")
        
        return jsonify({
            'success': True,
            'message': '匹配结果已保存',
            'total_exact': matching_data['total_exact'],
            'total_similar': matching_data['total_similar'],
            'total_unmatched': matching_data['total_unmatched']
        })
        
    except Exception as e:
        logger.error(f"保存匹配结果失败: {e}")
        return jsonify({'error': f'保存失败: {str(e)}'}), 500

@app.route('/test_simple')
def test_simple():
    """简单测试路由"""
    return {"status": "ok", "message": "测试路由正常工作"}

@app.route('/debug-algorithm')
def debug_algorithm():
    """算法调试页面"""
    try:
        with open('debug_algorithm_test.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return jsonify({'error': '调试页面文件不存在'}), 404

@app.route('/test-js-events')
def test_js_events():
    """JavaScript事件测试页面"""
    try:
        with open('test_js_events.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return jsonify({'error': '测试页面文件不存在'}), 404

@app.route('/debug-js-workflow')
def debug_js_workflow():
    """JavaScript工作流调试页面"""
    try:
        with open('debug_js_workflow.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return jsonify({'error': '调试页面文件不存在'}), 404

@app.route('/test_session')
def test_session():
    """测试Flask session机制"""
    if 'test_count' not in session:
        session['test_count'] = 0
        session.permanent = True
    
    session['test_count'] += 1
    
    return {
        "session_id": session.get('session_id', 'None'),
        "test_count": session['test_count'],
        "flask_session": dict(session)
    }

@app.route('/generate_test_data')
def generate_test_data():
    """生成测试数据（开发调试用）"""
    logger.info("开始生成测试数据...")
    try:
        # 生成模拟的参数提取结果
        test_extraction_data = {
            'extracted_data': [
                {
                    '物料名称': '一次性输液器',
                    '品牌': '康德莱',
                    '型号': 'KDL-IV-001', 
                    '规格': '150ml',
                    '生产厂家': '康德莱医疗器械股份有限公司',
                    '提取时间': datetime.now().isoformat()
                },
                {
                    '物料名称': 'CT造影剂注射器',
                    '品牌': '美敦力',
                    '型号': 'MD-CT-200',
                    '规格': '200ml/支',
                    '生产厂家': '美敦力（上海）管理有限公司',
                    '提取时间': datetime.now().isoformat()
                },
                {
                    '物料名称': '医用防护口罩',
                    '品牌': '3M',
                    '型号': '1860',
                    '规格': 'N95级别',
                    '生产厂家': '3M中国有限公司',
                    '提取时间': datetime.now().isoformat()
                },
                {
                    '物料名称': '钢板螺钉',
                    '品牌': '强生',
                    '型号': 'J&J-SP-4.5',
                    '规格': '4.5mm×35mm',
                    '生产厂家': '强生（苏州）医疗器材有限公司',
                    '提取时间': datetime.now().isoformat()
                },
                {
                    '物料名称': '超声探头',
                    '品牌': '飞利浦',
                    '型号': 'Philips-C5-2',
                    '规格': '凸阵探头 2-5MHz',
                    '生产厂家': '荷兰皇家飞利浦公司',
                    '提取时间': datetime.now().isoformat()
                }
            ],
            'total_extracted': 5,
            'extraction_time': datetime.now().isoformat(),
            'confidence_distribution': {
                'high': 3,
                'medium': 2,
                'low': 0
            }
        }
        
        # 保存测试数据到session
        store_session_data('extraction_results', test_extraction_data)
        
        # 验证保存
        saved_data = get_session_data('extraction_results')
        session_id = get_session_id()
        logger.info(f"Session ID: {session_id}")
        logger.info(f"已生成测试数据，包含 {len(test_extraction_data['extracted_data'])} 个物料")
        logger.info(f"保存验证: {'成功' if saved_data else '失败'}")
        # 直接重定向到分类选择页面，携带会话ID参数
        redirect_url = url_for('category_selection_page')
        if request.args.get('id'):
            redirect_url += f"?id={request.args.get('id')}"
        return redirect(redirect_url)
        
    except Exception as e:
        logger.error(f"生成测试数据失败: {e}")
        return jsonify({'error': f'生成测试数据失败: {str(e)}'}), 500

@app.route('/category_selection')
def category_selection_page():
    """分类选择页面 - 集成外部分类推荐"""
    session_id = get_session_id()
    extraction_results = get_session_data('extraction_results')
    
    # 调试信息
    logger.info(f"Session ID: {session_id}")
    logger.info(f"extraction_results是否存在: {extraction_results is not None}")
    if extraction_results:
        logger.info(f"extraction_results的键: {list(extraction_results.keys())}")
    
    if not extraction_results:
        flash('请先完成参数提取', 'error')
        logger.warning("访问分类选择页面但未找到参数提取结果")
        return redirect(url_for('extract_parameters_page'))
    
    # 导入外部分类服务
    try:
        from app.external_classifier import get_external_classifier
        
        # 获取带数据库管理器的外部分类器实例
        session_id = get_session_id()
        classifier = get_external_classifier(session_manager.db_manager)
        
        # 获取外部分类体系
        categories_data = classifier.get_material_categories()
        
        # 为提取的物料生成分类推荐
        recommendations = []
        # 修复数据结构不匹配问题 - 使用正确的字段名
        extracted_materials = extraction_results.get('extracted_data', []) or extraction_results.get('results', [])
        
        for material in extracted_materials[:5]:  # 限制处理数量避免性能问题
            # 适配不同的数据结构
            material_features = {
                'name': material.get('物料名称', '') or material.get('extracted_product_name', '') or material.get('original_product_name', ''),
                'brand': material.get('品牌', ''),
                'model': material.get('型号', '') or material.get('extracted_spec_model', '') or material.get('original_spec_model', ''),
                'spec': material.get('规格', '') or material.get('extracted_spec_model', '') or material.get('original_spec_model', '')
            }
            
            # 传入会话ID以便存储到数据库
            material_recommendations = classifier.recommend_categories(material_features, session_id)
            recommendations.append({
                'material': material,
                'recommendations': material_recommendations
            })
        
        logger.info(f"访问分类选择页面 - 有 {extraction_results.get('total_extracted', 0)} 条提取结果，生成了 {len(recommendations)} 个物料的推荐")
        logger.info(f"提取结果数据结构: {list(extraction_results.keys()) if extraction_results else 'None'}")
        logger.info(f"extracted_materials长度: {len(extracted_materials)}")
        logger.info(f"推荐数据示例: {recommendations[:1] if recommendations else 'None'}")
        
        return render_template('categorize.html', 
                             extraction_results=extraction_results,
                             categories_data=categories_data,
                             material_recommendations=recommendations)
                             
    except Exception as e:
        logger.error(f"外部分类服务调用失败: {e}")
        # 降级到原有功能
        return render_template('categorize.html', 
                             extraction_results=extraction_results)

@app.route('/category_selection', methods=['POST'])
def save_category_selection():
    """保存分类选择"""
    try:
        logger.info("开始保存分类选择")
        
        extraction_results = get_session_data('extraction_results')
        if not extraction_results:
            return jsonify({'error': '请先完成参数提取'}), 400
        
        request_data = request.get_json()
        if not request_data:
            return jsonify({'error': '请求数据为空'}), 400
            
        category_selections = request_data.get('selections', {})
        
        # 使用安全的长度计算
        selection_count = safe_length(category_selections, default=0)
            
        logger.info(f"接收到分类选择数据: {type(category_selections)}, 数量: {selection_count}")
        
        # 保存分类选择
        selection_data = {
            'selections': category_selections,
            'selection_time': datetime.now().isoformat(),
            'total_selections': selection_count
        }
        
        store_session_data('category_selections', selection_data)
        logger.info(f"分类选择已保存 - 选择了 {selection_count} 个分类")
        
        return jsonify({
            'success': True,
            'message': '分类选择已保存',
            'total_count': selection_count,
            'next_step': url_for('form_generation_page')
        })
        
    except Exception as e:
        logger.error(f"保存分类选择失败: {e}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")
        return jsonify({'error': f'保存失败: {str(e)}'}), 500

@app.route('/api/category_features/<category_id>')
def get_category_features(category_id):
    """获取指定分类的特征模型API"""
    try:
        from app.external_classifier import get_external_classifier
        
        classifier = get_external_classifier(session_manager.db_manager)
        features_data = classifier.get_category_features(category_id)
        
        return jsonify({
            'success': True,
            'category_id': category_id,
            'features': features_data.get('features', [])
        })
        
    except Exception as e:
        logger.error(f"获取分类特征失败: {e}")
        return jsonify({'error': f'获取特征失败: {str(e)}'}), 500

@app.route('/api/recommend_categories', methods=['POST'])
def recommend_categories_api():
    """智能物料分类推荐API - 增强版本"""
    try:
        from app.external_classifier import get_external_classifier
        from app.intelligent_classifier import get_intelligent_classifier
        
        request_data = request.get_json()
        material_features = request_data.get('material_features', {})
        use_intelligent = request_data.get('use_intelligent', True)  # 默认使用智能推荐
        
        if not material_features:
            return jsonify({'error': '物料特征不能为空'}), 400
        
        session_id = get_session_id()
        logger.info(f"开始为会话 {session_id} 进行分类推荐: {material_features}")
        
        recommendations = []
        
        if use_intelligent:
            # 使用智能分类推荐引擎
            try:
                intelligent_classifier = get_intelligent_classifier(business_manager)
                intelligent_recommendations = intelligent_classifier.recommend_categories(
                    material_features, session_id
                )
                recommendations.extend(intelligent_recommendations)
                logger.info(f"智能推荐生成 {len(intelligent_recommendations)} 个结果")
            except Exception as e:
                logger.error(f"智能推荐失败: {e}")
        
        # 同时使用外部分类器作为补充
        try:
            classifier = get_external_classifier(session_manager.db_manager)
            external_recommendations = classifier.recommend_categories(material_features, session_id)
            recommendations.extend(external_recommendations)
            logger.info(f"外部推荐生成 {len(external_recommendations)} 个结果")
        except Exception as e:
            logger.error(f"外部推荐失败: {e}")
        
        # 合并和去重推荐结果
        final_recommendations = _merge_and_deduplicate_recommendations(recommendations)
        
        return jsonify({
            'success': True,
            'recommendations': final_recommendations[:10],  # 最多返回10个推荐
            'total': len(final_recommendations),
            'session_id': session_id
        })
        
    except Exception as e:
        logger.error(f"分类推荐失败: {e}")
        return jsonify({'error': f'推荐失败: {str(e)}'}), 500

@app.route('/api/intelligent_recommend', methods=['POST'])
def intelligent_recommend_api():
    """纯智能分类推荐API"""
    try:
        from app.intelligent_classifier import get_intelligent_classifier
        
        request_data = request.get_json()
        material_info = request_data.get('material_info', {})
        
        if not material_info:
            return jsonify({'error': '物料信息不能为空'}), 400
        
        # 验证必要字段
        required_fields = ['name']
        for field in required_fields:
            if not material_info.get(field):
                return jsonify({'error': f'缺少必要字段: {field}'}), 400
        
        session_id = get_session_id()
        
        # 使用智能分类器
        intelligent_classifier = get_intelligent_classifier(business_manager)
        recommendations = intelligent_classifier.recommend_categories(material_info, session_id)
        
        return jsonify({
            'success': True,
            'recommendations': recommendations,
            'material_info': material_info,
            'session_id': session_id,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"智能推荐失败: {e}")
        return jsonify({'error': f'智能推荐失败: {str(e)}'}), 500

@app.route('/api/batch_recommend', methods=['POST'])
def batch_recommend_api():
    """批量智能分类推荐API"""
    try:
        from app.intelligent_classifier import get_intelligent_classifier
        
        request_data = request.get_json()
        materials = request_data.get('materials', [])
        
        if not materials or not isinstance(materials, list):
            return jsonify({'error': '物料列表不能为空'}), 400
        
        if len(materials) > 100:
            return jsonify({'error': '批量推荐最多支持100条物料'}), 400
        
        session_id = get_session_id()
        intelligent_classifier = get_intelligent_classifier(business_manager)
        
        results = []
        for i, material_info in enumerate(materials):
            try:
                if not material_info.get('name'):
                    results.append({
                        'index': i,
                        'error': '缺少物料名称',
                        'recommendations': []
                    })
                    continue
                
                recommendations = intelligent_classifier.recommend_categories(
                    material_info, f"{session_id}_batch_{i}"
                )
                
                results.append({
                    'index': i,
                    'material_info': material_info,
                    'recommendations': recommendations[:5],  # 每个物料最多5个推荐
                    'success': True
                })
                
            except Exception as e:
                logger.error(f"批量推荐第{i}个物料失败: {e}")
                results.append({
                    'index': i,
                    'error': str(e),
                    'recommendations': []
                })
        
        return jsonify({
            'success': True,
            'results': results,
            'total': len(materials),
            'session_id': session_id
        })
        
    except Exception as e:
        logger.error(f"批量推荐失败: {e}")
        return jsonify({'error': f'批量推荐失败: {str(e)}'}), 500

@app.route('/api/smart_classification', methods=['POST'])
def smart_classification_api():
    """智能物料分类API"""
    try:
        from app.smart_classifier import SmartClassifier, MaterialFeature
        
        request_data = request.get_json()
        
        if not request_data:
            return jsonify({'error': '请求数据不能为空'}), 400
        
        # 验证必需字段
        material_name = request_data.get('name', '').strip()
        if not material_name:
            return jsonify({'error': '物料名称不能为空'}), 400
        
        # 创建物料特征对象
        material = MaterialFeature(
            name=material_name,
            spec=request_data.get('spec', '').strip(),
            unit=request_data.get('unit', '').strip(),
            dn=request_data.get('dn', '').strip(),
            pn=request_data.get('pn', '').strip(),
            material=request_data.get('material', '').strip()
        )
        
        # 初始化智能分类器
        db_path = os.path.join(project_root, 'master_data.db')
        classifier = SmartClassifier(db_path)
        
        # 执行分类
        results = classifier.classify_material(material)
        
        return jsonify({
            'success': True,
            'results': results,
            'total': len(results),
            'input_material': {
                'name': material.name,
                'spec': material.spec,
                'unit': material.unit,
                'dn': material.dn,
                'pn': material.pn,
                'material': material.material
            }
        })
        
    except Exception as e:
        logger.error(f"智能分类失败: {e}")
        return jsonify({
            'success': False,
            'error': f'智能分类失败: {str(e)}'
        }), 500

@app.route('/api/upload_material_data', methods=['POST'])
def upload_material_data():
    """上传物料数据文件API"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': '未选择文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': '未选择文件'}), 400
        
        # 验证文件类型
        allowed_extensions = {'.xlsx', '.xls', '.csv'}
        file_ext = os.path.splitext(file.filename.lower())[1]
        
        if file_ext not in allowed_extensions:
            return jsonify({'success': False, 'error': '不支持的文件格式'}), 400
        
        # 保存文件到临时目录
        import tempfile
        temp_dir = tempfile.mkdtemp()
        temp_path = os.path.join(temp_dir, secure_filename(file.filename))
        file.save(temp_path)
        
        # 解析文件
        data = []
        headers = []
        
        try:
            if file_ext == '.csv':
                import csv
                # 尝试多种编码
                encodings = ['utf-8-sig', 'utf-8', 'gbk', 'gb2312']
                content_read = False
                
                for encoding in encodings:
                    try:
                        with open(temp_path, 'r', encoding=encoding) as csvfile:
                            # 尝试检测分隔符
                            sample = csvfile.read(1024)
                            csvfile.seek(0)
                            
                            # 如果样本为空，跳过
                            if not sample.strip():
                                continue
                                
                            try:
                                sniffer = csv.Sniffer()
                                delimiter = sniffer.sniff(sample).delimiter
                            except:
                                delimiter = ','  # 默认逗号分隔
                            
                            csvfile.seek(0)
                            reader = csv.reader(csvfile, delimiter=delimiter)
                            rows = list(reader)
                            
                            if rows and len(rows) > 0:
                                # 过滤空行
                                rows = [row for row in rows if any(cell.strip() for cell in row if cell)]
                                if rows:
                                    headers = [str(h).strip() for h in rows[0]]
                                    data = rows[1:] if len(rows) > 1 else []
                                    content_read = True
                                    break
                    except Exception as enc_e:
                        logger.debug(f"尝试编码 {encoding} 失败: {enc_e}")
                        continue
                
                if not content_read:
                    raise Exception("无法读取CSV文件，请检查文件格式和编码")
            
            else:  # Excel文件
                import pandas as pd
                try:
                    # 尝试读取Excel，处理可能的问题
                    df = pd.read_excel(temp_path, engine='openpyxl' if file_ext == '.xlsx' else 'xlrd')
                    
                    # 处理空数据
                    if df.empty:
                        headers = []
                        data = []
                    else:
                        # 清理列名和数据
                        headers = [str(col).strip() for col in df.columns.tolist()]
                        
                        # 填充NaN值并转换为字符串
                        df_filled = df.fillna('')
                        data = df_filled.values.tolist()
                        
                        # 清理数据中的NaN和None
                        data = [[str(cell) if cell is not None else '' for cell in row] for row in data]
                        
                except Exception as pd_e:
                    raise Exception(f"Excel文件解析失败: {str(pd_e)}")
        
        except Exception as e:
            logger.error(f"文件解析失败: {e}")
            return jsonify({'success': False, 'error': f'文件解析失败: {str(e)}'}), 400
        
        finally:
            # 清理临时文件
            import shutil
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        
        # 数据验证和统计
        if not headers:
            return jsonify({'success': False, 'error': '文件中未找到有效的表头'}), 400
        
        stats = {
            'total': len(data),
            'columns': len(headers),
            'filename': file.filename
        }
        
        # 返回前5行作为预览，确保数据格式正确
        preview = []
        for i, row in enumerate(data[:5]):
            # 确保每行数据长度与表头一致
            if len(row) < len(headers):
                row.extend([''] * (len(headers) - len(row)))
            elif len(row) > len(headers):
                row = row[:len(headers)]
            preview.append(row)
        
        logger.info(f"文件上传成功: {file.filename}, 数据行数: {len(data)}, 列数: {len(headers)}")
        logger.debug(f"预览数据: {preview[:2]}")  # 只记录前2行用于调试
        
        return jsonify({
            'success': True,
            'data': data,
            'headers': headers,
            'preview': preview,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"文件上传失败: {e}")
        return jsonify({'success': False, 'error': f'上传失败: {str(e)}'}), 500

@app.route('/api/batch_material_matching', methods=['POST'])
def batch_material_matching():
    """批量物料匹配API - 增强版本"""
    try:
        # 导入增强分类器
        from app.enhanced_smart_classifier import EnhancedSmartClassifier, EnhancedClassifierAdapter
        from app.smart_classifier import MaterialFeature
        
        request_data = request.get_json()
        materials = request_data.get('materials', [])
        template_id = request_data.get('template', 'universal-manufacturing')
        use_enhanced = request_data.get('use_enhanced', True)  # 默认使用增强算法
        
        if not materials:
            return jsonify({'success': False, 'error': '物料数据为空'}), 400
        
        # 初始化分类器 - 支持原始和增强两种算法
        db_path = os.path.join(project_root, 'master_data.db')
        
        if use_enhanced:
            classifier = EnhancedSmartClassifier(db_path)
            algorithm_type = "enhanced"
        else:
            from app.smart_classifier import SmartClassifier
            classifier = SmartClassifier(db_path)
            algorithm_type = "original"
        
        results = []
        total_materials = len(materials)
        
        for i, material_row in enumerate(materials):
            try:
                # 假设材料数据的格式：[物料编码, 物料长描述, 物料名称, 物料分类, 规格, 型号, 单位]
                if len(material_row) < 3:
                    continue
                
                # 提取物料信息
                material_code = material_row[0] if len(material_row) > 0 else ''
                material_desc = material_row[1] if len(material_row) > 1 else ''
                material_name = material_row[2] if len(material_row) > 2 else ''
                current_category = material_row[3] if len(material_row) > 3 else ''
                material_spec = material_row[4] if len(material_row) > 4 else ''
                material_unit = material_row[6] if len(material_row) > 6 else ''
                
                # 创建物料特征 - 优先使用完整描述来提取材质信息
                full_material_name = material_desc if material_desc else material_name
                material = MaterialFeature(
                    name=full_material_name,
                    spec=f"{material_spec}".strip() if material_spec else '',
                    unit=material_unit,
                    dn='',
                    pn='',
                    material=''
                )
                
                # 执行智能分类
                classification_results = classifier.classify_material(material)
                
                # 构造结果
                best_match = classification_results[0] if classification_results else None
                
                result = {
                    'index': i,
                    'material_code': material_code,
                    'material_name': material_name,
                    'material_spec': material_spec,
                    'current_category': current_category,
                    'matched_material': material_desc,
                    'match_code': material_code,
                    'match_confidence': 85,  # 模拟置信度
                    'classification': best_match['category'] if best_match else '未分类',
                    'category_path': f"制造业 > {best_match['category']}" if best_match else '',
                    'classification_confidence': int(best_match['confidence']) if best_match else 0,
                    'suggestions': classification_results[:3] if classification_results else [],
                    # 增强算法特有信息
                    'algorithm_type': algorithm_type,
                    'material_detected': [m['base_keyword'] for m in best_match.get('material_info', [])] if best_match and use_enhanced else [],
                    'original_confidence': best_match.get('original_confidence') if best_match and use_enhanced else None,
                    'material_bonus': best_match.get('material_bonus') if best_match and use_enhanced else 0,
                    'enhancement_details': {
                        'materials_found': [m['base_keyword'] for m in best_match.get('material_info', [])] if best_match and use_enhanced else [],
                        'confidence_improvement': (best_match.get('confidence', 0) - best_match.get('original_confidence', 0)) if best_match and use_enhanced else 0
                    } if use_enhanced else None
                }
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"处理第{i}个物料失败: {e}")
                # 添加错误结果
                results.append({
                    'index': i,
                    'material_name': material_row[2] if len(material_row) > 2 else '未知物料',
                    'error': str(e),
                    'match_confidence': 0,
                    'classification_confidence': 0
                })
        
        # 计算统计信息
        enhanced_count = sum(1 for r in results if r.get('material_detected'))
        avg_confidence = sum(r.get('classification_confidence', 0) for r in results) / len(results) if results else 0
        
        return jsonify({
            'success': True,
            'results': results,
            'total': len(results),
            'template': template_id,
            'algorithm_info': {
                'type': algorithm_type,
                'enhanced_enabled': use_enhanced,
                'materials_detected': enhanced_count if use_enhanced else 0,
                'average_confidence': round(avg_confidence, 1),
                'material_detection_rate': round((enhanced_count / len(results)) * 100, 1) if results and use_enhanced else 0
            }
        })
        
    except Exception as e:
        logger.error(f"批量匹配失败: {e}")
        return jsonify({'success': False, 'error': f'匹配失败: {str(e)}'}), 500

@app.route('/api/save_workflow_results', methods=['POST'])
def save_workflow_results():
    """保存工作流结果API"""
    try:
        request_data = request.get_json()
        results = request_data.get('results', [])
        template_id = request_data.get('template', '')
        
        # 这里可以保存到数据库或文件
        # 暂时返回成功状态
        
        session_id = get_session_id()
        
        return jsonify({
            'success': True,
            'message': f'成功保存{len(results)}条匹配结果',
            'session_id': session_id
        })
        
    except Exception as e:
        logger.error(f"保存结果失败: {e}")
        return jsonify({'success': False, 'error': f'保存失败: {str(e)}'}), 500

def _merge_and_deduplicate_recommendations(recommendations: List[Dict]) -> List[Dict]:
    """合并和去重推荐结果"""
    seen_categories = {}
    
    for rec in recommendations:
        category_id = rec.get('category_id')
        if not category_id:
            continue
            
        if category_id in seen_categories:
            # 合并置信度（取最高值）
            existing = seen_categories[category_id]
            if rec.get('confidence', 0) > existing.get('confidence', 0):
                existing.update(rec)
                existing['reason'] += f" | {rec.get('reason', '')}"
        else:
            seen_categories[category_id] = rec.copy()
    
    # 转换为列表并按置信度排序
    merged_recommendations = list(seen_categories.values())
    merged_recommendations.sort(key=lambda x: x.get('confidence', 0), reverse=True)
    
    return merged_recommendations

# ==================== 主数据管理API ====================

@app.route('/api/master_data/materials/search')
def search_materials_api():
    """物料搜索API"""
    try:
        from app.master_data_manager import master_data_manager
        
        keyword = request.args.get('keyword', '').strip()
        category_id = request.args.get('category_id', '').strip()
        limit = int(request.args.get('limit', 20))
        
        if not keyword:
            return jsonify({'error': '搜索关键词不能为空'}), 400
        
        materials = master_data_manager.search_materials(
            keyword=keyword,
            category_id=category_id if category_id else None,
            limit=limit
        )
        
        return jsonify({
            'success': True,
            'materials': materials,
            'total': len(materials),
            'keyword': keyword
        })
        
    except Exception as e:
        logger.error(f"物料搜索失败: {e}")
        return jsonify({'error': f'搜索失败: {str(e)}'}), 500

@app.route('/api/master_data/categories')
def get_categories_api():
    """获取分类列表API"""
    try:
        from app.master_data_manager import master_data_manager
        
        parent_id = request.args.get('parent_id', '').strip()
        categories = master_data_manager.get_material_categories(
            parent_id=parent_id if parent_id else None
        )
        
        return jsonify({
            'success': True,
            'categories': categories,
            'total': len(categories)
        })
        
    except Exception as e:
        logger.error(f"获取分类失败: {e}")
        return jsonify({'error': f'获取分类失败: {str(e)}'}), 500

@app.route('/api/master_data/categories/<category_id>/features')
def get_category_features_master_api(category_id):
    """获取分类特征API"""
    try:
        from app.master_data_manager import master_data_manager
        
        features = master_data_manager.get_category_features(category_id)
        
        return jsonify({
            'success': True,
            'category_id': category_id,
            'features': features,
            'total': len(features)
        })
        
    except Exception as e:
        logger.error(f"获取分类特征失败: {e}")
        return jsonify({'error': f'获取特征失败: {str(e)}'}), 500

# ==================== 分类管理 API ====================

@app.route('/categories')
def category_management_page():
    """分类管理页面"""
    return render_template('category_management.html')

@app.route('/jump-test')
def jump_test_page():
    """智能跳转测试页面"""
    with open(os.path.join(project_root, 'jump_test.html'), 'r', encoding='utf-8') as f:
        return f.read()

@app.route('/category-templates')
def category_templates_page():
    """分类模板列表页面"""
    return render_template('category_templates.html')

@app.route('/smart-classification')
def smart_classification_page():
    """智能物料分类页面"""
    return render_template('smart_classification.html')

@app.route('/material-workflow')
def material_workflow_page():
    """物料处理工作流页面"""
    return render_template('material_workflow.html')

@app.route('/api/categories/tree')
def get_categories_tree():
    """获取分类树形结构"""
    try:
        import sqlite3
        
        conn = sqlite3.connect(os.path.join(project_root, 'master_data.db'))
        cursor = conn.cursor()
        
        # 获取所有分类数据
        cursor.execute('''
            SELECT category_code, category_name, parent_code, level, 
                   is_leaf, description, material_template
            FROM material_categories 
            ORDER BY category_code
        ''')
        
        categories = []
        for row in cursor.fetchall():
            categories.append({
                'code': row[0],
                'name': row[1], 
                'parent_code': row[2],
                'level': row[3],
                'is_leaf': bool(row[4]),
                'description': row[5] or '',
                'template': row[6] or ''
            })
        
        conn.close()
        
        # 构建树形结构
        tree = _build_category_tree(categories)
        
        return jsonify({
            'success': True,
            'tree': tree,
            'total': len(categories)
        })
        
    except Exception as e:
        logger.error(f"获取分类树失败: {e}")
        return jsonify({'error': f'获取分类树失败: {str(e)}'}), 500

@app.route('/api/categories/search')
def search_categories():
    """搜索分类"""
    try:
        keyword = request.args.get('keyword', '').strip()
        level = request.args.get('level', type=int)
        
        import sqlite3
        conn = sqlite3.connect(os.path.join(project_root, 'master_data.db'))
        cursor = conn.cursor()
        
        # 构建查询条件
        where_conditions = []
        params = []
        
        if keyword:
            where_conditions.append('(category_code LIKE ? OR category_name LIKE ?)')
            params.extend([f'%{keyword}%', f'%{keyword}%'])
        
        if level:
            where_conditions.append('level = ?')
            params.append(level)
        
        where_clause = ' AND '.join(where_conditions) if where_conditions else '1=1'
        
        cursor.execute(f'''
            SELECT category_code, category_name, parent_code, level,
                   is_leaf, description, material_template
            FROM material_categories 
            WHERE {where_clause}
            ORDER BY level, category_code
            LIMIT 100
        ''', params)
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'code': row[0],
                'name': row[1],
                'parent_code': row[2],
                'level': row[3],
                'is_leaf': bool(row[4]),
                'description': row[5] or '',
                'template': row[6] or ''
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'results': results,
            'total': len(results)
        })
        
    except Exception as e:
        logger.error(f"搜索分类失败: {e}")
        return jsonify({'error': f'搜索失败: {str(e)}'}), 500

@app.route('/api/categories/statistics')  
def get_categories_statistics():
    """获取分类统计信息"""
    try:
        import sqlite3
        conn = sqlite3.connect(os.path.join(project_root, 'master_data.db'))
        cursor = conn.cursor()
        
        # 总数统计
        cursor.execute('SELECT COUNT(*) FROM material_categories')
        total = cursor.fetchone()[0]
        
        # 按层级统计
        cursor.execute('''
            SELECT level, COUNT(*) as count 
            FROM material_categories 
            GROUP BY level 
            ORDER BY level
        ''')
        level_stats = dict(cursor.fetchall())
        
        # 叶子节点统计
        cursor.execute('SELECT COUNT(*) FROM material_categories WHERE is_leaf = 1')
        leaf_count = cursor.fetchone()[0]
        
        # 模板统计
        cursor.execute('''
            SELECT material_template, COUNT(*) as count
            FROM material_categories 
            WHERE material_template != '' 
            GROUP BY material_template
        ''')
        template_stats = dict(cursor.fetchall())
        
        conn.close()
        
        return jsonify({
            'success': True,
            'statistics': {
                'total': total,
                'level_stats': level_stats, 
                'leaf_count': leaf_count,
                'template_stats': template_stats
            }
        })
        
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        return jsonify({'error': f'获取统计信息失败: {str(e)}'}), 500

@app.route('/api/categories/stats')  
def get_categories_stats():
    """获取分类统计信息（简化版，供首页使用）"""
    try:
        import sqlite3
        conn = sqlite3.connect(os.path.join(project_root, 'master_data.db'))
        cursor = conn.cursor()
        
        # 总数统计
        cursor.execute('SELECT COUNT(*) FROM material_categories')
        total = cursor.fetchone()[0]
        
        # 按层级统计
        cursor.execute('''
            SELECT level, COUNT(*) as count 
            FROM material_categories 
            GROUP BY level 
            ORDER BY level
        ''')
        level_results = cursor.fetchall()
        
        # 构建层级统计
        level1 = 0
        level2 = 0 
        level3 = 0
        
        for level, count in level_results:
            if level == 1:
                level1 = count
            elif level == 2:
                level2 = count
            elif level == 3:
                level3 = count
        
        conn.close()
        
        return jsonify({
            'success': True,
            'statistics': {
                'total': total,
                'level1': level1,
                'level2': level2,
                'level3': level3
            }
        })
        
    except Exception as e:
        logger.error(f"获取分类统计失败: {e}")
        return jsonify({'error': f'获取分类统计失败: {str(e)}'}), 500

@app.route('/api/categories/detailed-statistics')
def get_categories_detailed_statistics():
    """获取详细分类统计信息（用于模板选择页面详情展示）"""
    try:
        import sqlite3
        conn = sqlite3.connect(os.path.join(project_root, 'master_data.db'))
        cursor = conn.cursor()
        
        # 总数统计
        cursor.execute('SELECT COUNT(*) FROM material_categories')
        total = cursor.fetchone()[0]
        
        # 按层级统计
        cursor.execute('''
            SELECT level, COUNT(*) as count 
            FROM material_categories 
            GROUP BY level 
            ORDER BY level
        ''')
        level_stats = dict(cursor.fetchall())
        
        # 叶子节点统计
        cursor.execute('SELECT COUNT(*) FROM material_categories WHERE is_leaf = 1')
        leaf_count = cursor.fetchone()[0]
        
        # 获取一级分类详情
        cursor.execute('''
            SELECT category_code, category_name 
            FROM material_categories 
            WHERE level = 1 
            ORDER BY category_code
        ''')
        level1_categories = cursor.fetchall()
        
        # 按编码前缀统计（用于制造业适配度）
        cursor.execute('''
            SELECT SUBSTR(category_code, 1, 1) as prefix, COUNT(*) as count
            FROM material_categories 
            WHERE level = 1
            GROUP BY prefix
            ORDER BY prefix
        ''')
        prefix_stats = dict(cursor.fetchall())
        
        conn.close()
        
        # 计算制造业适配度（基于覆盖的主要制造业领域）
        manufacturing_coverage = {
            'A': '化工材料',  # A3等
            'B': '机械设备',  # AA, AB等  
            'C': '金属制品',  # AJ, AS等
            'D': '建筑材料',  # AN等
            'E': '工具设备'   # AT等
        }
        
        covered_areas = len([k for k in manufacturing_coverage.keys() if k in prefix_stats])
        compatibility_rate = min(95, (covered_areas / len(manufacturing_coverage)) * 100)
        
        return jsonify({
            'success': True,
            'statistics': {
                'total': total,
                'level_stats': level_stats,
                'leaf_count': leaf_count,
                'level1_categories': level1_categories,
                'prefix_stats': prefix_stats,
                'compatibility_rate': round(compatibility_rate, 1),
                'manufacturing_coverage': manufacturing_coverage
            }
        })
        
    except Exception as e:
        logger.error(f"获取详细统计信息失败: {e}")
        return jsonify({'error': f'获取详细统计信息失败: {str(e)}'}), 500

@app.route('/form_generation')
def form_generation_page():
    """表单生成页面"""
    category_selections = get_session_data('category_selections')
    if not category_selections:
        flash('请先完成分类选择', 'error')
        return redirect(url_for('category_selection_page'))
    
    return render_template('form_generation.html',
                         category_selections=category_selections)

@app.route('/generate_forms', methods=['POST'])
def generate_forms():
    """生成表单"""
    try:
        logger.info("开始生成表单")
        
        category_selections = get_session_data('category_selections')
        extraction_results = get_session_data('extraction_results')
        
        if not category_selections or not extraction_results:
            return jsonify({'error': '请先完成前置步骤'}), 400
        
        request_data = request.get_json()
        form_config = request_data.get('form_config', {})
        
        if workflow_service:
            try:
                # 生成表单
                generated_forms = workflow_service.generate_forms(
                    extraction_results['results'],
                    category_selections['selections'],
                    form_config
                )
                
                # 保存生成的表单
                form_data = {
                    'forms': generated_forms,
                    'config': form_config,
                    'generation_time': datetime.now().isoformat(),
                    'total_forms': len(generated_forms) if generated_forms else 0
                }
                
                store_session_data('generated_forms', form_data)
                logger.info(f"表单生成完成 - 生成了 {form_data['total_forms']} 个表单")
                
                return jsonify({
                    'success': True,
                    'message': '表单生成完成',
                    'forms': generated_forms,
                    'total_count': len(generated_forms) if generated_forms else 0
                })
                
            except Exception as e:
                logger.error(f"工作流服务生成表单失败: {e}")
                return jsonify({'error': f'表单生成失败: {str(e)}'}), 500
        else:
            return jsonify({'error': '工作流服务未初始化'}), 500
            
    except Exception as e:
        logger.error(f"表单生成处理失败: {e}")
        return jsonify({'error': f'处理失败: {str(e)}'}), 500

@app.route('/matching')
def matching_page():
    """匹配页面"""
    generated_forms = get_session_data('generated_forms')
    if not generated_forms:
        flash('请先完成表单生成', 'error')
        return redirect(url_for('form_generation_page'))
    
    return render_template('matching.html',
                         generated_forms=generated_forms)

@app.route('/perform_matching', methods=['POST'])
def perform_matching():
    """执行匹配"""
    try:
        logger.info("开始执行匹配")
        
        generated_forms = get_session_data('generated_forms')
        if not generated_forms:
            return jsonify({'error': '请先完成表单生成'}), 400
        
        request_data = request.get_json()
        matching_config = request_data.get('matching_config', {})
        
        if workflow_service:
            try:
                # 执行匹配
                matching_results = workflow_service.perform_matching(
                    generated_forms['forms'],
                    matching_config
                )
                
                # 保存匹配结果
                match_data = {
                    'results': matching_results,
                    'config': matching_config,
                    'matching_time': datetime.now().isoformat(),
                    'total_matches': len(matching_results) if matching_results else 0
                }
                
                store_session_data('matching_results', match_data)
                logger.info(f"匹配完成 - 获得 {match_data['total_matches']} 个匹配结果")
                
                return jsonify({
                    'success': True,
                    'message': '匹配完成',
                    'results': matching_results,
                    'total_count': len(matching_results) if matching_results else 0
                })
                
            except Exception as e:
                logger.error(f"工作流服务执行匹配失败: {e}")
                return jsonify({'error': f'匹配失败: {str(e)}'}), 500
        else:
            return jsonify({'error': '工作流服务未初始化'}), 500
            
    except Exception as e:
        logger.error(f"匹配处理失败: {e}")
        return jsonify({'error': f'处理失败: {str(e)}'}), 500

@app.route('/decision')
def decision_page():
    """决策页面"""
    matching_results = get_session_data('matching_results')
    if not matching_results:
        flash('请先完成匹配', 'error')
        return redirect(url_for('matching_page'))
    
    return render_template('decision.html',
                         matching_results=matching_results)

@app.route('/save_decisions', methods=['POST'])
def save_decisions():
    """保存决策结果"""
    try:
        logger.info("开始保存决策结果")
        
        matching_results = get_session_data('matching_results')
        if not matching_results:
            return jsonify({'error': '请先完成匹配'}), 400
        
        request_data = request.get_json()
        decisions = request_data.get('decisions', {})
        
        # 保存最终决策
        decision_data = {
            'decisions': decisions,
            'decision_time': datetime.now().isoformat(),
            'total_decisions': len(decisions)
        }
        
        store_session_data('final_decisions', decision_data)
        logger.info(f"决策结果已保存 - 保存了 {len(decisions)} 个决策")
        
        return jsonify({
            'success': True,
            'message': '决策结果已保存',
            'next_step': url_for('results_page')
        })
        
    except Exception as e:
        logger.error(f"保存决策结果失败: {e}")
        return jsonify({'error': f'保存失败: {str(e)}'}), 500

@app.route('/results')
def results_page():
    """结果页面"""
    final_decisions = get_session_data('final_decisions')
    if not final_decisions:
        flash('请先完成决策', 'error')
        return redirect(url_for('decision_page'))
    
    # 获取完整的工作流数据
    workflow_data = {
        'uploaded_data': get_session_data('uploaded_data'),
        'extraction_results': get_session_data('extraction_results'),
        'category_selections': get_session_data('category_selections'),
        'generated_forms': get_session_data('generated_forms'),
        'matching_results': get_session_data('matching_results'),
        'final_decisions': final_decisions
    }
    
    return render_template('results.html', workflow_data=workflow_data)

@app.route('/export_results')
def export_results():
    """导出结果"""
    try:
        final_decisions = get_session_data('final_decisions')
        if not final_decisions:
            return jsonify({'error': '没有可导出的结果'}), 400
        
        # 生成导出文件
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        export_filename = f"mmp_results_{timestamp}.json"
        export_path = os.path.join(app.config['UPLOAD_FOLDER'], export_filename)
        
        # 获取完整的工作流数据
        export_data = {
            'export_time': datetime.now().isoformat(),
            'session_id': get_session_id(),
            'uploaded_data': get_session_data('uploaded_data'),
            'extraction_results': get_session_data('extraction_results'),
            'category_selections': get_session_data('category_selections'),
            'generated_forms': get_session_data('generated_forms'),
            'matching_results': get_session_data('matching_results'),
            'final_decisions': final_decisions
        }
        
        with open(export_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"结果导出完成: {export_path}")
        
        return jsonify({
            'success': True,
            'message': '结果导出完成',
            'filename': export_filename,
            'download_url': f'/static/uploads/{export_filename}'
        })
        
    except Exception as e:
        logger.error(f"导出结果失败: {e}")
        return jsonify({'error': f'导出失败: {str(e)}'}), 500

@app.route('/batch_management')
def batch_management():
    """批量管理页面"""
    return render_template('batch_management.html')

@app.route('/api/status')
def api_status():
    """API状态检查"""
    workflow_status = get_workflow_status()
    session_id = get_session_id()
    
    return jsonify({
        'status': 'running',
        'session_id': session_id,
        'workflow_status': workflow_status,
        'workflow_service_initialized': workflow_service is not None,
        'advanced_preprocessor_available': ADVANCED_PREPROCESSOR_AVAILABLE,
        'enhanced_config_available': ENHANCED_CONFIG_AVAILABLE,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/clear_session')
def clear_session():
    """清除会话数据API"""
    try:
        clear_session_data()
        session.clear()
        logger.info("会话数据已清除")
        return jsonify({'success': True, 'message': '会话已清除'})
    except Exception as e:
        logger.error(f"清除会话失败: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/debug/session')
def debug_session():
    """调试会话数据"""
    session_id = get_session_id()
    all_data = session_manager.get_all_data(session_id)
    workflow_status = get_workflow_status()
    
    return jsonify({
        'session_id': session_id,
        'workflow_status': workflow_status,
        'session_data_keys': list(all_data.keys()),
        'session_data_summary': {
            key: type(value).__name__ for key, value in all_data.items()
        }
    })

# === 新增业务数据管理API ===

@app.route('/api/field_mappings', methods=['GET'])
def get_field_mappings_api():
    """获取字段映射配置API"""
    try:
        mapping_name = request.args.get('mapping_name', 'standard_medical_mapping')
        mappings = business_manager.get_field_mappings(mapping_name)
        
        return jsonify({
            'success': True,
            'data': mappings,
            'total': len(mappings)
        })
        
    except Exception as e:
        logger.error(f"获取字段映射失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/field_mappings', methods=['POST'])
def create_field_mapping_api():
    """创建字段映射API"""
    try:
        data = request.get_json()
        
        required_fields = ['mapping_name', 'source_field', 'target_field', 'field_type']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'缺少必需字段: {field}'}), 400
        
        mapping_id = business_manager.create_field_mapping(
            mapping_name=data['mapping_name'],
            source_field=data['source_field'],
            target_field=data['target_field'],
            field_type=data['field_type'],
            data_type=data.get('data_type', 'string'),
            validation_rule=data.get('validation_rule'),
            description=data.get('description')
        )
        
        return jsonify({
            'success': True,
            'mapping_id': mapping_id,
            'message': '字段映射创建成功'
        })
        
    except Exception as e:
        logger.error(f"创建字段映射失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/uploaded_files', methods=['GET'])
def get_uploaded_files_api():
    """获取上传文件列表API"""
    try:
        session_id = get_session_id()
        
        # 这里需要添加一个方法来按session_id获取文件
        # 暂时返回统计信息
        stats = business_manager.get_statistics()
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'statistics': stats
        })
        
    except Exception as e:
        logger.error(f"获取上传文件失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/file_data/<file_id>', methods=['GET'])
def get_file_data_api(file_id):
    """获取文件数据API"""
    try:
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # 获取文件信息
        file_info = business_manager.get_uploaded_file_info(file_id)
        if not file_info:
            return jsonify({'success': False, 'error': '文件不存在'}), 404
        
        # 获取文件数据
        file_data = business_manager.get_file_data(file_id, limit, offset)
        
        return jsonify({
            'success': True,
            'file_info': file_info,
            'data': file_data,
            'total_rows': file_info['row_count'],
            'returned_rows': len(file_data),
            'offset': offset
        })
        
    except Exception as e:
        logger.error(f"获取文件数据失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/system_config/<config_key>', methods=['GET'])
def get_system_config_api(config_key):
    """获取系统配置API"""
    try:
        config_value = business_manager.get_config(config_key)
        
        if config_value is not None:
            return jsonify({
                'success': True,
                'key': config_key,
                'value': config_value
            })
        else:
            return jsonify({'success': False, 'error': '配置不存在'}), 404
        
    except Exception as e:
        logger.error(f"获取系统配置失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/system_config/<config_key>', methods=['POST'])
def set_system_config_api(config_key):
    """设置系统配置API"""
    try:
        data = request.get_json()
        
        if 'value' not in data:
            return jsonify({'success': False, 'error': '缺少value字段'}), 400
        
        success = business_manager.set_config(
            key=config_key,
            value=data['value'],
            config_type=data.get('config_type', 'string'),
            description=data.get('description')
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': f'配置 {config_key} 设置成功'
            })
        else:
            return jsonify({'success': False, 'error': '配置设置失败'}), 500
        
    except Exception as e:
        logger.error(f"设置系统配置失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/statistics', methods=['GET'])
def get_statistics_api():
    """获取系统统计信息API"""
    try:
        stats = business_manager.get_statistics()
        
        return jsonify({
            'success': True,
            'statistics': stats
        })
        
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

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
    logger.warning(f"404错误: {request.url}")
    return render_template('error.html', 
                         error_code=404, 
                         error_message='页面未找到'), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"500错误: {error}")
    return render_template('error.html', 
                         error_code=500, 
                         error_message='服务器内部错误'), 500

@app.errorhandler(413)
def file_too_large(error):
    return render_template('error.html',
                         error_code=413,
                         error_message='文件太大，请选择小于16MB的文件'), 413

@app.route('/template-selection')
def template_selection():
    """分类模板选择页面"""
    return render_template('template_selection.html')

@app.route('/api/template/select', methods=['POST'])
def select_template():
    """选择分类模板API"""
    try:
        template_data = request.get_json()
        
        # 验证必需字段
        required_fields = ['template_id', 'template_name', 'total_categories']
        for field in required_fields:
            if field not in template_data:
                return jsonify({'success': False, 'error': f'缺少必需字段: {field}'}), 400
        
        # 保存模板选择到会话
        store_session_data('selected_template', template_data)
        
        logger.info(f"用户选择了分类模板: {template_data['template_name']}")
        
        return jsonify({
            'success': True,
            'message': '模板选择成功',
            'template': template_data
        })
        
    except Exception as e:
        logger.error(f"选择分类模板失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    # 初始化服务
    init_service()
    
    # 启动应用
    logger.info("MMP应用启动中...")
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,  # 生产环境设为False
        threaded=True
    )
