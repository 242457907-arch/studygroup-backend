import os
from datetime import datetime

from app.config import UPLOAD_CONFIG

def generate_store_name(group_id: int, original_filename: str, rule: str) -> str:
    """生成唯一存储文件名（按配置规则）"""
    suffix = os.path.splitext(original_filename)[1].lower()
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    # 替换规则中的占位符
    return rule.format(
        group_id=group_id,
        timestamp=timestamp,
        suffix=suffix
    )

def save_uploaded_file(upload_file, base_path: str, group_id: int, store_name: str) -> str:
    """保存上传文件到小组目录"""
    # 按小组ID创建子目录
    group_dir = os.path.join(base_path, str(group_id))
    if not os.path.exists(group_dir):
        os.makedirs(group_dir)
    # 保存文件
    file_path = os.path.join(group_dir, store_name)
    upload_file.save(file_path)
    return file_path

def delete_physical_file(file_path: str) -> bool:
    """删除物理文件"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    except Exception as e:
        print(f"文件删除失败：{str(e)}")
        return False

def get_file_size_kb(file_obj) -> int:
    """获取文件大小（KB）"""
    # 处理Flask上传文件对象或本地文件路径
    if hasattr(file_obj, 'stream'):
        # Flask上传文件：移动指针到末尾获取大小
        file_obj.stream.seek(0, os.SEEK_END)
        size_byte = file_obj.stream.tell()
        file_obj.stream.seek(0)  # 重置指针，避免后续读取失败
    else:
        # 本地文件路径
        size_byte = os.path.getsize(file_obj)
    return int(size_byte / 1024)  # 转为KB