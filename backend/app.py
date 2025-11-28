from flask import Flask, request, jsonify, send_from_directory, abort
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import uuid
import sys
import redis
from google import genai
from PIL import Image
import io

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.api_keys import GEMINI_API_KEY, GEMINI_MODEL, UPLOAD_FOLDER, RESULT_FOLDER, SUPPORTED_APIS, ALLOWED_EXTENSIONS, MAX_FILE_SIZE
from ai_image_generator import create_image_generator

# V2阶段：导入批量任务相关模块
from task_manager import task_manager, TaskStatus
from tasks import process_batch_task

# 导入每日限额管理器
from daily_limit_manager import daily_limit_manager

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE
CORS(app)  # 启用CORS支持

# 配置Gemini API - 使用新的google-genai包
# 注意：现在只使用用户提供的API key，不再使用配置文件中的
# client = genai.Client(api_key=GEMINI_API_KEY)  # 已禁用，只能使用用户配置的API key

# 确保目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_image_with_gemini(image_path, prompt, api_key=None):
    """使用Gemini API生成图片（已废弃，现在使用AIImageGenerator）"""
    # 这个函数已经不再使用，保留只是为了兼容性
    # 现在所有生成都通过 AIImageGenerator 进行
    return {
        "success": False,
        "error": "此接口已废弃，请使用批量生成接口"
    }

@app.route('/api/generate', methods=['POST'])
def generate_image():
    """单图生成接口"""
    try:
        # 检查每日限额（使用IP地址作为用户标识）
        user_id = request.remote_addr or 'unknown'
        allowed, used_count, remaining = daily_limit_manager.check_and_increment(user_id, image_count=1)
        if not allowed:
            return jsonify({
                'success': False,
                'error': f'今日生成限额已用完（已使用{used_count}张，每日限额100张）。请明天再试。'
            }), 429
        
        # 检查是否有文件
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        prompt = request.form.get('prompt', '')
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type'}), 400
        
        if not prompt.strip():
            return jsonify({'error': 'Prompt is required'}), 400
        
        # 保存上传的文件
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        file.save(file_path)
        
        # 调用Gemini API（使用统一的AIImageGenerator）
        # 获取API key
        # 获取API key（可选，如果没有则使用服务器配置的）
        api_key, api_type = get_api_key_from_request()
        
        from ai_image_generator import create_image_generator
        # 如果没有提供API key，传递None，让create_image_generator使用服务器配置的
        generator = create_image_generator('gemini', api_key if api_key else None)
        with open(file_path, 'rb') as f:
            file_data = f.read()
        result = generator.generate_image(file_data, prompt)
        
        if result['success']:
            response_data = {
                'success': True,
                'original_url': f'/static/uploads/{unique_filename}',
                'description': result['description'],
                'note': result['note']
            }
            
            # 如果有生成的图像，添加图像URL
            if 'generated_image_url' in result:
                response_data['generated_image_url'] = result['generated_image_url']
            else:
                # 保存结果描述到文件（如果没有生成图像）
                result_filename = f"result_{uuid.uuid4()}.txt"
                result_path = os.path.join(RESULT_FOLDER, result_filename)
                with open(result_path, 'w', encoding='utf-8') as f:
                    f.write(result['description'])
                response_data['result_url'] = f'/static/results/{result_filename}'
            
            return jsonify(response_data)
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
            
    except Exception as e:
        error_msg = str(e)
        app.logger.error(f"Generate image error: {error_msg}")
        return jsonify({'success': False, 'error': f'生成失败: {error_msg}'}), 500

@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    """提供上传文件的访问"""
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/static/results/<filename>')
def result_file(filename):
    """提供结果文件的访问"""
    return send_from_directory(RESULT_FOLDER, filename)

@app.route('/api/health')
def health_check():
    """健康检查接口"""
    return jsonify({'status': 'healthy', 'message': 'BatchGen Pro MVP is running'})

def get_session_id_or_abort():
    session_id = request.headers.get('X-Session-ID')
    if not session_id:
        return None
    return session_id

