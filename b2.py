import os
import requests
from b2sdk.v1 import InMemoryAccountInfo, B2Api
from flask import Flask, request, redirect, url_for, render_template_string
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
# 设置B2存储相关信息
B2_ACCOUNT_ID = "B2_ACCOUNT_ID"
B2_APPLICATION_KEY = "B2_APPLICATION_KEY"
B2_BUCKET_NAME = "B2_BUCKET_NAME"

# B2_ACCOUNT_ID = os.environ.get("B2_ACCOUNT_ID")
# B2_APPLICATION_KEY = os.environ.get("B2_APPLICATION_KEY")
# B2_BUCKET_NAME = os.environ.get("B2_BUCKET_NAME")

# 初始化Flask应用
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "your-secret-key")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'

# 初始化Flask-SQLAlchemy
db = SQLAlchemy(app)

# 初始化Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# B2认证
info = InMemoryAccountInfo()
b2_api = B2Api(info)
b2_api.authorize_account("production", B2_ACCOUNT_ID, B2_APPLICATION_KEY)
bucket = b2_api.get_bucket_by_name(B2_BUCKET_NAME)


# 用户模型
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)


# 创建数据库表
with app.app_context():
    db.create_all()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        hashed_password = generate_password_hash(password)
        user = User(username=username, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return '''
    <h1>注册</h1>
    <form method="post">
        <label for="username">用户名:</label>
        <input type="text" name="username">
        <br>
        <label for="password">密码:</label>
        <input type="password" name="password">
        <br><br>
        <input type="submit" value="注册">
    </form>
    '''


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            return "登录失败，请检查您的用户名和密码"
    return '''
    <h1>登录</h1>
    <form method="post">
    <label for="username">用户名:</label>
    <input type="text" name="username">
    <br>
    <label for="password">密码:</label>
    <input type="password" name="password">
    <br><br>
    <input type="submit" value="登录">
    </form>
    '''


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_files():
    if request.method == 'POST':
        uploaded_files = request.files.getlist('files[]')
        image_links = request.form.get('image_links', '').splitlines()
        image_urls = []
        html_image_links = []

    for file in uploaded_files:
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension in ['.jpg', '.jpeg', '.png', '.gif','.webp']:
            current_date = datetime.now().strftime('%Y/%m/%d/')
            b2_filename = current_date + file.filename
            bucket.upload_bytes(file.read(), b2_filename)
            b2_file_url = f'https://{B2_BUCKET_NAME}.s3.us-west-004.backblazeb2.com/{b2_filename}'
            image_urls.append(b2_file_url)
            html_image_links.append(f'<img src="{b2_file_url}" alt="{file.filename}" />')

    for image_url in image_links:
        try:
            response = requests.get(image_url)
            response.raise_for_status()
            file_extension = os.path.splitext(image_url)[1].lower()
            if file_extension in ['.jpg', '.jpeg', '.png', '.gif']:
                current_date = datetime.now().strftime('%Y/%m/%d/')
                filename = os.path.basename(image_url)
                b2_filename = current_date + filename
                bucket.upload_bytes(response.content, b2_filename)
                b2_file_url = f'https://{B2_BUCKET_NAME}.s3.us-west-002.backblazeb2.com/{b2_filename}'
                image_urls.append(b2_file_url)
                html_image_links.append(f'<img src="{b2_file_url}" alt="{filename}" />')
        except Exception as e:
            print(f"Error uploading {image_url}: {e}")
    if image_urls:
        return render_template_string('''
            <h1>图片已上传</h1>
            <ul>
            {% for url in image_urls %}
            <li><a href="{{ url }}" target="_blank">{{ url }}</a></li>
            {% endfor %}
            </ul>
            <p>HTML 图片链接:</p>
            <textarea id="htmlLinks" rows="10" cols="100" readonly>{% for link in html_image_links %}{{ link }}{% 
            endfor %}</textarea>
            <button onclick="copyLinks()">复制HTML链接</button>
            <script>
            function copyLinks() {
                const textarea = document.getElementById('htmlLinks');
                textarea.select();
                document.execCommand('copy');
            }
            </script>
            <p><a href="{{ url_for('index') }}">返回</a></p>
            ''', image_urls=image_urls, html_image_links=html_image_links)
    else:
        return redirect(url_for('index'))


@app.route('/')
@login_required
def index():
    return '''
    <!doctype html>
    <html>
    <head>
    <title>图片上传到B2存储</title>
    </head>
    <body>
    <h1>上传图片到B2存储</h1>
    <form action="/upload" method="post" enctype="multipart/form-data">
    <label for="files">选择文件上传：</label>
    <input type="file" name="files[]" multiple>
    <br><br>
    <label for="image_links">或粘贴图片链接（每行一个）：</label>
    <br>
    <textarea name="image_links" rows="10" cols="50"></textarea>
    <br><br>
    <input type="submit" value="上传">
    </form>
    <p><a href="{{ url_for('logout') }}">登出</a></p>
    </body>
    </html>
    '''
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)