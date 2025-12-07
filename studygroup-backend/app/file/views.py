from flask import Blueprint, request, jsonify, send_from_directory, send_file
from app.utils.db_utils import query_one, query_all, execute_sql
from app.utils.file_utils import generate_store_name, save_uploaded_file, delete_physical_file, get_file_size_kb
from app.config import UPLOAD_CONFIG, PERMISSION_CONFIG
from werkzeug.utils import secure_filename
from datetime import datetime
import os
from typing import Dict, Any

file_blueprint = Blueprint('file', __name__)

@file_blueprint.route('/upload', methods=['POST'])
def upload_file() -> Dict[str, Any]:
    """文件上传"""
    # 接收参数
    upload_file = request.files.get('file')
    group_id = request.form.get('group_id')
    uploader_id = request.form.get('uploader_id')
    
    # 基础校验
    if not upload_file or not group_id or not uploader_id:
        return jsonify({"code": 400, "msg": "文件、小组ID、上传人ID不能为空"})
    if upload_file.filename == '':
        return jsonify({"code": 400, "msg": "请选择有效文件"})
    
    # 类型转换
    try:
        group_id = int(group_id)
        uploader_id = int(uploader_id)
    except:
        return jsonify({"code": 400, "msg": "小组ID、上传人ID必须为整数"})
    
    # 文件合法性校验
    original_filename = upload_file.filename
    file_suffix = os.path.splitext(original_filename)[1].lower()
    if file_suffix not in UPLOAD_CONFIG["ALLOWED_TYPES"]:
        allowed_str = ", ".join(UPLOAD_CONFIG["ALLOWED_TYPES"])
        return jsonify({"code": 400, "msg": f"支持文件类型：{allowed_str}"})
    
    # 大小校验
    file_size_kb = get_file_size_kb(upload_file)
    if file_size_kb > UPLOAD_CONFIG["MAX_SIZE_KB"]:
        return jsonify({"code": 400, "msg": f"文件最大{UPLOAD_CONFIG['MAX_SIZE_KB']}KB"})
    
    # 权限与关联数据校验
    is_member = query_one(
        "SELECT 1 FROM sg_user_group WHERE user_id = %s AND group_id = %s",
        (uploader_id, group_id)
    )
    if not is_member:
        return jsonify({"code": 403, "msg": "仅小组成员可上传文件"})
    
    group_exist = query_one("SELECT 1 FROM sg_group WHERE group_id = %s", (group_id,))
    if not group_exist:
        return jsonify({"code": 404, "msg": f"小组ID={group_id}不存在"})
    
    user_exist = query_one("SELECT 1 FROM sg_user WHERE user_id = %s", (uploader_id,))
    if not user_exist:
        return jsonify({"code": 404, "msg": f"上传人ID={uploader_id}不存在"})
    
    # 执行上传
    upload_time = datetime.now()
    physical_file_path = None
    
    try:
        # 生成存储文件名
        store_name = generate_store_name(
            group_id=group_id,
            original_filename=original_filename,
            rule=UPLOAD_CONFIG["STORE_NAME_RULE"]
        )
        
        # 保存文件
        physical_file_path = save_uploaded_file(
            upload_file=upload_file,
            base_path=UPLOAD_CONFIG["BASE_PATH"],
            group_id=group_id,
            store_name=store_name
        )
        
        # 写入数据库
        insert_sql = """
            INSERT INTO sg_file (original_name, store_name, file_size, upload_time, group_id, uploader_id)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        file_success, file_id = execute_sql(
            insert_sql, (original_filename, store_name, file_size_kb, upload_time, group_id, uploader_id)
        )
        
        if not file_success or not file_id:
            raise Exception("文件信息写入失败")
        
        # ⭐ 新增：更新成员统计
        try:
            from app.utils.stats_utils import update_stats
            # 获取任务统计
            task_sql = """
                SELECT 
                    COUNT(*) as total_tasks,
                    SUM(CASE WHEN status = '完成' THEN 1 ELSE 0 END) as completed_tasks
                FROM sg_task 
                WHERE leader_id = %s AND group_id = %s
            """
            task_stats = query_one(task_sql, (uploader_id, group_id))
            
            # 获取文件统计（包括新上传的文件）
            file_count_sql = "SELECT COUNT(*) as uploaded_files FROM sg_file WHERE uploader_id = %s AND group_id = %s"
            file_count = query_one(file_count_sql, (uploader_id, group_id))
            
            if task_stats and file_count:
                update_stats(
                    user_id=uploader_id,
                    group_id=group_id,
                    total_tasks=task_stats['total_tasks'] or 0,
                    completed_tasks=task_stats['completed_tasks'] or 0,
                    uploaded_files=file_count['uploaded_files'] or 0
                )
        except Exception as e:
            print(f"更新成员统计失败: {e}")
            # 不中断主流程
        
        return jsonify({
            "code": 200,
            "msg": "上传成功",
            "data": {"file_id": file_id, "original_name": original_filename}
        })
        
    except Exception as e:
        # 异常回滚：删除物理文件
        if physical_file_path and os.path.exists(physical_file_path):
            delete_physical_file(physical_file_path)
        return jsonify({"code": 500, "msg": f"上传失败：{str(e)}"})

@file_blueprint.route('/group/<int:group_id>', methods=['GET'])
def get_group_files(group_id: int) -> Dict[str, Any]:
    """查询小组文件列表"""
    # 校验小组存在
    group_exist = query_one("SELECT 1 FROM sg_group WHERE group_id = %s", (group_id,))
    if not group_exist:
        return jsonify({"code": 404, "msg": f"小组ID={group_id}不存在"})
    
    # 联表查询文件与上传人信息
    query_sql = """
        SELECT f.*, u.user_name AS uploader_name
        FROM sg_file f
        LEFT JOIN sg_user u ON f.uploader_id = u.user_id
        WHERE f.group_id = %s
        ORDER BY f.upload_time DESC
    """
    file_list = query_all(query_sql, (group_id,))
    if file_list is None:
        return jsonify({"code": 500, "msg": "文件查询失败"})
    
    # 格式化时间
    for file in file_list:
        file['upload_time'] = file['upload_time'].strftime("%Y-%m-%d %H:%M:%S")
    
    return jsonify({
        "code": 200,
        "msg": "查询成功",
        "data": file_list
    })

@file_blueprint.route('/download/<int:file_id>', methods=['GET'])
def download_file(file_id: int):
    """文件下载（权限校验）- 改进版"""
    # 获取用户ID
    request_user_id = request.args.get('user_id')
    if not request_user_id:
        return jsonify({"code": 401, "msg": "请传入user_id"})
    
    try:
        request_user_id = int(request_user_id)
    except:
        return jsonify({"code": 400, "msg": "user_id必须为整数"})
    
    # 查询文件信息
    file_info = query_one("""
        SELECT f.*, g.group_id 
        FROM sg_file f
        LEFT JOIN sg_group g ON f.group_id = g.group_id
        WHERE f.file_id = %s
    """, (file_id,))
    
    if not file_info:
        return jsonify({"code": 404, "msg": "文件不存在"})
    
    # 校验是否为小组成员
    is_member = query_one(
        "SELECT 1 FROM sg_user_group WHERE user_id = %s AND group_id = %s",
        (request_user_id, file_info['group_id'])
    )
    if not is_member:
        return jsonify({"code": 403, "msg": "无权限下载，仅小组成员可下载文件"})
    
    # 构建文件路径
    file_store_path = os.path.join(str(file_info['group_id']), file_info['store_name'])
    full_path = os.path.join(UPLOAD_CONFIG["BASE_PATH"], file_store_path)
    
    if not os.path.exists(full_path):
        return jsonify({"code": 404, "msg": "文件不存在或已被删除"})
    
    try:
        # 使用send_file并提供更明确的参数
        return send_file(
            full_path,
            as_attachment=True,
            download_name=file_info['original_name'],
            mimetype='application/octet-stream'  # 通用MIME类型
        )
    except Exception as e:
        return jsonify({"code": 500, "msg": f"文件下载失败: {str(e)}"})

@file_blueprint.route('/preview/<int:file_id>', methods=['GET'])
def preview_file(file_id: int):
    """文件预览（权限校验）- 新增接口"""
    # 获取用户ID
    request_user_id = request.args.get('user_id')
    if not request_user_id:
        return jsonify({"code": 401, "msg": "请传入user_id"})
    
    try:
        request_user_id = int(request_user_id)
    except:
        return jsonify({"code": 400, "msg": "user_id必须为整数"})
    
    # 查询文件信息
    file_info = query_one("""
        SELECT f.*, g.group_id 
        FROM sg_file f
        LEFT JOIN sg_group g ON f.group_id = g.group_id
        WHERE f.file_id = %s
    """, (file_id,))
    
    if not file_info:
        return jsonify({"code": 404, "msg": "文件不存在"})
    
    # 校验是否为小组成员
    is_member = query_one(
        "SELECT 1 FROM sg_user_group WHERE user_id = %s AND group_id = %s",
        (request_user_id, file_info['group_id'])
    )
    if not is_member:
        return jsonify({"code": 403, "msg": "无权限预览"})
    
    # 构建文件路径
    file_store_path = os.path.join(str(file_info['group_id']), file_info['store_name'])
    full_path = os.path.join(UPLOAD_CONFIG["BASE_PATH"], file_store_path)
    
    if not os.path.exists(full_path):
        return jsonify({"code": 404, "msg": "文件不存在或已被删除"})
    
    # 尝试确定MIME类型
    file_ext = os.path.splitext(file_info['original_name'])[1].lower()
    mime_types = {
        '.pdf': 'application/pdf',
        '.doc': 'application/msword',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.xls': 'application/vnd.ms-excel',
        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        '.ppt': 'application/vnd.ms-powerpoint',
        '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.txt': 'text/plain',
    }
    
    mimetype = mime_types.get(file_ext, 'application/octet-stream')
    
    try:
        # 对于图片和PDF，可以在浏览器中预览
        if file_ext in ['.pdf', '.jpg', '.jpeg', '.png', '.gif']:
            return send_file(
                full_path,
                as_attachment=False,  # 不强制下载
                download_name=file_info['original_name'],
                mimetype=mimetype
            )
        else:
            # 其他文件类型强制下载
            return send_file(
                full_path,
                as_attachment=True,
                download_name=file_info['original_name'],
                mimetype=mimetype
            )
    except Exception as e:
        return jsonify({"code": 500, "msg": f"文件预览失败: {str(e)}"})

@file_blueprint.route('/<int:file_id>', methods=['DELETE'])
def delete_file(file_id: int) -> Dict[str, Any]:
    """文件删除（权限校验）"""
    # 权限校验
    request_user_id = request.args.get('user_id')
    if not request_user_id:
        return jsonify({"code": 401, "msg": "请传入user_id"})
    
    try:
        request_user_id = int(request_user_id)
    except:
        return jsonify({"code": 400, "msg": "user_id必须为整数"})
    
    # 查询文件信息
    file_info = query_one("""
        SELECT f.*, g.group_id 
        FROM sg_file f
        LEFT JOIN sg_group g ON f.group_id = g.group_id
        WHERE f.file_id = %s
    """, (file_id,))
    
    if not file_info:
        return jsonify({"code": 404, "msg": "文件不存在"})
    
    # 校验是否为小组成员
    is_member = query_one(
        "SELECT 1 FROM sg_user_group WHERE user_id = %s AND group_id = %s",
        (request_user_id, file_info['group_id'])
    )
    
    # 注意：PERMISSION_CONFIG["REQUIRE_MEMBER"] 是一个列表，检查是否在列表中
    if not is_member and "file_delete" in PERMISSION_CONFIG["REQUIRE_MEMBER"]:
        return jsonify({"code": 403, "msg": "无权限删除"})
    
    # 执行删除
    physical_file_path = os.path.join(
        UPLOAD_CONFIG["BASE_PATH"],
        str(file_info['group_id']),
        file_info['store_name']
    )
    
    # 删除数据库记录
    delete_sql = "DELETE FROM sg_file WHERE file_id = %s"
    delete_success, _ = execute_sql(delete_sql, (file_id,))
    
    if not delete_success:
        return jsonify({"code": 500, "msg": "文件删除失败"})
    
    # 删除物理文件
    if os.path.exists(physical_file_path):
        delete_physical_file(physical_file_path)
    
    return jsonify({"code": 200, "msg": "文件删除成功"})