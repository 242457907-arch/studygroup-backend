from typing import Dict, Tuple

def check_required_params(request_data: Dict, required_fields: list) -> Tuple[bool, str]:
    """校验必填参数"""
    missing_fields = [field for field in required_fields if not request_data.get(field)]
    if missing_fields:
        return False, f"缺少必填参数：{','.join(missing_fields)}"
    return True, ""

def check_param_type(request_data: Dict, type_map: Dict[str, str]) -> Tuple[bool, str]:
    """校验参数类型"""
    for field, target_type in type_map.items():
        value = request_data.get(field)
        if value is None:
            continue  # 非必填字段跳过
        try:
            if target_type == 'int':
                int(value)
            elif target_type == 'str':
                str(value).strip()
            elif target_type == 'datetime':
                # 简单校验ISO格式时间（YYYY-MM-DD HH:MM:SS）
                from datetime import datetime
                datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
            else:
                return False, f"不支持的参数类型：{target_type}"
        except (ValueError, TypeError):
            return False, f"{field}必须为{target_type}类型"
    return True, ""

def check_string_length(value: str, min_len: int, max_len: int, field_name: str) -> Tuple[bool, str]:
    """校验字符串长度"""
    length = len(value.strip())
    if length < min_len or length > max_len:
        return False, f"{field_name}长度需在{min_len}-{max_len}字之间"
    return True, ""