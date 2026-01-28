import os
import json
import requests

def get_config():
    with open(os.path.join(os.path.dirname(__file__), '../config.json'), 'r', encoding='utf-8') as f:
        return json.load(f)

def save_pdf(url, save_dir='pdfs'):
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    base_name = url.split('/')[-1]
    local_filename = os.path.join(save_dir, base_name)
    # 若文件已存在则自动重命名
    count = 1
    name, ext = os.path.splitext(base_name)
    while os.path.exists(local_filename):
        local_filename = os.path.join(save_dir, f"{name}_{count}{ext}")
        count += 1
    try:
        r = requests.get(url, stream=True, timeout=20)
        r.raise_for_status()
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        return local_filename
    except Exception as e:
        print(f"PDF下载失败: {url} 错误: {e}")
        return None
