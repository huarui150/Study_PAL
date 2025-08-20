// AI辅导页面智能聊天系统
class AIChatSystem {
    constructor() {
        this.messages = [];
        this.apiBaseUrl = 'http://localhost:5000/api';
        this.staticBaseUrl = 'http://localhost:5000/static';
        this.init();
    }

    init() {
        this.checkAuth();
        this.bindEvents();
        this.loadUserInfo();
        this.loadAIServiceStatus();
        this.addBotMessage('你好！我是大连理工智能学习助手 🤖\n\n我现在具备了真正的AI对话能力！你可以：\n\n🎯 **智能对话**\n• 问我任何学习相关的问题\n• 寻求学习方法和建议\n• 进行日常交流\n\n📋 **信息查询**\n• 📚 课程表和校历\n• 🚌 班车时刻表\n• 💻 系统状态\n\n试试问我一些问题吧！比如"如何提高学习效率？"或者"今天几点了？"');
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

    async loadAIServiceStatus() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/ai/status`);
            if (response.ok) {
                const status = await response.json();
                console.log('AI服务状态:', status);
                
                // 可以在界面上显示AI服务状态
                const statusIndicator = document.createElement('div');
                statusIndicator.style.cssText = 'position: fixed; top: 10px; right: 10px; background: #28a745; color: white; padding: 5px 10px; border-radius: 15px; font-size: 12px; z-index: 1000;';
                statusIndicator.textContent = `🤖 ${status.service_name} - ${status.status}`;
                document.body.appendChild(statusIndicator);
                
                // 3秒后自动隐藏
                setTimeout(() => {
                    statusIndicator.remove();
                }, 3000);
            }
        } catch (error) {
            console.log('获取AI服务状态失败:', error);
        }
    }

    bindEvents() {
        const messageInput = document.getElementById('messageInput');
        const sendButton = document.getElementById('sendButton');
        const quickActionButtons = document.querySelectorAll('.quick-action-btn');
        const coursesLink = document.querySelector('a[href="courses.html"], a[data-nav="courses"]');

        // 发送消息
        sendButton.addEventListener('click', () => {
            this.sendMessage();
        });

        // 回车发送
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });

        // 快捷操作按钮
        quickActionButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                const query = e.currentTarget.dataset.query;
                messageInput.value = query;
                this.sendMessage();
            });
        });

        // 课程按钮导航健壮性：若页面路径问题，统一跳到 /study-pal-frontend/src/courses.html
        if (coursesLink) {
            coursesLink.addEventListener('click', (e) => {
                e.preventDefault();
                const target = 'courses.html';
                if (window.location.pathname.includes('/study-pal-frontend/src/')) {
                    window.location.href = 'courses.html';
                } else {
                    window.location.href = '/study-pal-frontend/src/courses.html';
                }
            });
        }
    }

    async sendUserMessage(userText) {
        const userInfo = JSON.parse(localStorage.getItem('userInfo')) || {};
        const userId = userInfo.id || userInfo.student_id || 1;
        try {
            const resp = await fetch(`${this.apiBaseUrl}/ai/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: userText, user_id: userId })
            });
            const data = await resp.json();
            if (data && data.achievement_events && data.achievement_events.length) {
                data.achievement_events.forEach(evt => {
                    if (typeof window !== 'undefined') window.postMessage(evt, '*');
                    if (evt.event === 'achievement.unlocked') {
                        const event = new CustomEvent('achievementUnlocked', { detail: {
                            name: evt.name,
                            description: evt.description,
                            points: evt.points
                        }});
                        document.dispatchEvent(event);
                    }
                });
            }
            return data;
        } catch (e) {
            return { type: 'error', message: '服务暂时不可用' };
        }
    }

    sendMessage() {
        const input = document.getElementById('messageInput');
        const message = input.value.trim();
        
        if (message) {
            this.addUserMessage(message);
            this.processUserInput(message);
            input.value = '';
        }
    }

    addUserMessage(content) {
        const message = {
            type: 'user',
            content: content
        };
        this.addMessage(message);
    }

    addBotMessage(content, imageUrl = null) {
        const message = {
            type: 'bot',
            content: content,
            imageUrl: imageUrl
        };
        this.addMessage(message);
    }

    addMessage(message) {
        this.messages.push(message);
        this.renderMessage(message);
        this.scrollToBottom();
    }

    renderMessage(message) {
        const messagesContainer = document.getElementById('chatMessages');
        const messageElement = document.createElement('div');
        messageElement.className = `message ${message.type === 'user' ? 'sent' : 'received'}`;

        if (message.type === 'bot') {
            const avatar = document.createElement('div');
            avatar.className = 'message-avatar';
            avatar.textContent = 'AI';
            messageElement.appendChild(avatar);
        }

        const content = document.createElement('div');
        content.className = 'message-content';
        content.innerHTML = message.content.replace(/\n/g, '<br>');

        // 如果有图片，添加图片显示
        if (message.imageUrl) {
            const imageContainer = document.createElement('div');
            imageContainer.className = 'message-image';
            imageContainer.style.cssText = 'margin-top: 15px; text-align: center; padding: 10px; background: #f8f9fa; border-radius: 8px;';
            
            // 构建正确的图片URL
            let fullImageUrl;
            if (message.imageUrl.startsWith('http')) {
                fullImageUrl = message.imageUrl;
            } else if (message.imageUrl.startsWith('/static/')) {
                fullImageUrl = `${this.staticBaseUrl}${message.imageUrl.replace('/static', '')}`;
            } else {
                fullImageUrl = `${this.staticBaseUrl}/${message.imageUrl.replace(/^\//, '')}`;
            }
            
            console.log('图片URL:', fullImageUrl); // 调试用
            
            const image = document.createElement('img');
            image.src = fullImageUrl;
            image.style.cssText = `
                max-width: 100%; 
                max-height: 350px; 
                border-radius: 8px; 
                border: 2px solid #e9ecef;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                cursor: pointer;
                transition: transform 0.2s;
            `;
            image.alt = '真实数据图片';
            
            // 鼠标悬停效果
            image.onmouseenter = () => {
                image.style.transform = 'scale(1.02)';
            };
            image.onmouseleave = () => {
                image.style.transform = 'scale(1)';
            };
            
            // 点击放大功能
            image.onclick = () => {
                window.open(fullImageUrl, '_blank');
            };
            
            // 添加加载成功处理
            image.onload = () => {
                console.log('图片加载成功:', fullImageUrl);
                const loadingText = imageContainer.querySelector('.loading-text');
                if (loadingText) loadingText.remove();
            };
            
            // 添加加载错误处理
            image.onerror = () => {
                console.error('图片加载失败:', fullImageUrl);
                imageContainer.innerHTML = `
                    <div style="padding: 20px; background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 8px; color: #856404;">
                        <p><strong>📷 图片暂时无法显示</strong></p>
                        <p>这可能是因为：</p>
                        <ul style="text-align: left; margin: 10px 0;">
                            <li>服务器正在启动中</li>
                            <li>图片文件正在加载</li>
                            <li>网络连接问题</li>
                        </ul>
                        <small style="color: #6c757d;">图片路径: ${fullImageUrl}</small>
                        <br><br>
                        <button onclick="location.reload()" style="padding: 8px 16px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer;">
                            🔄 刷新页面重试
                        </button>
                    </div>
                `;
            };
            
            // 添加加载提示
            imageContainer.innerHTML = '<div class="loading-text" style="color: #6c757d; font-size: 14px;">📷 正在加载图片...</div>';
            imageContainer.appendChild(image);
            content.appendChild(imageContainer);
        }

        messageElement.appendChild(content);
        messagesContainer.appendChild(messageElement);
    }

    showTypingIndicator() {
        const messagesContainer = document.getElementById('chatMessages');
        const typingElement = document.createElement('div');
        typingElement.className = 'message received typing';
        typingElement.id = 'typingIndicator';

        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = 'AI';

        const content = document.createElement('div');
        content.className = 'message-content';
        content.innerHTML = `
            <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
            </div>
        `;

        typingElement.appendChild(avatar);
        typingElement.appendChild(content);
        messagesContainer.appendChild(typingElement);
        this.scrollToBottom();
    }

    hideTypingIndicator() {
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    scrollToBottom() {
        const messagesContainer = document.getElementById('chatMessages');
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    async processUserInput(input) {
        this.showTypingIndicator();

        try {
            // 调用后端AI聊天接口
            const response = await fetch(`${this.apiBaseUrl}/ai/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: input })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            
            setTimeout(() => {
                this.hideTypingIndicator();
                
                // 根据响应类型显示不同内容
                if (data.image_url) {
                    this.addBotMessage(data.message, data.image_url);
                } else if (data.data && typeof data.data === 'object') {
                    // 格式化JSON数据显示
                    const formattedData = this.formatObjectData(data.data);
                    this.addBotMessage(data.message + '\n\n' + formattedData);
                } else {
                    this.addBotMessage(data.message);
                }
            }, 500);

        } catch (error) {
            console.error('处理用户输入错误:', error);
            setTimeout(() => {
                this.hideTypingIndicator();
                this.addBotMessage('抱歉，处理您的请求时出现错误。请稍后再试。');
            }, 500);
        }
    }

    formatObjectData(data) {
        if (!data || typeof data !== 'object') return '';
        
        let formatted = '';
        for (const [key, value] of Object.entries(data)) {
            formatted += `${key}: ${value}\n`;
        }
        return formatted.trim();
    }
}

// 初始化AI聊天系统
document.addEventListener('DOMContentLoaded', function() {
    // 确保在用户登录状态下初始化
    const isLoggedIn = localStorage.getItem('isLoggedIn');
    if (isLoggedIn) {
        window.aiChatSystem = new AIChatSystem();
    }
});