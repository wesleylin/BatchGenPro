# API配置
GEMINI_API_KEY = "AIzaSyBe1CcdEtm6n--UTp6rXvErKfl3ZZK_Igs"
GEMINI_MODEL = "gemini-2.5-flash-image"

# 豆包API配置
DOUBAO_API_KEY = "0dd3cffa-9dad-4514-a732-3ff5a93e8122"
DOUBAO_MODEL = "doubao-seedream-4-0-250828"
DOUBAO_WATERMARK = False  # 是否添加水印，False=不添加，True=添加"AI生成"水印

# 文件存储配置
UPLOAD_FOLDER = "uploads"
RESULT_FOLDER = "results"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# 允许的文件类型
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# API选择配置
DEFAULT_API = "gemini"  # 默认使用Gemini
SUPPORTED_APIS = ["gemini", "doubao"]
