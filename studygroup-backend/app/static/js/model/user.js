/**
 * 用户模型 - 管理用户数据和操作
 */
class UserModel {
    constructor() {
        this.currentUser = null;
        this.initialize();
    }

    /**
     * 初始化当前用户
     */
    initialize() {
        // 从本地存储加载用户数据
        const storedUser = localStorage.getItem('user_data');
        if (storedUser) {
            try {
                this.currentUser = JSON.parse(storedUser);
                console.log('📱 用户数据已从本地存储加载:', this.currentUser);
            } catch (error) {
                console.error('❌ 解析用户数据失败:', error);
                this.currentUser = null;
            }
        }
    }

    /**
     * 获取当前用户
     * @returns {Object|null} 当前用户对象或null
     */
    getCurrentUser() {
        return this.currentUser;
    }

    /**
     * 获取用户ID
     * @returns {number|null} 用户ID
     */
    getUserId() {
        return this.currentUser?.user_id || parseInt(localStorage.getItem('user_id')) || null;
    }

    /**
     * 获取用户名
     * @returns {string} 用户名
     */
    getUserName() {
        return this.currentUser?.user_name || localStorage.getItem('user_name') || '用户';
    }

    /**
     * 检查用户是否已登录
     * @returns {boolean} 是否已登录
     */
    isLoggedIn() {
        return !!this.getUserId();
    }

    /**
     * 登录用户
     * @param {Object} userData - 用户数据
     */
    login(userData) {
        this.currentUser = userData;
        
        // 保存到本地存储
        localStorage.setItem('user_id', userData.user_id || '');
        localStorage.setItem('user_name', userData.user_name || '');
        localStorage.setItem('user_contact', userData.contact || '');
        localStorage.setItem('user_data', JSON.stringify(userData));
        
        console.log('✅ 用户登录成功:', userData);
        
        // 触发登录事件
        this.dispatchEvent('user:login', userData);
    }

    /**
     * 登出用户
     */
    logout() {
        const oldUser = this.currentUser;
        this.currentUser = null;
        
        // 清除本地存储
        localStorage.removeItem('user_id');
        localStorage.removeItem('user_name');
        localStorage.removeItem('user_contact');
        localStorage.removeItem('user_data');
        
        console.log('👋 用户已登出');
        
        // 触发登出事件
        this.dispatchEvent('user:logout', oldUser);
    }

    /**
     * 更新用户信息
     * @param {Object} updates - 更新的字段
     */
    updateUser(updates) {
        if (!this.currentUser) return;
        
        this.currentUser = { ...this.currentUser, ...updates };
        localStorage.setItem('user_data', JSON.stringify(this.currentUser));
        
        console.log('🔄 用户信息已更新:', updates);
        this.dispatchEvent('user:updated', this.currentUser);
    }

    /**
     * 事件监听器
     */
    listeners = {};

    /**
     * 添加事件监听
     * @param {string} event - 事件名称
     * @param {Function} callback - 回调函数
     */
    on(event, callback) {
        if (!this.listeners[event]) {
            this.listeners[event] = [];
        }
        this.listeners[event].push(callback);
    }

    /**
     * 移除事件监听
     * @param {string} event - 事件名称
     * @param {Function} callback - 回调函数
     */
    off(event, callback) {
        if (!this.listeners[event]) return;
        const index = this.listeners[event].indexOf(callback);
        if (index > -1) {
            this.listeners[event].splice(index, 1);
        }
    }

    /**
     * 触发事件
     * @param {string} event - 事件名称
     * @param {*} data - 事件数据
     */
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
     * 获取用户头像
     * @returns {string} 用户头像文本
     */
    getUserAvatar() {
        const name = this.getUserName();
        return name ? name.charAt(0).toUpperCase() : 'U';
    }
}

// 创建单例实例
const userModel = new UserModel();

// 暴露到全局
window.UserModel = userModel;

// 添加便捷方法到全局
window.getCurrentUserId = () => userModel.getUserId();
window.getCurrentUserName = () => userModel.getUserName();
window.isUserLoggedIn = () => userModel.isLoggedIn();