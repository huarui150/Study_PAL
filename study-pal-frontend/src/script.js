document.addEventListener('DOMContentLoaded', function() {
    // 页面加载动画
    document.body.classList.add('page-loaded');
    
    // 全局通用函数
    
    // 登录表单处理
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            e.preventDefault();
            handleLogin();
        });
    }
    
    // 注册表单处理
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', function(e) {
            e.preventDefault();
            handleRegister();
        });
    }
    
    // 输入框焦点效果
    const inputs = document.querySelectorAll('input');
    inputs.forEach(input => {
        // 初始化时检查是否有值
        if (input.value) {
            input.classList.add('has-value');
        }
        
        // 获得焦点时添加类
        input.addEventListener('focus', function() {
            this.parentElement.classList.add('focused');
        });
        
        // 失去焦点时移除类
        input.addEventListener('blur', function() {
            this.parentElement.classList.remove('focused');
            if (this.value) {
                this.classList.add('has-value');
            } else {
                this.classList.remove('has-value');
            }
        });
    });
    
    // 退出登录功能
    const logoutBtn = document.querySelector('.logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function(e) {
            e.preventDefault();
            handleLogout();
        });
    }
});

// 处理登录
function handleLogin() {
    const studentId = document.getElementById('studentId').value;
    const password = document.getElementById('password').value;
    const rememberMe = document.getElementById('rememberMe').checked;
    
    // 简单验证
    if (!studentId || !password) {
        showMessage('请填写所有字段', 'error');
        return;
    }
    
    // 准备请求数据
    const loginData = {
        student_id: studentId,
        password: password
    };
    
    // 登录请求
    const loginButton = document.querySelector('.auth-submit');
    const originalText = loginButton.innerHTML;
    loginButton.innerHTML = '<span>登录中...</span>';
    loginButton.disabled = true;
    
    // 发送登录请求到后端API
    fetch(getApiUrl(API_CONFIG.AUTH.LOGIN), {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(loginData)
    })
    .then(response => {
        return response.json().then(data => ({
            status: response.status,
            body: data
        }));
    })
    .then(result => {
        const data = result.body;
        const status = result.status;
        
        if (status >= 400) {
            showMessage(data.error || '登录失败', 'error');
            loginButton.innerHTML = originalText;
            loginButton.disabled = false;
            return;
        }
        
        if (data.error) {
            showMessage(data.error, 'error');
            loginButton.innerHTML = originalText;
            loginButton.disabled = false;
            return;
        }
        
        // 保存用户信息到本地存储
        localStorage.setItem('isLoggedIn', 'true');
        localStorage.setItem('token', data.token);
        localStorage.setItem('userInfo', JSON.stringify(data.user_info));
        
        if (rememberMe) {
            localStorage.setItem('rememberMe', 'true');
        }
        
        showMessage('登录成功！', 'success');
        
        // 跳转到主页面
        setTimeout(() => {
            window.location.href = 'dashboard.html';
        }, 1000);
    })
    .catch(error => {
        console.error('Error:', error);
        showMessage('网络错误，请稍后重试', 'error');
        loginButton.innerHTML = originalText;
        loginButton.disabled = false;
    });
}

// 处理注册
function handleRegister() {
    const name = document.getElementById('name').value;
    const studentId = document.getElementById('studentId').value;
    const major = document.getElementById('major').value;
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    const agreeTerms = document.getElementById('agreeTerms').checked;
    
    // 验证表单
    if (!name || !studentId || !major || !password || !confirmPassword) {
        showMessage('请填写所有字段', 'error');
        return;
    }
    
    if (password !== confirmPassword) {
        showMessage('两次输入的密码不一致', 'error');
        return;
    }
    
    if (!agreeTerms) {
        showMessage('请同意服务条款和隐私政策', 'error');
        return;
    }
    
    // 准备请求数据
    const registerData = {
        name: name,
        student_id: studentId,
        major: major,
        password: password
    };
    
    // 注册请求
    const registerButton = document.querySelector('.auth-submit');
    const originalText = registerButton.innerHTML;
    registerButton.innerHTML = '<span>注册中...</span>';
    registerButton.disabled = true;
    
    // 发送注册请求到后端API
    fetch(getApiUrl(API_CONFIG.AUTH.REGISTER), {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(registerData)
    })
    .then(response => {
        return response.json().then(data => ({
            status: response.status,
            body: data
        }));
    })
    .then(result => {
        const data = result.body;
        const status = result.status;
        
        if (status >= 400) {
            showMessage(data.error || '注册失败', 'error');
            registerButton.innerHTML = originalText;
            registerButton.disabled = false;
            return;
        }
        
        if (data.error) {
            showMessage(data.error, 'error');
            registerButton.innerHTML = originalText;
            registerButton.disabled = false;
            return;
        }
        
        // 保存用户信息到本地存储
        localStorage.setItem('isLoggedIn', 'true');
        localStorage.setItem('token', data.token);
        localStorage.setItem('userInfo', JSON.stringify(data.user_info));
        
        showMessage('注册成功！', 'success');
        
        // 跳转到主页面
        setTimeout(() => {
            window.location.href = 'dashboard.html';
        }, 1000);
    })
    .catch(error => {
        console.error('Error:', error);
        showMessage('网络错误，请稍后重试', 'error');
        registerButton.innerHTML = originalText;
        registerButton.disabled = false;
    });
}

