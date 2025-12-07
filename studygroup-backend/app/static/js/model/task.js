/**
 * 任务模型 - 管理任务数据和操作
 */
class TaskModel {
    constructor() {
        this.tasks = []; // 当前小组的任务列表
        this.statuses = ['待处理', '进行中', '已完成', '已延期']; // 任务状态选项
        this.priorities = ['低', '中', '高']; // 任务优先级选项
    }

    /**
     * 加载小组的任务列表
     * @param {number} groupId - 小组ID
     * @returns {Promise<Array>} 任务列表
     */
    async loadGroupTasks(groupId) {
        try {
            console.log('📋 加载小组任务，小组ID:', groupId);
            
            // 调用API获取任务列表
            const tasks = await window.api.getGroupTasks(groupId);
            
            // 格式化任务数据
            this.tasks = this.formatTasks(Array.isArray(tasks) ? tasks : []);
            
            console.log(`✅ 加载到 ${this.tasks.length} 个任务`);
            
            // 触发任务列表更新事件
            this.dispatchEvent('tasks:loaded', this.tasks);
            
            return this.tasks;
            
        } catch (error) {
            console.error('❌ 加载任务列表失败:', error);
            this.dispatchEvent('tasks:error', error);
            throw error;
        }
    }

    /**
     * 格式化任务数据
     * @param {Array} tasks - 原始任务数据
     * @returns {Array} 格式化后的任务数据
     */
    formatTasks(tasks) {
        return tasks.map(task => ({
            id: task.id || Date.now() + Math.random(),
            title: task.title || '未命名任务',
            description: task.description || '',
            status: task.status || '待处理',
            priority: task.priority || '中',
            assignee: task.assignee || '未分配',
            dueDate: task.due_date || task.dueDate || null,
            createdAt: task.created_at || task.createdAt || new Date().toISOString(),
            groupId: task.group_id || task.groupId,
            creator: task.creator || '未知',
            
            // 计算任务是否过期
            get isOverdue() {
                if (!this.dueDate) return false;
                return new Date(this.dueDate) < new Date();
            },
            
            // 获取状态颜色
            get statusColor() {
                const colors = {
                    '待处理': '#95a5a6',
                    '进行中': '#3498db',
                    '已完成': '#2ecc71',
                    '已延期': '#e74c3c'
                };
                return colors[this.status] || '#95a5a6';
            },
            
            // 获取优先级颜色
            get priorityColor() {
                const colors = {
                    '低': '#2ecc71',
                    '中': '#f39c12',
                    '高': '#e74c3c'
                };
                return colors[this.priority] || '#f39c12';
            }
        }));
    }

    /**
     * 获取任务列表
     * @returns {Array} 任务列表
     */
    getTasks() {
        return this.tasks;
    }

    /**
     * 根据状态过滤任务
     * @param {string} status - 状态
     * @returns {Array} 过滤后的任务列表
     */
    getTasksByStatus(status) {
        return this.tasks.filter(task => task.status === status);
    }

    /**
     * 根据ID获取任务
     * @param {number} taskId - 任务ID
     * @returns {Object|null} 任务对象或null
     */
    getTaskById(taskId) {
        return this.tasks.find(task => task.id === taskId) || null;
    }

    /**
     * 创建新任务
     * @param {Object} taskData - 任务数据
     * @returns {Promise<Object>} 创建的任务对象
     */
    async createTask(taskData) {
        try {
            console.log('🆕 创建新任务:', taskData);
            
            // 格式化任务数据
            const formattedData = {
                title: taskData.title,
                description: taskData.description || '',
                status: taskData.status || '待处理',
                priority: taskData.priority || '中',
                assignee: taskData.assignee || '',
                due_date: taskData.dueDate || null,
                group_id: taskData.groupId
            };
            
            // 调用API创建任务
            const newTask = await window.api.createTask(formattedData);
            
            // 格式化并添加到本地列表
            const formattedTask = this.formatTasks([newTask])[0];
            this.tasks.push(formattedTask);
            
            console.log('✅ 任务创建成功:', formattedTask);
            
            // 触发任务创建事件
            this.dispatchEvent('task:created', formattedTask);
            this.dispatchEvent('tasks:updated', this.tasks);
            
            return formattedTask;
            
        } catch (error) {
            console.error('❌ 创建任务失败:', error);
            this.dispatchEvent('task:createError', error);
            throw error;
        }
    }

