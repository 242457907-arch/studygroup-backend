/**
 * 小组列表页面逻辑
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('🔧 group-list.js 开始加载');
    
    // 获取DOM元素
    const userNameElement = document.getElementById('userName');
    const userContactElement = document.getElementById('userContact');
    const userAvatarElement = document.getElementById('userAvatar');
    const groupsListElement = document.getElementById('groupsList');
    const createGroupBtn = document.getElementById('createGroupBtn');
    const createModal = document.getElementById('createModal');
    const cancelCreateBtn = document.getElementById('cancelCreateBtn');
    const createGroupForm = document.getElementById('createGroupForm');
    const submitCreateBtn = document.getElementById('submitCreateBtn');
    const groupNameInput = document.getElementById('groupName');
    
    // 检查用户登录状态
    const userId = localStorage.getItem('user_id');
    const userName = localStorage.getItem('user_name');
    const userContact = localStorage.getItem('user_contact');
    
    console.log('用户信息:', { userId, userName, userContact });
    
    // 如果没有登录，跳转到登录页
    if (!userId) {
        console.error('❌ 用户未登录');
        alert('请先登录');
        window.location.href = '/static/pages/login.html';
        return;
    }
    
    // 显示用户信息
    userNameElement.textContent = userName || '用户';
    userContactElement.textContent = `用户ID: ${userId}`;
    userAvatarElement.textContent = (userName || 'U').charAt(0).toUpperCase();
    
    // 加载小组列表
    loadUserGroups(userId);
    
    // ========== 事件监听器 ==========
    
    // 创建小组按钮点击事件
    if (createGroupBtn) {
        createGroupBtn.addEventListener('click', function() {
            console.log('➕ 创建小组按钮被点击');
            createModal.style.display = 'flex';
            groupNameInput.focus();
        });
    }
    
    // 取消创建按钮
    if (cancelCreateBtn) {
        cancelCreateBtn.addEventListener('click', function() {
            console.log('❌ 取消创建');
            createModal.style.display = 'none';
            createGroupForm.reset();
        });
    }
    
    // 点击模态框背景关闭
    if (createModal) {
        createModal.addEventListener('click', function(e) {
            if (e.target === createModal) {
                console.log('点击模态框背景关闭');
                createModal.style.display = 'none';
                createGroupForm.reset();
            }
        });
    }
    
    // 创建小组表单提交事件
    if (createGroupForm) {
        createGroupForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            console.log('📝 提交创建小组表单');
            
            const groupName = groupNameInput.value.trim();
            
            if (!groupName) {
                alert('请输入小组名称');
                groupNameInput.focus();
                return;
            }
            
            // 保存原始按钮文本
            const originalText = submitCreateBtn.textContent;
            
            try {
                // 禁用按钮，显示加载状态
                submitCreateBtn.disabled = true;
                submitCreateBtn.innerHTML = '<span class="loading"></span> 创建中...';
                
                console.log('准备创建小组:', { 
                    groupName, 
                    userId: userId,
                    userName: userName
                });
                
                // 调用API创建小组
                // 参数：groupName, courseId=1（默认）, creatorId=当前用户
                const newGroup = await window.api.createGroup(groupName, 1, userId);
                console.log('创建小组成功:', newGroup);
                
                // 1. 关闭模态框并重置表单
                createModal.style.display = 'none';
                createGroupForm.reset();
                
                // 2. 显示成功消息
                alert(`小组 "${groupName}" 创建成功！`);
                
                // 3. 刷新小组列表 - 这是关键！
                await loadUserGroups(userId);
                
                console.log('✅ 小组创建流程完成，页面已刷新');
                
            } catch (error) {
                console.error('❌ 创建小组失败:', error);
                alert(`创建失败: ${error.message}`);
            } finally {
                // 恢复按钮状态
                submitCreateBtn.disabled = false;
                submitCreateBtn.textContent = originalText;
            }
        });
    }
    
    // ========== 功能函数 ==========
    
    /**
     * 加载用户的小组列表
     */
    async function loadUserGroups(userId) {
        console.log('📋 开始加载用户小组列表，用户ID:', userId);
        
        // 显示加载状态
        groupsListElement.innerHTML = `
            <div style="text-align: center; padding: 40px;">
                <div class="loading"></div>
                <p>正在加载小组列表...</p>
            </div>
        `;
        
        try {
            // 确保userId是数字
            const numericUserId = parseInt(userId);
            if (isNaN(numericUserId)) {
                throw new Error('用户ID无效');
            }
            
            console.log('调用API: getUserGroups with userId', numericUserId);
            
            // 调用API获取用户的小组列表
            const groups = await window.api.getUserGroups(numericUserId);
            console.log('获取到的小组列表:', groups);
            
            // 渲染小组列表
            renderGroupsList(groups);
            
        } catch (error) {
            console.error('❌ 加载小组列表失败:', error);
            
            // 使用模拟数据
            console.log('使用模拟数据');
            const mockGroups = getMockGroups();
            renderGroupsList(mockGroups);
            
            alert('小组列表加载失败，显示模拟数据: ' + error.message);
        }
    }
    
    /**
     * 渲染小组列表
     */
    function renderGroupsList(groups) {
        console.log('🎨 渲染小组列表，数量:', groups?.length || 0);
        
        if (!groups || groups.length === 0) {
            groupsListElement.innerHTML = `
                <div class="empty-state">
                    <h3>暂无学习小组</h3>
                    <p>创建一个小组开始学习吧！</p>
                </div>
            `;
            return;
        }
        
        let html = '';
        
        groups.forEach((group) => {
            // 格式化创建时间
            const createTime = group.create_time ? 
                formatDateTime(group.create_time) : 
                '未知时间';
            
            html += `
                <div class="group-card" data-group-id="${group.group_id}">
                    <div class="group-header">
                        <div class="group-title">
                            <h4>${group.group_name || '未命名小组'}</h4>
                            <div class="group-members">
                                <span>📅 创建于 ${createTime}</span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="group-info">
                        ${group.course_name ? `课程：${group.course_name} (${group.course_code || ''})` : '未关联课程'}
                    </div>
                    
                    <div class="group-actions">
                        <button class="enter-btn" onclick="enterGroup(${group.group_id})">
                            进入小组
                        </button>
                    </div>
                </div>
            `;
        });
        
        groupsListElement.innerHTML = html;
        console.log('✅ 小组列表渲染完成');
    }
    
    /**
     * 格式化日期时间
     */
    function formatDateTime(dateString) {
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('zh-CN');
        } catch (e) {
            return dateString;
        }
    }
    
    /**
     * 获取模拟小组数据
     */
    function getMockGroups() {
        return [
            {
                group_id: 1,
                group_name: "第一小组",
                create_time: "2025-12-01 20:58:57",
                course_id: 1,
                course_name: "数据库系统",
                course_code: "CS301"
            },
            {
                group_id: 2,
                group_name: "第二小组",
                create_time: "2025-12-01 20:58:57",
                course_id: 2,
                course_name: "Web开发",
                course_code: "CS302"
            }
        ];
    }
});

/**
 * 进入小组函数（全局可访问）
 */
function enterGroup(groupId) {
    console.log('进入小组:', groupId);
    window.location.href = `/static/pages/group-home.html?group=${groupId}`;
}