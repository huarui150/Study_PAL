// 成就系统页面逻辑
document.addEventListener('DOMContentLoaded', function() {
    // 检查用户登录状态
    checkAuth();

    // 加载用户信息
    loadUserInfo();

    // 自动检测成就并加载成就和任务信息
    autoCheckAchievements();

    // 绑定事件
    bindEvents();

    // 检查是否有新解锁的成就
    checkNewAchievements();
    // 初始化粒子与音效引擎
    initEffectsEngine();

    // 绑定测试成就按钮
    const testBtn = document.getElementById('testAchievementsBtn');
    if (testBtn) {
        testBtn.addEventListener('click', function() {
            console.log('测试成就按钮被点击');
            const userInfo = JSON.parse(localStorage.getItem('userInfo'));
            console.log('用户信息:', userInfo);

            if (userInfo && (userInfo.id || userInfo.student_id)) {
                const userId = userInfo.id || userInfo.student_id;
                console.log('发送测试成就请求, userId:', userId);

                fetch(getApiUrl(`/achievements/test/${userId}`), {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'}
                })
                .then(response => {
                    console.log('响应状态:', response.status);
                    return response.json();
                })
                .then(data => {
                    console.log('测试成就响应:', data);
                    if (data.events && data.events.length > 0) {
                        // 处理每个事件
                        data.events.forEach(event => {
                            console.log('处理事件:', event);
                            if (event.event === 'achievement.unlocked') {
                                showAchievementPopup(event.achievement);
                            } else if (event.event === 'coin.rewarded') {
                                showCoinReward(event.amount);
                            }
                        });
                        // 重新加载成就数据
                        setTimeout(() => {
                            loadAchievementsAndTasks();
                        }, 2000);
                    } else {
                        alert('测试成就已授予，但无新事件（可能已经拥有这些成就）');
                    }
                })
                .catch(error => {
                    console.error('测试成就失败:', error);
                    alert('测试成就失败: ' + error.message);
                });
            } else {
                alert('无法获取用户信息，请重新登录');
            }
        });
    } else {
        console.error('找不到测试成就按钮元素');
    }
});

// 检查用户是否已登录
function checkAuth() {
    const isLoggedIn = localStorage.getItem('isLoggedIn');
    if (!isLoggedIn) {
        window.location.href = 'login.html';
        return;
    }
}

// 加载用户信息
function loadUserInfo() {
    const userInfo = JSON.parse(localStorage.getItem('userInfo'));
    if (userInfo) {
        document.getElementById('userName').textContent = userInfo.name;
    }
}

// 自动检测成就并加载成就和任务信息
function autoCheckAchievements() {
    const userInfo = JSON.parse(localStorage.getItem('userInfo'));
    if (!userInfo) return;

    // 显示加载状态
    document.getElementById('achievementsGrid').innerHTML = '<div class="loading">检测成就中...</div>';
    document.getElementById('tasksContainer').innerHTML = '<div class="loading">加载任务中...</div>';

    const userId = userInfo.id || userInfo.student_id;

    // 首先触发成就检测
    fetch(getApiUrl(`/achievements/check/${userId}`), {
        method: 'POST',
        headers: {'Content-Type': 'application/json'}
    })
    .then(response => response.json())
    .then(data => {
        console.log('成就检测结果:', data);

        // 如果有新解锁的成就，显示动画
        if (data.events && data.events.length > 0) {
            data.events.forEach(event => {
                if (event.event === 'achievement.unlocked') {
                    showAchievementPopup(event);
                } else if (event.event === 'coin.rewarded') {
                    showCoinReward(event.amount);
                }
            });
        }

        // 然后加载成就和任务信息
        loadAchievementsAndTasks();
    })
    .catch(error => {
        console.error('成就检测失败:', error);
        // 即使检测失败，也继续加载成就信息
        loadAchievementsAndTasks();
    });
}

