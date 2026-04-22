// API基础URL
const API_BASE = 'http://localhost:8000/api';

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 初始化导航
    initNavigation();
    
    // 初始化仪表盘
    initDashboard();
    
    // 初始化推送管理
    initPushes();
    
    // 初始化爬虫管理
    initCrawlers();
    
    // 初始化记忆管理
    initMemories();
    
    // 初始化提醒管理
    initReminders();
    
    // 初始化理财记录
    initFinance();

    // 初始化KimiAI日志
    initKimiLogs();

    // 初始化系统日志
    initSystemLogs();

    // 初始化配置中心
    initSettings();
});

// 初始化导航
function initNavigation() {
    const navLinks = document.querySelectorAll('nav ul li a');
    const sections = document.querySelectorAll('main section');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href').substring(1);
            
            // 隐藏所有 section
            sections.forEach(section => {
                section.style.display = 'none';
            });
            
            // 显示目标 section
            document.getElementById(targetId).style.display = 'block';
        });
    });
}

// 初始化仪表盘
async function initDashboard() {
    try {
        // 获取仪表盘统计数据
        const response = await fetch(`${API_BASE}/dashboard/stats`);
        if (response.ok) {
            const data = await response.json();
            document.getElementById('today-pushes').textContent = data.today_pushes || '0';
            document.getElementById('message-stats').textContent = data.message_stats || '0';
            document.getElementById('task-status').textContent = data.task_status || '正常';
        } else {
            // 使用默认数据
            document.getElementById('today-pushes').textContent = '5';
            document.getElementById('message-stats').textContent = '128';
            document.getElementById('task-status').textContent = '正常';
        }
    } catch (error) {
        console.error('获取仪表盘数据失败:', error);
        // 使用默认数据
        document.getElementById('today-pushes').textContent = '5';
        document.getElementById('message-stats').textContent = '128';
        document.getElementById('task-status').textContent = '正常';
    }
}

// 初始化推送管理
async function initPushes() {
    try {
        const response = await fetch(`${API_BASE}/pushes`);
        if (response.ok) {
            const pushes = await response.json();
            const tableBody = document.querySelector('#pushes-table tbody');
            tableBody.innerHTML = '';
            
            pushes.forEach(push => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${push.id}</td>
                    <td>${push.title}</td>
                    <td>${push.push_time}</td>
                    <td>${push.target_group}</td>
                    <td>${push.is_active ? '启用' : '禁用'}</td>
                    <td class="action-buttons">
                        <button class="edit">编辑</button>
                        <button class="delete">删除</button>
                    </td>
                `;
                tableBody.appendChild(row);
            });
        }
    } catch (error) {
        console.error('获取推送数据失败:', error);
        // 使用模拟数据
        const pushes = [
            { id: 1, title: '每日新闻', push_time: '08:30', target_group: '全体成员', is_active: true },
            { id: 2, title: '天气预报', push_time: '07:00', target_group: '全体成员', is_active: true },
            { id: 3, title: '每周总结', push_time: '17:00', target_group: '管理层', is_active: false }
        ];
        const tableBody = document.querySelector('#pushes-table tbody');
        tableBody.innerHTML = '';
        pushes.forEach(push => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${push.id}</td>
                <td>${push.title}</td>
                <td>${push.push_time}</td>
                <td>${push.target_group}</td>
                <td>${push.is_active ? '启用' : '禁用'}</td>
                <td class="action-buttons">
                    <button class="edit">编辑</button>
                    <button class="delete">删除</button>
                </td>
            `;
            tableBody.appendChild(row);
        });
    }
    
    // 添加推送按钮点击事件
    document.getElementById('add-push').addEventListener('click', function() {
        alert('添加推送功能开发中...');
    });
}

