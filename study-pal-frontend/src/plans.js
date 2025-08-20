// 学习计划列表页面逻辑 - v2024120802
console.log('Plans.js loaded - version 2024120802');

let currentPlans = [];
let aiSuggestions = null;
let currentFilter = 'all';
let currentSort = 'priority';

// 获取用户特定的存储键
function getPlansStorageKey() {
    const userInfo = JSON.parse(localStorage.getItem('userInfo')) || {};
    return `plans_user_${userInfo.id || userInfo.student_id || 1}`;
}

// 保存计划到localStorage
function savePlansToStorage(plans) {
    try {
        localStorage.setItem(getPlansStorageKey(), JSON.stringify(plans));
        // 同时更新缓存（为了与课程页兼容）
        localStorage.setItem(plansCacheKey(), JSON.stringify(plans));
        console.log('Plans saved to storage:', plans.length);
    } catch (error) {
        console.error('Failed to save plans:', error);
    }
}

// 从localStorage加载计划
function loadPlansFromStorage() {
    try {
        const stored = localStorage.getItem(getPlansStorageKey());
        if (stored) {
            const plans = JSON.parse(stored);
            console.log('Plans loaded from storage:', plans.length);
            return plans;
        }
    } catch (error) {
        console.error('Failed to load plans:', error);
    }
    return [];
}

