### 1.图片自动以年月份的格式上传到b2对象存储中

### 2.图片会自动生成html格式

### 3.需要用户登录才能上传图片

### 4.支持批量上传和批量复制图片地址上传

### 5.
#### 5.1 运行app.py 或者b2.py 需要用户登录才上传

#### 5.2 运行b2-1.py 或者b2-2.py 无需要用户登录


你需要正确更改以下性信息
```
B2_ACCOUNT_ID = "B2_ACCOUNT_ID"
B2_APPLICATION_KEY = "B2_APPLICATION_KEY"
B2_BUCKET_NAME = "B2_BUCKET_NAME"
```
你可能还需要修改b2地址
```
 b2_file_url = f'https://{B2_BUCKET_NAME}.s3.us-west-002.backblazeb2.com/{b2_filename}'

b2_file_url = f'https://{B2_BUCKET_NAME}.s3.us-west-002.backblazeb2.com/{b2_filename}'
```