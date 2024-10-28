import os
import re
import toml
from pathlib import Path
import boto3
from botocore.config import Config
import platform

def load_config(config_file):
    return toml.load(config_file)

def get_s3_client(endpoint_url, access_key, secret_key, region):
    s3_config = Config(
        region_name=region,
        signature_version='s3v4',
        retries={
            'max_attempts': 10,
            'mode': 'standard'
        }
    )

    s3_client = boto3.client(
        's3',
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=s3_config
    )

    return s3_client

def upload_image(s3_client, backup_s3_client, bucket_name, backup_bucket_name, image_path):
    file_name = os.path.basename(image_path)
    s3_key = file_name  # 上传到存储桶的根目录
    try:
        # 上传到主S3
        s3_client.upload_file(image_path, bucket_name, s3_key, ExtraArgs={'ACL': 'public-read'})
        print(f"图片上传成功到主S3: {image_path} -> s3://{bucket_name}/{s3_key}")
        # 上传到备份S3
        backup_s3_client.upload_file(image_path, backup_bucket_name, s3_key, ExtraArgs={'ACL': 'public-read'})
        print(f"图片上传成功到备份S3: {image_path} -> s3://{backup_bucket_name}/{s3_key}")
        return f'https://img.chlorinechan.top/{file_name}'
    except Exception as e:
        print(f"图片上传失败: {e}")
        return None


def collect_image_urls(markdown_file, image_directory, s3_client, backup_s3_client, bucket_name):
    image_urls = {}
    image_pattern = re.compile(r'!\[.*?\]\((.*?)\)')
    
    # 查找 Markdown 文件中的图片链接
    with open(markdown_file, 'r', encoding='utf-8') as file:
        content = file.read()
        matches = image_pattern.findall(content)
        for image_name in set(matches):
            image_path = Path(image_directory) / image_name
            if image_path.exists() and image_name not in image_urls:
                image_url = upload_image(s3_client, backup_s3_client, bucket_name, backup_bucket_name, image_path)

                if image_url:
                    image_urls[image_name] = image_url
    return image_urls

def update_markdown_file(markdown_file, image_urls, destination_directory):
    image_pattern = re.compile(r'!\[.*?\]\((.*?)\)')
    link_pattern = re.compile(r'\[\[(.*?)\|(.*?)\]\]')
    single_link_pattern = re.compile(r'\[\[(.*?)\]\]')

    with open(markdown_file, 'r', encoding='utf-8') as file:
        content = file.read()

    def replace_image_link(match):
        image_name = os.path.basename(match.group(1))
        return f'![{match.group(0).split("(")[0][2:-1]}](https://img.chlorinechan.top/{image_name})'

    content = image_pattern.sub(replace_image_link, content)

    # 替换 [[文件名|显示文本]] 为 Hugo 风格的短代码链接
    content = link_pattern.sub(r'[\2]({{< relref "\1.md" >}})', content)

    # 替换 [[文件名]] 为 Hugo 风格的短代码链接
    content = single_link_pattern.sub(r'[\1]({{< relref "\1.md" >}})', content)

    # 替换 GitHub 风格警告 为 Hugo 风格警告
    alert_pattern = re.compile(r'^>\s*\[!(.*?)\]\s*\n((?:>.*\n?)*)', re.MULTILINE)
    def replace_alert(match):
        alert_type = match.group(1).strip().lower()
        alert_content = match.group(2).replace('>', '').strip()
        return f'{{{{< alert "{alert_type}" >}}}}\n{alert_content}\n{{{{< /alert >}}}}\n'
    
    content = alert_pattern.sub(replace_alert, content)

    # 确保目标目录存在
    os.makedirs(destination_directory, exist_ok=True)

    # 确定目标文件路径
    destination_file = Path(destination_directory) / Path(markdown_file).name

    # 将替换后的内容写入目标文件
    with open(destination_file, 'w', encoding='utf-8') as file:
        file.write(content)

    print(f"文件已处理: {markdown_file} -> {destination_file}")

def find_latest_file(directory, extension):
    files = [f for f in Path(directory).glob(f'*{extension}') if f.is_file()]
    if not files:
        return None
    
    if platform.system() == 'Windows':
        def getctime(f):
            return f.stat().st_ctime
    else:
        def getctime(f):
            return f.stat().st_birthtime

    latest_file = max(files, key=getctime)
    return latest_file

if __name__ == "__main__":
    # 加载配置文件
    config = load_config('config.toml')

    # 配置路径
    path_a = config["source"]["origin_directory"]
    path_b = config["source"]["destination_directory"]
    image_directory = config["source"]["image_directory"]

    # 主S3 配置
    endpoint_url = config["s3"]["endpoint_url"]
    access_key = config["s3"]["access_key"]
    secret_key = config["s3"]["secret_key"]
    region = config["s3"]["region"]
    bucket_name = config["s3"]["bucket_name"]

    # 备份S3 配置
    backup_endpoint_url = config["backup_s3"]["endpoint_url"]
    backup_access_key = config["backup_s3"]["access_key"]
    backup_secret_key = config["backup_s3"]["secret_key"]
    backup_region = config["backup_s3"]["region"]
    backup_bucket_name = config["backup_s3"]["bucket_name"]

    # 获取S3客户端
    s3_client = get_s3_client(endpoint_url, access_key, secret_key, region)
    backup_s3_client = get_s3_client(backup_endpoint_url, backup_access_key, backup_secret_key, backup_region)

    # 查找最新的Markdown文件
    latest_file = find_latest_file(path_a, '.md')
    if latest_file:
        # 收集图片URL
        image_urls = collect_image_urls(latest_file, image_directory, s3_client, backup_s3_client, bucket_name)
        # 更新Markdown文件中的图片链接
        update_markdown_file(latest_file, image_urls, path_b)
    else:
        print("未找到Markdown文件")