// 处理退出登录
function handleLogout(e) {
    e.preventDefault();
    
    // 清除本地存储的用户信息
    localStorage.removeItem('isLoggedIn');
    localStorage.removeItem('userInfo');
    localStorage.removeItem('token');
    
    // 跳转到登录页面
    window.location.href = 'login.html';
}

// 显示消息提示
function showMessage(message, type = 'info') {
    // 创建消息元素
    const messageElement = document.createElement('div');
    messageElement.className = `message message-${type}`;
    messageElement.textContent = message;
    
    // 添加样式
    Object.assign(messageElement.style, {
        position: 'fixed',
        top: '20px',
        right: '20px',
        padding: '15px 20px',
        borderRadius: '8px',
        color: 'white',
        fontWeight: '500',
        zIndex: '1000',
        boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
        transform: 'translateX(100%)',
        transition: 'transform 0.3s ease'
    });
    
    // 根据消息类型设置背景色
    switch(type) {
        case 'success':
            messageElement.style.background = 'linear-gradient(135deg, #28a745, #218838)';
            break;
        case 'error':
            messageElement.style.background = 'linear-gradient(135deg, #dc3545, #c82333)';
            break;
        case 'warning':
            messageElement.style.background = 'linear-gradient(135deg, #ffc107, #e0a800)';
            break;
        default:
            messageElement.style.background = 'linear-gradient(135deg, #3A5FCD, #2a4bb0)';
    }
    
    // 添加到页面
    document.body.appendChild(messageElement);
    
    // 动画显示
    setTimeout(() => {
        messageElement.style.transform = 'translateX(0)';
    }, 100);
    
    // 3秒后自动移除
    setTimeout(() => {
        messageElement.style.transform = 'translateX(100%)';
        setTimeout(() => {
            document.body.removeChild(messageElement);
        }, 300);
    }, 3000);
}

// 检查认证状态
function checkAuth() {
    const isLoggedIn = localStorage.getItem('isLoggedIn');
    if (!isLoggedIn && !window.location.href.includes('login.html') && !window.location.href.includes('register.html')) {
        window.location.href = 'login.html';
        return false;
    }
    return true;
}

// 加载用户信息
function loadUserInfo() {
    const userInfo = JSON.parse(localStorage.getItem('userInfo'));
    if (userInfo) {
        const userNameElements = document.querySelectorAll('#userName');
        userNameElements.forEach(element => {
            element.textContent = userInfo.name;
        });
    }
}

// 格式化日期
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

// 格式化时间
function formatTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

// 防抖函数
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// 节流函数
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// 检查成就解锁事件
function checkAchievementEvents() {
    // 监听来自服务器的成就事件
    // 这里可以实现WebSocket连接或者定期轮询
    
    // 示例：模拟成就解锁事件
    // 在实际应用中，这应该通过WebSocket或服务器推送实现
    /*
    setInterval(() => {
        // 模拟随机成就解锁
        if (Math.random() > 0.99) {
            const event = new CustomEvent('achievementUnlocked', {
                detail: {
                    name: '学习达人',
                    description: '连续学习30分钟',
                    points: 10
                }
            });
            document.dispatchEvent(event);
        }
    }, 5000);
    */
}

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 检查认证状态（除了登录和注册页面）
    if (!window.location.href.includes('login.html') && 
        !window.location.href.includes('register.html') &&
        !window.location.href.includes('index.html')) {
        checkAuth();
        loadUserInfo();
    }
    
    // 检查成就事件
    checkAchievementEvents();
});