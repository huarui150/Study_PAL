// 学习计划详情页面逻辑
let currentSessionId = null;
let timerInterval = null;
let remainingTime = 0;
let isRunning = false;
let currentMode = 'standard';
let currentRound = 1;
let maxRounds = 4;
let isBreakTime = false;
let sessionStartTime = null;
let emotionHistory = [];

// 番茄钟模式配置
const pomodoroModes = {
    standard: { focus: 25, break: 5, longBreak: 15, rounds: 4, name: '标准模式' },
    deep: { focus: 50, break: 10, longBreak: 20, rounds: 2, name: '深度模式' },
    sprint: { focus: 35, break: 7, longBreak: 15, rounds: 3, name: '冲刺模式' },
    adaptive: { focus: 28, break: 6, longBreak: 16, rounds: 4, name: '自适应模式' },
    custom: { focus: 25, break: 5, longBreak: 15, rounds: 4, name: '自定义模式' }
};

document.addEventListener('DOMContentLoaded', function() {
    // 检查用户登录状态
    checkAuth();
    
    // 加载用户信息
    loadUserInfo();
    
    // 获取计划ID
    const urlParams = new URLSearchParams(window.location.search);
    const planId = urlParams.get('id');
    const autostart = urlParams.get('autostart');
    
    if (planId) {
        // 加载计划详情
        loadPlanDetail(planId);
        
        // 如果有autostart参数，延迟2秒后自动开始
        if (autostart === 'true') {
            setTimeout(() => {
                startPomodoro();
            }, 2000);
        }
    } else {
        showMessage('未指定计划ID', 'error');
        setTimeout(() => {
            window.location.href = 'plans.html';
        }, 2000);
    }
    
    // 初始化番茄钟模式
    initializePomodoroModes();
    
    // 绑定事件
    bindEvents();
    
    // 绑定模式切换事件
    bindModeEvents();
    
    // 加载AI建议
    loadAIRecommendation();
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

// 加载计划详情
function loadPlanDetail(planId) {
    console.log('Loading plan detail for ID:', planId);
    
    // 从localStorage加载计划数据
    const plan = loadPlanFromStorage(planId);
    
    if (plan) {
        console.log('Plan found:', plan);
        renderPlanDetail(plan);
        
        // 保存当前计划ID到全局变量
        window.currentPlanId = planId;
        window.currentPlan = plan;
    } else {
        console.error('Plan not found:', planId);
        showMessage('计划不存在或已被删除', 'error');
        setTimeout(() => {
            window.location.href = 'plans.html';
        }, 2000);
    }
}

// 从localStorage加载指定计划
function loadPlanFromStorage(planId) {
    try {
        const userInfo = JSON.parse(localStorage.getItem('userInfo')) || {};
        const storageKey = `plans_user_${userInfo.id || userInfo.student_id || 1}`;
        const plans = JSON.parse(localStorage.getItem(storageKey)) || [];
        
        // 查找指定ID的计划
        const plan = plans.find(p => p.id == planId);
        console.log('Found plan from storage:', plan);
        return plan;
    } catch (error) {
        console.error('Failed to load plan from storage:', error);
        return null;
    }
}

// 初始化番茄钟模式
function initializePomodoroModes() {
    // 设置默认模式描述
    updateModeDescription('standard');
}

// 绑定模式切换事件
function bindModeEvents() {
    const modeTabs = document.querySelectorAll('.mode-tab');
    modeTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const mode = this.dataset.mode;
            selectMode(mode);
        });
    });
    
    // 绑定自定义时间设置的变化事件
    const customInputs = ['customFocusTime', 'customBreakTime', 'customRounds'];
    customInputs.forEach(inputId => {
        const input = document.getElementById(inputId);
        if (input) {
            input.addEventListener('change', updateCustomMode);
        }
    });
}

