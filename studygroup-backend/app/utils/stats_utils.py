from app.utils.db_utils import query_one, query_all, execute_sql
from typing import Dict, Any, Optional

def get_member_stats(user_id: int, group_id: int) -> Optional[Dict[str, Any]]:
    """获取成员在小组中的贡献统计"""
    try:
        # 1. 查询任务统计
        task_stats = query_one("""
            SELECT 
                COUNT(*) as total_tasks,
                SUM(CASE WHEN status = '完成' THEN 1 ELSE 0 END) as completed_tasks
            FROM sg_task 
            WHERE leader_id = %s AND group_id = %s
        """, (user_id, group_id))
        
        # 2. 查询文件统计
        file_stats = query_one("""
            SELECT COUNT(*) as uploaded_files
            FROM sg_file 
            WHERE uploader_id = %s AND group_id = %s
        """, (user_id, group_id))
        
        # 3. 查询角色
        role_info = query_one("""
            SELECT role, join_time 
            FROM sg_user_group 
            WHERE user_id = %s AND group_id = %s
        """, (user_id, group_id))
        
        if not task_stats or not file_stats or not role_info:
            return None
            
        # 4. 计算完成率
        total_tasks = task_stats['total_tasks'] or 0
        completed_tasks = task_stats['completed_tasks'] or 0
        uploaded_files = file_stats['uploaded_files'] or 0
        completion_rate = int((completed_tasks / total_tasks * 100)) if total_tasks > 0 else 0
        
        # 5. 更新统计表（保持数据同步）
        update_stats(user_id, group_id, total_tasks, completed_tasks, uploaded_files)
        
        return {
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'uploaded_files': uploaded_files,
            'completion_rate': completion_rate,
            'role': role_info['role'],
            'join_time': role_info['join_time'].strftime('%Y-%m-%d %H:%M:%S') if role_info['join_time'] else None
        }
        
    except Exception as e:
        print(f"获取成员统计失败: {e}")
        return None

def update_stats(user_id: int, group_id: int, total_tasks: int, completed_tasks: int, uploaded_files: int) -> bool:
    """更新成员统计表"""
    try:
        sql = """
            INSERT INTO sg_member_stats (user_id, group_id, total_tasks, completed_tasks, uploaded_files, last_active)
            VALUES (%s, %s, %s, %s, %s, NOW())
            ON DUPLICATE KEY UPDATE 
                total_tasks = VALUES(total_tasks),
                completed_tasks = VALUES(completed_tasks),
                uploaded_files = VALUES(uploaded_files),
                last_active = NOW()
        """
        success, _ = execute_sql(sql, (user_id, group_id, total_tasks, completed_tasks, uploaded_files))
        return success
    except Exception as e:
        print(f"更新统计失败: {e}")
        return False

def get_group_members_with_stats(group_id: int) -> Optional[list]:
    """获取小组成员及其统计信息"""
    try:
        sql = """
            SELECT 
                u.user_id, u.user_name, u.contact,
                ug.role, ug.join_time,
                COALESCE(ms.total_tasks, 0) as total_tasks,
                COALESCE(ms.completed_tasks, 0) as completed_tasks,
                COALESCE(ms.uploaded_files, 0) as uploaded_files,
                CASE 
                    WHEN COALESCE(ms.total_tasks, 0) > 0 
                    THEN ROUND((COALESCE(ms.completed_tasks, 0) * 100.0 / COALESCE(ms.total_tasks, 0)), 1)
                    ELSE 0 
                END as completion_rate
            FROM sg_user_group ug
            LEFT JOIN sg_user u ON ug.user_id = u.user_id
            LEFT JOIN sg_member_stats ms ON ug.user_id = ms.user_id AND ug.group_id = ms.group_id
            WHERE ug.group_id = %s
            ORDER BY 
                CASE ug.role 
                    WHEN 'creator' THEN 1
                    WHEN 'leader' THEN 2
                    ELSE 3 
                END,
                u.user_name
        """
        members = query_all(sql, (group_id,))
        
        if members:
            for member in members:
                if member['join_time']:
                    member['join_time'] = member['join_time'].strftime('%Y-%m-%d %H:%M:%S')
        return members
        
    except Exception as e:
        print(f"获取成员统计列表失败: {e}")
        return None