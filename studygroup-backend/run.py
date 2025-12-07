from app import app

if __name__ == "__main__":
    # 启动Flask服务（开发环境）
    app.run(
        host='0.0.0.0',  # 允许局域网访问
        port=5000,        # 端口（可修改）
        debug=app.config['DEBUG']  # 调试模式（生产环境关闭）
    )