#!/usr/bin/env python3
"""
豆包API客户端
根据官方文档：https://www.volcengine.com/docs/82379/1541523
"""
import requests
import json
import base64
import io
from PIL import Image
import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.api_keys import DOUBAO_API_KEY, DOUBAO_MODEL

class DoubaoAPIClient:
    def __init__(self, api_key=None, model=None):
        self.api_key = api_key or DOUBAO_API_KEY
        self.model = model or DOUBAO_MODEL
        self.base_url = "https://ark.cn-beijing.volces.com/api/v3"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def generate_image(self, image_data, prompt):
        """
        使用豆包API生成图片
        
        Args:
            image_data: 图片的二进制数据
            prompt: 生成提示词
            
        Returns:
            dict: 包含生成结果的字典
        """
        try:
            # 将图片转换为base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # 构造请求数据
            request_data = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"请根据我的图片和以下要求生成新图片：{prompt}"
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 1000,
                "temperature": 0.7
            }
            
            # 发送请求
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=request_data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return self._process_response(result, prompt)
            else:
                return {
                    "success": False,
                    "error": f"API请求失败: {response.status_code} - {response.text}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"豆包API调用失败: {str(e)}"
            }
    
    def _process_response(self, response_data, prompt):
        """
        处理豆包API响应
        
        Args:
            response_data: API响应数据
            prompt: 原始提示词
            
        Returns:
            dict: 处理后的结果
        """
        try:
            if "choices" in response_data and len(response_data["choices"]) > 0:
                choice = response_data["choices"][0]
                if "message" in choice and "content" in choice["message"]:
                    content = choice["message"]["content"]
                    
                    # 检查是否包含图片
                    if isinstance(content, str):
                        # 纯文本响应
                        return {
                            "success": True,
                            "description": content,
                            "generated_image_url": None,
                            "note": "豆包API返回文本描述，未生成图片"
                        }
                    elif isinstance(content, list):
                        # 多模态响应
                        for item in content:
                            if item.get("type") == "image_url":
                                # 处理图片URL
                                image_url = item["image_url"]["url"]
                                return self._save_generated_image(image_url, prompt)
                    
                    return {
                        "success": True,
                        "description": str(content),
                        "generated_image_url": None,
                        "note": "豆包API返回内容，但未识别到图片"
                    }
            
            return {
                "success": False,
                "error": "豆包API响应格式异常"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"处理豆包API响应失败: {str(e)}"
            }
    
    def _save_generated_image(self, image_url, prompt):
        """
        保存生成的图片
        
        Args:
            image_url: 图片URL或base64数据
            prompt: 原始提示词
            
        Returns:
            dict: 保存结果
        """
        try:
            import uuid
            from config.api_keys import RESULT_FOLDER
            
            # 确保结果目录存在
            os.makedirs(RESULT_FOLDER, exist_ok=True)
            
            # 生成文件名
            generated_filename = f"doubao_generated_{uuid.uuid4()}.png"
            generated_path = os.path.join(RESULT_FOLDER, generated_filename)
            
            if image_url.startswith("data:image"):
                # base64数据
                header, data = image_url.split(",", 1)
                image_data = base64.b64decode(data)
                with open(generated_path, 'wb') as f:
                    f.write(image_data)
            else:
                # URL数据
                img_response = requests.get(image_url, timeout=30)
                if img_response.status_code == 200:
                    with open(generated_path, 'wb') as f:
                        f.write(img_response.content)
                else:
                    return {
                        "success": False,
                        "error": f"下载图片失败: {img_response.status_code}"
                    }
            
            return {
                "success": True,
                "description": f"成功使用豆包API生成图片: {prompt}",
                "generated_image_url": f"/static/results/{generated_filename}",
                "note": "图片已使用豆包API生成"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"保存生成图片失败: {str(e)}"
            }

# 测试函数
def test_doubao_api():
    """测试豆包API"""
    client = DoubaoAPIClient()
    
    # 读取测试图片
    test_image_path = "/Users/wesley/Desktop/Repos/BatchGen Pro/test_image.png"
    if os.path.exists(test_image_path):
        with open(test_image_path, 'rb') as f:
            image_data = f.read()
        
        result = client.generate_image(image_data, "添加一朵花")
        print("豆包API测试结果:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("测试图片不存在")

if __name__ == "__main__":
    test_doubao_api()
