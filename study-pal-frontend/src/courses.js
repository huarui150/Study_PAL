// 课程管理JavaScript
class CourseManager {
    constructor() {
        this.apiBaseUrl = 'http://localhost:5000/api';
        this.courses = [];
        this.currentCourse = null;
        this.selectedColor = '#007bff';
        this.init();
    }

    init() {
        this.checkAuth();
        this.loadUserInfo();
        this.bindEvents();
        this.loadCourses();
    }

    checkAuth() {
        const isLoggedIn = localStorage.getItem('isLoggedIn');
        if (!isLoggedIn) {
            window.location.href = 'login.html';
            return;
        }
    }

    loadUserInfo() {
        const userInfo = JSON.parse(localStorage.getItem('userInfo'));
        if (userInfo) {
            const userNameElement = document.getElementById('userName');
            if (userNameElement) {
                userNameElement.textContent = userInfo.name;
            }
        }
    }

    bindEvents() {
        // 表单提交
        document.getElementById('courseForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveCourse();
        });

        // 颜色选择
        document.querySelectorAll('.color-option').forEach(option => {
            option.addEventListener('click', (e) => {
                document.querySelectorAll('.color-option').forEach(opt => opt.classList.remove('selected'));
                e.target.classList.add('selected');
                this.selectedColor = e.target.dataset.color;
            });
        });