def get_api_key_from_request():
    """从请求header中获取API key和类型"""
    api_key = request.headers.get('X-API-Key')
    # 如果api_key是空字符串，转换为None，以便使用服务器配置的key
    if api_key and api_key.strip():
        api_key = api_key.strip()
    else:
        api_key = None
    api_type = request.headers.get('X-API-Type', 'gemini')
    return api_key, api_type

# ==================== V2阶段：批量生成API ====================

@app.route('/api/batch/generate', methods=['POST'])
def create_batch_task():
    """创建批量生成任务"""
    session_id = get_session_id_or_abort()
    if not session_id:
        return jsonify({'error': '缺少 Session-ID'}), 400
    
    # 获取API key（可选，如果没有则使用服务器配置的）
    api_key, api_type = get_api_key_from_request()
    
    try:
        # 检查是否有文件
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        prompt = request.form.get('prompt', '')
        api_type = request.form.get('api_type', 'gemini')
        
        if not files or all(file.filename == '' for file in files):
            return jsonify({'error': 'No files selected'}), 400
        
        if not prompt.strip():
            return jsonify({'error': 'Prompt is required'}), 400
        
        if api_type not in SUPPORTED_APIS:
            return jsonify({'error': f'Unsupported API type: {api_type}'}), 400
        
        # 验证文件
        valid_files = []
        for file in files:
            if file and file.filename and allowed_file(file.filename):
                valid_files.append(file)
        
        if not valid_files:
            return jsonify({'error': 'No valid files provided'}), 400
        
        # 检查每日限额（使用session_id作为用户标识）
        image_count = len(valid_files)
        allowed, used_count, remaining = daily_limit_manager.check_and_increment(session_id, image_count=image_count)
        if not allowed:
            return jsonify({
                'success': False,
                'error': f'今日生成限额不足（已使用{used_count}张，剩余{remaining}张，需要{image_count}张，每日限额100张）。请明天再试。'
            }), 429
        
        # 准备图片数据
        images_data = []
        for file in valid_files:
            filename = secure_filename(file.filename)
            file_id = str(uuid.uuid4())
            new_filename = f"{file_id}_{filename}"
            
            # 保存文件
            file_path = os.path.join(UPLOAD_FOLDER, new_filename)
            file.save(file_path)
            
            # 读取文件数据
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            images_data.append({
                'filename': filename,
                'file_data': file_data,
                'file_path': file_path
            })
        
        # 创建批量任务
        task_id, task_data = task_manager.create_task(session_id, images_data, prompt, api_type)
        
        # 添加items字段，让前端能够显示所有任务项
        task_data['items'] = []
        for i, image in enumerate(images_data):
            task_data['items'].append({
                'index': i,
                'prompt': prompt,
                'status': 'pending'
            })
        
        # 更新任务状态为处理中，并保存items
        task_manager.update_task_status(session_id, task_id, TaskStatus.PROCESSING, items=task_data['items'])
        
        # 获取API key和模型名称
        api_key, request_api_type = get_api_key_from_request()
        # 如果header中有api_type，优先使用header中的
        if request_api_type:
            api_type = request_api_type
        
        # 获取模型名称
        model_name = request.form.get('model_name')
        
        # 暂时使用同步处理，避免Celery复杂性
        try:
            # 直接调用处理函数
            from tasks import process_batch_task_sync
            result = process_batch_task_sync(session_id, task_id, images_data, prompt, api_type, api_key, model_name)
            
            if result['success']:
                task_manager.update_task_status(session_id, task_id, TaskStatus.COMPLETED)
            else:
                task_manager.update_task_status(session_id, task_id, TaskStatus.FAILED)
        except Exception as e:
            app.logger.error(f"Batch processing error: {str(e)}")
            task_manager.update_task_status(session_id, task_id, TaskStatus.FAILED)
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': f'批量任务已创建，共{len(images_data)}张图片',
            'task_data': task_data
        })
        
    except Exception as e:
        app.logger.error(f"Create batch task error: {str(e)}")
        return jsonify({'success': False, 'error': f'创建任务失败: {str(e)}'}), 500

