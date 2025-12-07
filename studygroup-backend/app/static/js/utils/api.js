// API基础地址
const API_BASE = 'http://127.0.0.1:5000/api';

// 通用请求函数 - 适用于 {code, data, msg} 格式
async function apiRequest(endpoint, method = 'GET', data = null) {
    console.log(`📡 API调用: ${method} ${API_BASE}${endpoint}`);
    console.log('📦 请求数据:', data);
    
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
        },
    };
    
    if (data && (method === 'POST' || method === 'PUT' || method === 'DELETE')) {
        options.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, options);
        const result = await response.json();
        
        console.log('✅ API响应:', result);
        
        // 处理 {code, data, msg} 格式
        if (result.code !== undefined) {
            if (result.code === 200) {
                // 成功时返回data字段
                return result.data || {};
            } else {
                // 失败时抛出错误信息
                throw new Error(result.msg || `请求失败，错误码: ${result.code}`);
            }
        }
        
        // 如果没有code字段，直接返回结果
        console.warn('⚠️ API返回格式异常，未包含code字段');
        return result;
        
    } catch (error) {
        console.error('❌ API请求失败:', error);
        
        // 友好的错误提示
        let userMessage = error.message;
        if (error.message.includes('Failed to fetch')) {
            userMessage = '无法连接到服务器，请检查后端是否启动';
        } else if (error.message.includes('NetworkError')) {
            userMessage = '网络连接失败，请检查网络';
        }
        
        alert(`请求失败: ${userMessage}`);
        throw error;
    }
}

// 具体的API函数 - 根据实际API清单修正
const api = {
    // 用户模块
    login: (userId, contact) => {
        return apiRequest('/user/login', 'POST', {
            user_id: Number(userId),
            contact: contact
        });
    },
    
    getUser: (userId) => {
        return apiRequest(`/user/${userId}`);
    },
    
    // 小组模块
    getUserGroups: (userId) => {
        return apiRequest(`/group/user/${userId}`);
    },
    
    createGroup: (groupName, courseId = 1, creatorId = null) => {
        // 如果未提供creatorId，从localStorage获取当前用户ID
        if (!creatorId) {
            creatorId = localStorage.getItem('user_id');
        }
    
        return apiRequest('/group/create', 'POST', {
            group_name: groupName,
            course_id: courseId || 1,  // 默认为课程ID 1（数据库系统）
            creator_id: creatorId ? parseInt(creatorId) : 1  // 默认用户ID 1
        });
    },
    
    getGroupDetail: (groupId) => {
        return apiRequest(`/group/${groupId}`);
    },
    
    getGroupMembers: (groupId, userId = null) => {
        // 如果后端需要user_id，添加到查询参数
        let endpoint = `/group/${groupId}/members`;
    
        // 尝试从localStorage获取user_id
        if (!userId) {
            userId = localStorage.getItem('user_id');
        }
    
        // 如果获取到user_id，添加到URL
        if (userId) {
            endpoint += `?user_id=${userId}`;
        }
    
        return apiRequest(endpoint);
    },
    
    // 任务模块
    getGroupTasks: (groupId) => {
        return apiRequest(`/task/group/${groupId}`);
    },
    
    createTask: (taskData) => {
        // 根据数据库sg_task表结构：task_desc, group_id, leader_id
        return apiRequest('/task/create', 'POST', {
            task_desc: taskData.task_desc,
            group_id: taskData.group_id,
            leader_id: taskData.leader_id || taskData.leaderId
        });
    },
    
    updateTaskStatus: (taskId, status) => {
        return apiRequest(`/task/${taskId}/status`, 'PUT', { 
            status: status 
        });
    },
    
    getTaskProgress: (groupId) => {
        return apiRequest(`/task/group/${groupId}/progress`);
    },
    
    // 文件模块
    getGroupFiles: (groupId) => {
        return apiRequest(`/file/group/${groupId}`);
    },
    
    uploadFile: (formData) => {
        // 注意：文件上传需要使用FormData，不能用JSON
        // 这里只是占位符，实际实现需要在调用处处理
        console.warn('文件上传需要使用FormData，请使用fetch直接调用');
        return null;
    },
    
    downloadFile: (fileId) => {
        return apiRequest(`/file/download/${fileId}`);
    },
    
    deleteFile: (fileId) => {
        return apiRequest(`/file/${fileId}`, 'DELETE');
    }
};

// 暴露到全局
window.api = api;

// 添加文件上传辅助函数
window.uploadFile = async function(groupId, file) {
    try {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('group_id', groupId);
        
        console.log('📤 上传文件:', file.name, '大小:', file.size);
        
        const response = await fetch(`${API_BASE}/file/upload`, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        console.log('✅ 文件上传响应:', result);
        
        if (result.code === 200) {
            return result.data || {};
        } else {
            throw new Error(result.msg || '文件上传失败');
        }
    } catch (error) {
        console.error('❌ 文件上传失败:', error);
        throw error;
    }
};