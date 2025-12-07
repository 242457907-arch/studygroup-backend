# app/routes.py
from . import app  # 导入 app 实例

# 首页路由（访问 / 时触发）
@app.route('/')
def index():
    return "<h1>Study Group Hub 启动成功！🎉</h1><p>虚拟环境配置完成，Flask 服务正常运行~</p>"