@app.route('/api/batch/generate-from-image', methods=['POST'])
def create_batch_generate_task():
    """创建批量生图任务（同一参考图重复生成N次）"""
    session_id = get_session_id_or_abort()
    if not session_id:
        return jsonify({'error': '缺少 Session-ID'}), 400
    
    # 获取API key（可选，如果没有则使用服务器配置的）
    api_key, api_type = get_api_key_from_request()
    
    try:
        prompt = request.form.get('prompt', '')
        image_count = int(request.form.get('image_count', 1))
        api_type = request.form.get('api_type', 'gemini')
        
        if not prompt.strip():
            return jsonify({'error': 'Prompt is required'}), 400
        
        if image_count < 1 or image_count > 10:
            return jsonify({'error': 'Image count must be between 1 and 10'}), 400
        
        if api_type not in SUPPORTED_APIS:
            return jsonify({'error': f'Unsupported API type: {api_type}'}), 400
        
        # 检查每日限额（使用session_id作为用户标识）
        allowed, used_count, remaining = daily_limit_manager.check_and_increment(session_id, image_count=image_count)
        if not allowed:
            return jsonify({
                'success': False,
                'error': f'今日生成限额不足（已使用{used_count}张，剩余{remaining}张，需要{image_count}张，每日限额100张）。请明天再试。'
            }), 429
        
        # 参考图是可选的
        reference_image_data = None
        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename and allowed_file(file.filename):
                # 保存参考图片
                filename = secure_filename(file.filename)
                file_id = str(uuid.uuid4())
                new_filename = f"{file_id}_{filename}"
                file_path = os.path.join(UPLOAD_FOLDER, new_filename)
                file.save(file_path)
                
                # 读取参考图数据
                with open(file_path, 'rb') as f:
                    reference_image_data = f.read()
        
        # 创建虚拟的images_data用于任务管理
        images_data = [{'filename': f'generated_{i+1}.png'} for i in range(image_count)]
        
        # 创建批量任务
        task_id, task_data = task_manager.create_task(session_id, images_data, prompt, api_type)
        
        # 添加items字段，让前端能够显示所有任务项
        task_data['items'] = []
        for i in range(image_count):
            task_data['items'].append({
                'index': i,
                'prompt': prompt,
                'status': 'pending'
            })
        
        # 更新任务状态为处理中，并保存items
        task_manager.update_task_status(session_id, task_id, TaskStatus.PROCESSING, items=task_data['items'])
        
        # 获取API key和模型名称
        api_key, request_api_type = get_api_key_from_request()
        # 如果header中有api_type，优先使用header中的
        if request_api_type:
            api_type = request_api_type
        
        # 获取模型名称
        model_name = request.form.get('model_name')
        
        # 同步处理批量生图
        try:
            from tasks import process_batch_generate_sync
            result = process_batch_generate_sync(session_id, task_id, reference_image_data, prompt, image_count, api_type, api_key, model_name)
            
            if result['success']:
                task_manager.update_task_status(session_id, task_id, TaskStatus.COMPLETED)
            else:
                task_manager.update_task_status(session_id, task_id, TaskStatus.FAILED)
        except Exception as e:
            app.logger.error(f"Batch generate processing error: {str(e)}")
            task_manager.update_task_status(session_id, task_id, TaskStatus.FAILED)
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': f'批量生图任务已创建，将生成{image_count}张图片',
            'task_data': task_data
        })
        
    except Exception as e:
        app.logger.error(f"Create batch generate task error: {str(e)}")
        return jsonify({'success': False, 'error': f'创建任务失败: {str(e)}'}), 500