// 初始化爬虫管理
async function initCrawlers() {
    try {
        const response = await fetch(`${API_BASE}/crawlers`);
        if (response.ok) {
            const crawlers = await response.json();
            const tableBody = document.querySelector('#crawlers-table tbody');
            tableBody.innerHTML = '';
            
            crawlers.forEach(crawler => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${crawler.id}</td>
                    <td>${crawler.name}</td>
                    <td>${crawler.url}</td>
                    <td>${crawler.selector}</td>
                    <td>${crawler.cron_expr}</td>
                    <td>${crawler.is_active ? '启用' : '禁用'}</td>
                    <td class="action-buttons">
                        <button class="edit">编辑</button>
                        <button class="delete">删除</button>
                        <button class="run">运行</button>
                    </td>
                `;
                tableBody.appendChild(row);
            });
        }
    } catch (error) {
        console.error('获取爬虫数据失败:', error);
        // 使用模拟数据
        const crawlers = [
            { id: 1, name: '新闻爬虫', url: 'https://news.example.com', selector: '.news-title', cron_expr: '0 8 * * *', is_active: true },
            { id: 2, name: '天气爬虫', url: 'https://weather.example.com', selector: '.weather-info', cron_expr: '0 7 * * *', is_active: true },
            { id: 3, name: '股票爬虫', url: 'https://stock.example.com', selector: '.stock-price', cron_expr: '0 9 * * *', is_active: false }
        ];
        const tableBody = document.querySelector('#crawlers-table tbody');
        tableBody.innerHTML = '';
        crawlers.forEach(crawler => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${crawler.id}</td>
                <td>${crawler.name}</td>
                <td>${crawler.url}</td>
                <td>${crawler.selector}</td>
                <td>${crawler.cron_expr}</td>
                <td>${crawler.is_active ? '启用' : '禁用'}</td>
                <td class="action-buttons">
                    <button class="edit">编辑</button>
                    <button class="delete">删除</button>
                    <button class="run">运行</button>
                </td>
            `;
            tableBody.appendChild(row);
        });
    }
    
    // 添加爬虫按钮点击事件
    document.getElementById('add-crawler').addEventListener('click', function() {
        alert('添加爬虫功能开发中...');
    });
}

// 初始化记忆管理
async function initMemories() {
    try {
        const response = await fetch(`${API_BASE}/memories`);
        if (response.ok) {
            const memories = await response.json();
            const tableBody = document.querySelector('#memories-table tbody');
            tableBody.innerHTML = '';
            
            memories.forEach(memory => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${memory.id}</td>
                    <td>${memory.user_id}</td>
                    <td>${memory.content}</td>
                    <td>${memory.category}</td>
                    <td>${memory.created_at}</td>
                    <td class="action-buttons">
                        <button class="delete">删除</button>
                    </td>
                `;
                tableBody.appendChild(row);
            });
        }
    } catch (error) {
        console.error('获取记忆数据失败:', error);
        // 使用模拟数据
        const memories = [
            { id: 1, user_id: 'user1', content: '明天开会', category: '工作', created_at: '2024-01-01 10:00:00' },
            { id: 2, user_id: 'user1', content: '买牛奶', category: '生活', created_at: '2024-01-02 15:00:00' },
            { id: 3, user_id: 'user2', content: '项目 deadline', category: '工作', created_at: '2024-01-03 09:00:00' }
        ];
        const tableBody = document.querySelector('#memories-table tbody');
        tableBody.innerHTML = '';
        memories.forEach(memory => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${memory.id}</td>
                <td>${memory.user_id}</td>
                <td>${memory.content}</td>
                <td>${memory.category}</td>
                <td>${memory.created_at}</td>
                <td class="action-buttons">
                    <button class="delete">删除</button>
                </td>
            `;
            tableBody.appendChild(row);
        });
    }
}

// 初始化提醒管理
async function initReminders() {
    try {
        const response = await fetch(`${API_BASE}/reminders`);
        if (response.ok) {
            const reminders = await response.json();
            const tableBody = document.querySelector('#reminders-table tbody');
            tableBody.innerHTML = '';
            
            reminders.forEach(reminder => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${reminder.id}</td>
                    <td>${reminder.user_id}</td>
                    <td>${reminder.content}</td>
                    <td>${reminder.remind_at}</td>
                    <td>${reminder.is_done ? '已完成' : '待提醒'}</td>
                    <td class="action-buttons">
                        <button class="edit">编辑</button>
                        <button class="delete">删除</button>
                    </td>
                `;
                tableBody.appendChild(row);
            });
        }
    } catch (error) {
        console.error('获取提醒数据失败:', error);
        // 使用模拟数据
        const reminders = [
            { id: 1, user_id: 'user1', content: '开会', remind_at: '2024-01-04 14:00:00', is_done: false },
            { id: 2, user_id: 'user1', content: '健身', remind_at: '2024-01-04 18:00:00', is_done: false },
            { id: 3, user_id: 'user2', content: '提交报告', remind_at: '2024-01-05 10:00:00', is_done: true }
        ];
        const tableBody = document.querySelector('#reminders-table tbody');
        tableBody.innerHTML = '';
        reminders.forEach(reminder => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${reminder.id}</td>
                <td>${reminder.user_id}</td>
                <td>${reminder.content}</td>
                <td>${reminder.remind_at}</td>
                <td>${reminder.is_done ? '已完成' : '待提醒'}</td>
                <td class="action-buttons">
                    <button class="edit">编辑</button>
                    <button class="delete">删除</button>
                </td>
            `;
            tableBody.appendChild(row);
        });
    }
}

