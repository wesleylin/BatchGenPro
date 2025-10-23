from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import uuid
import sys
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

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE
CORS(app)  # 启用CORS支持

# 配置Gemini API - 使用新的google-genai包
client = genai.Client(api_key=GEMINI_API_KEY)

# 确保目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_image_with_gemini(image_path, prompt):
    """使用Gemini API生成图片"""
    try:
        # 读取图片
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        # 转换为PIL Image
        image = Image.open(io.BytesIO(image_data))
        
        # 构建提示词 - 使用图像编辑模式
        full_prompt = f"Create a picture of my image with the following changes: {prompt}"
        
        # 使用Gemini 2.5 Flash Image模型进行图像生成/编辑
        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=[full_prompt, image]
        )
        
        # 检查响应中是否有生成的图像
        generated_image = None
        description = ""
        
        for part in response.candidates[0].content.parts:
            if part.text is not None:
                description = part.text
            elif part.inline_data is not None:
                # 保存生成的图像
                generated_image = Image.open(io.BytesIO(part.inline_data.data))
                generated_filename = f"generated_{uuid.uuid4()}.png"
                generated_path = os.path.join(RESULT_FOLDER, generated_filename)
                generated_image.save(generated_path)
                
                return {
                    "success": True,
                    "description": description or f"Successfully generated image based on: {prompt}",
                    "generated_image_url": f'/static/results/{generated_filename}',
                    "note": "Image successfully generated using Gemini 2.5 Flash Image"
                }
        
        # 如果没有生成图像，返回描述
        return {
            "success": True,
            "description": description or f"Processed request: {prompt}",
            "note": "Request processed but no image was generated"
        }
        
    except Exception as e:
        error_msg = str(e)
        app.logger.error(f"Gemini API Error: {error_msg}")
        
        return {
            "success": False,
            "error": f"API调用失败: {error_msg}"
        }

@app.route('/api/generate', methods=['POST'])
def generate_image():
    """单图生成接口"""
    try:
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
        
        # 调用Gemini API
        result = generate_image_with_gemini(file_path, prompt)
        
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

# ==================== V2阶段：批量生成API ====================

@app.route('/api/batch/generate', methods=['POST'])
def create_batch_task():
    """创建批量生成任务"""
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
        task_id, task_data = task_manager.create_task(images_data, prompt, api_type)
        
        # 更新任务状态为处理中
        task_manager.update_task_status(task_id, TaskStatus.PROCESSING)
        
        # 暂时使用同步处理，避免Celery复杂性
        try:
            # 直接调用处理函数
            from tasks import process_batch_task_sync
            result = process_batch_task_sync(task_id, images_data, prompt, api_type)
            
            if result['success']:
                task_manager.update_task_status(task_id, TaskStatus.COMPLETED)
            else:
                task_manager.update_task_status(task_id, TaskStatus.FAILED)
        except Exception as e:
            app.logger.error(f"Batch processing error: {str(e)}")
            task_manager.update_task_status(task_id, TaskStatus.FAILED)
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': f'批量任务已创建，共{len(images_data)}张图片',
            'task_data': task_data
        })
        
    except Exception as e:
        app.logger.error(f"Create batch task error: {str(e)}")
        return jsonify({'success': False, 'error': f'创建任务失败: {str(e)}'}), 500

@app.route('/api/batch/tasks', methods=['GET'])
def get_batch_tasks():
    """获取所有批量任务列表"""
    try:
        tasks = task_manager.get_all_tasks()
        return jsonify({
            'success': True,
            'tasks': tasks
        })
    except Exception as e:
        app.logger.error(f"Get batch tasks error: {str(e)}")
        return jsonify({'success': False, 'error': f'获取任务列表失败: {str(e)}'}), 500

@app.route('/api/batch/tasks/<task_id>', methods=['GET'])
def get_batch_task(task_id):
    """获取特定任务详情"""
    try:
        task_data = task_manager.get_task(task_id)
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
    try:
        task_data = task_manager.get_task(task_id)
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
    try:
        task_data = task_manager.cancel_task(task_id)
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
    try:
        task_data = task_manager.get_task(task_id)
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
