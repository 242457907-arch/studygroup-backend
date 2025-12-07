// 任务看板页面逻辑
class TaskBoard {
    constructor() {
        if (!this.checkRequiredElements()) {
            console.error('TaskBoard: 必要的DOM元素缺失');
            return;
        }
        this.groupId = this.getGroupIdFromURL();
        this.tasks = [];
        this.isDragging = false;
        this.draggedTask = null;


        this.init();
    }

    checkRequiredElements() {
        const requiredElements = [
            'backBtn',
            'refreshBtn',
            'boardTitle',
            'groupName',
            'groupIcon',
            'createTaskModal',
            'todoList',
            'doingList',
            'doneList'
        ];
        
        for (const id of requiredElements) {
            if (!document.getElementById(id)) {
                console.error(`缺少元素: ${id}`);
                return false;
            }
        }
        return true;
    }

    // 初始化页面
    async init() {
        if (!this.groupId) {
            alert('小组ID无效');
            window.location.href = '/groups';
            return;
        }

        await this.loadPageData();
        this.setupEventListeners();
        this.setupDragAndDrop();
    }

    // 从URL获取小组ID
    getGroupIdFromURL() {
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get('group_id');
    }

    // 加载页面数据
    async loadPageData() {
        try {
            // 显示加载状态
            this.showLoading(true);

            // 并行加载小组信息和任务列表
            const [groupData, tasksData] = await Promise.all([
                groupModel.getGroup(this.groupId),
                taskModel.getGroupTasks(this.groupId)
            ]);

            this.tasks = tasksData;
            this.renderPage(groupData);
            this.renderTasks();

        } catch (error) {
            console.error('加载数据失败:', error);
            this.showError('加载数据失败，请刷新重试');
        } finally {
            this.showLoading(false);
        }
    }

    // 渲染页面信息
    renderPage(group) {
        // 更新页面标题
        document.getElementById('boardTitle').textContent = `任务看板 - ${group.name}`;
        document.getElementById('groupName').textContent = group.name;
        document.getElementById('groupIcon').textContent = group.getIconLetter();
    }

    // 渲染所有任务
    renderTasks() {
        // 清空所有列
        document.querySelectorAll('.task-list').forEach(list => {
            list.innerHTML = '';
        });

        // 统计数据
        let todoCount = 0, doingCount = 0, doneCount = 0, overdueCount = 0;

        // 渲染每个任务
        this.tasks.forEach(task => {
            this.renderTaskCard(task);
            
            // 统计数量
            if (task.status === '待处理') todoCount++;
            if (task.status === '进行中') doingCount++;
            if (task.status === '已完成') doneCount++;
            if (task.isOverdue()) overdueCount++;
        });

        // 更新统计数据
        this.updateStats(todoCount, doingCount, doneCount, overdueCount);
        
        // 更新列标题数量
        this.updateColumnCounts(todoCount, doingCount, doneCount);

        // 显示空状态
        this.showEmptyStates();
    }

    // 渲染单个任务卡片
    renderTaskCard(task) {
        const taskList = document.getElementById(`${task.status}List`);
        if (!taskList) return;

        const taskCard = document.createElement('div');
        taskCard.className = `task-card ${task.getPriorityClass()}`;
        taskCard.dataset.taskId = task.id;
        taskCard.draggable = true;

        // 检查是否过期
        const isOverdue = task.isOverdue();
        const dueDateClass = isOverdue ? 'overdue' : '';

        // 获取负责人首字母
        const assigneeInitial = task.assignee ? task.assignee.charAt(0).toUpperCase() : '?';

        taskCard.innerHTML = `
            <div class="task-header">
                <h3 class="task-title">${this.escapeHtml(task.title)}</h3>
                <span class="task-priority ${task.getPriorityClass()}">${task.priority}优先级</span>
            </div>
            <div class="task-description" title="${this.escapeHtml(task.description)}">
                ${this.truncateText(this.escapeHtml(task.description), 60)}
            </div>
            <div class="task-footer">
                <div class="assignee">
                    <div class="assignee-avatar" style="background-color: ${this.getColorFromName(task.assignee)}">
                        ${assigneeInitial}
                    </div>
                    <span>${task.assignee || '未分配'}</span>
                </div>
                <div class="due-date ${dueDateClass}" title="截止日期: ${task.dueDate ? task.dueDate.toLocaleDateString('zh-CN') : '无'}">
                    📅 ${task.getDueDateText()}
                </div>
            </div>
        `;

        // 添加双击编辑功能
        taskCard.addEventListener('dblclick', () => this.editTask(task.id));

        taskList.appendChild(taskCard);
    }

