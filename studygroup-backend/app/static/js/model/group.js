/**
 * 小组模型 - 管理小组数据和操作
 */
class GroupModel {
    constructor() {
        this.groups = []; // 当前用户的小组列表
        this.currentGroup = null; // 当前选中的小组
    }

    /**
     * 加载用户的小组列表
     * @param {number} userId - 用户ID
     * @returns {Promise<Array>} 小组列表
     */
    async loadUserGroups(userId) {
        try {
            console.log('📋 加载用户小组列表，用户ID:', userId);
            
            // 调用API获取小组列表
            const groups = await window.api.getUserGroups(userId);
            
            this.groups = Array.isArray(groups) ? groups : [];
            
            console.log(`✅ 加载到 ${this.groups.length} 个小组`);
            
            // 触发小组列表更新事件
            this.dispatchEvent('groups:loaded', this.groups);
            
            return this.groups;
            
        } catch (error) {
            console.error('❌ 加载小组列表失败:', error);
            this.dispatchEvent('groups:error', error);
            throw error;
        }
    }

    /**
     * 获取小组列表
     * @returns {Array} 小组列表
     */
    getGroups() {
        return this.groups;
    }

    /**
     * 根据ID获取小组
     * @param {number} groupId - 小组ID
     * @returns {Object|null} 小组对象或null
     */
    getGroupById(groupId) {
        return this.groups.find(group => group.id === groupId) || null;
    }

    /**
     * 设置当前选中的小组
     * @param {number|Object} group - 小组ID或小组对象
     */
    setCurrentGroup(group) {
        if (typeof group === 'number') {
            this.currentGroup = this.getGroupById(group);
        } else {
            this.currentGroup = group;
        }
        
        if (this.currentGroup) {
            // 保存到本地存储，便于页面刷新后恢复
            localStorage.setItem('current_group', JSON.stringify(this.currentGroup));
            console.log('🎯 当前小组已设置:', this.currentGroup);
            
            // 触发小组切换事件
            this.dispatchEvent('group:changed', this.currentGroup);
        }
    }

    /**
     * 获取当前选中的小组
     * @returns {Object|null} 当前小组对象
     */
    getCurrentGroup() {
        if (!this.currentGroup) {
            // 尝试从本地存储恢复
            const storedGroup = localStorage.getItem('current_group');
            if (storedGroup) {
                try {
                    this.currentGroup = JSON.parse(storedGroup);
                } catch (error) {
                    console.error('解析本地存储的小组数据失败:', error);
                }
            }
        }
        return this.currentGroup;
    }

    /**
     * 创建新小组
     * @param {string} name - 小组名称
     * @param {string} description - 小组描述
     * @returns {Promise<Object>} 创建的小组对象
     */
    async createGroup(name, description = '') {
        try {
            console.log('🆕 创建新小组:', { name, description });
            
            // 调用API创建小组
            const newGroup = await window.api.createGroup(name, description);
            
            // 添加到本地列表
            this.groups.push(newGroup);
            
            console.log('✅ 小组创建成功:', newGroup);
            
            // 触发小组创建事件
            this.dispatchEvent('group:created', newGroup);
            this.dispatchEvent('groups:updated', this.groups);
            
            return newGroup;
            
        } catch (error) {
            console.error('❌ 创建小组失败:', error);
            this.dispatchEvent('group:createError', error);
            throw error;
        }
    }

    /**
     * 获取小组成员
     * @param {number} groupId - 小组ID
     * @returns {Promise<Array>} 成员列表
     */
    async getGroupMembers(groupId) {
        try {
            console.log('👥 加载小组成员，小组ID:', groupId);
            
            // 调用API获取成员
            const members = await window.api.getGroupMembers(groupId);
            
            // 格式化成员数据
            const formattedMembers = Array.isArray(members) ? members : [];
            
            console.log(`✅ 加载到 ${formattedMembers.length} 位成员`);
            
            return formattedMembers;
            
        } catch (error) {
            console.error('❌ 加载小组成员失败:', error);
            throw error;
        }
    }

    /**
     * 获取小组详情
     * @param {number} groupId - 小组ID
     * @returns {Promise<Object>} 小组详情
     */
    async getGroupDetail(groupId) {
        try {
            console.log('🔍 加载小组详情，小组ID:', groupId);
            
            // 调用API获取小组详情
            const detail = await window.api.getGroupDetail(groupId);
            
            // 更新本地缓存
            const index = this.groups.findIndex(g => g.id === groupId);
            if (index > -1) {
                this.groups[index] = { ...this.groups[index], ...detail };
            }
            
            console.log('✅ 小组详情加载成功:', detail);
            
            return detail;
            
        } catch (error) {
            console.error('❌ 加载小组详情失败:', error);
            throw error;
        }
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
     * 清除当前小组
     */
    clearCurrentGroup() {
        this.currentGroup = null;
        localStorage.removeItem('current_group');
    }

    /**
     * 统计小组任务数量（模拟）
     * @param {number} groupId - 小组ID
     * @returns {Promise<number>} 任务数量
     */
    async getTaskCount(groupId) {
        // 实际项目中应该调用API，这里模拟
        return Math.floor(Math.random() * 10) + 1;
    }

    /**
     * 统计小组成员数量（模拟）
     * @param {number} groupId - 小组ID
     * @returns {Promise<number>} 成员数量
     */
    async getMemberCount(groupId) {
        // 实际项目中应该调用API，这里模拟
        return Math.floor(Math.random() * 15) + 3;
    }
}

// 创建单例实例
const groupModel = new GroupModel();

// 暴露到全局
window.GroupModel = groupModel;