// 选择模式
function selectMode(mode) {
    console.log('Selecting mode:', mode);
    
    // 更新模式标签状态
    document.querySelectorAll('.mode-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelector(`[data-mode="${mode}"]`).classList.add('active');
    
    // 显示/隐藏自定义设置
    const customSettings = document.getElementById('customTimerSettings');
    if (mode === 'custom') {
        customSettings.style.display = 'block';
        updateCustomMode(); // 更新自定义模式配置
    } else {
        customSettings.style.display = 'none';
    }
    
    // 更新当前模式
    currentMode = mode;
    
    // 更新模式描述
    updateModeDescription(mode);
    
    // 重置计时器状态（如果不在运行中）
    if (!isRunning) {
        remainingTime = 0;
        updateTimerDisplay();
    }
}

// 更新自定义模式配置
function updateCustomMode() {
    const focusTime = parseInt(document.getElementById('customFocusTime').value) || 25;
    const breakTime = parseInt(document.getElementById('customBreakTime').value) || 5;
    const rounds = parseInt(document.getElementById('customRounds').value) || 4;
    
    // 更新自定义模式配置
    pomodoroModes.custom = {
        focus: focusTime,
        break: breakTime,
        longBreak: Math.floor(breakTime * 2.5), // 长休息时间为短休息的2.5倍
        rounds: rounds,
        name: '自定义模式'
    };
    
    console.log('Updated custom mode:', pomodoroModes.custom);
    
    // 更新模式描述
    updateModeDescription('custom');
}

// 加载AI建议
function loadAIRecommendation() {
    // 模拟AI建议
    const recommendations = [
        '标准模式 - 适合当前任务难度',
        '深度模式 - 推荐用于复杂任务',
        '冲刺模式 - 临近截止日期时使用',
        '自适应模式 - 根据最近表现调整'
    ];
    
    const randomRecommendation = recommendations[Math.floor(Math.random() * recommendations.length)];
    document.getElementById('aiRecommendation').querySelector('.recommendation-text').textContent = `AI推荐: ${randomRecommendation}`;
}

// 渲染计划详情
function renderPlanDetail(plan) {
    document.getElementById('planTitle').textContent = plan.title;
    document.getElementById('planStatus').textContent = getStatusText(plan.status);
    document.getElementById('planTopic').textContent = plan.topic;
    document.getElementById('planEstimate').textContent = `${plan.estimate_min} 分钟`;
    document.getElementById('planDeadline').textContent = plan.deadline;
    document.getElementById('planDifficulty').textContent = plan.difficulty;
    document.getElementById('planImportance').textContent = plan.importance;
    
    // 设置课程名称（简化处理）
    document.getElementById('planCourse').textContent = '课程' + plan.course_id;
    
    // 根据任务特征推荐模式
    recommendMode(plan);
}

// 根据任务特征推荐模式
function recommendMode(plan) {
    let recommendedMode = 'standard';
    
    if (plan.difficulty >= 4 && plan.estimate_min >= 60) {
        recommendedMode = 'deep';
    } else if (plan.importance >= 4 && isNearDeadline(plan.deadline)) {
        recommendedMode = 'sprint';
    } else if (hasRecentEmotionData()) {
        recommendedMode = 'adaptive';
    }
    
    // 高亮推荐的模式
    document.querySelectorAll('.mode-tab').forEach(tab => {
        tab.classList.remove('recommended');
        if (tab.dataset.mode === recommendedMode) {
            tab.classList.add('recommended');
        }
    });
}

// 检查是否临近截止日期
function isNearDeadline(deadline) {
    const today = new Date();
    const deadlineDate = new Date(deadline);
    const diffDays = Math.ceil((deadlineDate - today) / (1000 * 60 * 60 * 24));
    return diffDays <= 3;
}

// 检查是否有最近的情绪数据
function hasRecentEmotionData() {
    return emotionHistory.length > 0;
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

// 绑定事件
function bindEvents() {
    // 模式切换按钮
    document.querySelectorAll('.mode-tab').forEach(tab => {
        tab.addEventListener('click', function() {
            if (!isRunning) {
                switchMode(this.dataset.mode);
            }
        });
    });
    
    // 开始专注按钮
    document.getElementById('startPomodoroBtn').addEventListener('click', startPomodoro);
    
    // 中断按钮
    document.getElementById('interruptPomodoroBtn').addEventListener('click', interruptPomodoro);
    
    // 完成按钮
    document.getElementById('completePomodoroBtn').addEventListener('click', function() {
        console.log('=== COMPLETE BUTTON CLICKED ===');
        completePomodoro();
    });
    
    // 情绪按钮
    document.querySelectorAll('.emotion-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.emotion-btn').forEach(b => b.classList.remove('selected'));
            this.classList.add('selected');
            document.getElementById('submitEmotionBtn').disabled = false;
            
            // 检查是否需要显示AI建议
            const emotionLevel = parseInt(this.dataset.level);
            // checkEmotionSuggestion(emotionLevel); // 暂时注释掉，功能尚未实现
            console.log('情绪等级:', emotionLevel);
        });
    });
    
    // 提交情绪按钮
    document.getElementById('submitEmotionBtn').addEventListener('click', submitEmotion);
    
    // 跳过情绪打卡按钮
    document.getElementById('skipEmotionBtn').addEventListener('click', function() {
        hideEmotionSection();
        showMessage('已跳过情绪打卡', 'info');
    });
}

