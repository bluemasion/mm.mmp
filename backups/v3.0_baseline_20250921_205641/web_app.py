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
app.secret_key = 'mmp-secure-key-change-in-production-' + str(uuid.uuid4())
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
    """会话数据管理器 - 持久化版本"""
    
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.memory_cache = {}  # 内存缓存
        self.cache_timeout = 300  # 5分钟内存缓存
    
    def _get_session_file(self, session_id: str) -> str:
        """获取会话数据文件路径"""
        return os.path.join(self.base_dir, f"session_{session_id}.pkl")
    
    def store_data(self, session_id: str, key: str, data: Any):
        """存储会话数据"""
        try:
            # 存储到内存缓存
            if session_id not in self.memory_cache:
                self.memory_cache[session_id] = {'data': {}, 'timestamp': datetime.now()}
            
            self.memory_cache[session_id]['data'][key] = data
            self.memory_cache[session_id]['timestamp'] = datetime.now()
            
            # 持久化到文件
            session_file = self._get_session_file(session_id)
            session_data = self.memory_cache[session_id]['data']
            
            with open(session_file, 'wb') as f:
                pickle.dump(session_data, f)
            
            logger.info(f"会话数据已存储: session_id={session_id}, key={key}")
            
        except Exception as e:
            logger.error(f"存储会话数据失败: {e}")
    
    def get_data(self, session_id: str, key: str, default=None):
        """获取会话数据"""
        try:
            # 首先检查内存缓存
            if (session_id in self.memory_cache and 
                datetime.now() - self.memory_cache[session_id]['timestamp'] < timedelta(seconds=self.cache_timeout)):
                data = self.memory_cache[session_id]['data'].get(key, default)
                logger.info(f"从内存缓存获取数据: session_id={session_id}, key={key}, found={'Yes' if data != default else 'No'}")
                return data
            
            # 从文件加载
            session_file = self._get_session_file(session_id)
            if os.path.exists(session_file):
                with open(session_file, 'rb') as f:
                    session_data = pickle.load(f)
                
                # 更新内存缓存
                self.memory_cache[session_id] = {
                    'data': session_data,
                    'timestamp': datetime.now()
                }
                
                data = session_data.get(key, default)
                logger.info(f"从文件加载数据: session_id={session_id}, key={key}, found={'Yes' if data != default else 'No'}")
                return data
            
            logger.info(f"未找到会话数据: session_id={session_id}, key={key}")
            return default
            
        except Exception as e:
            logger.error(f"获取会话数据失败: {e}")
            return default
    
    def get_all_data(self, session_id: str) -> dict:
        """获取会话的所有数据"""
        try:
            session_file = self._get_session_file(session_id)
            if os.path.exists(session_file):
                with open(session_file, 'rb') as f:
                    return pickle.load(f)
            return {}
        except Exception as e:
            logger.error(f"获取所有会话数据失败: {e}")
            return {}
    
    def clear_data(self, session_id: str):
        """清除会话数据"""
        try:
            session_file = self._get_session_file(session_id)
            if os.path.exists(session_file):
                os.remove(session_file)
            
            if session_id in self.memory_cache:
                del self.memory_cache[session_id]
            
            logger.info(f"会话数据已清除: session_id={session_id}")
        except Exception as e:
            logger.error(f"清除会话数据失败: {e}")

# 创建会话数据管理器实例
session_manager = SessionDataManager(SESSION_DATA_DIR)

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
    """获取或创建会话ID"""
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
        session.permanent = True
        logger.info(f"创建新会话: {session['session_id']}")
    return session['session_id']

def store_session_data(key: str, data: Any):
    """存储会话数据"""
    session_id = get_session_id()
    session_manager.store_data(session_id, key, data)

def get_session_data(key: str, default=None):
    """获取会话数据"""
    session_id = get_session_id()
    return session_manager.get_data(session_id, key, default)

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
            
            # 预览数据
            try:
                file_config = {
                    'source_type': 'file',
                    'path': filepath,
                    'type': filename.split('.')[-1].lower()
                }
                
                preview_df = load_data_from_config(file_config)
                
                # 限制预览行数
                preview_data = preview_df.head(10).to_dict('records') if len(preview_df) > 10 else preview_df.to_dict('records')
                columns = list(preview_df.columns)
                total_rows = len(preview_df)
                
                # 存储上传的数据信息
                upload_info = {
                    'filename': filename,
                    'filepath': filepath,
                    'columns': columns,
                    'total_rows': total_rows,
                    'preview_data': preview_data,
                    'upload_time': datetime.now().isoformat()
                }
                
                store_session_data('uploaded_data', upload_info)
                logger.info(f"文件上传成功，数据已存储到会话 - 行数: {total_rows}, 列数: {len(columns)}")
                
                return jsonify({
                    'success': True,
                    'message': '文件上传成功',
                    'filename': filename,
                    'columns': columns,
                    'total_rows': total_rows,
                    'preview_data': preview_data
                })
                
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
    uploaded_data = get_session_data('uploaded_data')
    if not uploaded_data:
        flash('请先上传数据文件', 'error')
        return redirect(url_for('upload_page'))
    
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

@app.route('/category_selection')
def category_selection_page():
    """分类选择页面"""
    extraction_results = get_session_data('extraction_results')
    if not extraction_results:
        flash('请先完成参数提取', 'error')
        logger.warning("访问分类选择页面但未找到参数提取结果")
        return redirect(url_for('extract_parameters_page'))
    
    logger.info(f"访问分类选择页面 - 有 {extraction_results.get('total_extracted', 0)} 条提取结果")
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
        category_selections = request_data.get('selections', {})
        
        # 保存分类选择
        selection_data = {
            'selections': category_selections,
            'selection_time': datetime.now().isoformat(),
            'total_selections': len(category_selections)
        }
        
        store_session_data('category_selections', selection_data)
        logger.info(f"分类选择已保存 - 选择了 {len(category_selections)} 个分类")
        
        return jsonify({
            'success': True,
            'message': '分类选择已保存',
            'next_step': url_for('form_generation_page')
        })
        
    except Exception as e:
        logger.error(f"保存分类选择失败: {e}")
        return jsonify({'error': f'保存失败: {str(e)}'}), 500

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
