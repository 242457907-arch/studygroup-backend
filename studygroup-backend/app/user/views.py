from flask import Blueprint, request, jsonify
from app.utils.db_utils import query_one, execute_sql
from app.utils.validate_utils import check_required_params, check_param_type, check_string_length
from typing import Dict, Any

user_blueprint = Blueprint('user', __name__)

@user_blueprint.route('/login', methods=['GET','POST'])
def user_login() -> Dict[str, Any]:
    """
    用户登录接口
    请求参数（JSON）：user_id(int)、contact(str)
    返回：用户信息（user_id、user_name）
    """
    if request.method == 'GET':
        # GET 请求直接返回测试信息
        return jsonify({
            "code": 200, 
            "msg": "登录接口正常（请使用POST方法）",
            "method": "GET",
            "example": {
                "user_id": 1,
                "contact": "13800138000"
            }
        })
    request_data = request.json or {}
    # 校验必填参数
    required_fields = ['user_id', 'contact']
    is_valid, err_msg = check_required_params(request_data, required_fields)
    if not is_valid:
        return jsonify({"code": 400, "msg": err_msg})
    # 校验参数类型
    type_map = {'user_id': 'int'}
    is_type_valid, type_err_msg = check_param_type(request_data, type_map)
    if not is_type_valid:
        return jsonify({"code": 400, "msg": type_err_msg})
    # 提取参数
    user_id = request_data['user_id']
    contact = request_data['contact'].strip()
    # 校验用户存在且联系方式匹配
    query_sql = "SELECT user_id, user_name FROM sg_user WHERE user_id = %s AND contact = %s"
    user_info = query_one(query_sql, (user_id, contact))
    if not user_info:
        return jsonify({"code": 401, "msg": "用户ID或联系方式错误"})
    # 返回成功结果
    return jsonify({
        "code": 200,
        "msg": "登录成功",
        "data": user_info
    })

@user_blueprint.route('/<int:user_id>', methods=['GET'])
def get_user_info(user_id: int) -> Dict[str, Any]:
    """查询用户详情"""
    query_sql = "SELECT user_id, user_name, contact FROM sg_user WHERE user_id = %s"
    user_info = query_one(query_sql, (user_id,))
    if not user_info:
        return jsonify({"code": 404, "msg": f"用户ID={user_id}不存在"})
    return jsonify({
        "code": 200,
        "msg": "查询成功",
        "data": user_info
    })

@user_blueprint.route('/<int:user_id>/stats', methods=['GET'])
def get_user_stats(user_id: int) -> Dict[str, Any]:
    """获取用户在各小组的统计信息"""
    # 获取查询参数
    group_id = request.args.get('group_id')
    
    try:
        if group_id:
            # 获取用户在指定小组的统计
            from app.utils.stats_utils import get_member_stats
            group_id = int(group_id)
            stats = get_member_stats(user_id, group_id)
            
            if not stats:
                return jsonify({"code": 404, "msg": "统计信息不存在"})
            
            return jsonify({
                "code": 200,
                "msg": "查询成功",
                "data": stats
            })
        else:
            # 获取用户在所有小组的统计汇总
            sql = """
                SELECT 
                    g.group_id, g.group_name,
                    COALESCE(ms.total_tasks, 0) as total_tasks,
                    COALESCE(ms.completed_tasks, 0) as completed_tasks,
                    COALESCE(ms.uploaded_files, 0) as uploaded_files,
                    ug.role
                FROM sg_user_group ug
                LEFT JOIN sg_group g ON ug.group_id = g.group_id
                LEFT JOIN sg_member_stats ms ON ug.user_id = ms.user_id AND ug.group_id = ms.group_id
                WHERE ug.user_id = %s
                ORDER BY g.create_time DESC
            """
            group_stats = query_all(sql, (user_id,))
            
            if group_stats is None:
                return jsonify({"code": 500, "msg": "统计查询失败"})
            
            # 计算总计
            totals = {
                'total_tasks': sum(g['total_tasks'] for g in group_stats),
                'completed_tasks': sum(g['completed_tasks'] for g in group_stats),
                'uploaded_files': sum(g['uploaded_files'] for g in group_stats)
            }
            
            return jsonify({
                "code": 200,
                "msg": "查询成功",
                "data": {
                    'groups': group_stats,
                    'totals': totals
                }
            })
            
    except Exception as e:
        return jsonify({"code": 500, "msg": f"查询失败: {str(e)}"})