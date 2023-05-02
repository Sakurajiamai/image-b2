# !usr/bin/env python
# -*- coding:utf-8 _*-
"""
@Author:Sakurajima Mai
@Blog(个人博客地址): blog.ixacg.com
@Sakura:不积跬步无以至千里，不积小流无以成江海，程序人生的精彩需要坚持不懈地积累！
"""
import os
from datetime import datetime
from flask import Flask, request, render_template_string
from b2sdk.v1 import InMemoryAccountInfo, B2Api

B2_ACCOUNT_ID = "B2_ACCOUNT_ID"
B2_APPLICATION_KEY = "B2_APPLICATION_KEY"
B2_BUCKET_NAME = "B2_BUCKET_NAME"
# 初始化Flask应用
app = Flask(__name__)

# B2认证
info = InMemoryAccountInfo()
b2_api = B2Api(info)
b2_api.authorize_account("production", B2_ACCOUNT_ID, B2_APPLICATION_KEY)
bucket = b2_api.get_bucket_by_name(B2_BUCKET_NAME)

@app.route('/upload', methods=['POST'])
def upload_files():
    uploaded_files = request.files.getlist('files[]')
    image_links = []

    for file in uploaded_files:
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension in ['.jpg', '.jpeg', '.png', '.gif']:
            current_date = datetime.now().strftime('%Y/%m/%d/')
            b2_filename = current_date + file.filename
            bucket.upload_bytes(file.read(), b2_filename)
            b2_file_url = f'https://{B2_BUCKET_NAME}.s3.us-west-004.backblazeb2.com/{b2_filename}'
            image_links.append(b2_file_url)

    if image_links:
        return render_template_string('''
            <h1>图片已上传</h1>
            <ul>
            {% for link in image_links %}
                <li><a href="{{ link }}" target="_blank">{{ link }}</a></li>
            {% endfor %}
            </ul>
            <p><a href="{{ url_for('index') }}">返回</a></p>
            ''', image_links=image_links)
    else:
        return "上传失败，请重试"

@app.route('/')
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
        <input type="file" name="files[]" multiple>
        <input type="submit" value="上传">
      </form>
    </body>
    </html>
    '''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)