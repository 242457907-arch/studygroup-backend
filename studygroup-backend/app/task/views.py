from flask import Blueprint, request, jsonify
from app.utils.db_utils import query_one, query_all, execute_sql
from app.utils.validate_utils import check_required_params, check_param_type, check_string_length
from app.config import PERMISSION_CONFIG
from datetime import datetime
from typing import Dict, Any

task_blueprint = Blueprint('task', __name__)

@task_blueprint.route('/create', methods=['POST'])
def create_task() -> Dict[str, Any]:
    """创建任务"""
    request_data = request.json or {}
    # 校验必填参数
    required_fields = ['task_desc', 'group_id', 'leader_id']
    is_param_valid, err_msg = check_required_params(request_data, required_fields)
    if not is_param_valid:
        return jsonify({"code": 400, "msg": err_msg})
    # 校验参数类型
    type_map = {'group_id': 'int', 'leader_id': 'int'}
    is_type_valid, type_err_msg = check_param_type(request_data, type_map)
    if not is_type_valid:
        return jsonify({"code": 400, "msg": type_err_msg})
    # 提取参数并校验
    task_desc = request_data['task_desc'].strip()
    group_id = request_data['group_id']
    leader_id = request_data['leader_id']
    # 校验任务描述长度
    is_len_valid, len_err_msg = check_string_length(task_desc, 1, 500, "任务描述")
    if not is_len_valid:
        return jsonify({"code": 400, "msg": len_err_msg})
    # 校验关联数据存在性
    group_exist = query_one("SELECT 1 FROM sg_group WHERE group_id = %s", (group_id,))
    if not group_exist:
        return jsonify({"code": 404, "msg": f"小组ID={group_id}不存在"})
    leader_exist = query_one("SELECT 1 FROM sg_user WHERE user_id = %s", (leader_id,))
    if not leader_exist:
        return jsonify({"code": 404, "msg": f"负责人ID={leader_id}不存在"})
    # 校验负责人是否为小组成员
    is_member = query_one(
        "SELECT 1 FROM sg_user_group WHERE user_id = %s AND group_id = %s",
        (leader_id, group_id)
    )
    if not is_member:
        return jsonify({"code": 403, "msg": "负责人必须是小组成员"})
    # 执行创建
    create_time = datetime.now()
    task_status = "待办"  # 默认状态
    insert_sql = """
        INSERT INTO sg_task (task_desc, create_time, status, group_id, leader_id)
        VALUES (%s, %s, %s, %s, %s)
    """
    task_success, task_id = execute_sql(
        insert_sql, (task_desc, create_time, task_status, group_id, leader_id)
    )
    if not task_success or not task_id:
        return jsonify({"code": 500, "msg": "任务创建失败"})
    return jsonify({
        "code": 200,
        "msg": "任务创建成功",
        "data": {"task_id": task_id, "status": task_status}
    })

@task_blueprint.route('/group/<int:group_id>', methods=['GET'])
def get_group_tasks(group_id: int) -> Dict[str, Any]:
    """查询小组任务（支持状态筛选）"""
    # 接收筛选参数
    status = request.args.get('status', '')
    # 校验小组存在
    group_exist = query_one("SELECT 1 FROM sg_group WHERE group_id = %s", (group_id,))
    if not group_exist:
        return jsonify({"code": 404, "msg": f"小组ID={group_id}不存在"})
    # 构建查询SQL
    base_sql = """
        SELECT t.*, u.user_name AS leader_name
        FROM sg_task t
        LEFT JOIN sg_user u ON t.leader_id = u.user_id
        WHERE t.group_id = %s
    """
    params = [group_id]
    if status in ['待办', '完成']:
        base_sql += " AND t.status = %s"
        params.append(status)
    base_sql += " ORDER BY t.create_time DESC"
    # 执行查询
    task_list = query_all(base_sql, params)
    if task_list is None:
        return jsonify({"code": 500, "msg": "任务查询失败"})
    # 格式化时间
    for task in task_list:
        task['create_time'] = task['create_time'].strftime("%Y-%m-%d %H:%M:%S")
    return jsonify({
        "code": 200,
        "msg": "查询成功",
        "data": task_list
    })