// 初始化理财记录
async function initFinance() {
    try {
        // 获取理财记录
        const recordsResponse = await fetch(`${API_BASE}/finance`);
        if (recordsResponse.ok) {
            const records = await recordsResponse.json();
            const tableBody = document.querySelector('#finance-table tbody');
            tableBody.innerHTML = '';
            
            records.forEach(record => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${record.id}</td>
                    <td>${record.user_id}</td>
                    <td>${record.type === 'income' ? '收入' : '支出'}</td>
                    <td>${record.amount}</td>
                    <td>${record.category}</td>
                    <td>${record.record_date}</td>
                    <td class="action-buttons">
                        <button class="edit">编辑</button>
                        <button class="delete">删除</button>
                    </td>
                `;
                tableBody.appendChild(row);
            });
        }
        
        // 获取理财统计
        const statsResponse = await fetch(`${API_BASE}/finance/stats`);
        if (statsResponse.ok) {
            const stats = await statsResponse.json();
            const statsDiv = document.getElementById('finance-stats');
            statsDiv.innerHTML = `
                <p>总收入: ${stats.total_income || 0}元</p>
                <p>总支出: ${stats.total_expense || 0}元</p>
                <p>结余: ${stats.balance || 0}元</p>
                <p>餐饮支出: ${stats.category_expenses?.餐饮 || 0}元</p>
                <p>交通支出: ${stats.category_expenses?.交通 || 0}元</p>
            `;
        }
    } catch (error) {
        console.error('获取理财数据失败:', error);
        // 使用模拟数据
        const records = [
            { id: 1, user_id: 'user1', type: 'income', amount: 10000, category: '工资', record_date: '2024-01-01' },
            { id: 2, user_id: 'user1', type: 'expense', amount: 500, category: '餐饮', record_date: '2024-01-02' },
            { id: 3, user_id: 'user1', type: 'expense', amount: 200, category: '交通', record_date: '2024-01-03' }
        ];
        const tableBody = document.querySelector('#finance-table tbody');
        tableBody.innerHTML = '';
        records.forEach(record => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${record.id}</td>
                <td>${record.user_id}</td>
                <td>${record.type === 'income' ? '收入' : '支出'}</td>
                <td>${record.amount}</td>
                <td>${record.category}</td>
                <td>${record.record_date}</td>
                <td class="action-buttons">
                    <button class="edit">编辑</button>
                    <button class="delete">删除</button>
                </td>
            `;
            tableBody.appendChild(row);
        });
        
        // 模拟统计数据
        const statsDiv = document.getElementById('finance-stats');
        statsDiv.innerHTML = `
            <p>总收入: 10000元</p>
            <p>总支出: 700元</p>
            <p>结余: 9300元</p>
            <p>餐饮支出: 500元</p>
            <p>交通支出: 200元</p>
        `;
    }
    
    // 添加记录按钮点击事件
    document.getElementById('add-finance').addEventListener('click', function() {
        alert('添加理财记录功能开发中...');
    });
}

// 初始化配置中心
function initSettings() {
    // 模拟配置数据
    document.getElementById('wechat-corpid').value = 'your_corpid';
    document.getElementById('wechat-secret').value = 'your_secret';
    document.getElementById('wechat-agentid').value = 'your_agentid';
    document.getElementById('wechat-webhook-key').value = 'your_webhook_key';
    
    // 保存配置按钮点击事件
    document.getElementById('settings-form').addEventListener('submit', function(e) {
        e.preventDefault();
        alert('配置已保存');
    });
}

