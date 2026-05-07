// API基础URL
const API_BASE = '/api';

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

    // 初始化聊天功能
    initChat();
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
            
            // 如果切换到KimiAI日志页面，刷新日志
            if (targetId === 'kimi-logs') {
                initKimiLogs();
            }
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
            const container = document.getElementById('memories-container');
            container.innerHTML = '';
            
            if (memories.length === 0) {
                container.innerHTML = '<div style="text-align: center; color: #666; padding: 20px;">暂无记忆记录</div>';
                return;
            }
            
            // 按日期分组
            const memoriesByDay = {};
            memories.forEach(memory => {
                const date = new Date(memory.created_at);
                const dateStr = date.toLocaleDateString('zh-CN', {
                    year: 'numeric',
                    month: '2-digit',
                    day: '2-digit'
                });
                if (!memoriesByDay[dateStr]) {
                    memoriesByDay[dateStr] = [];
                }
                memoriesByDay[dateStr].push(memory);
            });
            
            // 按日期倒序排序
            const sortedDates = Object.keys(memoriesByDay).sort((a, b) => {
                return new Date(b) - new Date(a);
            });
            
            // 为每个日期创建分组
            sortedDates.forEach(date => {
                const dayMemories = memoriesByDay[date];
                const dayGroup = document.createElement('div');
                dayGroup.className = 'day-group';
                
                // 日期头部
                const dayHeader = document.createElement('div');
                dayHeader.className = 'day-header';
                dayHeader.innerHTML = `
                    <span class="day-date">${date}</span>
                    <span class="day-count">${dayMemories.length} 条记忆</span>
                `;
                
                // 日期内容
                const dayContent = document.createElement('div');
                dayContent.className = 'day-content expanded';
                
                // 为每条记忆创建条目
                dayMemories.forEach(memory => {
                    const memoryEntry = document.createElement('div');
                    memoryEntry.className = 'memory-entry';
                    memoryEntry.innerHTML = `
                        <div class="memory-meta">
                            <span class="memory-time">${new Date(memory.created_at).toLocaleTimeString('zh-CN')}</span>
                            <span class="memory-category">${memory.category}</span>
                        </div>
                        <div class="memory-content">${memory.content}</div>
                        <div class="memory-actions">
                            <button class="delete-btn" data-id="${memory.id}">删除</button>
                        </div>
                    `;
                    dayContent.appendChild(memoryEntry);
                });
                
                // 点击头部展开/折叠
                dayHeader.addEventListener('click', function() {
                    dayContent.classList.toggle('expanded');
                });
                
                dayGroup.appendChild(dayHeader);
                dayGroup.appendChild(dayContent);
                container.appendChild(dayGroup);
            });
            
            // 添加删除事件监听
            container.querySelectorAll('.delete-btn').forEach(btn => {
                btn.addEventListener('click', async function() {
                    const memoryId = this.getAttribute('data-id');
                    if (confirm('确定要删除这条记忆吗？')) {
                        try {
                            const response = await fetch(`${API_BASE}/memories/${memoryId}`, {
                                method: 'DELETE'
                            });
                            if (response.ok) {
                                initMemories(); // 刷新列表
                            }
                        } catch (error) {
                            console.error('删除记忆失败:', error);
                        }
                    }
                });
            });
        }
    } catch (error) {
        console.error('获取记忆数据失败:', error);
        const container = document.getElementById('memories-container');
        container.innerHTML = '<div style="text-align: center; color: red; padding: 20px;">获取记忆数据失败，请刷新页面重试</div>';
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

// 全局变量存储理财数据
let financeMonthlyData = {};
let financeYearlyData = {};

// 初始化理财记录
async function initFinance() {
    try {
        // 获取理财记录
        const recordsResponse = await fetch(`${API_BASE}/finance`);
        if (recordsResponse.ok) {
            const records = await recordsResponse.json();
            renderFinanceTable(records);
        }

        // 获取月度统计
        const monthlyResponse = await fetch(`${API_BASE}/finance/monthly-stats`);
        if (monthlyResponse.ok) {
            const data = await monthlyResponse.json();
            financeMonthlyData = data.monthly || {};
            financeYearlyData = data.yearly || {};

            // 初始化年份选择器
            initYearMonthSelectors(data.yearly || {});

            // 渲染年度概览
            renderFinanceOverview(data.yearly || {});

            // 默认显示当前月份
            const currentMonth = data.current_month || new Date().toISOString().slice(0, 7);
            renderMonthlyReport(currentMonth);

            // 默认显示当前年份
            const currentYear = data.current_year || new Date().getFullYear().toString();
            renderYearlyReport(currentYear);
        }
    } catch (error) {
        console.error('获取理财数据失败:', error);
    }

    // 添加记录按钮点击事件
    document.getElementById('add-finance').addEventListener('click', function() {
        alert('添加理财记录功能开发中...');
    });

    // 筛选按钮事件
    document.getElementById('finance-filter-btn').addEventListener('click', function() {
        const year = document.getElementById('finance-year-select').value;
        const month = document.getElementById('finance-month-select').value;

        if (year) {
            renderYearlyReport(year);
        }
        if (month) {
            renderMonthlyReport(month);
        }
    });

    // 查看全部按钮
    document.getElementById('finance-all-btn').addEventListener('click', function() {
        const currentMonth = new Date().toISOString().slice(0, 7);
        const currentYear = new Date().getFullYear().toString();
        renderMonthlyReport(currentMonth);
        renderYearlyReport(currentYear);
    });
}

// 渲染理财记录表格
function renderFinanceTable(records) {
    const tableBody = document.querySelector('#finance-table tbody');
    tableBody.innerHTML = '';

    if (records.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: #999;">暂无记录</td></tr>';
        return;
    }

    records.forEach(record => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${record.id}</td>
            <td><span class="badge ${record.type === 'income' ? 'income-badge' : 'expense-badge'}">${record.type === 'income' ? '收入' : '支出'}</span></td>
            <td>${record.amount.toFixed(2)}</td>
            <td>${record.category}</td>
            <td>${record.note || '-'}</td>
            <td>${record.record_date}</td>
            <td class="action-buttons">
                <button class="edit">编辑</button>
                <button class="delete">删除</button>
            </td>
        `;
        tableBody.appendChild(row);
    });
}

// 初始化年月选择器
function initYearMonthSelectors(yearlyData) {
    const yearSelect = document.getElementById('finance-year-select');
    const monthSelect = document.getElementById('finance-month-select');

    // 清空并添加年份选项
    yearSelect.innerHTML = '<option value="">选择年份</option>';
    Object.keys(yearlyData).sort((a, b) => b - a).forEach(year => {
        const option = document.createElement('option');
        option.value = year;
        option.textContent = year + '年';
        yearSelect.appendChild(option);
    });

    // 添加月份选项
    monthSelect.innerHTML = '<option value="">选择月份</option>';
    for (let i = 1; i <= 12; i++) {
        const month = i.toString().padStart(2, '0');
        const option = document.createElement('option');
        option.value = month;
        option.textContent = month + '月';
        monthSelect.appendChild(option);
    }
}

// 渲染年度概览卡片
function renderFinanceOverview(yearlyData) {
    const container = document.getElementById('finance-overview');
    container.innerHTML = '';

    const years = Object.keys(yearlyData).sort((a, b) => b - a);
    if (years.length === 0) {
        container.innerHTML = '<div style="text-align: center; color: #999; padding: 20px;">暂无理财数据</div>';
        return;
    }

    years.forEach(year => {
        const data = yearlyData[year];
        const card = document.createElement('div');
        card.className = 'overview-card';
        card.innerHTML = `
            <div class="overview-label">${year}年结余</div>
            <div class="overview-value">${data.balance.toFixed(2)}元</div>
        `;
        container.appendChild(card);
    });
}

// 渲染月度报表
function renderMonthlyReport(yearMonth) {
    const data = financeMonthlyData[yearMonth];
    if (!data) {
        // 清空显示
        document.getElementById('month-income').textContent = '0元';
        document.getElementById('month-expense').textContent = '0元';
        document.getElementById('month-balance').textContent = '0元';
        document.getElementById('month-savings-rate').textContent = '0%';
        document.getElementById('category-list').innerHTML = '<div style="color: #999;">该月份暂无数据</div>';
        return;
    }

    // 更新卡片数据
    document.getElementById('month-income').textContent = data.income.toFixed(2) + '元';
    document.getElementById('month-expense').textContent = data.expense.toFixed(2) + '元';
    document.getElementById('month-balance').textContent = data.balance.toFixed(2) + '元';
    document.getElementById('month-savings-rate').textContent = data.savings_rate.toFixed(1) + '%';

    // 更新预算进度条
    const budgetProgress = document.getElementById('budget-progress');
    const budgetText = document.getElementById('budget-text');
    const budgetPercent = data.budget > 0 ? (data.expense / data.budget * 100) : 0;

    budgetProgress.style.width = Math.min(budgetPercent, 100) + '%';
    budgetText.textContent = `${data.expense.toFixed(2)} / ${data.budget.toFixed(2)}元`;

    // 设置进度条颜色
    budgetProgress.className = 'budget-progress';
    if (budgetPercent > 100) {
        budgetProgress.classList.add('danger');
    } else if (budgetPercent > 80) {
        budgetProgress.classList.add('warning');
    }

    // 渲染分类支出
    renderCategoryList('category-list', data.categories || {}, data.expense);
}

// 渲染年度报表
async function renderYearlyReport(year) {
    try {
        const response = await fetch(`${API_BASE}/finance/yearly-report/${year}`);
        if (!response.ok) return;

        const data = await response.json();

        // 更新年度卡片
        document.getElementById('year-income').textContent = data.total_income.toFixed(2) + '元';
        document.getElementById('year-expense').textContent = data.total_expense.toFixed(2) + '元';
        document.getElementById('year-balance').textContent = data.total_balance.toFixed(2) + '元';
        document.getElementById('year-savings-rate').textContent = data.savings_rate.toFixed(1) + '%';

        // 渲染月度趋势表格
        const tbody = document.querySelector('#monthly-trend-table tbody');
        tbody.innerHTML = '';

        const months = data.months || {};
        Object.keys(months).sort().forEach(month => {
            const mData = months[month];
            const row = document.createElement('tr');
            const savingsClass = mData.balance >= 0 ? 'trend-positive' : 'trend-negative';
            row.innerHTML = `
                <td>${month}月</td>
                <td>${mData.income.toFixed(2)}</td>
                <td>${mData.expense.toFixed(2)}</td>
                <td class="${savingsClass}">${mData.balance.toFixed(2)}</td>
                <td>${mData.savings_rate.toFixed(1)}%</td>
            `;
            tbody.appendChild(row);
        });

        if (Object.keys(months).length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: #999;">暂无月度数据</td></tr>';
        }

        // 渲染年度分类支出
        renderCategoryList('yearly-category-list', data.category_breakdown || {}, data.total_expense);
    } catch (error) {
        console.error('获取年度报表失败:', error);
    }
}

// 渲染分类列表
function renderCategoryList(elementId, categories, totalExpense) {
    const container = document.getElementById(elementId);
    container.innerHTML = '';

    const sortedCategories = Object.entries(categories).sort((a, b) => b[1] - a[1]);

    if (sortedCategories.length === 0) {
        container.innerHTML = '<div style="color: #999;">暂无分类数据</div>';
        return;
    }

    sortedCategories.forEach(([category, amount]) => {
        const percent = totalExpense > 0 ? (amount / totalExpense * 100) : 0;
        const item = document.createElement('div');
        item.className = 'category-item';
        item.innerHTML = `
            <div class="category-name">${category}</div>
            <div class="category-bar-wrapper">
                <div class="category-bar" style="width: ${percent}%"></div>
            </div>
            <div class="category-amount">${amount.toFixed(2)}</div>
            <div class="category-percent">${percent.toFixed(1)}%</div>
        `;
        container.appendChild(item);
    });
}

// 初始化配置中心
function initSettings() {
    // 加载已保存的配置
    loadSettings();
    
    // 保存配置按钮点击事件
    document.getElementById('settings-form').addEventListener('submit', function(e) {
        e.preventDefault();
        saveSettings();
    });
}

// 加载配置
function loadSettings() {
    const settings = JSON.parse(localStorage.getItem('smtp_settings') || '{}');
    document.getElementById('smtp-host').value = settings.host || '';
    document.getElementById('smtp-port').value = settings.port || '587';
    document.getElementById('smtp-user').value = settings.user || '';
    document.getElementById('smtp-password').value = settings.password || '';
    document.getElementById('smtp-to').value = settings.to || '';
}

// 保存配置
function saveSettings() {
    const settings = {
        host: document.getElementById('smtp-host').value,
        port: document.getElementById('smtp-port').value,
        user: document.getElementById('smtp-user').value,
        password: document.getElementById('smtp-password').value,
        to: document.getElementById('smtp-to').value
    };
    
    localStorage.setItem('smtp_settings', JSON.stringify(settings));
    alert('SMTP配置已保存');
}

// 初始化KimiAI日志
async function initKimiLogs() {
    try {
        const response = await fetch(`${API_BASE}/chat/history`);
        if (response.ok) {
            const result = await response.json();
            const container = document.getElementById('kimi-logs-container');
            container.innerHTML = '';

            if (result.code === 200 && result.data) {
                const logsByDay = result.data;
                
                // 按日期倒序排序
                const sortedDates = Object.keys(logsByDay).sort((a, b) => {
                    return new Date(b) - new Date(a);
                });

                if (sortedDates.length === 0) {
                    container.innerHTML = '<div style="text-align: center; color: #666; padding: 20px;">暂无聊天记录</div>';
                    return;
                }

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
                        <span class="day-count">${dayLogs.length} 条对话</span>
                    `;

                    // 日期内容
                    const dayContent = document.createElement('div');
                    dayContent.className = 'day-content expanded';

                    // 为每条日志创建条目
                    dayLogs.forEach(log => {
                        const logEntry = document.createElement('div');
                        logEntry.className = 'log-entry';
                        logEntry.innerHTML = `
                            <div class="log-meta">
                                <span class="log-time">${log.timestamp}</span>
                            </div>
                            <div class="log-content"><strong>用户:</strong> ${log.user_message}</div>
                            <div class="log-response"><strong>AI助手:</strong> ${log.ai_response}</div>
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
            } else {
                container.innerHTML = '<div style="text-align: center; color: #666; padding: 20px;">暂无聊天记录</div>';
            }
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

// 初始化聊天功能
function initChat() {
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');
    const chatMessages = document.getElementById('chat-messages');

    // 设置欢迎消息时间
    const welcomeTime = document.getElementById('bot-welcome-time');
    if (welcomeTime) {
        welcomeTime.textContent = formatCurrentTime();
    }

    // 自动调整输入框高度
    chatInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 100) + 'px';
    });

    // 发送按钮点击事件
    sendBtn.addEventListener('click', sendMessage);

    // 回车发送消息
    chatInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    async function sendMessage() {
        const message = chatInput.value.trim();
        if (!message) return;

        console.log('准备发送消息:', message);

        // 添加用户消息
        addMessage(message, 'sent');
        chatInput.value = '';
        chatInput.style.height = 'auto';

        // 添加机器人正在输入的状态
        const typingMessage = addTypingIndicator();

        try {
            console.log('正在调用API:', `${API_BASE}/chat/send`);
            
            // 调用API获取AI回复
            const response = await fetch(`${API_BASE}/chat/send`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: message
                })
            });

            console.log('API响应状态:', response.status);
            
            const data = await response.json();
            console.log('API响应数据:', data);

            // 移除正在输入的状态
            removeTypingIndicator(typingMessage);

            if (data.code === 0 || data.code === 200) {
                console.log('收到AI回复:', data.response);
                addMessage(data.response || '抱歉，我没有收到有效的回复', 'received');
            } else {
                console.error('API返回错误:', data);
                addMessage('抱歉，发生了错误: ' + (data.msg || data.message || '未知错误'), 'received');
            }
        } catch (error) {
            console.error('发送消息失败:', error);
            removeTypingIndicator(typingMessage);
            addMessage('网络错误，请检查网络连接后重试: ' + error.message, 'received');
        }
    }

    function addMessage(text, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;

        const avatar = type === 'sent' ? '👤' : '🤖';
        const time = formatCurrentTime();

        messageDiv.innerHTML = `
            <div class="message-avatar">${avatar}</div>
            <div class="message-content">
                <div class="message-text">${escapeHtml(text)}</div>
                <div class="message-time">${time}</div>
            </div>
        `;

        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        return messageDiv;
    }

    function addTypingIndicator() {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message received typing';
        messageDiv.innerHTML = `
            <div class="message-avatar">🤖</div>
            <div class="message-content">
                <div class="message-text"></div>
            </div>
        `;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return messageDiv;
    }

    function removeTypingIndicator(element) {
        if (element && element.parentNode) {
            element.parentNode.removeChild(element);
        }
    }

    function formatCurrentTime() {
        const now = new Date();
        return now.toLocaleTimeString('zh-CN', {
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
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
