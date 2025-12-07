from flask import Blueprint, request, jsonify
from app.utils.db_utils import query_one, query_all, execute_sql
from app.utils.validate_utils import check_required_params, check_param_type, check_string_length
from app.config import PERMISSION_CONFIG
from datetime import datetime
from typing import Dict, Any

group_blueprint = Blueprint('group', __name__)

@group_blueprint.route('/create', methods=['POST'])
def create_group() -> Dict[str, Any]:
    """创建小组"""
    request_data = request.json or {}
    # 校验必填参数
    required_fields = ['group_name', 'course_id', 'creator_id']
    is_param_valid, err_msg = check_required_params(request_data, required_fields)
    if not is_param_valid:
        return jsonify({"code": 400, "msg": err_msg})
    # 校验参数类型
    type_map = {'course_id': 'int', 'creator_id': 'int'}
    is_type_valid, type_err_msg = check_param_type(request_data, type_map)
    if not is_type_valid:
        return jsonify({"code": 400, "msg": type_err_msg})
    # 提取参数并校验业务规则
    group_name = request_data['group_name'].strip()
    course_id = request_data['course_id']
    creator_id = request_data['creator_id']
    # 校验小组名称长度
    is_len_valid, len_err_msg = check_string_length(group_name, 1, 30, "小组名称")
    if not is_len_valid:
        return jsonify({"code": 400, "msg": len_err_msg})
    # 校验关联数据存在性
    course_exist = query_one("SELECT 1 FROM sg_course WHERE course_id = %s", (course_id,))
    if not course_exist:
        return jsonify({"code": 404, "msg": f"课程ID={course_id}不存在"})
    user_exist = query_one("SELECT 1 FROM sg_user WHERE user_id = %s", (creator_id,))
    if not user_exist:
        return jsonify({"code": 404, "msg": f"用户ID={creator_id}不存在"})
    # 执行创建逻辑
    create_time = datetime.now()
    # 创建小组
    insert_group_sql = """
        INSERT INTO sg_group (group_name, course_id, create_time)
        VALUES (%s, %s, %s)
    """
    group_success, group_id = execute_sql(insert_group_sql, (group_name, course_id, create_time))
    if not group_success or not group_id:
        return jsonify({"code": 500, "msg": "小组创建失败"})
    # 绑定创建人到小组
    insert_relation_sql = """
        INSERT INTO sg_user_group (user_id, group_id)
        VALUES (%s, %s)
    """
    relation_success, _ = execute_sql(insert_relation_sql, (creator_id, group_id))
    if not relation_success:
        # 回滚小组创建
        execute_sql("DELETE FROM sg_group WHERE group_id = %s", (group_id,))
        return jsonify({"code": 500, "msg": "小组创建成功，创建人绑定失败"})
    # 返回结果
    return jsonify({
        "code": 200,
        "msg": "小组创建成功",
        "data": {"group_id": group_id, "group_name": group_name}
    })

@group_blueprint.route('/user/<int:user_id>', methods=['GET'])
def get_user_groups(user_id: int) -> Dict[str, Any]:
    """查询用户关联的所有小组"""
    # 校验用户存在
    user_exist = query_one("SELECT 1 FROM sg_user WHERE user_id = %s", (user_id,))
    if not user_exist:
        return jsonify({"code": 404, "msg": f"用户ID={user_id}不存在"})
    # 联表查询
    query_sql = """
        SELECT 
            g.group_id, g.group_name, g.create_time,
            c.course_id, c.course_name, c.semester
        FROM sg_user_group ug
        LEFT JOIN sg_group g ON ug.group_id = g.group_id
        LEFT JOIN sg_course c ON g.course_id = c.course_id
        WHERE ug.user_id = %s
        ORDER BY g.create_time DESC
    """
    group_list = query_all(query_sql, (user_id,))
    if group_list is None:
        return jsonify({"code": 500, "msg": "小组查询失败"})
    # 格式化时间
    for group in group_list:
        group['create_time'] = group['create_time'].strftime("%Y-%m-%d %H:%M:%S")
    return jsonify({
        "code": 200,
        "msg": "查询成功",
        "data": group_list
    })

@group_blueprint.route('/<int:group_id>', methods=['GET'])
def get_group_detail(group_id: int) -> Dict[str, Any]:
    """查询小组详情"""
    query_sql = """
        SELECT g.*, c.course_name, c.course_code, c.semester
        FROM sg_group g
        LEFT JOIN sg_course c ON g.course_id = c.course_id
        WHERE g.group_id = %s
    """
    group_info = query_one(query_sql, (group_id,))
    if not group_info:
        return jsonify({"code": 404, "msg": f"小组ID={group_id}不存在"})
    # 格式化时间
    group_info['create_time'] = group_info['create_time'].strftime("%Y-%m-%d %H:%M:%S")
    return jsonify({
        "code": 200,
        "msg": "查询成功",
        "data": group_info
    })

