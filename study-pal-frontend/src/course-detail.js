// 课程详情页面JavaScript
class CourseDetailManager {
    constructor() {
        this.apiBaseUrl = 'http://localhost:5000/api';
        this.courseId = null;
        this.course = null;
        this.materials = [];
        this.currentTab = 'materials';
        this.init();
    }

    init() {
        try {
            this.checkAuth();
            this.loadUserInfo();
            this.getCourseIdFromUrl();
            this.bindEvents();
            this.loadCourseData();
        } catch (e) {
            console.error('初始化出错:', e);
        }
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
            document.getElementById('userName').textContent = userInfo.name;
        }
    }

    getCourseIdFromUrl() {
        const urlParams = new URLSearchParams(window.location.search);
        this.courseId = urlParams.get('id');
        if (!this.courseId) {
            alert('课程ID未找到');
            window.location.href = 'courses.html';
        }
    }

    bindEvents() {
        // 标签页切换
        document.querySelectorAll('.tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                this.switchTab(e.target.dataset.tab);
            });
        });

        // 文件上传
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');

        if (uploadArea && fileInput) {
            uploadArea.addEventListener('click', () => fileInput.click());
            uploadArea.addEventListener('dragover', this.handleDragOver.bind(this));
            uploadArea.addEventListener('dragleave', this.handleDragLeave.bind(this));
            uploadArea.addEventListener('drop', this.handleDrop.bind(this));
            fileInput.addEventListener('change', (e) => {
                this.uploadFiles(e.target.files);
            });
        }
    }

    switchTab(tabName) {
        // 更新标签样式
        document.querySelectorAll('.tab').forEach(tab => {
            tab.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

        // 更新内容显示
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(tabName).classList.add('active');

        this.currentTab = tabName;

        // 加载对应内容
        if (tabName === 'cards') {
            this.loadCards();
        } else if (tabName === 'quiz') {
            this.loadQuiz();
        }
    }

    async loadCourseData() {
        try {
            // 加载课程信息 - 简化为使用课程ID
            this.course = {
                id: this.courseId,
                name: `课程 ${this.courseId}`,
                weight: 1.0,
                exam_ratio: 0.6,
                color: '#007bff'
            };
            
            this.updateCourseHeader();
            this.loadMaterials();
        } catch (error) {
            console.error('加载课程数据失败:', error);
        }
    }

    updateCourseHeader() {
        if (!this.course) return;

        const header = document.getElementById('courseHeader');
        if (header) {
            header.style.background = `linear-gradient(135deg, ${this.course.color} 0%, #764ba2 100%)`;
        }
        const titleEl = document.getElementById('courseTitle');
        if (titleEl) titleEl.textContent = this.course.name;
        const weightEl = document.getElementById('courseWeight');
        if (weightEl) weightEl.textContent = this.course.weight;
        const ratioEl = document.getElementById('examRatio');
        if (ratioEl) ratioEl.textContent = `${Math.round(this.course.exam_ratio * 100)}%`;
    }

    async loadMaterials() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/courses/${this.courseId}/materials?user_id=1`);
            
            if (response.ok) {
                const data = await response.json();
                this.materials = data.materials || [];
                this.renderMaterials();
                document.getElementById('materialCount').textContent = this.materials.length;
            } else {
                console.error('加载资料失败');
                this.showEmptyMaterials();
            }
        } catch (error) {
            console.error('加载资料错误:', error);
            this.showEmptyMaterials();
        }
    }

    renderMaterials() {
        const materialList = document.getElementById('materialList');
        const emptyState = document.getElementById('materialsEmpty');

        if (this.materials.length === 0) {
            this.showEmptyMaterials();
            return;
        }

        emptyState.style.display = 'none';
        materialList.innerHTML = '';

        // 批量插入，减少回流
        const fragment = document.createDocumentFragment();
        for (const material of this.materials) {
            const item = this.createMaterialItem(material);
            fragment.appendChild(item);
        }
        materialList.appendChild(fragment);
    }

    createMaterialItem(material) {
        const item = document.createElement('div');
        item.className = 'material-item';
        
        const iconClass = this.getFileTypeIcon(material.type);
        const uploadDate = new Date(material.uploaded_at).toLocaleDateString();
        
        item.innerHTML = `
            <div class="material-icon ${material.type}">
                ${iconClass}
            </div>
            <div class="material-info">
                <div class="material-title">${material.title}</div>
                <div class="material-meta">
                    ${material.type.toUpperCase()} • 上传于 ${uploadDate}
                    ${material.card_count > 0 ? ` • 已生成卡片` : ''}
                </div>
            </div>
            <div class="material-actions">
                <button class="btn-icon btn-generate" 
                        onclick="courseDetail.generateCards(event, ${material.id})"
                        title="生成知识卡片"
                        ${material.card_count > 0 ? 'style="background: #6c757d;"' : ''}>
                    🎴
                </button>
                <button class="btn-icon btn-view" 
                        onclick="courseDetail.viewMaterial(${material.id})"
                        title="查看详情">
                    👁️
                </button>
                <button class="btn-icon btn-delete" 
                        onclick="courseDetail.deleteMaterial(${material.id})"
                        title="删除资料">
                    🗑️
                </button>
            </div>
        `;

        return item;
    }

    getFileTypeIcon(type) {
        const icons = {
            'pdf': '📄',
            'ppt': '📊',
            'doc': '📝',
            'image': '🖼️'
        };
        return icons[type] || '📄';
    }

    showEmptyMaterials() {
        document.getElementById('materialsEmpty').style.display = 'block';
        document.getElementById('materialList').innerHTML = '';
    }

    // 拖拽上传处理
    handleDragOver(e) {
        e.preventDefault();
        e.stopPropagation();
        document.getElementById('uploadArea').classList.add('dragover');
    }

    handleDragLeave(e) {
        e.preventDefault();
        e.stopPropagation();
        document.getElementById('uploadArea').classList.remove('dragover');
    }

    handleDrop(e) {
        e.preventDefault();
        e.stopPropagation();
        document.getElementById('uploadArea').classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        this.uploadFiles(files);
    }

    async uploadFiles(files) {
        if (!files || files.length === 0) return;

        const progressContainer = document.getElementById('uploadProgress');
        const progressFill = document.getElementById('progressFill');
        const uploadText = document.getElementById('uploadText');
        const uploadPercent = document.getElementById('uploadPercent');

        progressContainer.style.display = 'block';

        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            
            try {
                uploadText.textContent = `正在上传: ${file.name}`;
                
                const formData = new FormData();
                formData.append('file', file);
                formData.append('course_id', this.courseId);
                formData.append('title', file.name);
                formData.append('user_id', '1');

                const response = await fetch(`${this.apiBaseUrl}/materials`, {
                    method: 'POST',
                    body: formData
                });

                if (response.ok) {
                    const progress = ((i + 1) / files.length) * 100;
                    progressFill.style.width = `${progress}%`;
                    uploadPercent.textContent = `${Math.round(progress)}%`;
                    
                    this.showNotification(`${file.name} 上传成功`, 'success');
                } else {
                    let errorMessage = `HTTP ${response.status}`;
                    try {
                        const error = await response.json();
                        errorMessage = error.error || errorMessage;
                    } catch {
                        // 如果响应不是JSON，使用状态文本
                        errorMessage = response.statusText || errorMessage;
                    }
                    this.showNotification(`${file.name} 上传失败: ${errorMessage}`, 'error');
                }
            } catch (error) {
                console.error('上传文件错误:', error);
                this.showNotification(`${file.name} 上传失败`, 'error');
            }
        }

        // 隐藏进度条并重新加载资料列表
        setTimeout(() => {
            progressContainer.style.display = 'none';
            this.loadMaterials();
        }, 1000);
    }

    async generateCards(event, materialId) {
        try {
            // 显示加载状态
            const button = event ? event.target : null;
            const originalText = button.innerHTML;
            if (button) {
                button.innerHTML = '⏳';
                button.disabled = true;
            }
            
            this.showNotification('正在使用AI分析文档内容，生成知识卡片...', 'info');
            
            const response = await fetch(`${this.apiBaseUrl}/materials/${materialId}/cards`, {
                method: 'POST'
            });

            if (response.ok) {
                const data = await response.json();
                this.showNotification(`知识卡片生成成功！生成了${data.key_points_count}个要点，${data.terms_count}个术语`, 'success');
                this.loadMaterials(); // 重新加载以更新状态
                
                // 自动切换到卡片标签页
                setTimeout(() => this.switchTab('cards'), 500);
            } else {
                let errorMessage = '生成失败';
                try {
                    const error = await response.json();
                    errorMessage = error.error || errorMessage;
                } catch {
                    errorMessage = `HTTP ${response.status}: ${response.statusText}`;
                }
                this.showNotification(errorMessage, 'error');
            }
        } catch (error) {
            console.error('生成卡片错误:', error);
            this.showNotification('网络连接错误，请检查后端服务是否启动', 'error');
        } finally {
            // 恢复按钮状态
            try {
                if (button) {
                    button.innerHTML = '🎴';
                    button.disabled = false;
                }
            } catch (e) {
                // 按钮可能已被重新渲染
            }
        }
    }

    async loadCards() {
        const cardsContent = document.getElementById('cardsContent');
        const cardsEmpty = document.getElementById('cardsEmpty');
        const cardsLoading = document.getElementById('cardsLoading');

        // 查找有卡片的资料
        const materialsWithCards = this.materials.filter(m => m.card_count > 0);
        
        if (materialsWithCards.length === 0) {
            cardsEmpty.style.display = 'block';
            cardsContent.innerHTML = '';
            return;
        }

        cardsEmpty.style.display = 'none';
        cardsLoading.style.display = 'block';
        cardsContent.innerHTML = '';

        try {
            for (const material of materialsWithCards) {
                const response = await fetch(`${this.apiBaseUrl}/materials/${material.id}/cards?user_id=1`);
                
                if (response.ok) {
                    const data = await response.json();
                    const cardElement = this.createCardElement(material, data.card);
                    cardsContent.appendChild(cardElement);
                }
            }
        } catch (error) {
            console.error('加载卡片错误:', error);
        } finally {
            cardsLoading.style.display = 'none';
        }
    }

    createCardElement(material, card) {
        const cardDiv = document.createElement('div');
        cardDiv.className = 'card-preview';
        
        cardDiv.innerHTML = `
            <h3 style="margin-bottom: 20px; color: #333;">📚 ${material.title}</h3>
            
            <div class="card-section">
                <div class="card-section-title">📝 内容摘要</div>
                <p style="color: #666; line-height: 1.6;">${card.summary || '暂无摘要'}</p>
            </div>

            <div class="card-section">
                <div class="card-section-title">🎯 关键要点</div>
                <ul class="key-points">
                    ${(card.key_points || []).map(point => `<li>${point}</li>`).join('')}
                </ul>
            </div>

            <div class="card-section">
                <div class="card-section-title">📖 专业术语</div>
                <div class="terms-grid">
                    ${(card.terms || []).map(term => `
                        <div class="term-item">
                            <div class="term-name">${term.term || term}</div>
                            <div class="term-definition">${term.definition || '暂无定义'}</div>
                        </div>
                    `).join('')}
                </div>
            </div>

            <div class="card-section">
                <div class="card-section-title">💡 例题解析</div>
                <div class="examples-grid">
                    ${(card.examples || []).map(example => `
                        <div class="example-item">
                            <div class="example-title">${example.title || '例题'}</div>
                            <div class="example-content">${example.content || example}</div>
                            ${example.solution ? `<div class="example-solution"><strong>解答：</strong>${example.solution}</div>` : ''}
                        </div>
                    `).join('')}
                </div>
            </div>
        `;

        return cardDiv;
    }

    async loadQuiz() {
        // 简化实现，显示测验功能说明
        const quizContent = document.getElementById('quizContent');
        const quizEmpty = document.getElementById('quizEmpty');

        const materialsWithCards = this.materials.filter(m => m.card_count > 0);
        
        if (materialsWithCards.length === 0) {
            quizEmpty.style.display = 'block';
            quizContent.innerHTML = '';
            return;
        }

        quizEmpty.style.display = 'none';
        quizContent.innerHTML = `
            <div style="background: white; border-radius: 12px; padding: 25px;">
                <h3>📝 智能测验</h3>
                <p style="color: #666; margin-bottom: 20px;">基于已生成的知识卡片创建测验题</p>
                <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center;">
                    <div style="font-size: 48px; margin-bottom: 15px;">🚧</div>
                    <h4>测验功能开发中</h4>
                    <p style="color: #666;">即将支持自动生成选择题和填空题</p>
                </div>
            </div>
        `;
    }

    async viewMaterial(materialId) {
        const material = this.materials.find(m => m.id === materialId);
        if (material) {
            alert(`查看资料: ${material.title}\n类型: ${material.type}\n上传时间: ${material.uploaded_at}`);
        }
    }

    async deleteMaterial(materialId) {
        const material = this.materials.find(m => m.id === materialId);
        if (!material) return;

        if (!confirm(`确定要删除资料"${material.title}"吗？这将删除所有相关的卡片和数据。`)) {
            return;
        }

        try {
            const response = await fetch(`${this.apiBaseUrl}/materials/${materialId}?user_id=1`, {
                method: 'DELETE'
            });

            if (response.ok) {
                this.showNotification('资料删除成功', 'success');
                this.loadMaterials(); // 重新加载资料列表
            } else {
                const error = await response.json();
                this.showNotification(`删除失败: ${error.error}`, 'error');
            }
        } catch (error) {
            console.error('删除资料错误:', error);
            this.showNotification('网络错误，请稍后重试', 'error');
        }
    }

    showNotification(message, type = 'info') {
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

        if (!document.querySelector('#notification-styles')) {
            const style = document.createElement('style');
            style.id = 'notification-styles';
            style.textContent = `
                @keyframes slideIn {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
            `;
            document.head.appendChild(style);
        }

        document.body.appendChild(notification);

        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 3000);
    }
}

// 全局函数
function logout() {
    localStorage.removeItem('isLoggedIn');
    localStorage.removeItem('userInfo');
    window.location.href = 'login.html';
}

// 初始化课程详情管理器
let courseDetail;
document.addEventListener('DOMContentLoaded', function() {
    courseDetail = new CourseDetailManager();
});
