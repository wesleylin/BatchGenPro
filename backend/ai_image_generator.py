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
    GEMINI_MODEL, 
    DOUBAO_MODEL, DOUBAO_WATERMARK,
    RESULT_FOLDER
)

class AIImageGenerator:
    """统一的AI图片生成器"""
    
    def __init__(self, api_type="gemini", api_key=None, model_name=None, base_url=None):
        self.api_type = api_type
        self.result_folder = RESULT_FOLDER
        self.base_url = base_url  # 保存 base_url，用于第三方 API
        
        # 确保结果目录存在
        os.makedirs(self.result_folder, exist_ok=True)
        
        if api_type == "gemini":
            self._init_gemini(api_key, model_name, base_url)
        elif api_type == "doubao":
            self._init_doubao(api_key, model_name, base_url)
        else:
            raise ValueError(f"不支持的API类型: {api_type}")
    
    def _init_gemini(self, api_key=None, model_name=None, base_url=None):
        """初始化Gemini客户端"""
        # 必须使用用户提供的API key，不再使用服务器配置
        if not api_key or not api_key.strip() or api_key.strip() == "your_gemini_api_key_here":
            raise ValueError("Gemini API Key 未提供，请先在设置中配置 API Key")
        
        final_api_key = api_key.strip()
        
        self.api_key = final_api_key
        
        # 如果提供了 base_url，使用第三方 API（HTTP 请求）
        # 否则使用官方 API（genai.Client）
        if base_url and base_url.strip():
            self.use_custom_base_url = True
            # 清理 URL：去除末尾斜杠，并处理双斜杠问题
            cleaned_url = base_url.strip().rstrip('/')
            # 处理协议后的双斜杠（保留 http:// 或 https:// 后的双斜杠，但去除路径中的双斜杠）
            if '://' in cleaned_url:
                parts = cleaned_url.split('://', 1)
                protocol = parts[0]
                path = parts[1].replace('//', '/')  # 去除路径中的双斜杠
                self.custom_base_url = f"{protocol}://{path}"
            else:
                self.custom_base_url = cleaned_url.replace('//', '/')
            # 不使用 genai.Client，改用 HTTP 请求
            self.client = None
        else:
            self.use_custom_base_url = False
            self.custom_base_url = None
            self.client = genai.Client(api_key=final_api_key)
        
        # 优先使用传入的model_name，否则使用配置文件中的
        # 如果模型名称是 gemini-3-pro-image-preview，需要加上 models/ 前缀（仅官方API）
        if model_name:
            if model_name == 'gemini-3-pro-image-preview':
                # 官方API需要 models/ 前缀，第三方API保持原样
                if base_url and base_url.strip():
                    # 第三方API：保持原样
                    self.model = 'gemini-3-pro-image-preview'
                else:
                    # 官方API：加上 models/ 前缀
                    self.model = 'models/gemini-3-pro-image-preview'
            else:
                self.model = model_name
        else:
            self.model = GEMINI_MODEL
    
    def _init_doubao(self, api_key=None, model_name=None, base_url=None):
        """初始化豆包客户端"""
        # 必须使用用户提供的API key，不再使用服务器配置
        if not api_key or not api_key.strip() or api_key.strip() == "your_doubao_api_key_here":
            raise ValueError("豆包 API Key 未提供，请先在设置中配置 API Key")
        
        final_api_key = api_key.strip()
        self.api_key = final_api_key
        # 优先使用传入的model_name，否则使用配置文件中的
        self.model = model_name or DOUBAO_MODEL
        self.watermark = DOUBAO_WATERMARK
        # 如果提供了 base_url，使用自定义 URL，否则使用默认的官方 URL
        if base_url and base_url.strip():
            # 清理 URL：去除末尾斜杠，并处理双斜杠问题
            cleaned_url = base_url.strip().rstrip('/')
            # 处理协议后的双斜杠（保留 http:// 或 https:// 后的双斜杠，但去除路径中的双斜杠）
            if '://' in cleaned_url:
                parts = cleaned_url.split('://', 1)
                protocol = parts[0]
                path = parts[1].replace('//', '/')  # 去除路径中的双斜杠
                self.base_url = f"{protocol}://{path}"
            else:
                self.base_url = cleaned_url.replace('//', '/')
        else:
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
            # 如果使用自定义 base_url，使用 HTTP 请求（Google 原生 REST API 格式）
            if self.use_custom_base_url:
                return self._generate_with_gemini_http(image_data, prompt)
            
            # 否则使用官方 API（genai.Client）
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
    
    def _generate_with_gemini_http(self, image_data, prompt):
        """使用 HTTP 请求调用第三方 Gemini API（Google 原生 REST API 格式）"""
        try:
            # 构建请求 URL
            # 格式：{base_url}/v1beta/models/{model}:generateContent
            # 如果 base_url 已经包含 /v1beta，直接使用；否则添加
            if '/v1beta' in self.custom_base_url:
                endpoint = f"{self.custom_base_url}/models/{self.model}:generateContent"
            else:
                endpoint = f"{self.custom_base_url}/v1beta/models/{self.model}:generateContent"
            
            # 构建请求体
            if image_data:
                # 有参考图：图像编辑模式
                image_base64 = base64.b64encode(image_data).decode('utf-8')
                # 检测图片格式
                image = Image.open(io.BytesIO(image_data))
                mime_type = f"image/{image.format.lower()}" if image.format else "image/png"
                
                payload = {
                    "contents": [
                        {
                            "parts": [
                                {
                                    "text": f"Create a picture of my image with the following changes: {prompt}"
                                },
                                {
                                    "inlineData": {
                                        "mimeType": mime_type,
                                        "data": image_base64
                                    }
                                }
                            ]
                        }
                    ],
                    "generationConfig": {
                        "temperature": 0.7,
                        "maxOutputTokens": 4000,
                    }
                }
            else:
                # 无参考图：纯文本生成模式
                payload = {
                    "contents": [
                        {
                            "parts": [
                                {
                                    "text": f"Create an image based on this description: {prompt}"
                                }
                            ]
                        }
                    ],
                    "generationConfig": {
                        "temperature": 0.7,
                        "maxOutputTokens": 4000,
                    }
                }
            
            # 发送 HTTP 请求
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            }
            
            response = requests.post(
                endpoint,
                headers=headers,
                json=payload,
                timeout=600.0  # 10分钟超时
            )
            
            if response.status_code == 200:
                response_data = response.json()
                
                # 处理响应（Google 原生格式）
                if "candidates" in response_data and len(response_data["candidates"]) > 0:
                    candidate = response_data["candidates"][0]
                    if "content" in candidate and "parts" in candidate["content"]:
                        parts = candidate["content"]["parts"]
                        
                        for part in parts:
                            if "inlineData" in part:
                                inline_data = part["inlineData"]
                                data = inline_data.get("data", "")
                                
                                # 解码并保存图片
                                image_bytes = base64.b64decode(data)
                                generated_filename = f"gemini_generated_{uuid.uuid4()}.png"
                                generated_path = os.path.join(self.result_folder, generated_filename)
                                
                                with open(generated_path, 'wb') as f:
                                    f.write(image_bytes)
                                
                                return {
                                    "success": True,
                                    "description": f"成功使用第三方 Gemini API 生成图片: {prompt}",
                                    "generated_image_url": f"/static/results/{generated_filename}",
                                    "api_type": "gemini",
                                    "note": "图片已使用第三方 Gemini API 生成"
                                }
                
                # 如果没有生成图片，返回错误
                return {
                    "success": False,
                    "error": "第三方 Gemini API 响应中未找到图片数据",
                    "api_type": "gemini"
                }
            else:
                return {
                    "success": False,
                    "error": f"第三方 Gemini API 请求失败: {response.status_code} - {response.text}",
                    "api_type": "gemini"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"第三方 Gemini API 调用失败: {str(e)}",
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
            # 检查 base_url 是否已经包含 /images/generations 路径
            if '/images/generations' in self.base_url:
                # 如果已经包含完整路径，直接使用
                endpoint = self.base_url
            else:
                # 否则添加 /images/generations 路径
                endpoint = f"{self.base_url}/images/generations"
            
            response = requests.post(
                endpoint,
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
def create_image_generator(api_type="gemini", api_key=None, model_name=None, base_url=None):
    """
    创建图片生成器实例
    
    Args:
        api_type: API类型 ("gemini" 或 "doubao")
        api_key: API密钥（可选，如果不提供则使用配置文件中的）
        model_name: 模型名称（可选，如果不提供则使用配置文件中的）
        base_url: 自定义 base URL（可选，如果提供则使用第三方 API）
        
    Returns:
        AIImageGenerator: 图片生成器实例
    """
    return AIImageGenerator(api_type, api_key, model_name, base_url)

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