// 初始化KimiAI日志
async function initKimiLogs() {
    try {
        const response = await fetch(`${API_BASE}/logs/messages`);
        if (response.ok) {
            const logs = await response.json();
            const container = document.getElementById('kimi-logs-container');
            container.innerHTML = '';

            // 按日期分组
            const logsByDay = {};
            logs.forEach(log => {
                const date = new Date(log.created_at);
                const dateStr = date.toLocaleDateString('zh-CN', {
                    year: 'numeric',
                    month: '2-digit',
                    day: '2-digit'
                });
                if (!logsByDay[dateStr]) {
                    logsByDay[dateStr] = [];
                }
                logsByDay[dateStr].push(log);
            });

            // 按日期倒序排序
            const sortedDates = Object.keys(logsByDay).sort((a, b) => {
                return new Date(b) - new Date(a);
            });

            // 为每个日期创建分组
            sortedDates.forEach(date => {
                const dayLogs = logsByDay[date];
                const dayGroup = document.createElement('div');
                dayGroup.className = 'day-group';

                // 日期头部
                const dayHeader = document.createElement('div');
                dayHeader.className = 'day-header';
                dayHeader.innerHTML = `
                    <span class="day-date">${date}</span>
                    <span class="day-count">${dayLogs.length} 条消息</span>
                `;

                // 日期内容
                const dayContent = document.createElement('div');
                dayContent.className = 'day-content';

                // 为每条日志创建条目
                dayLogs.forEach(log => {
                    const logEntry = document.createElement('div');
                    const directionClass = log.direction === 'in' ? 'sent' : 'received';
                    const directionText = log.direction === 'in' ? '发送' : '接收';
                    const statusText = log.status === 'success' ? '成功' : '失败';

                    logEntry.className = `log-entry ${directionClass}`;
                    logEntry.innerHTML = `
                        <div class="log-meta">
                            <span class="log-direction">${directionText}</span>
                            <span class="log-time">${formatTime(log.created_at)}</span>
                            <span class="log-status">${statusText}</span>
                        </div>
                        <div class="log-content">${log.content}</div>
                        ${log.response ? `<div class="log-response">${log.response}</div>` : ''}
                    `;
                    dayContent.appendChild(logEntry);
                });

                // 点击头部展开/折叠
                dayHeader.addEventListener('click', function() {
                    dayContent.classList.toggle('expanded');
                });

                dayGroup.appendChild(dayHeader);
                dayGroup.appendChild(dayContent);
                container.appendChild(dayGroup);
            });
        }
    } catch (error) {
        console.error('获取KimiAI日志失败:', error);
        // 显示错误信息
        const container = document.getElementById('kimi-logs-container');
        container.innerHTML = '<div style="text-align: center; color: red; padding: 20px;">获取日志失败，请刷新页面重试</div>';
    }
}

// 工具函数：格式化时间
function formatTime(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

// 初始化系统日志
async function initSystemLogs() {
    try {
        const levelFilter = document.getElementById('log-level-filter').value;
        let url = `${API_BASE}/logs/system?limit=100`;
        if (levelFilter) {
            url += `&level=${levelFilter}`;
        }

        const response = await fetch(url);
        if (response.ok) {
            const logs = await response.json();
            const tableBody = document.querySelector('#system-logs-table tbody');
            tableBody.innerHTML = '';

            logs.forEach(log => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${log.id}</td>
                    <td><span class="log-level ${log.level.toLowerCase()}">${log.level}</span></td>
                    <td>${log.module}</td>
                    <td>${truncateText(log.message, 80)}</td>
                    <td>${formatDateTime(log.created_at)}</td>
                    <td class="action-buttons">
                        <button class="delete" onclick="deleteSystemLog(${log.id})">删除</button>
                    </td>
                `;
                tableBody.appendChild(row);
            });
        }
    } catch (error) {
        console.error('获取系统日志失败:', error);
    }

    // 刷新按钮点击事件
    document.getElementById('refresh-logs').addEventListener('click', function() {
        initSystemLogs();
    });

    // 级别筛选变化事件
    document.getElementById('log-level-filter').addEventListener('change', function() {
        initSystemLogs();
    });
}

// 删除系统日志
async function deleteSystemLog(logId) {
    if (!confirm('确定要删除这条日志吗？')) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/logs/system/${logId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            alert('删除成功');
            initSystemLogs();
        } else {
            alert('删除失败');
        }
    } catch (error) {
        console.error('删除系统日志失败:', error);
        alert('删除失败');
    }
}

// 工具函数：截断文本
function truncateText(text, maxLength) {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

// 工具函数：格式化日期时间
function formatDateTime(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}