// 加载成就和任务信息
function loadAchievementsAndTasks() {
    const userInfo = JSON.parse(localStorage.getItem('userInfo'));
    if (!userInfo) return;

    // 显示加载状态
    document.getElementById('achievementsGrid').innerHTML = '<div class="loading">加载中...</div>';
    document.getElementById('tasksContainer').innerHTML = '<div class="loading">加载中...</div>';

    // 加载成就信息（优先使用id；无id时调用无参端点由后端解析）
    const achievementsUrl = userInfo && userInfo.id ?
        getApiUrl(`/achievements/${encodeURIComponent(userInfo.id)}`) :
        getApiUrl('/achievements');
    fetch(achievementsUrl)
        .then(response => response.json())
        .then(data => {
            renderAchievements(data.achievements);
            updateStats(data);
        })
        .catch(error => {
            console.error('加载成就信息失败:', error);
            document.getElementById('achievementsGrid').innerHTML = '<div class="empty-state">加载失败，请稍后重试</div>';
        });

    // 加载任务信息
    const tasksUrl = userInfo && userInfo.id ?
        getApiUrl(`/tasks/${encodeURIComponent(userInfo.id)}`) :
        getApiUrl('/tasks');
    fetch(tasksUrl)
        .then(response => response.json())
        .then(data => {
            renderTasks(data.daily_tasks);
            // 更新今日任务完成数
            const completedTasks = (data.daily_tasks || []).filter(task => task.completed).length;
            document.getElementById('todayTasksCount').innerHTML = `${completedTasks} <span>个</span>`;
        })
        .catch(error => {
            console.error('加载任务信息失败:', error);
            document.getElementById('tasksContainer').innerHTML = '<div class="empty-state">加载失败，请稍后重试</div>';
        });
}

// 渲染成就
function renderAchievements(achievements) {
    const grid = document.getElementById('achievementsGrid');
    grid.innerHTML = '';

    if (!achievements || achievements.length === 0) {
        grid.innerHTML = '<div class="empty-state">暂无成就，请继续努力学习！</div>';
        return;
    }

    // 按分类组织成就
    const categories = {};
    achievements.forEach(achievement => {
        if (!categories[achievement.category]) {
            categories[achievement.category] = [];
        }
        categories[achievement.category].push(achievement);
    });

    // 添加成就统计信息
    const statsElement = document.createElement('div');
    statsElement.className = 'achievement-stats-summary';
    statsElement.innerHTML = `
        <div class="stats-summary">
            <div class="stat-item">
                <span class="stat-label">总成就数:</span>
                <span class="stat-value">${achievements.length}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">总StudyCoin:</span>
                <span class="stat-value">${achievements.reduce((sum, a) => sum + (a.points || 0), 0)}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">成就分类:</span>
                <span class="stat-value">${Object.keys(categories).length}</span>
            </div>
        </div>
    `;
    grid.appendChild(statsElement);

    // 渲染所有成就
    Object.keys(categories).forEach(category => {
        const categoryElement = document.createElement('div');
        categoryElement.className = 'achievement-category-section';
        categoryElement.innerHTML = `
            <h5 class="category-title">
                ${category} 
                <span class="category-count">(${categories[category].length}个成就)</span>
            </h5>
        `;

        const categoryGrid = document.createElement('div');
        categoryGrid.className = 'category-achievements-grid';

        categories[category].forEach(achievement => {
            const achievementElement = document.createElement('div');
            achievementElement.className = 'achievement-item unlocked';
            achievementElement.innerHTML = `
                <div class="achievement-icon">🏆</div>
                <div class="achievement-info">
                    <h5>${achievement.name}</h5>
                    <p class="achievement-description">${achievement.description}</p>
                    <div class="achievement-points">+${achievement.points} StudyCoin</div>
                </div>
            `;
            categoryGrid.appendChild(achievementElement);
        });

        categoryElement.appendChild(categoryGrid);
        grid.appendChild(categoryElement);
    });
}

// 渲染任务
function renderTasks(tasks) {
    const container = document.getElementById('tasksContainer');
    container.innerHTML = '';

    if (!tasks || tasks.length === 0) {
        container.innerHTML = '<div class="empty-state">暂无任务</div>';
        return;
    }

    tasks.forEach(task => {
        const taskElement = document.createElement('div');
        taskElement.className = `task-item ${task.completed ? 'completed' : ''}`;
        taskElement.innerHTML = `
            <div class="task-info">
                <h5>${task.name}</h5>
                <p>${task.description}</p>
            </div>
            <div class="task-progress">
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${(task.progress/task.target)*100}%"></div>
                </div>
                <div class="progress-text">${task.progress}/${task.target}</div>
            </div>
            ${task.completed ? '<div class="task-status completed">已完成</div>' : ''}
        `;
        container.appendChild(taskElement);
    });
}

// 更新统计信息
function updateStats(data) {
    document.getElementById('studyCoinAmount').textContent = data.studycoin || 0;

    // 更新连续登录天数
    if (data.stats && data.stats.login_streak) {
        document.getElementById('loginStreakCount').innerHTML = `${data.stats.login_streak} <span>天</span>`;
    }

    // 更新已解锁成就数
    if (data.achievements) {
        document.getElementById('unlockedAchievementsCount').innerHTML = `${data.achievements.length} <span>个</span>`;
    }

    // 今日任务完成数
    const tasks = data.daily_tasks || [];
    const completedTasks = tasks.filter(task => task.completed).length;
    document.getElementById('todayTasksCount').innerHTML = `${completedTasks} <span>个</span>`;
}

