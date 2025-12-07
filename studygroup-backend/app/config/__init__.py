import os
from datetime import timedelta

# 基础路径配置
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 数据库配置（优先环境变量，支持部署灵活配置）
MYSQL_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "port": int(os.getenv("MYSQL_PORT", 3306)),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", ""),
    "db": "study_group_hub",
    "charset": "utf8mb4"
}

# 文件上传配置
UPLOAD_CONFIG = {
    "BASE_PATH": os.path.join(BASE_DIR, "static/uploads"),
    "ALLOWED_TYPES": [".docx", ".pdf", ".ppt", ".pptx", ".xlsx", ".xls", ".jpg", ".png", ".txt"],
    "MAX_SIZE_KB": 1024 * 5,  # 5MB
    "STORE_NAME_RULE": "{group_id}_{timestamp}{suffix}"  # 存储文件名规则
}

# Flask应用配置
FLASK_CONFIG = {
    "SECRET_KEY": os.getenv("SECRET_KEY", "study_group_hub_2025_secure_key"),
    "DEBUG": os.getenv("FLASK_DEBUG", "True") == "True",
    "PERMANENT_SESSION_LIFETIME": timedelta(days=7),
    "JSON_AS_ASCII": False  # 支持中文JSON响应
}

# 权限配置（可扩展角色）
PERMISSION_CONFIG = {
    "REQUIRE_MEMBER": ["file_delete", "task_update", "group_member_query"],
    "REQUIRE_LEADER": ["group_delete", "task_assign", "member_remove"]
}

# 前端配置（供前端引用，保持前后端一致）
FRONTEND_CONFIG = {
    "API_BASE_URL": "/api",
    "MAX_FILE_SIZE_KB": UPLOAD_CONFIG["MAX_SIZE_KB"],
    "ALLOWED_FILE_TYPES": UPLOAD_CONFIG["ALLOWED_TYPES"]
}