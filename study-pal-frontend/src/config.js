// API配置文件
const API_CONFIG = {
    // 后端API基础地址
    BASE_URL: 'http://localhost:5000/api',
    
    // 认证相关API
    AUTH: {
        LOGIN: '/auth/login',
        REGISTER: '/auth/register'
    },
    
    // 健康检查
    HEALTH: '/health'
};

// MCP服务配置 - 通过后端代理访问
const MCP_CONFIG = {
    // 通过后端代理访问MCP服务
    BASE_URL: 'http://localhost:5000/api/mcp',
    
    // 认证Token（现在由后端处理）
    TOKEN: 'linyang-z2ylmqsUn96r6D3UBlspk1shedZ7o1Nhg7MlUjO_qA8',
    
    // MCP工具接口路径（通过代理）
    TOOLS: {
        COURSES: '/courses',      // 形策课程查询
        CALENDAR: '/calendar',    // 校历信息查询
        BUS: '/bus',             // 班车时刻查询
        STATUS: '/status'         // 系统状态查询
    }
};

// 获取完整的API URL
function getApiUrl(endpoint) {
    return API_CONFIG.BASE_URL + endpoint;
}

// 获取完整的MCP URL（通过代理）
function getMcpUrl(endpoint) {
    return MCP_CONFIG.BASE_URL + endpoint;
}

// 导出配置
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { API_CONFIG, MCP_CONFIG, getApiUrl, getMcpUrl };
} else {
    // 在浏览器环境中也导出
    window.API_CONFIG = API_CONFIG;
    window.MCP_CONFIG = MCP_CONFIG;
    window.getApiUrl = getApiUrl;
    window.getMcpUrl = getMcpUrl;
}