@group_blueprint.route('/<int:group_id>/members', methods=['GET'])
def get_group_members(group_id: int) -> Dict[str, Any]:
    """查询小组成员（包含统计信息）"""
    # 权限校验
    request_user_id = request.args.get('user_id')
    if not request_user_id:
        return jsonify({"code": 401, "msg": "请传入user_id"})
    
    try:
        request_user_id = int(request_user_id)
    except:
        return jsonify({"code": 400, "msg": "user_id必须为整数"})
    
    # 校验是否为小组成员
    is_member = query_one(
        "SELECT 1 FROM sg_user_group WHERE user_id = %s AND group_id = %s",
        (request_user_id, group_id)
    )
    if not is_member and "group_member_query" in PERMISSION_CONFIG["REQUIRE_MEMBER"]:
        return jsonify({"code": 403, "msg": "无权限查询该小组成员"})
    
    # 校验小组存在
    group_exist = query_one("SELECT 1 FROM sg_group WHERE group_id = %s", (group_id,))
    if not group_exist:
        return jsonify({"code": 404, "msg": f"小组ID={group_id}不存在"})
    
    # 查询成员列表（使用新的工具函数）
    from app.utils.stats_utils import get_group_members_with_stats
    
    member_list = get_group_members_with_stats(group_id)
    if member_list is None:
        return jsonify({"code": 500, "msg": "成员查询失败"})
    
    return jsonify({
        "code": 200,
        "msg": "查询成功",
        "data": member_list
    })

@group_blueprint.route('/<int:group_id>/invite', methods=['POST'])
def invite_member(group_id: int) -> Dict[str, Any]:
    """邀请成员加入小组（超级简化版）"""
    request_data = request.json or {}
    
    # 基础校验
    inviter_id = request_data.get('inviter_id')
    invitee_id = request_data.get('invitee_id')
    
    if not inviter_id or not invitee_id:
        return jsonify({"code": 400, "msg": "邀请人和被邀请人ID不能为空"})
    
    # 简单校验
    if inviter_id == invitee_id:
        return jsonify({"code": 400, "msg": "不能邀请自己"})
    
    # 直接将被邀请人加入小组（跳过所有权限检查）
    try:
        # 检查是否已加入
        is_member = query_one(
            "SELECT 1 FROM sg_user_group WHERE user_id = %s AND group_id = %s",
            (invitee_id, group_id)
        )
        
        if is_member:
            return jsonify({"code": 400, "msg": "该用户已经是小组成员"})
        
        # 加入小组
        join_sql = "INSERT INTO sg_user_group (user_id, group_id) VALUES (%s, %s)"
        join_success, _ = execute_sql(join_sql, (invitee_id, group_id))
        
        if not join_success:
            return jsonify({"code": 500, "msg": "加入小组失败"})
        
        # 记录邀请（可选）
        try:
            invite_sql = """
                INSERT INTO sg_invitation (group_id, inviter_id, invitee_id)
                VALUES (%s, %s, %s)
            """
            execute_sql(invite_sql, (group_id, inviter_id, invitee_id))
        except:
            pass  # 邀请记录失败不影响主流程
        
        # 获取被邀请人信息
        invitee_info = query_one(
            "SELECT user_id, user_name FROM sg_user WHERE user_id = %s",
            (invitee_id,)
        )
        
        return jsonify({
            "code": 200,
            "msg": "邀请成功",
            "data": {
                "invitee_info": invitee_info or {"user_id": invitee_id, "user_name": "用户"}
            }
        })
        
    except Exception as e:
        return jsonify({"code": 500, "msg": f"操作失败: {str(e)}"})

@group_blueprint.route('/<int:group_id>/remove', methods=['POST'])
def remove_member(group_id: int) -> Dict[str, Any]:
    """移除小组成员（超级简化版）"""
    request_data = request.json or {}
    
    # 基础校验
    target_id = request_data.get('target_id')
    
    if not target_id:
        return jsonify({"code": 400, "msg": "目标成员ID不能为空"})
    
    # 简单移除（跳过权限检查）
    try:
        # 移除成员
        delete_sql = "DELETE FROM sg_user_group WHERE user_id = %s AND group_id = %s"
        delete_success, affected_rows = execute_sql(delete_sql, (target_id, group_id))
        
        if not delete_success or affected_rows == 0:
            return jsonify({"code": 400, "msg": "该用户不是小组成员"})
        
        return jsonify({
            "code": 200,
            "msg": "成员移除成功"
        })
        
    except Exception as e:
        return jsonify({"code": 500, "msg": f"移除失败: {str(e)}"})