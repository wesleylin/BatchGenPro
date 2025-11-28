#!/usr/bin/env python3
"""
统一的AI图片生成API客户端
支持Gemini和豆包API
"""
import requests
import json
import base64
import io
import uuid
import os
import sys
from PIL import Image
from google import genai

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.api_keys import (
    GEMINI_API_KEY, GEMINI_MODEL, 
    DOUBAO_API_KEY, DOUBAO_MODEL, DOUBAO_WATERMARK,
    RESULT_FOLDER
)

class AIImageGenerator:
    """统一的AI图片生成器"""
    
    def __init__(self, api_type="gemini", api_key=None, model_name=None):
        self.api_type = api_type
        self.result_folder = RESULT_FOLDER
        
        # 确保结果目录存在
        os.makedirs(self.result_folder, exist_ok=True)
        
        if api_type == "gemini":
            self._init_gemini(api_key, model_name)
        elif api_type == "doubao":
            self._init_doubao(api_key, model_name)
        else:
            raise ValueError(f"不支持的API类型: {api_type}")
    
    def _init_gemini(self, api_key=None, model_name=None):
        """初始化Gemini客户端"""
        # 优先使用用户提供的API key，如果没有则使用服务器配置的
        final_api_key = api_key or GEMINI_API_KEY
        if not final_api_key:
            raise ValueError("Gemini API Key 未提供，请先配置 API Key")
        self.client = genai.Client(api_key=final_api_key)
        # 优先使用传入的model_name，否则使用配置文件中的
        self.model = model_name or GEMINI_MODEL
    
    def _init_doubao(self, api_key=None, model_name=None):
        """初始化豆包客户端"""
        # 优先使用用户提供的API key，如果没有则使用服务器配置的
        final_api_key = api_key or DOUBAO_API_KEY
        if not final_api_key:
            raise ValueError("豆包 API Key 未提供，请先配置 API Key")
        self.api_key = final_api_key
        # 优先使用传入的model_name，否则使用配置文件中的
        self.model = model_name or DOUBAO_MODEL
        self.watermark = DOUBAO_WATERMARK
        self.base_url = "https://ark.cn-beijing.volces.com/api/v3"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def generate_image(self, image_data, prompt):
        """
        生成图片的统一接口
        
        Args:
            image_data: 原始图片的二进制数据（可选，None表示纯文本生成）
            prompt: 生成提示词
            
        Returns:
            dict: 包含生成结果的字典
        """
        if self.api_type == "gemini":
            return self._generate_with_gemini(image_data, prompt)
        elif self.api_type == "doubao":
            return self._generate_with_doubao(image_data, prompt)
        else:
            return {
                "success": False,
                "error": f"不支持的API类型: {self.api_type}"
            }
    
    def _generate_with_gemini(self, image_data, prompt):
        """使用Gemini API生成图片"""
        try:
            # 根据是否有参考图选择不同的prompt
            if image_data:
                # 有参考图：图像编辑模式
                image = Image.open(io.BytesIO(image_data))
                full_prompt = f"Create a picture of my image with the following changes: {prompt}"
                contents = [full_prompt, image]
            else:
                # 无参考图：纯文本生成模式
                full_prompt = f"Create an image based on this description: {prompt}"
                contents = [full_prompt]
            
            # 调用Gemini API生成图片
            response = self.client.models.generate_content(
                model=self.model,
                contents=contents
            )
            
            # 处理响应
            if response and hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and candidate.content:
                    for part in candidate.content.parts:
                        if hasattr(part, 'inline_data') and part.inline_data:
                            # 保存生成的图片
                            generated_filename = f"gemini_generated_{uuid.uuid4()}.png"
                            generated_path = os.path.join(self.result_folder, generated_filename)
                            
                            with open(generated_path, 'wb') as f:
                                f.write(part.inline_data.data)
                            
                            return {
                                "success": True,
                                "description": f"成功使用Gemini API生成图片: {prompt}",
                                "generated_image_url": f"/static/results/{generated_filename}",
                                "api_type": "gemini",
                                "note": "图片已使用Gemini API生成"
                            }
            
            # 如果没有生成图片，返回描述
            return {
                "success": True,
                "description": f"Gemini处理了图片: {prompt}，但未生成新图片",
                "generated_image_url": None,
                "api_type": "gemini",
                "note": "Gemini API返回文本描述，未生成图片"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Gemini API调用失败: {str(e)}",
                "api_type": "gemini"
            }
    
    def _generate_with_doubao(self, image_data, prompt):
        """使用豆包API生成图片"""
        try:
            # 构造请求数据
            request_data = {
                "model": self.model,
                "size": "2K",
                "sequential_image_generation": "disabled",
                "stream": False,
                "response_format": "url",
                "watermark": self.watermark  # 使用配置的水印设置
            }
            
            # 根据是否有参考图选择不同的prompt
            if image_data:
                # 有参考图：图像编辑模式
                image_base64 = base64.b64encode(image_data).decode('utf-8')
                request_data["prompt"] = f"基于我的图片进行以下修改: {prompt}"
                request_data["image"] = f"data:image/png;base64,{image_base64}"
            else:
                # 无参考图：纯文本生成模式
                request_data["prompt"] = prompt
            
            # 发送请求
            response = requests.post(
                f"{self.base_url}/images/generations",
                headers=self.headers,
                json=request_data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return self._process_doubao_response(result, prompt)
            else:
                return {
                    "success": False,
                    "error": f"豆包API请求失败: {response.status_code} - {response.text}",
                    "api_type": "doubao"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"豆包API调用失败: {str(e)}",
                "api_type": "doubao"
            }
    
    def _process_doubao_response(self, response_data, prompt):
        """处理豆包API响应"""
        try:
            if "data" in response_data and len(response_data["data"]) > 0:
                image_data = response_data["data"][0]
                
                if "url" in image_data:
                    # 下载并保存图片
                    return self._save_doubao_image(image_data["url"], prompt)
                else:
                    return {
                        "success": False,
                        "error": "豆包API响应中未找到图片URL",
                        "api_type": "doubao"
                    }
            else:
                return {
                    "success": False,
                    "error": "豆包API响应格式异常",
                    "api_type": "doubao"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"处理豆包API响应失败: {str(e)}",
                "api_type": "doubao"
            }
    
    def _save_doubao_image(self, image_url, prompt):
        """保存豆包生成的图片"""
        try:
            # 下载图片
            img_response = requests.get(image_url, timeout=30)
            if img_response.status_code == 200:
                # 生成文件名
                generated_filename = f"doubao_generated_{uuid.uuid4()}.png"
                generated_path = os.path.join(self.result_folder, generated_filename)
                
                # 保存图片
                with open(generated_path, 'wb') as f:
                    f.write(img_response.content)
                
                return {
                    "success": True,
                    "description": f"成功使用豆包API生成图片: {prompt}",
                    "generated_image_url": f"/static/results/{generated_filename}",
                    "api_type": "doubao",
                    "note": "图片已使用豆包API生成"
                }
            else:
                return {
                    "success": False,
                    "error": f"下载豆包生成的图片失败: {img_response.status_code}",
                    "api_type": "doubao"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"保存豆包生成的图片失败: {str(e)}",
                "api_type": "doubao"
            }

# 工厂函数
def create_image_generator(api_type="gemini", api_key=None, model_name=None):
    """
    创建图片生成器实例
    
    Args:
        api_type: API类型 ("gemini" 或 "doubao")
        api_key: API密钥（可选，如果不提供则使用配置文件中的）
        model_name: 模型名称（可选，如果不提供则使用配置文件中的）
        
    Returns:
        AIImageGenerator: 图片生成器实例
    """
    return AIImageGenerator(api_type, api_key, model_name)

# 测试函数
def test_apis():
    """测试所有API"""
    test_image_path = "/Users/wesley/Desktop/Repos/BatchGen Pro/test_image.png"
    
    if not os.path.exists(test_image_path):
        print("测试图片不存在")
        return
    
    with open(test_image_path, 'rb') as f:
        image_data = f.read()
    
    # 测试Gemini
    print("=== 测试Gemini API ===")
    gemini_gen = create_image_generator("gemini")
    gemini_result = gemini_gen.generate_image(image_data, "添加一朵花")
    print(json.dumps(gemini_result, indent=2, ensure_ascii=False))
    
    print("\n=== 测试豆包API ===")
    doubao_gen = create_image_generator("doubao")
    doubao_result = doubao_gen.generate_image(image_data, "添加一朵花")
    print(json.dumps(doubao_result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    test_apis()