    // 更新统计数据
    updateStats(todo, doing, done, overdue) {
        document.getElementById('todoCount').textContent = todo;
        document.getElementById('doingCount').textContent = doing;
        document.getElementById('doneCount').textContent = done;
        document.getElementById('overdueCount').textContent = overdue;
    }

    // 更新列标题数量
    updateColumnCounts(todo, doing, done) {
        document.getElementById('todoColumnCount').textContent = todo;
        document.getElementById('doingColumnCount').textContent = doing;
        document.getElementById('doneColumnCount').textContent = done;
    }

    // 显示空状态
    showEmptyStates() {
        const columns = ['待处理', '进行中', '已完成'];
        
        columns.forEach(status => {
            const list = document.getElementById(`${status}List`);
            const emptyState = document.createElement('div');
            emptyState.className = 'empty-state';
            
            if (list.children.length === 0) {
                emptyState.innerHTML = `
                    <h4>暂无任务</h4>
                    <p>点击"添加任务"按钮创建新任务</p>
                `;
                list.appendChild(emptyState);
            }
        });
    }

    // 设置事件监听器
    setupEventListeners() {
        // 返回按钮
        document.getElementById('backBtn').addEventListener('click', () => {
            window.history.back();
        });

        // 刷新按钮
        document.getElementById('refreshBtn').addEventListener('click', () => {
            this.loadPageData();
        });

        // 添加任务按钮
        document.querySelectorAll('.add-task-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const status = e.target.dataset.status;
                this.openCreateTaskModal(status);
            });
        });

        // 创建任务模态框
        const createModal = document.getElementById('createTaskModal');
        const closeModalBtn = document.getElementById('closeCreateModal');
        const cancelBtn = document.getElementById('cancelCreateTask');
        const createForm = document.getElementById('createTaskForm');

        // 打开模态框
        document.getElementById('submitCreateTask').addEventListener('click', async (e) => {
            e.preventDefault();
            await this.handleCreateTask();
        });

        // 关闭模态框
        [closeModalBtn, cancelBtn].forEach(btn => {
            btn.addEventListener('click', () => {
                createModal.style.display = 'none';
            });
        });

        // 点击模态框外部关闭
        createModal.addEventListener('click', (e) => {
            if (e.target === createModal) {
                createModal.style.display = 'none';
            }
        });

        // 表单提交
        createForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.handleCreateTask();
        });
    }

    // 设置拖放功能
    setupDragAndDrop() {
        const taskLists = document.querySelectorAll('.task-list');
        const columns = document.querySelectorAll('.board-column');

        // 拖拽开始
        document.addEventListener('dragstart', (e) => {
            if (e.target.classList.contains('task-card')) {
                this.draggedTask = e.target;
                e.target.classList.add('dragging');
                
                // 设置拖拽效果
                e.dataTransfer.effectAllowed = 'move';
                e.dataTransfer.setData('text/plain', e.target.dataset.taskId);
            }
        });

        // 拖拽结束
        document.addEventListener('dragend', (e) => {
            if (e.target.classList.contains('task-card')) {
                e.target.classList.remove('dragging');
                columns.forEach(col => col.classList.remove('drop-zone'));
                this.draggedTask = null;
            }
        });

        // 拖拽经过
        columns.forEach(column => {
            column.addEventListener('dragover', (e) => {
                e.preventDefault();
                if (this.draggedTask) {
                    e.dataTransfer.dropEffect = 'move';
                    column.classList.add('drop-zone');
                }
            });

            column.addEventListener('dragleave', () => {
                column.classList.remove('drop-zone');
            });

            column.addEventListener('drop', async (e) => {
                e.preventDefault();
                column.classList.remove('drop-zone');
                
                if (!this.draggedTask) return;
                
                const taskId = this.draggedTask.dataset.taskId;
                const newStatus = column.querySelector('.task-list').dataset.status;
                
                // 如果状态未改变，不做处理
                if (this.draggedTask.closest('.task-list').dataset.status === newStatus) {
                    return;
                }
                
                await this.updateTaskStatus(taskId, newStatus);
            });
        });
    }

    // 打开创建任务模态框
    openCreateTaskModal(defaultStatus = '待处理') {
        const modal = document.getElementById('createTaskModal');
        const statusSelect = document.getElementById('taskStatus');
        
        // 设置默认状态
        statusSelect.value = defaultStatus;
        
        // 设置截止日期最小值为今天
        const today = new Date().toISOString().split('T')[0];
        document.getElementById('taskDueDate').min = today;
        
        // 重置表单
        document.getElementById('createTaskForm').reset();
        
        modal.style.display = 'flex';
        document.getElementById('taskTitle').focus();
    }

    // 处理创建任务
    async handleCreateTask() {
        try {
            // 获取表单数据
            const taskData = {
                title: document.getElementById('taskTitle').value.trim(),
                description: document.getElementById('taskDescription').value.trim(),
                priority: document.getElementById('taskPriority').value,
                assignee: document.getElementById('taskAssignee').value.trim(),
                status: document.getElementById('taskStatus').value,
                dueDate: document.getElementById('taskDueDate').value || null,
            };

            // 验证标题
            if (!taskData.title) {
                alert('请输入任务标题');
                return;
            }

            // 创建任务
            const newTask = await taskModel.createTask(this.groupId, taskData);
            
            // 添加到任务列表
            this.tasks.push(newTask);
            
            // 重新渲染任务
            this.renderTasks();
            
            // 关闭模态框
            document.getElementById('createTaskModal').style.display = 'none';
            
            // 显示成功消息
            this.showMessage('任务创建成功！', 'success');
            
        } catch (error) {
            console.error('创建任务失败:', error);
            this.showError('创建任务失败，请重试');
        }
    }

    // 更新任务状态（拖放后）
    async updateTaskStatus(taskId, newStatus) {
        try {
            // 更新后端
            await taskModel.updateTaskStatus(taskId, newStatus);
            
            // 更新本地数据
            const taskIndex = this.tasks.findIndex(task => task.id == taskId);
            if (taskIndex !== -1) {
                this.tasks[taskIndex].status = newStatus;
            }
            
            // 重新渲染任务
            this.renderTasks();
            
            // 显示成功消息
            this.showMessage('任务状态已更新！', 'success');
            
        } catch (error) {
            console.error('更新任务状态失败:', error);
            this.showError('更新任务状态失败');
            // 回滚UI
            this.renderTasks();
        }
    }

    // 编辑任务（双击）
    async editTask(taskId) {
        // 这里可以扩展编辑功能
        // 例如打开编辑模态框
        console.log('编辑任务:', taskId);
        // 提示用户
        this.showMessage('编辑功能开发中...', 'info');
    }

    // 显示加载状态
    showLoading(show) {
        const container = document.querySelector('.task-board-container');
        if (show) {
            container.style.opacity = '0.6';
            container.style.pointerEvents = 'none';
        } else {
            container.style.opacity = '1';
            container.style.pointerEvents = 'auto';
        }
    }

    // 显示消息
    showMessage(message, type = 'info') {
        // 移除现有消息
        const existingMessage = document.querySelector('.toast-message');
        if (existingMessage) {
            existingMessage.remove();
        }
        
        // 创建新消息
        const toast = document.createElement('div');
        toast.className = `toast-message toast-${type}`;
        toast.textContent = message;
        
        // 添加到页面
        document.body.appendChild(toast);
        
        // 显示动画
        setTimeout(() => {
            toast.classList.add('show');
        }, 10);
        
        // 3秒后自动移除
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.remove();
                }
            }, 300);
        }, 3000);
    }

    // 显示错误
    showError(message) {
        this.showMessage(message, 'error');
    }

    // 工具函数：截断文本
    truncateText(text, maxLength) {
        if (!text) return '暂无描述';
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    }

    // 工具函数：转义HTML
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // 工具函数：根据名字生成颜色
    getColorFromName(name) {
        if (!name) return '#95a5a6';
        
        const colors = [
            '#3498db', '#2ecc71', '#e74c3c', '#f39c12',
            '#9b59b6', '#1abc9c', '#34495e', '#16a085',
            '#27ae60', '#2980b9', '#8e44ad', '#2c3e50',
            '#d35400', '#c0392b', '#7f8c8d'
        ];
        
        // 使用名字的字符代码总和来确定颜色
        let sum = 0;
        for (let i = 0; i < name.length; i++) {
            sum += name.charCodeAt(i);
        }
        
        return colors[sum % colors.length];
    }
}

// 添加Toast消息样式
const toastStyle = document.createElement('style');
toastStyle.textContent = `
    .toast-message {
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 20px;
        border-radius: 8px;
        color: white;
        font-size: 14px;
        z-index: 3000;
        transform: translateX(100%);
        opacity: 0;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    .toast-message.show {
        transform: translateX(0);
        opacity: 1;
    }
    
    .toast-success {
        background-color: #2ecc71;
    }
    
    .toast-error {
        background-color: #e74c3c;
    }
    
    .toast-info {
        background-color: #3498db;
    }
`;
document.head.appendChild(toastStyle);


// // 页面加载完成后初始化
// document.addEventListener('DOMContentLoaded', () => {
//     // 检查用户是否登录
//     userModel.getCurrentUser().then(() => {
//         new TaskBoard();
//     }).catch(error => {
//         console.error('用户未登录或获取用户信息失败:', error);
//         // 重定向到登录页面
//         window.location.href = '/login';
//     });
// });