// 绑定事件
function bindEvents() {
    // 分类按钮点击事件
    document.querySelectorAll('.category-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            // 更新活动状态
            document.querySelectorAll('.category-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');

            // 这里可以添加筛选成就的逻辑
            const category = this.dataset.category;
            filterAchievements(category);
        });
    });

    // 退出登录
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function(e) {
            e.preventDefault();

            // 清除本地存储的用户信息
            localStorage.removeItem('isLoggedIn');
            localStorage.removeItem('userInfo');
            localStorage.removeItem('token');

            // 跳转到登录页面
            window.location.href = 'login.html';
        });
    }
}

// 筛选成就
function filterAchievements(category) {
    const sections = document.querySelectorAll('.achievement-category-section');
    if (category === 'all') {
        sections.forEach(section => {
            section.style.display = 'block';
        });
    } else {
        sections.forEach(section => {
            const title = section.querySelector('.category-title').textContent;
            section.style.display = title === category ? 'block' : 'none';
        });
    }
}

// 显示成就解锁动画
function showAchievementPopup(achievement) {
    const popup = document.getElementById('achievementPopup');
    document.getElementById('achievementName').textContent = achievement.name;
    document.getElementById('achievementDescription').textContent = achievement.description;
    document.getElementById('rewardAmount').textContent = achievement.points;

    popup.style.display = 'block';

    // 添加动画类
    popup.classList.add('show');
    // 触发粒子与音效
    emitParticles({ big: achievement.name === '学习自驱力' });
    playSound('unlock');

    // 3秒后隐藏弹窗
    setTimeout(() => {
        popup.classList.remove('show');
        setTimeout(() => {
            popup.style.display = 'none';
        }, 500);
    }, 3000);
}