document.addEventListener('DOMContentLoaded', function() {
    // 检查用户登录状态
    checkAuth();
    
    // 加载用户信息
    loadUserInfo();
    
    // 加载AI建议
    loadAISuggestions();
    
    // 加载学习计划
    loadPlans();
    
    // 加载课程列表
    loadCourses();
    
    // 绑定事件（确保元素已存在）
    setTimeout(bindEvents, 0);
    
    // 初始化时间显示
    updateTimeDisplay();
    setInterval(updateTimeDisplay, 60000); // 每分钟更新一次
    
    // 确保统计数据更新
    setTimeout(() => {
        console.log('Force updating stats on page load');
        updateStats(currentPlans);
    }, 500);
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

// 加载AI建议
function loadAISuggestions() {
    const userInfo = JSON.parse(localStorage.getItem('userInfo'));
    if (!userInfo) return;
    
    console.log('Loading AI suggestions...');
    
    // 直接使用本地生成的智能建议
    aiSuggestions = generateDefaultSuggestions();
    renderAISuggestions(aiSuggestions);
    
    // 更新时间显示
    document.getElementById('lastUpdateTime').textContent = `更新于: ${new Date().toLocaleTimeString('zh-CN', {hour:'2-digit', minute:'2-digit'})}`;
}

// 生成默认AI建议（基于真实数据）
function generateDefaultSuggestions() {
    // 基于真实的疲劳数据和用户设置
    const realStats = getRealPomodoroStats();
    const userPrefs = getUserPreferences();
    const fatigueLevel = calculateFatigueLevel();
    
    // 基于当前计划生成建议
    const recommendations = generatePlanRecommendations();
    
    return {
        mode: userPrefs.preferredMode || '标准模式',
        target_pomodoros: userPrefs.dailyTarget || 0,
        fatigue_level: fatigueLevel,
        recommendations: recommendations
    };
}

// 基于当前计划生成推荐
function generatePlanRecommendations() {
    if (!currentPlans || currentPlans.length === 0) {
        return [];
    }
    
    const today = new Date();
    const todayStr = today.toISOString().split('T')[0];
    
    // 筛选待完成的计划
    const pendingPlans = currentPlans.filter(plan => 
        plan.status === 'pending' || plan.status === 'in_progress'
    );
    
    if (pendingPlans.length === 0) {
        return [];
    }
    
    // 按优先级和紧急程度排序
    const sortedPlans = pendingPlans.sort((a, b) => {
        const aUrgency = calculateUrgency(a);
        const bUrgency = calculateUrgency(b);
        const aPriority = a.importance || 3;
        const bPriority = b.importance || 3;
        
        // 综合分数：紧急程度 * 0.6 + 重要程度 * 0.4
        const aScore = aUrgency * 0.6 + aPriority * 0.4;
        const bScore = bUrgency * 0.6 + bPriority * 0.4;
        
        return bScore - aScore;
    });
    
    // 生成前3个推荐
    const recommendations = [];
    const startHour = 9; // 从9点开始
    
    for (let i = 0; i < Math.min(3, sortedPlans.length); i++) {
        const plan = sortedPlans[i];
        const startTime = `${String(startHour + i * 2).padStart(2, '0')}:00`;
        const endTime = `${String(startHour + i * 2 + 1).padStart(2, '0')}:30`;
        
        let reason = '';
        if (plan.importance >= 4) reason += '高优先级';
        if (calculateUrgency(plan) > 0.7) {
            if (reason) reason += '，';
            reason += '临近截止日期';
        }
        if (!reason) reason = '建议完成';
        
        recommendations.push({
            plan_id: plan.id,
            plan_title: plan.title,
            start_time: startTime,
            end_time: endTime,
            reason: reason
        });
    }
    
    return recommendations;
}

// 计算紧急程度
function calculateUrgency(plan) {
    if (!plan.deadline) return 0.3;
    
    const deadline = new Date(plan.deadline);
    const now = new Date();
    const daysToDeadline = (deadline - now) / (1000 * 60 * 60 * 24);
    
    if (daysToDeadline <= 0) return 1.0; // 已过期
    if (daysToDeadline <= 1) return 0.9; // 1天内
    if (daysToDeadline <= 3) return 0.7; // 3天内
    if (daysToDeadline <= 7) return 0.5; // 1周内
    
    return 0.3; // 超过1周
}

// 获取用户偏好设置
function getUserPreferences() {
    try {
        const userId = getUserId();
        const prefsKey = `user_preferences_${userId}`;
        return JSON.parse(localStorage.getItem(prefsKey)) || {
            preferredMode: '标准模式',
            dailyTarget: 0
        };
    } catch (error) {
        return {
            preferredMode: '标准模式',
            dailyTarget: 0
        };
    }
}

// 计算当前疲劳水平
function calculateFatigueLevel() {
    try {
        const userId = getUserId();
        const emotionKey = `emotion_daily_user_${userId}`;
        const today = new Date().toISOString().split('T')[0];
        const emotionData = JSON.parse(localStorage.getItem(emotionKey)) || {};
        const todayEmotions = emotionData[today] || [];
        
        if (todayEmotions.length === 0) return '未知';
        
        // 计算平均情绪值（😄=5, 🙂=4, 😐=3, 😫=2, 😵=1）
        const emotionValues = { '😄': 5, '🙂': 4, '😐': 3, '😫': 2, '😵': 1 };
        const recentEmotions = todayEmotions.slice(-3); // 只看最近3次
        const avgEmotion = recentEmotions.reduce((sum, emotionObj) => 
            sum + (emotionValues[emotionObj.emotion] || 3), 0) / recentEmotions.length;
        
        if (avgEmotion >= 4.5) return '低';
        if (avgEmotion >= 3.5) return '中';
        if (avgEmotion >= 2.5) return '高';
        return '极高';
    } catch (error) {
        return '未知';
    }
}

// 获取情绪相关的AI建议
function getEmotionBasedRecommendations() {
    try {
        const fatigueLevel = calculateFatigueLevel();
        const recommendations = [];
        
        switch (fatigueLevel) {
            case '极高':
                recommendations.push('建议先休息15-30分钟再开始学习');
                recommendations.push('考虑进行轻松的活动，如散步或听音乐');
                break;
            case '高':
                recommendations.push('建议使用较短的专注时间（15-20分钟）');
                recommendations.push('增加休息时间，每轮后休息10分钟');
                break;
            case '中':
                recommendations.push('标准模式即可，注意劳逸结合');
                break;
            case '低':
                recommendations.push('状态良好，可以尝试深度模式');
                recommendations.push('适合处理难度较高的任务');
                break;
            default:
                recommendations.push('开始学习后系统会根据您的情绪反馈调整建议');
        }
        
        return recommendations;
    } catch (error) {
        return ['暂时无法获取情绪建议'];
    }
}

// 渲染AI建议面板
function renderAISuggestions(suggestions) {
    document.getElementById('recommendedMode').textContent = suggestions.mode || '标准模式';
    const targetCount = suggestions.target_pomodoros || 0;
    document.getElementById('targetPomodoros').textContent = targetCount > 0 ? targetCount + '个' : '未设置';
    
    const fatigueElement = document.getElementById('fatigueLevel');
    const fatigueLevel = suggestions.fatigue_level || '低';
    fatigueElement.textContent = fatigueLevel;
    fatigueElement.className = 'value fatigue-indicator ' + fatigueLevel.toLowerCase();
    
    // 渲染推荐学习顺序和情绪建议
    const suggestedOrderContainer = document.getElementById('suggestedOrder');
    let content = '';
    
    // 添加情绪相关建议
    const emotionRecommendations = getEmotionBasedRecommendations();
    if (emotionRecommendations.length > 0) {
        content += `
            <div class="emotion-recommendations">
                <h5 style="color: rgba(255,255,255,0.9); margin-bottom: 10px;">💡 基于情绪状态的建议：</h5>
                ${emotionRecommendations.map(rec => `
                    <div class="emotion-suggestion">${rec}</div>
                `).join('')}
            </div>
        `;
    }
    
    // 添加计划推荐
    if (suggestions.recommendations && suggestions.recommendations.length > 0) {
        content += `
            <div class="plan-recommendations">
                <h5 style="color: rgba(255,255,255,0.9); margin: 15px 0 10px 0;">📅 今日学习安排：</h5>
                ${suggestions.recommendations.map((rec, index) => `
                    <div class="suggestion-item">
                        <div class="suggestion-header">
                            <div class="suggestion-time">${rec.start_time} - ${rec.end_time}</div>
                            <div class="suggestion-title">${rec.plan_title || '计划' + (index + 1)}</div>
                        </div>
                        <div class="suggestion-reason">${rec.reason}</div>
                    </div>
                `).join('')}
            </div>
        `;
    } else if (emotionRecommendations.length === 0) {
        content = '<p style="color: rgba(255,255,255,0.7); text-align: center; margin: 20px 0;">暂无推荐，请添加学习计划</p>';
    }
    
    suggestedOrderContainer.innerHTML = content;
}

// 加载学习计划
function getUserId() {
    const userInfo = JSON.parse(localStorage.getItem('userInfo')) || {};
    return userInfo.id || userInfo.user_id || 1;
}

function plansCacheKey() {
    return `plans_cache_user_${getUserId()}`;
}

function savePlansCache(plans) {
    try { localStorage.setItem(plansCacheKey(), JSON.stringify(plans)); } catch (_) {}
}

function readPlansCache() {
    try { return JSON.parse(localStorage.getItem(plansCacheKey())) || []; } catch (_) { return []; }
}

function loadPlans() {
    const userInfo = JSON.parse(localStorage.getItem('userInfo'));
    if (!userInfo) return;
    
    console.log('Loading plans for user:', userInfo.id || userInfo.student_id);
    
    // 优先从localStorage加载
    currentPlans = loadPlansFromStorage();
    
    // 如果没有存储的计划，初始化为空数组（不要自动生成mock数据）
    if (currentPlans.length === 0) {
        console.log('No plans found in storage, starting with empty list');
        currentPlans = [];
    }
    
    applyFiltersAndSort();
    updateStats(currentPlans);
    
    // 后台尝试同步到服务器（可选，不影响前端功能）
    syncPlansToServer();
}

// 后台同步到服务器（可选）
function syncPlansToServer() {
    // 这个函数可以在后端API就绪时用于同步数据
    // 目前只是占位符，不会影响前端功能
    console.log('TODO: 后端API就绪时可在此同步数据');
}

// 同步单个计划到服务器（占位符）
function syncPlanToServer(plan) {
    console.log('TODO: 同步计划到服务器:', plan.title);
}

// 同步删除到服务器（占位符）
function syncDeleteToServer(planId) {
    console.log('TODO: 同步删除到服务器:', planId);
}

// 生成模拟数据
function generateMockPlans() {
    return [
        {
            id: 1,
            title: '数据结构复习',
            topic: '二叉树与图论',
            course_id: 1,
            estimate_min: 90,
            difficulty: 4,
            importance: 5,
            deadline: '2024-01-15',
            status: 'pending',
            progress: 30,
            created_at: '2024-01-10'
        },
        {
            id: 2,
            title: '机器学习作业',
            topic: '神经网络实现',
            course_id: 2,
            estimate_min: 120,
            difficulty: 5,
            importance: 4,
            deadline: '2024-01-18',
            status: 'in_progress',
            progress: 60,
            created_at: '2024-01-09'
        },
        {
            id: 3,
            title: '英语阅读练习',
            topic: '学术论文阅读',
            course_id: 3,
            estimate_min: 45,
            difficulty: 2,
            importance: 3,
            deadline: '2024-01-20',
            status: 'pending',
            progress: 0,
            created_at: '2024-01-08'
        }
    ];
}

// 渲染学习计划列表
function renderPlans(plans) {
    const plansGrid = document.getElementById('plansGrid');
    const emptyState = document.getElementById('emptyState');
    
    // 清除现有的计划卡片（但保留添加计划卡片）
    const existingPlanCards = plansGrid.querySelectorAll('.plan-card:not(.add-plan-card)');
    existingPlanCards.forEach(card => card.remove());
    
    if (!plans || plans.length === 0) {
        emptyState.style.display = 'block';
        return;
    }
    
    emptyState.style.display = 'none';
    
    plans.forEach(plan => {
        const planElement = document.createElement('div');
        const priorityClass = getPriorityClass(plan.importance);
        const isAIRecommended = aiSuggestions && aiSuggestions.recommendations && 
                               aiSuggestions.recommendations.some(rec => rec.plan_id === plan.id);
        const lastEmotion = getRecentEmotion(plan.id);
        
        planElement.className = `plan-card ${priorityClass}${isAIRecommended ? ' ai-recommended' : ''}`;
        planElement.innerHTML = `
            <div class="plan-header">
                <h3 class="plan-title">${plan.title}</h3>
                <span class="plan-status ${plan.status}">${getStatusText(plan.status)}</span>
            </div>
            <div class="plan-content">
                <p style="color: #666; margin-bottom: 15px; font-size: 14px;">${plan.topic}</p>
                <div class="plan-stats">
                    <div class="plan-stat-item">
                        <span class="plan-stat-number">${plan.estimate_min}</span>
                        <span class="plan-stat-label">分钟</span>
                    </div>
                    <div class="plan-stat-item">
                        <span class="plan-stat-number">${'★'.repeat(plan.difficulty)}</span>
                        <span class="plan-stat-label">难度</span>
                    </div>
                    <div class="plan-stat-item">
                        <span class="plan-stat-number">${getPriorityIcon(plan.importance)}</span>
                        <span class="plan-stat-label">优先级</span>
                    </div>
                    <div class="plan-stat-item">
                        <span class="plan-stat-number">${formatDate(plan.deadline)}</span>
                        <span class="plan-stat-label">截止日期</span>
                    </div>
                    ${lastEmotion ? `
                    <div class="plan-stat-item">
                        <span class="plan-stat-number">${lastEmotion.emoji}</span>
                        <span class="plan-stat-label">上次情绪</span>
                    </div>` : ''}
                </div>
            </div>
            <div class="plan-actions">
                <button class="btn btn-sm btn-success" onclick="startPomodoroSession(${plan.id})">🍅 专注</button>
                <button class="btn btn-sm btn-primary" onclick="viewPlanDetail(${plan.id})">详情</button>
                <button class="btn btn-sm btn-secondary" onclick="editPlan(${plan.id})">编辑</button>
                <button class="btn btn-sm ${plan.status==='completed' ? 'btn-outline' : 'btn-primary'}" onclick="togglePlanStatus(${plan.id})">${plan.status==='completed' ? '恢复' : '标记完成'}</button>
                <button class="btn btn-sm btn-danger" onclick="deletePlan(${plan.id})">删除</button>
            </div>
        `;
        
        // 将新的计划卡片插入到添加计划卡片之前
        const addPlanCard = plansGrid.querySelector('.add-plan-card');
        plansGrid.insertBefore(planElement, addPlanCard);
    });
}

// 最近情绪读取（本地缓存）
function getRecentEmotion(planId) {
    try {
        const key = `emotion_recent_user_${getUserId()}`;
        const obj = JSON.parse(localStorage.getItem(key)) || {};
        return obj[planId];
    } catch (_) { return null; }
}

// 切换计划完成状态
function togglePlanStatus(planId) {
    const plan = currentPlans.find(p => p.id == planId);
    if (!plan) {
        console.error('Plan not found:', planId);
        return;
    }
    
    const newStatus = plan.status === 'completed' ? 'pending' : 'completed';
    console.log('Toggling plan status:', planId, 'from', plan.status, 'to', newStatus);
    
    // 直接更新状态
    plan.status = newStatus;
    plan.updated_at = new Date().toISOString();
    
    // 保存到localStorage
    savePlansToStorage(currentPlans);
    
    // 更新显示
    applyFiltersAndSort();
    updateStats(currentPlans);
    
    showMessage(newStatus === 'completed' ? '已标记为完成' : '已恢复为待完成', 'success');
    
    // 后台同步到服务器（如果需要）
    syncPlanToServer(plan);
}

// 获取状态文本
function getStatusText(status) {
    switch (status) {
        case 'pending': return '待完成';
        case 'in_progress': return '进行中';
        case 'completed': return '已完成';
        case 'overdue': return '已过期';
        default: return '未知';
    }
}

// 获取优先级类名
function getPriorityClass(importance) {
    if (importance >= 4) return 'high-priority';
    if (importance >= 3) return 'medium-priority';
    return 'low-priority';
}

// 获取优先级图标
function getPriorityIcon(importance) {
    if (importance >= 4) return '🔴';
    if (importance >= 3) return '🟡';
    return '🟢';
}

// 获取优先级文本
function getPriorityText(importance) {
    if (importance >= 4) return '高';
    if (importance >= 3) return '中';
    return '低';
}

// 获取截止日期紧急程度
function getDeadlineUrgency(deadline) {
    const today = new Date();
    const deadlineDate = new Date(deadline);
    const diffDays = Math.ceil((deadlineDate - today) / (1000 * 60 * 60 * 24));
    
    if (diffDays < 0) return 'urgent';
    if (diffDays <= 3) return 'urgent';
    if (diffDays <= 7) return 'soon';
    return 'normal';
}

// 格式化日期
function formatDate(dateStr) {
    const date = new Date(dateStr);
    const today = new Date();
    const diffDays = Math.ceil((date - today) / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) return '今天';
    if (diffDays === 1) return '明天';
    if (diffDays === -1) return '昨天';
    if (diffDays < -1) return `${Math.abs(diffDays)}天前`;
    if (diffDays > 0) return `${diffDays}天后`;
    
    return date.toLocaleDateString('zh-CN');
}

// 应用筛选和排序
function applyFiltersAndSort() {
    let filteredPlans = [...currentPlans];
    
    // 应用状态筛选
    if (currentFilter !== 'all') {
        filteredPlans = filteredPlans.filter(plan => plan.status === currentFilter);
    }
    
    // 应用排序
    filteredPlans.sort((a, b) => {
        switch (currentSort) {
            case 'priority':
                return calculatePriority(b) - calculatePriority(a);
            case 'deadline':
                return new Date(a.deadline) - new Date(b.deadline);
            case 'difficulty':
                return b.difficulty - a.difficulty;
            case 'created':
                return new Date(b.created_at) - new Date(a.created_at);
            default:
                return 0;
        }
    });
    
    renderPlans(filteredPlans);
}

// 计算优先级分数（基于AI算法）
function calculatePriority(plan) {
    const today = new Date();
    const deadline = new Date(plan.deadline);
    const daysToDeadline = Math.ceil((deadline - today) / (1000 * 60 * 60 * 24));
    
    // 紧迫度计算
    const urgency = Math.max(0, 1 - daysToDeadline / 7);
    
    // 优先级计算
    const priority = 0.5 * (plan.importance / 5) + 0.5 * urgency;
    
    return priority;
}

// 更新统计信息
function updateStats(plans) {
    console.log('=== UPDATING STATS ===');
    console.log('Plans received:', plans);
    
    if (!plans) plans = [];
    
    const today = new Date().toISOString().split('T')[0];
    
    // "今日计划"显示所有未完成的计划
    const todayPlans = plans.filter(plan => 
        plan.status === 'pending' || plan.status === 'in_progress'
    );
    
    console.log('Today plans filter - showing all pending/in-progress plans:');
    plans.forEach(plan => {
        console.log(`Plan "${plan.title}": status=${plan.status}, included=${plan.status === 'pending' || plan.status === 'in_progress'}`);
    });
    const completedPlans = plans.filter(plan => plan.status === 'completed');
    
    console.log('Today plans:', todayPlans.length);
    console.log('Completed plans:', completedPlans.length);
    
    // 从真实的番茄钟会话数据统计
    const realStats = getRealPomodoroStats();
    console.log('Real pomodoro stats:', realStats);
    
    // 更新显示
    const elements = {
        todayPlansCount: document.getElementById('todayPlansCount'),
        completedPlansCount: document.getElementById('completedPlansCount'),
        pomodoroCount: document.getElementById('pomodoroCount'),
        focusTimeCount: document.getElementById('focusTimeCount')
    };
    
    if (elements.todayPlansCount) {
        elements.todayPlansCount.textContent = todayPlans.length;
        console.log('✅ Updated todayPlansCount:', todayPlans.length);
    } else {
        console.error('❌ todayPlansCount element not found');
    }
    
    if (elements.completedPlansCount) {
        elements.completedPlansCount.textContent = completedPlans.length;
        console.log('✅ Updated completedPlansCount:', completedPlans.length);
    } else {
        console.error('❌ completedPlansCount element not found');
    }
    
    if (elements.pomodoroCount) {
        elements.pomodoroCount.textContent = realStats.totalPomodoros;
        console.log('✅ Updated pomodoroCount:', realStats.totalPomodoros);
    } else {
        console.error('❌ pomodoroCount element not found');
    }
    
    if (elements.focusTimeCount) {
        elements.focusTimeCount.textContent = realStats.totalFocusTime;
        console.log('✅ Updated focusTimeCount:', realStats.totalFocusTime);
    } else {
        console.error('❌ focusTimeCount element not found');
    }
}

// 获取真实的番茄钟统计数据
function getRealPomodoroStats() {
    try {
        const userId = getUserId();
        const today = new Date().toISOString().split('T')[0];
        const sessionKey = `pomodoro_sessions_user_${userId}`;
        const sessions = JSON.parse(localStorage.getItem(sessionKey)) || [];
        
        console.log('Getting pomodoro stats for user:', userId);
        console.log('Today:', today);
        console.log('Session key:', sessionKey);
        console.log('All sessions found:', sessions);
        
        // 筛选今日的会话
        const todaySessions = sessions.filter(session => {
            const isToday = session.date === today;
            const isCompleted = session.completed === true;
            console.log(`Session ${session.id}: date=${session.date}, completed=${session.completed}, isToday=${isToday}, isCompleted=${isCompleted}`);
            return isToday && isCompleted;
        });
        
        console.log('Today sessions filtered:', todaySessions);
        
        const totalPomodoros = todaySessions.length;
        const totalFocusTime = todaySessions.reduce((total, session) => 
            total + (session.duration || 25), 0
        );
        
        console.log('Final stats - Pomodoros:', totalPomodoros, 'Focus time:', totalFocusTime);
        
        return {
            totalPomodoros,
            totalFocusTime
        };
    } catch (error) {
        console.error('Error getting pomodoro stats:', error);
        return {
            totalPomodoros: 0,
            totalFocusTime: 0
        };
    }
}

// 更新时间显示
function updateTimeDisplay() {
    const now = new Date();
    const timeStr = now.toLocaleTimeString('zh-CN', { 
        hour: '2-digit', 
        minute: '2-digit' 
    });
    const element = document.getElementById('lastUpdateTime');
    if (element) {
        element.textContent = `更新于: ${timeStr}`;
    }
}

// 加载课程列表（已废弃，改为手动输入）
function loadCourses() {
    // 课程现在改为手动输入，不再需要加载课程列表
    console.log('课程选择已改为手动输入模式');
}

// 绑定事件
function bindEvents() {
    console.log('bindEvents called');
    
    // 添加计划按钮
    const addPlanBtn = document.getElementById('addPlanBtn');
    if (addPlanBtn) {
        console.log('Found addPlanBtn, binding event');
        addPlanBtn.addEventListener('click', openAddPlanModal);
    } else {
        console.error('addPlanBtn not found!');
    }
    
    // 刷新AI建议按钮
    document.getElementById('refreshSuggestionsBtn').addEventListener('click', function() {
        this.innerHTML = '🔄 刷新中...';
        this.disabled = true;
        
        setTimeout(() => {
            loadAISuggestions();
            this.innerHTML = '🔄 刷新建议';
            this.disabled = false;
            showMessage('AI建议已更新', 'success');
        }, 1000);
    });
    
    // 快速操作按钮
    document.getElementById('startFocusBtn').addEventListener('click', function() {
        // 找到第一个待完成的高优先级任务
        const pendingPlans = currentPlans.filter(plan => plan.status === 'pending');
        if (pendingPlans.length > 0) {
            const highPriorityPlan = pendingPlans.sort((a, b) => calculatePriority(b) - calculatePriority(a))[0];
            startPomodoroSession(highPriorityPlan.id);
        } else {
            showMessage('暂无待完成的学习计划', 'info');
        }
    });
    
    document.getElementById('reviewNotesBtn').addEventListener('click', function() {
        showMessage('复习功能开发中...', 'info');
    });
    
    document.getElementById('weeklyReportBtn').addEventListener('click', function() {
        showMessage('周报告功能开发中...', 'info');
    });
    
    // 筛选和排序控件
    document.getElementById('statusFilter').addEventListener('change', function(e) {
        currentFilter = e.target.value;
        applyFiltersAndSort();
    });
    
    document.getElementById('sortBy').addEventListener('change', function(e) {
        currentSort = e.target.value;
        applyFiltersAndSort();
    });
    
    // 关闭模态框
    document.getElementById('closeModal').addEventListener('click', function() {
        document.getElementById('addPlanModal').style.display = 'none';
    });
    
    // 点击模态框外部关闭
    window.addEventListener('click', function(event) {
        const modal = document.getElementById('addPlanModal');
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
    
    // 添加计划表单提交
    document.getElementById('addPlanForm').addEventListener('submit', function(e) {
        e.preventDefault();
        addPlan();
    });
    
    // 设置目标表单提交事件
    document.getElementById('setTargetForm').addEventListener('submit', function(e) {
        e.preventDefault();
        saveTarget();
    });
    
    // 模态框关闭事件
    document.getElementById('closeModal').addEventListener('click', function() {
        document.getElementById('addPlanModal').style.display = 'none';
    });
    
    // 点击模态框外部关闭
    window.addEventListener('click', function(event) {
        const addModal = document.getElementById('addPlanModal');
        const targetModal = document.getElementById('setTargetModal');
        if (event.target === addModal) {
            addModal.style.display = 'none';
        }
        if (event.target === targetModal) {
            targetModal.style.display = 'none';
        }
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

// 打开添加计划模态框
function openAddPlanModal() {
    console.log('openAddPlanModal called');
    const modal = document.getElementById('addPlanModal');
    if (modal) {
        console.log('Found modal, showing it');
        modal.style.display = 'block';
        
        // 设置默认截止日期为明天
        const tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 1);
        const deadlineInput = document.getElementById('planDeadline');
        if (deadlineInput) {
            deadlineInput.value = tomorrow.toISOString().split('T')[0];
        }
    } else {
        console.error('addPlanModal not found!');
    }
}

// 打开设置目标模态框
function openSetTargetModal() {
    const modal = document.getElementById('setTargetModal');
    modal.style.display = 'block';
    
    // 加载当前设置
    const userPrefs = getUserPreferences();
    document.getElementById('dailyTarget').value = userPrefs.dailyTarget || 0;
    document.getElementById('preferredMode').value = userPrefs.preferredMode || '标准模式';
}

// 关闭设置目标模态框
function closeSetTargetModal() {
    document.getElementById('setTargetModal').style.display = 'none';
}

// 保存目标设置
function saveTarget() {
    const dailyTarget = parseInt(document.getElementById('dailyTarget').value) || 0;
    const preferredMode = document.getElementById('preferredMode').value;
    
    const userId = getUserId();
    const prefsKey = `user_preferences_${userId}`;
    const userPrefs = {
        dailyTarget: dailyTarget,
        preferredMode: preferredMode,
        lastUpdated: new Date().toISOString()
    };
    
    try {
        localStorage.setItem(prefsKey, JSON.stringify(userPrefs));
        closeSetTargetModal();
        
        // 刷新AI建议显示
        loadAISuggestions();
        
        showMessage('目标设置已保存', 'success');
    } catch (error) {
        showMessage('保存失败，请重试', 'error');
    }
}

// 添加学习计划
function addPlan() {
    console.log('addPlan function called');
    const userInfo = JSON.parse(localStorage.getItem('userInfo'));
    if (!userInfo) {
        console.log('No user info found');
        showMessage('用户信息未找到，请重新登录', 'error');
        return;
    }
    
    // 获取表单数据
    const title = document.getElementById('planTitle').value.trim();
    const course_id = document.getElementById('planCourse').value.trim();
    const topic = document.getElementById('planTopic').value.trim();
    const estimate_min = parseInt(document.getElementById('planEstimate').value);
    const difficulty = parseInt(document.getElementById('planDifficulty').value);
    const importance = parseInt(document.getElementById('planImportance').value);
    const deadline = document.getElementById('planDeadline').value;
    
    const planData = {
        user_id: userInfo.id,
        title: title,
        course_id: course_id,
        topic: topic,
        estimate_min: estimate_min,
        difficulty: difficulty,
        importance: importance,
        deadline: deadline
    };
    
    // 验证表单
    console.log('Form validation - planData:', planData);
    console.log('Title:', planData.title, 'Course:', planData.course_id, 'Topic:', planData.topic);
    console.log('Estimate:', planData.estimate_min, 'Deadline:', planData.deadline);
    
    // 详细验证每个字段
    if (!planData.title) {
        showMessage('请输入计划标题', 'error');
        return;
    }
    if (!planData.course_id) {
        showMessage('请输入关联课程', 'error');
        return;
    }
    if (!planData.topic) {
        showMessage('请输入学习主题', 'error');
        return;
    }
    if (isNaN(planData.estimate_min) || planData.estimate_min <= 0) {
        showMessage('请输入有效的预估时长（大于0的整数）', 'error');
        return;
    }
    if (!planData.deadline) {
        showMessage('请选择截止日期', 'error');
        return;
    }
    
    // 直接保存到localStorage
    const newPlan = {
        id: Date.now(), // 使用时间戳作为ID
        ...planData,
        status: 'pending',
        created_at: new Date().toISOString()
    };
    
    console.log('Adding new plan:', newPlan);
    
    // 添加到当前列表
    currentPlans.push(newPlan);
    
    // 保存到localStorage
    savePlansToStorage(currentPlans);
    
    // 更新显示
    applyFiltersAndSort();
    updateStats(currentPlans);
    
    // 关闭模态框
    document.getElementById('addPlanModal').style.display = 'none';
    document.getElementById('addPlanForm').reset();
    
    showMessage('计划添加成功', 'success');
    
    // 后台同步到服务器（如果需要）
    syncPlanToServer(newPlan);
}

// 查看计划详情
function viewPlanDetail(planId) {
    window.location.href = `plan-detail.html?id=${planId}`;
}

// 编辑计划
function editPlan(planId) {
    // 这里可以实现编辑功能
    showMessage('编辑功能待实现', 'info');
}

// 删除计划
function deletePlan(planId) {
    console.log('deletePlan function called with ID:', planId);
    if (!confirm('确定要删除这个学习计划吗？')) {
        return;
    }
    
    // 直接从localStorage删除
    console.log('Deleting plan:', planId);
    
    // 从当前列表删除
    currentPlans = currentPlans.filter(plan => plan.id != planId);
    
    // 保存到localStorage
    savePlansToStorage(currentPlans);
    
    // 更新显示
    applyFiltersAndSort();
    updateStats(currentPlans);
    
    showMessage('计划删除成功', 'success');
    
    // 后台同步到服务器（如果需要）
    syncDeleteToServer(planId);
}

// 开始番茄钟会话
function startPomodoroSession(planId) {
    // 跳转到计划详情页面并开始番茄钟
    window.location.href = `plan-detail.html?id=${planId}&autostart=true`;
}