@task_blueprint.route('/<int:task_id>/status', methods=['PUT'])
def update_task_status(task_id: int) -> Dict[str, Any]:
    """更新任务状态"""
     # ⭐ 需要添加的代码：获取和验证请求参数
    request_data = request.json or {}
    
    # 校验必填参数
    required_fields = ['status', 'user_id']
    is_param_valid, err_msg = check_required_params(request_data, required_fields)
    if not is_param_valid:
        return jsonify({"code": 400, "msg": err_msg})
    
    # 校验参数类型
    type_map = {'user_id': 'int'}
    is_type_valid, type_err_msg = check_param_type(request_data, type_map)
    if not is_type_valid:
        return jsonify({"code": 400, "msg": type_err_msg})
    
    # 提取参数
    status = request_data['status'].strip()
    user_id = request_data['user_id']
    
    # 校验状态值
    if status not in ['待办', '完成']:
        return jsonify({"code": 400, "msg": "状态值必须是'待办'或'完成'"})
    
    # 校验任务存在
    task_sql = """
        SELECT t.*, g.group_id 
        FROM sg_task t
        LEFT JOIN sg_group g ON t.group_id = g.group_id
        WHERE t.task_id = %s
    """
    task_info = query_one(task_sql, (task_id,))
    if not task_info:
        return jsonify({"code": 404, "msg": f"任务ID={task_id}不存在"})
    
    # 校验用户权限：用户必须是任务的负责人或是小组管理员
    # 检查是否是负责人
    if task_info['leader_id'] != user_id:
        # 检查是否是小组管理员
        permission_sql = """
            SELECT permission_level 
            FROM sg_user_group 
            WHERE user_id = %s AND group_id = %s
        """
        user_permission = query_one(permission_sql, (user_id, task_info['group_id']))
        if not user_permission or user_permission['permission_level'] < PERMISSION_CONFIG['group']['admin']:
            return jsonify({"code": 403, "msg": "无权限更新该任务状态"})
    
    # 获取当前状态，避免重复更新
    current_status = task_info['status']
    if current_status == status:
        return jsonify({"code": 400, "msg": f"任务已经是'{status}'状态"})
    
    # 执行更新
    update_sql = "UPDATE sg_task SET status = %s WHERE task_id = %s"
    if status == '完成':
        update_sql = "UPDATE sg_task SET status = %s, complete_time = NOW() WHERE task_id = %s"
    
    update_success, affected_rows = execute_sql(update_sql, (status, task_id))
    if not update_success or affected_rows == 0:
        return jsonify({"code": 500, "msg": "状态更新失败"})
    
    # ⭐ 新增：更新成员统计
    try:
        from app.utils.stats_utils import update_stats
        # 重新计算该成员在小组中的统计
        stats_sql = """
            SELECT 
                COUNT(*) as total_tasks,
                SUM(CASE WHEN status = '完成' THEN 1 ELSE 0 END) as completed_tasks
            FROM sg_task 
            WHERE leader_id = %s AND group_id = %s
        """
        task_stats = query_one(stats_sql, (user_id, task_info['group_id']))
        
        if task_stats:
            # 获取文件统计
            file_sql = "SELECT COUNT(*) as uploaded_files FROM sg_file WHERE uploader_id = %s AND group_id = %s"
            file_stats = query_one(file_sql, (user_id, task_info['group_id']))
            
            update_stats(
                user_id=user_id,
                group_id=task_info['group_id'],
                total_tasks=task_stats['total_tasks'] or 0,
                completed_tasks=task_stats['completed_tasks'] or 0,
                uploaded_files=file_stats['uploaded_files'] or 0 if file_stats else 0
            )
    except Exception as e:
        print(f"更新成员统计失败: {e}")
        # 不中断主流程
    
    return jsonify({"code": 200, "msg": "状态更新成功"})

@task_blueprint.route('/group/<int:group_id>/progress', methods=['GET'])
def get_task_progress(group_id: int) -> Dict[str, Any]:
    """查询小组任务进度"""
    # 校验小组存在
    group_exist = query_one("SELECT 1 FROM sg_group WHERE group_id = %s", (group_id,))
    if not group_exist:
        return jsonify({"code": 404, "msg": f"小组ID={group_id}不存在"})
    # 查询统计数据
    total_sql = "SELECT COUNT(*) AS total FROM sg_task WHERE group_id = %s"
    completed_sql = "SELECT COUNT(*) AS completed FROM sg_task WHERE group_id = %s AND status = '完成'"
    total = query_one(total_sql, (group_id,))['total']
    completed = query_one(completed_sql, (group_id,))['completed']
    # 计算进度
    progress = int((completed / total) * 100) if total > 0 else 0
    return jsonify({
        "code": 200,
        "msg": "查询成功",
        "data": {
            "total": total,
            "completed": completed,
            "pending": total - completed,
            "progress": progress  # 进度百分比
        }
    })