        // ESC键关闭模态框
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeCourseModal();
            }
        });
    }

    async loadCourses() {
        try {
            const userInfo = JSON.parse(localStorage.getItem('userInfo'));
            // 临时使用student_id作为user_id（因为数据库中的user_id应该对应student_id）
            const response = await fetch(`${this.apiBaseUrl}/courses?user_id=1`);
            
            if (response.ok) {
                const data = await response.json();
                this.courses = data.courses || [];
                this.renderCourses();
            } else {
                console.error('加载课程失败');
                this.showEmptyState();
            }
        } catch (error) {
            console.error('加载课程错误:', error);
            this.showEmptyState();
        }
    }

    renderCourses() {
        const courseGrid = document.getElementById('courseGrid');
        const emptyState = document.getElementById('emptyState');
        
        if (this.courses.length === 0) {
            this.showEmptyState();
            return;
        }

        emptyState.style.display = 'none';
        
        // 保留添加课程卡片，清除其他内容
        const addCourseCard = courseGrid.querySelector('.add-course-card');
        courseGrid.innerHTML = '';
        courseGrid.appendChild(addCourseCard);

        // 渲染课程卡片
        // 使用文档片段批量插入，减少reflow
        const fragment = document.createDocumentFragment();
        for (const course of this.courses) {
            const courseCard = this.createCourseCard(course);
            fragment.appendChild(courseCard);
        }
        courseGrid.appendChild(fragment);
    }

    createCourseCard(course) {
        const card = document.createElement('div');
        card.className = 'course-card';
        card.style.borderLeftColor = course.color;
        
        card.innerHTML = `
            <div class="course-header">
                <h3 class="course-title">${course.name}</h3>
                <span class="course-weight">权重 ${course.weight}</span>
            </div>
            
            <div class="course-stats">
                <div class="stat-item">
                    <span class="stat-number">${course.material_count || 0}</span>
                    <span class="stat-label">资料</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number">${course.event_count || 0}</span>
                    <span class="stat-label">事件</span>
                </div>
                <div class="stat-item">
                    <span class="stat-number">${Math.round(course.exam_ratio * 100)}%</span>
                    <span class="stat-label">考试权重</span>
                </div>
            </div>
            
            <div class="course-actions">
                <button class="btn-sm btn-primary" onclick="courseManager.viewCourse(${course.id})">
                    查看详情
                </button>
                <button class="btn-sm btn-secondary" onclick="courseManager.editCourse(${course.id})">
                    编辑
                </button>
                <button class="btn-sm btn-danger" onclick="courseManager.deleteCourse(${course.id})">
                    删除
                </button>
            </div>
        `;

        return card;
    }

    showEmptyState() {
        document.getElementById('emptyState').style.display = 'block';
    }

    openAddCourseModal() {
        this.currentCourse = null;
        document.getElementById('modalTitle').textContent = '添加课程';
        document.getElementById('courseForm').reset();
        document.getElementById('courseWeight').value = '1.0';
        document.getElementById('examRatio').value = '0.6';
        
        // 重置颜色选择
        document.querySelectorAll('.color-option').forEach(opt => opt.classList.remove('selected'));
        document.querySelector('.color-option[data-color="#007bff"]').classList.add('selected');
        this.selectedColor = '#007bff';
        
        document.getElementById('courseModal').style.display = 'block';
    }

    closeCourseModal() {
        document.getElementById('courseModal').style.display = 'none';
    }

    async saveCourse() {
        try {
            const formData = {
                name: document.getElementById('courseName').value,
                weight: parseFloat(document.getElementById('courseWeight').value),
                exam_ratio: parseFloat(document.getElementById('examRatio').value),
                color: this.selectedColor
            };

            // 临时使用固定user_id
            formData.user_id = 1;

            let url = `${this.apiBaseUrl}/courses`;
            let method = 'POST';

            if (this.currentCourse) {
                url += `/${this.currentCourse.id}`;
                method = 'PUT';
            }

            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            if (response.ok) {
                this.closeCourseModal();
                this.loadCourses(); // 重新加载课程列表
                this.showNotification(this.currentCourse ? '课程更新成功' : '课程创建成功', 'success');
            } else {
                const error = await response.json();
                this.showNotification(error.error || '操作失败', 'error');
            }
        } catch (error) {
            console.error('保存课程错误:', error);
            this.showNotification('网络错误，请稍后重试', 'error');
        }
    }

    editCourse(courseId) {
        const course = this.courses.find(c => c.id === courseId);
        if (!course) return;

        this.currentCourse = course;
        document.getElementById('modalTitle').textContent = '编辑课程';
        document.getElementById('courseName').value = course.name;
        document.getElementById('courseWeight').value = course.weight;
        document.getElementById('examRatio').value = course.exam_ratio;

        // 设置颜色选择
        document.querySelectorAll('.color-option').forEach(opt => opt.classList.remove('selected'));
        const colorOption = document.querySelector(`[data-color="${course.color}"]`);
        if (colorOption) {
            colorOption.classList.add('selected');
            this.selectedColor = course.color;
        }

        document.getElementById('courseModal').style.display = 'block';
    }

    async deleteCourse(courseId) {
        const course = this.courses.find(c => c.id === courseId);
        if (!course) return;

        if (!confirm(`确定要删除课程"${course.name}"吗？这将删除所有相关的资料和数据。`)) {
            return;
        }

        try {
            const response = await fetch(`${this.apiBaseUrl}/courses/${courseId}?user_id=1`, {
                method: 'DELETE'
            });

            if (response.ok) {
                this.loadCourses(); // 重新加载课程列表
                this.showNotification('课程删除成功', 'success');
            } else {
                const error = await response.json();
                this.showNotification(error.error || '删除失败', 'error');
            }
        } catch (error) {
            console.error('删除课程错误:', error);
            this.showNotification('网络错误，请稍后重试', 'error');
        }
    }

    viewCourse(courseId) {
        // 跳转到课程详情页面
        window.location.href = `course-detail.html?id=${courseId}`;
    }

    showNotification(message, type = 'info') {
        // 创建通知元素
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            background: ${type === 'success' ? '#28a745' : type === 'error' ? '#dc3545' : '#007bff'};
            color: white;
            border-radius: 6px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 10000;
            font-size: 14px;
            max-width: 300px;
            animation: slideIn 0.3s ease;
        `;
        notification.textContent = message;

        // 添加CSS动画
        if (!document.querySelector('#notification-styles')) {
            const style = document.createElement('style');
            style.id = 'notification-styles';
            style.textContent = `
                @keyframes slideIn {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
                @keyframes slideOut {
                    from { transform: translateX(0); opacity: 1; }
                    to { transform: translateX(100%); opacity: 0; }
                }
            `;
            document.head.appendChild(style);
        }

        document.body.appendChild(notification);

        // 3秒后自动消失
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }
}

// 全局函数
function openAddCourseModal() {
    if (courseManager) {
        courseManager.openAddCourseModal();
    }
}

function closeCourseModal() {
    if (courseManager) {
        courseManager.closeCourseModal();
    }
}

function logout() {
    localStorage.removeItem('isLoggedIn');
    localStorage.removeItem('userInfo');
    window.location.href = 'login.html';
}

// 初始化课程管理器
let courseManager;
document.addEventListener('DOMContentLoaded', function() {
    courseManager = new CourseManager();
    
    // 绑定退出登录事件
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function(e) {
            e.preventDefault();
            logout();
        });
    }
});