// 切换番茄钟模式
function switchMode(mode) {
    currentMode = mode;
    
    // 更新UI
    document.querySelectorAll('.mode-tab').forEach(tab => {
        tab.classList.remove('active');
        if (tab.dataset.mode === mode) {
            tab.classList.add('active');
        }
    });
    
    // 更新模式描述
    updateModeDescription(mode);
    
    // 重置计时器显示
    const config = pomodoroModes[mode];
    maxRounds = config.rounds;
    remainingTime = config.focus * 60;
    updateTimerDisplay();
    resetProgressRing();
}

// 更新模式描述
function updateModeDescription(mode) {
    const config = pomodoroModes[mode];
    const descriptions = {
        standard: `专注${config.focus}分钟，休息${config.break}分钟，${config.rounds}轮后长休息${config.longBreak}分钟`,
        deep: `深度专注${config.focus}分钟，休息${config.break}分钟，${config.rounds}轮后长休息${config.longBreak}分钟`,
        sprint: `快速冲刺${config.focus}分钟，休息${config.break}分钟，自动强提醒模式`,
        adaptive: `智能调整时长，根据近期表现优化专注和休息时间`,
        custom: `自定义专注${config.focus}分钟，休息${config.break}分钟，${config.rounds}轮后长休息${config.longBreak}分钟`
    };
    
    document.getElementById('modeDescription').textContent = descriptions[mode];
}

// 开始番茄钟
function startPomodoro() {
    console.log('Starting pomodoro with mode:', currentMode);
    
    const config = pomodoroModes[currentMode];
    const focusMinutes = isBreakTime ? 
        (currentRound === maxRounds ? config.longBreak : config.break) : 
        config.focus;
    
    sessionStartTime = new Date();
    remainingTime = focusMinutes * 60; // 转换为秒
    isRunning = true;

    // 向后端登记会话以便成就/扣分生效
    try {
        const userInfo = JSON.parse(localStorage.getItem('userInfo')) || {};
        const userId = userInfo.id || userInfo.student_id || 1;
        fetch(getApiUrl('/pomodoro/start'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: userId,
                plan_id: Number(window.currentPlanId),
                focus_minutes: focusMinutes
            })
        }).then(r => r.json())
        .then(res => {
            if (res && res.session_id) {
                currentSessionId = res.session_id;
            } else {
                currentSessionId = Date.now();
            }
        }).catch(() => { currentSessionId = Date.now(); });
    } catch (_) {
        currentSessionId = Date.now();
    }
    
    console.log(`Starting ${isBreakTime ? 'break' : 'focus'} for ${focusMinutes} minutes`);
        
        // 更新UI
    updateTimerButtons(true);
    updateSessionInfo();
    
    const statusText = isBreakTime ? 
        (currentRound === maxRounds ? '长休息中...' : '休息中...') : 
        '专注中...';
    document.getElementById('timerStatus').textContent = statusText;
    
    // 显示会话信息
    document.getElementById('sessionInfo').style.display = 'flex';
        
        // 开始计时
        startTimer();
    
    // 冲刺模式的特殊处理
    if (currentMode === 'sprint' && !isBreakTime) {
        enableSprintMode();
    }
    
    showMessage(`${isBreakTime ? '休息' : '专注'}开始！时长${focusMinutes}分钟`, 'success');
}

