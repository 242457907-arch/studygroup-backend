from flask import Flask, send_from_directory
from flask_cors import CORS  # 如果还没安装，运行: pip install flask-cors
from app.config import FLASK_CONFIG, UPLOAD_CONFIG
import os

# 初始化Flask应用
app = Flask(__name__, static_folder='static', template_folder='templates')
# 加载配置
app.config.update(FLASK_CONFIG)

# 启用CORS（允许跨域请求）
CORS(app, resources={r"/api/*": {"origins": "*"}})

# 设置文件上传配置
app.config['UPLOAD_FOLDER'] = UPLOAD_CONFIG["BASE_PATH"]
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB限制

# 创建上传目录（不存在则自动生成）
if not os.path.exists(UPLOAD_CONFIG["BASE_PATH"]):
    os.makedirs(UPLOAD_CONFIG["BASE_PATH"])

# 注册蓝图（按模块划分）
from app.user.views import user_blueprint
from app.group.views import group_blueprint
from app.task.views import task_blueprint
from app.file.views import file_blueprint

app.register_blueprint(user_blueprint, url_prefix='/api/user')
app.register_blueprint(group_blueprint, url_prefix='/api/group')
app.register_blueprint(task_blueprint, url_prefix='/api/task')
app.register_blueprint(file_blueprint, url_prefix='/api/file')


# 注册前端页面路由（直接访问HTML页面）
@app.route('/')
def index():
    return app.send_static_file('pages/login.html')

@app.route('/<path:filename>')
def static_pages(filename):
    try:
        return send_from_directory(app.static_folder, f'pages/{filename}')
    except:
        return "页面不存在", 404