# api.py
# 需要先安装 flask: pip install Flask
from flask import Flask, request, jsonify
import logging
from app.workflow_service import MaterialWorkflowService
from app import config

app = Flask(__name__)
logging.basicConfig(level=config.LOG_LEVEL, format='%(asctime)s - %(levelname)s - %(message)s')

# 在服务启动时，一次性初始化服务
# 这避免了每次请求都重新加载模型和数据的开销
material_service = MaterialWorkflowService()

@app.route('/match', methods=['POST'])
def match_material():
    """接收物料数据并返回匹配结果的API接口"""
    if not request.json:
        return jsonify({"error": "请求体不能为空且必须为JSON格式"}), 400
    
    item_data = request.json
    
    try:
        result = material_service.process_single_item(item_data)
        return jsonify(result)
    except Exception as e:
        logging.error(f"处理请求时发生错误: {e}")
        return jsonify({"error": "服务器内部错误"}), 500

if __name__ == '__main__':
    # 启动web服务，监听在本地5000端口
    # 生产环境中应使用 Gunicorn 或 uWSGI 等部署
    app.run(host='0.0.0.0', port=5000, debug=True)