// 更新计时器按钮状态
function updateTimerButtons(running) {
    document.getElementById('startPomodoroBtn').style.display = running ? 'none' : 'flex';
    document.getElementById('interruptPomodoroBtn').style.display = running ? 'flex' : 'none';
    document.getElementById('completePomodoroBtn').style.display = running ? 'flex' : 'none';
    
    // 禁用模式切换
    document.querySelectorAll('.mode-tab').forEach(tab => {
        tab.style.pointerEvents = running ? 'none' : 'auto';
        tab.style.opacity = running ? '0.6' : '1';
    });
}

// 更新会话信息
function updateSessionInfo() {
    document.getElementById('currentRound').textContent = `${currentRound}/${maxRounds}`;
    const sessionType = isBreakTime ? 
        (currentRound === maxRounds ? '长休息' : '短休息') : 
        '专注时间';
    document.getElementById('sessionType').textContent = sessionType;
}

// 启用冲刺模式特殊功能
function enableSprintMode() {
    // 冲刺模式下的强提醒和通知抑制
    if ('Notification' in window && Notification.permission === 'granted') {
        // 每10分钟发送一次鼓励通知
        const encourageInterval = setInterval(() => {
            if (isRunning && !isBreakTime) {
                new Notification('💪 保持专注！', {
                    body: '你正在冲刺模式中，继续加油！',
                    icon: '/favicon.ico'
                });
            } else {
                clearInterval(encourageInterval);
            }
        }, 10 * 60 * 1000);
    }
}

// 开始计时器
function startTimer() {
    isRunning = true;
    const totalTime = remainingTime;
    
    timerInterval = setInterval(() => {
        if (remainingTime <= 0) {
            // 时间到，自动完成
            clearInterval(timerInterval);
            handleTimerComplete();
            return;
        }
        
        remainingTime--;
        updateTimerDisplay();
        updateProgressRing(totalTime);
        
        // 每60秒发送tick事件
        if (remainingTime % 60 === 0) {
            sendTickEvent();
        }
    }, 1000);
    
    updateTimerDisplay();
    updateProgressRing(totalTime);
}