@app.route('/api/batch/generate-with-prompts', methods=['POST'])
def create_batch_generate_multi_prompt_task():
    """创建批量生图任务（支持多个不同的prompt）"""
    session_id = get_session_id_or_abort()
    if not session_id:
        return jsonify({'error': '缺少 Session-ID'}), 400
    
    # 获取API key（可选，如果没有则使用服务器配置的）
    api_key, api_type = get_api_key_from_request()
    
    try:
        import json
        
        # 获取prompts列表
        prompts_str = request.form.get('prompts', '')
        api_type = request.form.get('api_type', 'gemini')
        
        if not prompts_str:
            return jsonify({'error': 'Prompts are required'}), 400
        
        try:
            prompts = json.loads(prompts_str)
        except:
            return jsonify({'error': 'Invalid prompts format'}), 400
        
        if not isinstance(prompts, list) or len(prompts) == 0:
            return jsonify({'error': 'Prompts must be a non-empty list'}), 400
        
        if len(prompts) > 10:
            return jsonify({'error': 'Maximum 10 prompts allowed'}), 400
        
        if api_type not in SUPPORTED_APIS:
            return jsonify({'error': f'Unsupported API type: {api_type}'}), 400
        
        # 检查每日限额（使用session_id作为用户标识）
        image_count = len(prompts)
        allowed, used_count, remaining = daily_limit_manager.check_and_increment(session_id, image_count=image_count)
        if not allowed:
            return jsonify({
                'success': False,
                'error': f'今日生成限额不足（已使用{used_count}张，剩余{remaining}张，需要{image_count}张，每日限额100张）。请明天再试。'
            }), 429
        
        # 参考图是可选的
        reference_image_data = None
        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename and allowed_file(file.filename):
                # 保存参考图片
                filename = secure_filename(file.filename)
                file_id = str(uuid.uuid4())
                new_filename = f"{file_id}_{filename}"
                file_path = os.path.join(UPLOAD_FOLDER, new_filename)
                file.save(file_path)
                
                # 读取参考图数据
                with open(file_path, 'rb') as f:
                    reference_image_data = f.read()
        
        # 创建虚拟的images_data用于任务管理
        images_data = [{'filename': f'generated_{i+1}.png'} for i in range(len(prompts))]
        
        # 创建批量任务（使用第一个prompt作为任务prompt）
        task_id, task_data = task_manager.create_task(session_id, images_data, prompts[0], api_type)
        
        # 立即添加每个item的prompt信息，让前端能够显示
        task_data['items'] = []
        for i, prompt in enumerate(prompts):
            task_data['items'].append({
                'index': i,
                'prompt': prompt,
                'status': 'pending'
            })
        
        # 保存items到Redis
        task_manager.update_task_status(session_id, task_id, TaskStatus.PROCESSING, items=task_data['items'])
        
        # 获取API key和模型名称
        api_key, request_api_type = get_api_key_from_request()
        # 如果header中有api_type，优先使用header中的
        if request_api_type:
            api_type = request_api_type
        
        # 获取模型名称
        model_name = request.form.get('model_name')
        
        # 同步处理批量生图（使用多个prompt）
        try:
            from tasks import process_batch_generate_multi_prompt_sync
            result = process_batch_generate_multi_prompt_sync(session_id, task_id, reference_image_data, prompts, api_type, api_key, model_name)
            
            if result['success']:
                task_manager.update_task_status(session_id, task_id, TaskStatus.COMPLETED)
            else:
                task_manager.update_task_status(session_id, task_id, TaskStatus.FAILED)
        except Exception as e:
            app.logger.error(f"Batch generate multi-prompt processing error: {str(e)}")
            task_manager.update_task_status(session_id, task_id, TaskStatus.FAILED)
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': f'批量生图任务已创建，将生成{len(prompts)}张图片',
            'task_data': task_data
        })
        
    except Exception as e:
        app.logger.error(f"Create batch generate multi-prompt task error: {str(e)}")
        return jsonify({'success': False, 'error': f'创建任务失败: {str(e)}'}), 500

