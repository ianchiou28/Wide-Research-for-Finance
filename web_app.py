from flask import Flask, render_template, jsonify, request
import os
import sys
import logging
from dotenv import load_dotenv

load_dotenv()

sys.path.append('src')

# ============== 日志配置 ==============
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('web_app')


# ============== Flask 应用 ==============
# static_folder: Vite 构建的 assets 目录
# template_folder: Vue SPA 的 index.html 所在目录
app = Flask(__name__, static_folder="frontend/dist/assets", template_folder="frontend/dist")
app.static_url_path = "/assets"


# ============== 注册 Blueprint ==============
from web.routes.report import report_bp
from web.routes.hot_search import hot_search_bp
from web.routes.stock import stock_bp
from web.routes.crypto import crypto_bp
from web.routes.analysis import analysis_bp
from web.routes.system import system_bp

app.register_blueprint(report_bp)
app.register_blueprint(hot_search_bp)
app.register_blueprint(stock_bp)
app.register_blueprint(crypto_bp)
app.register_blueprint(analysis_bp)
app.register_blueprint(system_bp)

logger.info(f"已注册 {len(app.blueprints)} 个 Blueprint 模块")


# ============== 初始化 ==============
from web.helpers import init_database


if __name__ == '__main__':
    # 初始化数据库
    init_database()
    
    # 生产环境通过 gunicorn 启动，此处仅用于本地开发
    is_debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    
    app.run(
        debug=is_debug,
        host='0.0.0.0',  # 监听所有接口，允许容器间访问
        port=5000,
        threaded=True
    )
