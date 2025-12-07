// 登录页面逻辑
document.addEventListener('DOMContentLoaded', function() {
    // 获取DOM元素
    const loginForm = document.getElementById('loginForm');
    const userIdInput = document.getElementById('user_id');
    const contactInput = document.getElementById('contact');
    const loginBtn = document.getElementById('loginBtn');
    const errorDiv = document.getElementById('errorMessage');
    const successDiv = document.getElementById('successMessage');
    
    // 自动填充测试账号（方便调试）
    userIdInput.value = '1';
    contactInput.value = '13800138000';
    
    // 显示消息函数
    function showMessage(element, message) {
        element.textContent = message;
        element.style.display = 'block';
        setTimeout(() => {
            element.style.display = 'none';
        }, 5000);
    }
    
    // 表单提交事件
    loginForm.addEventListener('submit', async function(event) {
        event.preventDefault(); // 阻止表单默认提交
        
        // 获取输入值
        const userId = userIdInput.value.trim();
        const contact = contactInput.value.trim();
        
        // 验证输入
        if (!userId) {
            showMessage(errorDiv, '请输入用户ID');
            userIdInput.focus();
            return;
        }
        
        if (!contact) {
            showMessage(errorDiv, '请输入联系方式');
            contactInput.focus();
            return;
        }
        
        // 禁用按钮，显示加载状态
        loginBtn.disabled = true;
        loginBtn.innerHTML = '<span class="loading"></span> 登录中...';
        
        try {
            console.log('开始登录，参数:', { userId, contact });
            
            // 调用API登录
            const result = await window.api.login(userId, contact);
            
            console.log('登录API返回:', result);
            
            // 保存用户信息到本地存储
            localStorage.setItem('user_id', result.user_id || userId);
            localStorage.setItem('user_contact', result.contact || contact);
            localStorage.setItem('user_name', result.user_name || '用户');
            localStorage.setItem('user_data', JSON.stringify(result || {}));
            
            showMessage(successDiv, '登录成功！正在跳转...');
            // 等待1秒后跳转
            setTimeout(() => {
                window.location.href = '/static/pages/group-list.html';
            }, 1000);
            
        } catch (error) {
            console.error('登录错误:', error);
            
            // 显示错误信息
            let errorMsg = error.message || '登录失败，请检查网络连接';
            
            // 如果是特定错误，提供友好提示
            if (errorMsg.includes('404') || errorMsg.includes('Not Found')) {
                errorMsg = 'API接口不存在，请检查后端是否正常运行';
            } else if (errorMsg.includes('NetworkError') || errorMsg.includes('Failed to fetch')) {
                errorMsg = '无法连接到服务器，请检查后端是否启动';
            }
            
            showMessage(errorDiv, errorMsg);
            
            // 恢复按钮状态
            loginBtn.disabled = false;
            loginBtn.textContent = '登录';
        }
    });
    
    // 输入框变化时隐藏错误信息
    userIdInput.addEventListener('input', () => {
        errorDiv.style.display = 'none';
    });
    
    contactInput.addEventListener('input', () => {
        errorDiv.style.display = 'none';
    });
    
    // 检查是否已经登录
    const savedUserId = localStorage.getItem('user_id');
    if (savedUserId) {
        console.log('检测到已登录用户:', savedUserId);
        // 可以选择自动跳转
        // window.location.href = '/static/pages/group-list.html';
    }
});