@app.route('/api/batch/tasks', methods=['GET'])
def get_batch_tasks():
    """获取所有批量任务列表"""
    session_id = get_session_id_or_abort()
    if not session_id:
        return jsonify({'success': False, 'error': '缺少 Session-ID'}), 400
    try:
        tasks = task_manager.get_all_tasks(session_id)
        return jsonify({
            'success': True,
            'tasks': tasks
        })
    except redis.ConnectionError as e:
        app.logger.error(f"Redis connection error: {str(e)}")
        return jsonify({'success': False, 'error': 'Redis连接失败，请检查Redis服务是否运行'}), 500
    except Exception as e:
        app.logger.error(f"Get batch tasks error: {str(e)}")
        import traceback
        app.logger.error(traceback.format_exc())
        return jsonify({'success': False, 'error': f'获取任务列表失败: {str(e)}'}), 500

@app.route('/api/batch/tasks/<task_id>', methods=['GET'])
def get_batch_task(task_id):
    """获取特定任务详情"""
    session_id = get_session_id_or_abort()
    if not session_id:
        return jsonify({'success': False, 'error': '缺少 Session-ID'}), 400
    try:
        task_data = task_manager.get_task(task_id, session_id)
        if task_data:
            return jsonify({
                'success': True,
                'task': task_data
            })
        else:
            return jsonify({'success': False, 'error': '任务不存在'}), 404
    except Exception as e:
        app.logger.error(f"Get batch task error: {str(e)}")
        return jsonify({'success': False, 'error': f'获取任务详情失败: {str(e)}'}), 500

@app.route('/api/batch/tasks/<task_id>/status', methods=['GET'])
def get_batch_task_status(task_id):
    """获取任务状态"""
    session_id = get_session_id_or_abort()
    if not session_id:
        return jsonify({'success': False, 'error': '缺少 Session-ID'}), 400
    try:
        task_data = task_manager.get_task(task_id, session_id)
        if task_data:
            return jsonify({
                'success': True,
                'status': task_data['status'],
                'progress': task_data['progress'],
                'processed_images': task_data['processed_images'],
                'total_images': task_data['total_images']
            })
        else:
            return jsonify({'success': False, 'error': '任务不存在'}), 404
    except Exception as e:
        app.logger.error(f"Get batch task status error: {str(e)}")
        return jsonify({'success': False, 'error': f'获取任务状态失败: {str(e)}'}), 500

@app.route('/api/batch/tasks/<task_id>', methods=['DELETE'])
def cancel_batch_task(task_id):
    """取消任务"""
    session_id = get_session_id_or_abort()
    if not session_id:
        return jsonify({'success': False, 'error': '缺少 Session-ID'}), 400
    try:
        task_data = task_manager.cancel_task(task_id, session_id=session_id)
        if task_data:
            return jsonify({
                'success': True,
                'message': '任务已取消',
                'task': task_data
            })
        else:
            return jsonify({'success': False, 'error': '任务不存在'}), 404
    except Exception as e:
        app.logger.error(f"Cancel batch task error: {str(e)}")
        return jsonify({'success': False, 'error': f'取消任务失败: {str(e)}'}), 500

@app.route('/api/batch/tasks/<task_id>/results', methods=['GET'])
def get_batch_task_results(task_id):
    """获取任务结果"""
    session_id = get_session_id_or_abort()
    if not session_id:
        return jsonify({'success': False, 'error': '缺少 Session-ID'}), 400
    try:
        task_data = task_manager.get_task(task_id, session_id)
        if task_data:
            return jsonify({
                'success': True,
                'results': task_data['results'],
                'images': task_data['images']
            })
        else:
            return jsonify({'success': False, 'error': '任务不存在'}), 404
    except Exception as e:
        app.logger.error(f"Get batch task results error: {str(e)}")
        return jsonify({'success': False, 'error': f'获取任务结果失败: {str(e)}'}), 500

if __name__ == '__main__':
    # 检查是否为Docker环境
    is_docker = os.path.exists('/.dockerenv')
    debug_mode = os.getenv('FLASK_ENV') != 'production'
    
    app.run(
        debug=debug_mode, 
        host='0.0.0.0', 
        port=int(os.getenv('PORT', 5001))
    )