function showCoinReward(amount) {
    // 创建一个临时的StudyCoin奖励提示
    const coinReward = document.createElement('div');
    coinReward.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: linear-gradient(135deg, #ffd700, #ffed4e);
        color: #333;
        padding: 20px 30px;
        border-radius: 15px;
        font-size: 24px;
        font-weight: bold;
        z-index: 10000;
        box-shadow: 0 8px 32px rgba(255, 215, 0, 0.3);
        animation: coinPop 2s ease-out forwards;
    `;
    coinReward.innerHTML = `🪙 +${amount} StudyCoin`;

    // 添加动画样式
    const style = document.createElement('style');
    style.textContent = `
        @keyframes coinPop {
            0% { transform: translate(-50%, -50%) scale(0.5); opacity: 0; }
            20% { transform: translate(-50%, -50%) scale(1.2); opacity: 1; }
            80% { transform: translate(-50%, -50%) scale(1); opacity: 1; }
            100% { transform: translate(-50%, -50%) scale(1); opacity: 0; }
        }
    `;
    document.head.appendChild(style);

    document.body.appendChild(coinReward);

    // 播放获币音效
    playSound('coin');

    // 2秒后移除
    setTimeout(() => {
        document.body.removeChild(coinReward);
        document.head.removeChild(style);
    }, 2000);
}

// 检查新解锁的成就
function checkNewAchievements() {
    // 检查URL参数中是否有新解锁的成就
    const urlParams = new URLSearchParams(window.location.search);
    const newAchievement = urlParams.get('new_achievement');

    if (newAchievement) {
        try {
            const achievement = JSON.parse(decodeURIComponent(newAchievement));
            showAchievementPopup(achievement);

            // 清除URL参数
            window.history.replaceState({}, document.title, window.location.pathname);
        } catch (e) {
            console.error('解析成就信息失败:', e);
        }
    }
}

// 监听成就解锁事件
document.addEventListener('achievementUnlocked', function(e) {
    showAchievementPopup(e.detail);
});

// 统一事件处理：coin.rewarded、task.completed
window.addEventListener('message', function(e) {
    try {
        const data = e.data || {};
        if (data.event === 'coin.rewarded') {
            // 更新余额显示并播放获币音效
            const amount = data.amount || 0;
            const el = document.getElementById('studyCoinAmount');
            if (el) el.textContent = (parseInt(el.textContent || '0', 10) + amount);
            playSound('coin');
            emitParticles({});
        } else if (data.event === 'task.completed') {
            playSound('unlock');
            emitParticles({});
            // 轻提示
            console.log(`任务完成：${data.name} +${data.reward}SC`);
        }
    } catch (_) {}
});

// 粒子与音效引擎（简化实现，遵循规范参数）
let reduceMotion = false;
function initEffectsEngine() {
    try {
        reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    } catch (_) { reduceMotion = false; }
}

function emitParticles(opts) {
    if (reduceMotion) return;
    const big = !!(opts && opts.big);
    const duration = big ? 2500 : 1800;
    const count = big ? 120 : 60;
    const extraTrails = big ? 20 : 0;
    const container = document.body;
    const centerX = window.innerWidth / 2;
    const topY = 120;
    for (let i = 0; i < count + extraTrails; i++) {
        const p = document.createElement('div');
        p.className = 'particle';
        const isTrail = i >= count;
        p.style.position = 'fixed';
        p.style.left = centerX + 'px';
        p.style.top = topY + 'px';
        p.style.width = isTrail ? '3px' : '6px';
        p.style.height = isTrail ? '3px' : '6px';
        p.style.borderRadius = '50%';
        p.style.background = isTrail ? 'gold' : (Math.random() < 0.7 ? '#ffd166' : '#ffe66d');
        p.style.pointerEvents = 'none';
        p.style.zIndex = 9999;
        container.appendChild(p);
        const angle = (Math.random() * 45 - 22.5) * (Math.PI / 180);
        const speed = (400 + Math.random() * 400) / 1000; // px/ms
        const gravity = 900 / 1000; // px/ms^2
        const fade = 600; // ms
        const start = performance.now();
        const vx = Math.cos(angle) * speed * (Math.random() < 0.5 ? -1 : 1);
        const vy0 = -Math.sin(angle) * speed;
        function frame(t) {
            const elapsed = t - start;
            const x = centerX + vx * elapsed;
            const y = topY + vy0 * elapsed + 0.5 * gravity * elapsed * elapsed;
            p.style.transform = `translate(${x - centerX}px, ${y - topY}px)`;
            const remain = duration - elapsed;
            if (remain < fade) {
                p.style.opacity = (remain / fade).toFixed(2);
            }
            if (elapsed < duration) {
                requestAnimationFrame(frame);
            } else {
                p.remove();
            }
        }
        requestAnimationFrame(frame);
    }
}

let audioCtx;
function playSound(type) {
    if (reduceMotion) return;
    try {
        audioCtx = audioCtx || new (window.AudioContext || window.webkitAudioContext)();
        const o = audioCtx.createOscillator();
        const g = audioCtx.createGain();
        o.connect(g); g.connect(audioCtx.destination);
        const now = audioCtx.currentTime;
        if (type === 'unlock') {
            // C5→E5→G5 三音上行，300ms
            const freqs = [523.25, 659.25, 783.99];
            o.type = 'sine';
            g.gain.value = 0.001;
            o.start(now);
            freqs.forEach((f, idx) => {
                const t = now + idx * 0.1;
                o.frequency.setValueAtTime(f, t);
                g.gain.exponentialRampToValueAtTime(0.05, t + 0.09);
                g.gain.exponentialRampToValueAtTime(0.01, t + 0.1);
            });
            o.stop(now + 0.35);
        } else if (type === 'coin') {
            // 软木鱼音色 120ms
            o.type = 'triangle';
            o.frequency.value = 880;
            g.gain.value = 0.07;
            o.start(now);
            g.gain.exponentialRampToValueAtTime(0.001, now + 0.12);
            o.stop(now + 0.13);
        } else if (type === 'fail') {
            // 低音 G3 200ms（40%）
            o.type = 'sine';
            o.frequency.value = 196.00;
            g.gain.value = 0.04;
            o.start(now);
            g.gain.exponentialRampToValueAtTime(0.001, now + 0.2);
            o.stop(now + 0.21);
        } else {
            o.disconnect(); g.disconnect();
        }
    } catch (_) {}
}

// 监听来自服务器的成就事件（通过WebSocket或轮询）
function listenForAchievementEvents() {
    // 在实际应用中，这里应该通过WebSocket连接或定期轮询来获取成就事件
    // 示例：每30秒检查一次新成就
    /*
    setInterval(() => {
        const userInfo = JSON.parse(localStorage.getItem('userInfo'));
        if (userInfo) {
            fetch(getApiUrl(`/achievements/${encodeURIComponent(userInfo.id)}/new`))
                .then(response => response.json())
                .then(data => {
                    if (data.new_achievements) {
                        data.new_achievements.forEach(achievement => {
                            showAchievementPopup(achievement);
                        });

                        // 重新加载成就列表
                        loadAchievementsAndTasks();
                    }
                })
                .catch(error => {
                    console.error('检查新成就失败:', error);
                });
        }
    }, 30000);
    */
}

// 页面可见性变化时重新检查成就
document.addEventListener('visibilitychange', function() {
    if (!document.hidden) {
        loadAchievementsAndTasks();
    }
});