    /**
     * 更新任务状态
     * @param {number} taskId - 任务ID
     * @param {string} status - 新状态
     * @returns {Promise<Object>} 更新后的任务对象
     */
    async updateTaskStatus(taskId, status) {
        try {
            console.log('🔄 更新任务状态，任务ID:', taskId, '新状态:', status);
            
            // 调用API更新状态
            await window.api.updateTaskStatus(taskId, status);
            
            // 更新本地数据
            const taskIndex = this.tasks.findIndex(task => task.id === taskId);
            if (taskIndex > -1) {
                this.tasks[taskIndex].status = status;
                
                console.log('✅ 任务状态更新成功');
                
                // 触发任务更新事件
                this.dispatchEvent('task:updated', this.tasks[taskIndex]);
                this.dispatchEvent('tasks:updated', this.tasks);
                
                return this.tasks[taskIndex];
            }
            
            throw new Error('任务不存在');
            
        } catch (error) {
            console.error('❌ 更新任务状态失败:', error);
            this.dispatchEvent('task:updateError', error);
            throw error;
        }
    }

    /**
     * 更新任务信息
     * @param {number} taskId - 任务ID
     * @param {Object} updates - 更新的字段
     * @returns {Object} 更新后的任务对象
     */
    updateTask(taskId, updates) {
        const taskIndex = this.tasks.findIndex(task => task.id === taskId);
        if (taskIndex > -1) {
            this.tasks[taskIndex] = { ...this.tasks[taskIndex], ...updates };
            
            console.log('✅ 任务信息已更新:', updates);
            
            // 触发任务更新事件
            this.dispatchEvent('task:updated', this.tasks[taskIndex]);
            this.dispatchEvent('tasks:updated', this.tasks);
            
            return this.tasks[taskIndex];
        }
        
        throw new Error('任务不存在');
    }

    /**
     * 删除任务
     * @param {number} taskId - 任务ID
     */
    deleteTask(taskId) {
        const taskIndex = this.tasks.findIndex(task => task.id === taskId);
        if (taskIndex > -1) {
            const deletedTask = this.tasks[taskIndex];
            this.tasks.splice(taskIndex, 1);
            
            console.log('🗑️ 任务已删除:', deletedTask);
            
            // 触发任务删除事件
            this.dispatchEvent('task:deleted', deletedTask);
            this.dispatchEvent('tasks:updated', this.tasks);
        }
    }

    /**
     * 获取任务统计信息
     * @returns {Object} 统计信息
     */
    getTaskStats() {
        const stats = {
            total: this.tasks.length,
            todo: this.getTasksByStatus('待处理').length,
            doing: this.getTasksByStatus('进行中').length,
            done: this.getTasksByStatus('已完成').length,
            overdue: this.tasks.filter(task => task.isOverdue && task.status !== '已完成').length
        };
        
        stats.progress = stats.total > 0 
            ? Math.round((stats.done / stats.total) * 100) 
            : 0;
            
        return stats;
    }

    /**
     * 获取所有状态选项
     * @returns {Array} 状态选项
     */
    getStatusOptions() {
        return this.statuses;
    }

    /**
     * 获取所有优先级选项
     * @returns {Array} 优先级选项
     */
    getPriorityOptions() {
        return this.priorities;
    }

    /**
     * 事件系统
     */
    listeners = {};

    on(event, callback) {
        if (!this.listeners[event]) {
            this.listeners[event] = [];
        }
        this.listeners[event].push(callback);
    }

    off(event, callback) {
        if (!this.listeners[event]) return;
        const index = this.listeners[event].indexOf(callback);
        if (index > -1) {
            this.listeners[event].splice(index, 1);
        }
    }

    dispatchEvent(event, data) {
        if (!this.listeners[event]) return;
        this.listeners[event].forEach(callback => {
            try {
                callback(data);
            } catch (error) {
                console.error(`事件 ${event} 监听器错误:`, error);
            }
        });
    }

    /**
     * 清空任务列表
     */
    clearTasks() {
        this.tasks = [];
    }
}

// 创建单例实例
const taskModel = new TaskModel();

// 暴露到全局
window.TaskModel = taskModel;