// 更新计时器显示
function updateTimerDisplay() {
    const minutes = Math.floor(remainingTime / 60);
    const seconds = remainingTime % 60;
    document.getElementById('timer').textContent = 
        `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
}

// 更新进度环
function updateProgressRing(totalTime) {
    const progressRing = document.getElementById('progressRing');
    if (progressRing && totalTime > 0) {
        const progress = (totalTime - remainingTime) / totalTime;
        const circumference = 2 * Math.PI * 45; // radius = 45
        const strokeDashoffset = circumference - (progress * circumference);
        progressRing.style.strokeDashoffset = strokeDashoffset;
    }
}

// 重置进度环
function resetProgressRing() {
    const progressRing = document.getElementById('progressRing');
    if (progressRing) {
        const circumference = 2 * Math.PI * 45;
        progressRing.style.strokeDashoffset = circumference;
    }
}

// 发送tick事件
function sendTickEvent() {
    if (currentSessionId) {
        fetch(getApiUrl('/pomodoro/tick'), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: currentSessionId,
                remaining_time: remainingTime
            })
        }).catch(error => {
            console.log('Tick event failed:', error);
        });
    }
}

// 处理计时器完成
function handleTimerComplete() {
    if (isBreakTime) {
        // 休息结束，开始下一轮专注或结束整个会话
        if (currentRound < maxRounds) {
            currentRound++;
            isBreakTime = false;
            showAutoNextDialog();
        } else {
            // 所有轮次完成
            completeAllRounds();
        }
    } else {
        // 专注时间结束，开始休息或完成
        isBreakTime = true;
        completePomodoro();
    }
}

// 中断番茄钟
function interruptPomodoro() {
    if (!currentSessionId) return;
    
    const reason = prompt('请输入中断原因：');
    if (!reason) return;
    
    // 模拟API调用中断番茄钟会话
    fetch(getApiUrl('/pomodoro/interrupt'), {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            session_id: currentSessionId,
            reason: reason
        })
    })
    .then(response => response.json())
    .then(result => {
        if (result.error) {
            throw new Error(result.error);
        }
        
        // 停止计时器
        clearInterval(timerInterval);
        isRunning = false;
        
        // 更新UI
        document.getElementById('startPomodoroBtn').style.display = 'inline-block';
        document.getElementById('interruptPomodoroBtn').style.display = 'none';
        document.getElementById('completePomodoroBtn').style.display = 'none';
        document.getElementById('timerStatus').textContent = '已中断';
        
        showMessage('番茄钟已中断', 'info');
        if (result.achievement_events && result.achievement_events.length > 0) {
            result.achievement_events.forEach(evt => {
                if (evt.event === 'coin.rewarded' && typeof window !== 'undefined') {
                    window.postMessage(evt, '*');
                }
            });
            // 失败扣分音效
            try { if (typeof playSound === 'function') playSound('fail'); } catch (_) {}
        }
        
        // 如果中断时间超过90秒，显示复盘建议
        if (result.failed) {
            setTimeout(() => {
                alert('复盘建议：专注时间较长，建议下次缩短专注时长或选择更合适的时间段进行学习。');
            }, 1000);
        }
    })
    .catch(error => {
        console.error('中断番茄钟失败:', error);
        showMessage('中断番茄钟失败: ' + error.message, 'error');
    });
}

// 完成番茄钟
function completePomodoro() {
    if (!currentSessionId) return;
    
    console.log('Completing pomodoro session:', currentSessionId);
    
    // 停止计时器
    clearInterval(timerInterval);
    isRunning = false;
    
    // 保存会话数据到localStorage
    savePomodoroSession();
    
    // 更新UI
    updateTimerButtons(false);
    document.getElementById('timerStatus').textContent = '已完成';
    
    // 重置计时器状态
    remainingTime = 0;
    isRunning = false;
    const completedSessionId = currentSessionId;  // 保存会话ID用于后续API调用
    currentSessionId = null;
    
    // 发送完成事件到后端，触发成就/金币
    try {
        const userInfo = JSON.parse(localStorage.getItem('userInfo')) || {};
        const userId = userInfo.id || userInfo.student_id || 1;
        if (completedSessionId) {
            fetch(getApiUrl('/pomodoro/complete'), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    session_id: completedSessionId, 
                    user_id: userId, 
                    emotion: null, 
                    note: null,
                    actual_minutes: Math.ceil(focusMinutes)
                })
            }).then(r => r.json()).then(res => {
                if (res && res.achievement_events && res.achievement_events.length) {
                    res.achievement_events.forEach(evt => {
                        if (typeof window !== 'undefined') {
                            window.postMessage(evt, '*');
                        }
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
            }).catch(() => {});
        }
    } catch (_) {}

    // 简化逻辑：只要点击完成就显示情绪打卡
    console.log('=== COMPLETE POMODORO - SHOWING EMOTION FEEDBACK ===');
    
    // 显示完成消息
    showMessage('番茄钟已完成！', 'success');
    
    // 立即显示情绪打卡区域
    setTimeout(() => {
        const emotionSection = document.getElementById('emotionSection');
        if (emotionSection) {
            emotionSection.style.display = 'block';
            emotionSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
            console.log('✅ Emotion section is now visible');
        } else {
            console.error('❌ emotionSection element not found!');
            // 备用方案：用alert确保用户能看到
            alert('专注完成！请记录您的情绪状态：\n😄 非常开心\n🙂 感觉良好\n😐 一般般\n😫 有点累\n😵 很疲惫');
        }
    }, 100);
}

// 保存番茄钟会话数据
function savePomodoroSession() {
    try {
        const userInfo = JSON.parse(localStorage.getItem('userInfo')) || {};
        const userId = userInfo.id || userInfo.student_id || 1;
        const sessionsKey = `pomodoro_sessions_user_${userId}`;
        
        const session = {
            id: currentSessionId,
            plan_id: window.currentPlanId,
            user_id: userId,
            mode: currentMode,
            type: isBreakTime ? 'break' : 'focus',
            duration: pomodoroModes[currentMode].focus,
            start_time: sessionStartTime,
            end_time: new Date(),
            completed: true,
            date: new Date().toISOString().split('T')[0],
            round: currentRound
        };
        
        const sessions = JSON.parse(localStorage.getItem(sessionsKey)) || [];
        sessions.push(session);
        localStorage.setItem(sessionsKey, JSON.stringify(sessions));
        
        console.log('Pomodoro session saved:', session);
    } catch (error) {
        console.error('Failed to save pomodoro session:', error);
    }
}



// 提交情绪
function submitEmotion() {
    const selectedEmotion = document.querySelector('.emotion-btn.selected');
    if (!selectedEmotion) {
        showMessage('请选择一个情绪', 'error');
        return;
    }
    
    const emotion = selectedEmotion.dataset.emotion;
    const note = document.getElementById('emotionNote').value;
    
    console.log('Submitting emotion:', emotion, note);
    
    // 保存情绪数据
    saveEmotionData(emotion, note);
    
    // 检查是否是连续的负面情绪
    checkConsecutiveNegativeEmotions(emotion);
    
    // 隐藏情绪打卡区域
    const emotionSection = document.getElementById('emotionSection');
    if (emotionSection) {
        emotionSection.style.display = 'none';
        console.log('Emotion section hidden after submission');
    }
    
    // 重置选择
    document.querySelectorAll('.emotion-btn').forEach(btn => btn.classList.remove('selected'));
    const noteInput = document.getElementById('emotionNote');
    if (noteInput) noteInput.value = '';
    
    showMessage('情绪打卡成功，数据已保存', 'success');
    
    // 更新最近情绪缓存（用于计划列表显示）
    updateRecentEmotionCache(emotion);
}

// 保存情绪数据
function saveEmotionData(emotion, note) {
    try {
        const userInfo = JSON.parse(localStorage.getItem('userInfo')) || {};
        const userId = userInfo.id || userInfo.student_id || 1;
        const today = new Date().toISOString().split('T')[0];
        
        // 保存到每日情绪数据
        const emotionKey = `emotion_daily_user_${userId}`;
        const emotionData = JSON.parse(localStorage.getItem(emotionKey)) || {};
        
        if (!emotionData[today]) {
            emotionData[today] = [];
        }
        
        emotionData[today].push({
            emotion: emotion,
            note: note,
            timestamp: new Date().toISOString(),
            session_id: currentSessionId,
            plan_id: window.currentPlanId
        });
        
        localStorage.setItem(emotionKey, JSON.stringify(emotionData));
        console.log('Emotion data saved:', emotionData[today]);
    } catch (error) {
        console.error('Failed to save emotion data:', error);
    }
}

// 检查连续负面情绪
function checkConsecutiveNegativeEmotions(currentEmotion) {
    if (currentEmotion === '😵' || currentEmotion === '😫') {
        try {
            const userInfo = JSON.parse(localStorage.getItem('userInfo')) || {};
            const userId = userInfo.id || userInfo.student_id || 1;
            const today = new Date().toISOString().split('T')[0];
            const emotionKey = `emotion_daily_user_${userId}`;
            const emotionData = JSON.parse(localStorage.getItem(emotionKey)) || {};
            const todayEmotions = emotionData[today] || [];
            
            // 检查最近3次情绪
            const recentEmotions = todayEmotions.slice(-3);
            const negativeCount = recentEmotions.filter(e => 
                e.emotion === '😵' || e.emotion === '😫'
            ).length;
            
            if (negativeCount >= 3) {
                setTimeout(() => {
                    showMessage('系统提醒：检测到您连续感到疲惫，建议适当休息一下再继续学习', 'warning');
                }, 1000);
            }
        } catch (error) {
            console.error('Failed to check consecutive emotions:', error);
        }
    }
}

// 更新最近情绪缓存（用于计划列表显示）
function updateRecentEmotionCache(emotion) {
    try {
        const userInfo = JSON.parse(localStorage.getItem('userInfo')) || {};
        const userId = userInfo.id || userInfo.student_id || 1;
        const recentKey = `emotion_recent_user_${userId}`;
        const recentEmotions = JSON.parse(localStorage.getItem(recentKey)) || {};
        
        if (window.currentPlanId) {
            recentEmotions[window.currentPlanId] = {
                emoji: emotion,
                timestamp: new Date().toISOString()
            };
            
            localStorage.setItem(recentKey, JSON.stringify(recentEmotions));
            console.log('Recent emotion updated for plan:', window.currentPlanId, emotion);
        }
    } catch (error) {
        console.error('Failed to update recent emotion cache:', error);
    }
}