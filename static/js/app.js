// LOF基金套利工具 - 前端JavaScript

let autoRefreshInterval = null;
let updateInterval = 60; // 默认60秒
let favoriteFunds = new Set(); // 自选基金集合
let showFavoritesOnly = false; // 是否只显示自选基金
let currentUser = null; // 当前登录用户
let notificationCheckInterval = null; // 通知检查定时器

// 初始化
document.addEventListener('DOMContentLoaded', async function() {
    // #region agent log
    fetch('http://127.0.0.1:7243/ingest/c359bf7a-79f8-4b93-af0b-f5a5dba44447',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:DOMContentLoaded:entry',message:'页面初始化开始',data:{},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'1'})}).catch(()=>{});
    // #endregion
    
    try {
        // #region agent log
        fetch('http://127.0.0.1:7243/ingest/c359bf7a-79f8-4b93-af0b-f5a5dba44447',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:DOMContentLoaded:before_initEventListeners',message:'初始化事件监听器前',data:{},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'1'})}).catch(()=>{});
        // #endregion
        initEventListeners();
        
        // #region agent log
        fetch('http://127.0.0.1:7243/ingest/c359bf7a-79f8-4b93-af0b-f5a5dba44447',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:DOMContentLoaded:before_loadConfig',message:'加载配置前',data:{},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'1'})}).catch(()=>{});
        // #endregion
        loadConfig();
        
        // #region agent log
        fetch('http://127.0.0.1:7243/ingest/c359bf7a-79f8-4b93-af0b-f5a5dba44447',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:DOMContentLoaded:before_checkAuthStatus',message:'检查登录状态前',data:{},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'1'})}).catch(()=>{});
        // #endregion
        await checkAuthStatus(); // 检查登录状态（先检查登录状态）
        
        // #region agent log
        fetch('http://127.0.0.1:7243/ingest/c359bf7a-79f8-4b93-af0b-f5a5dba44447',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:DOMContentLoaded:before_loadFavoriteFunds',message:'加载自选基金前',data:{},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'1'})}).catch(()=>{});
        // #endregion
        await loadFavoriteFunds(); // 加载自选基金列表（登录状态检查后再加载）
        await loadUnreadNotificationCount(); // 加载未读通知数量
        startNotificationCheck(); // 开始定期检查通知
        
        // #region agent log
        fetch('http://127.0.0.1:7243/ingest/c359bf7a-79f8-4b93-af0b-f5a5dba44447',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:DOMContentLoaded:before_loadFunds',message:'加载基金列表前',data:{},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'1'})}).catch(()=>{});
        // #endregion
        loadFunds();
        
        // #region agent log
        fetch('http://127.0.0.1:7243/ingest/c359bf7a-79f8-4b93-af0b-f5a5dba44447',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:DOMContentLoaded:success',message:'页面初始化完成',data:{},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'1'})}).catch(()=>{});
        // #endregion
    } catch (error) {
        // #region agent log
        fetch('http://127.0.0.1:7243/ingest/c359bf7a-79f8-4b93-af0b-f5a5dba44447',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:DOMContentLoaded:error',message:'页面初始化错误',data:{error:error.message,stack:error.stack},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'1'})}).catch(()=>{});
        // #endregion
        console.error('页面初始化失败:', error);
        alert('页面初始化失败: ' + error.message);
    }
});

// 初始化事件监听
function initEventListeners() {
    // #region agent log
    fetch('http://127.0.0.1:7243/ingest/c359bf7a-79f8-4b93-af0b-f5a5dba44447',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:initEventListeners:entry',message:'初始化事件监听器',data:{},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'2'})}).catch(()=>{});
    // #endregion
    
    // 安全地绑定事件监听器（检查元素是否存在）
    const safeAddEventListener = (id, event, handler) => {
        const element = document.getElementById(id);
        if (element) {
            element.addEventListener(event, handler);
            // #region agent log
            fetch('http://127.0.0.1:7243/ingest/c359bf7a-79f8-4b93-af0b-f5a5dba44447',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:initEventListeners:bind_success',message:'事件绑定成功',data:{elementId:id,event:event},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'2'})}).catch(()=>{});
            // #endregion
        } else {
            // #region agent log
            fetch('http://127.0.0.1:7243/ingest/c359bf7a-79f8-4b93-af0b-f5a5dba44447',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:initEventListeners:element_missing',message:'元素不存在',data:{elementId:id},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'2'})}).catch(()=>{});
            // #endregion
            console.warn(`元素 ${id} 不存在，跳过事件绑定`);
        }
    };
    
    safeAddEventListener('refreshBtn', 'click', loadFunds);
    safeAddEventListener('autoRefreshBtn', 'click', toggleAutoRefresh);
    safeAddEventListener('arbitrageRecordsBtn', 'click', openArbitrageRecords);
    safeAddEventListener('settingsBtn', 'click', openSettings);
    safeAddEventListener('dataSourceConfigBtn', 'click', openDataSourceConfig);
    safeAddEventListener('userManagementBtn', 'click', openUserManagement);
    safeAddEventListener('adminArbitrageRecordsBtn', 'click', function(e) {
        // #region agent log
        fetch('http://127.0.0.1:7243/ingest/c359bf7a-79f8-4b93-af0b-f5a5dba44447',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:adminArbitrageRecordsBtn:click',message:'所有套利记录按钮被点击',data:{},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'1'})}).catch(()=>{});
        // #endregion
        e.preventDefault();
        openAdminArbitrageRecords();
    });
    safeAddEventListener('closeAdminArbitrageRecordsBtn', 'click', closeAdminArbitrageRecords);
    safeAddEventListener('closeAdminArbitrageRecordsFooterBtn', 'click', closeAdminArbitrageRecords);
    safeAddEventListener('refreshAdminArbitrageRecordsBtn', 'click', loadAdminArbitrageRecords);
    safeAddEventListener('applyAdminArbitrageFilterBtn', 'click', applyAdminArbitrageFilter);
    safeAddEventListener('notificationBtn', 'click', openNotifications);
    safeAddEventListener('closeNotificationBtn', 'click', closeNotifications);
    safeAddEventListener('closeNotificationFooterBtn', 'click', closeNotifications);
    safeAddEventListener('markAllReadBtn', 'click', markAllNotificationsRead);
    safeAddEventListener('deleteReadBtn', 'click', deleteAllReadNotifications);
    safeAddEventListener('closeSettingsBtn', 'click', closeSettings);
    safeAddEventListener('closeDataSourceConfigBtn', 'click', closeDataSourceConfig);
    safeAddEventListener('cancelDataSourceConfigBtn', 'click', closeDataSourceConfig);
    safeAddEventListener('saveDataSourceConfigBtn', 'click', saveDataSourceConfig);
    safeAddEventListener('closeUserManagementBtn', 'click', closeUserManagement);
    safeAddEventListener('closeUserManagementFooterBtn', 'click', closeUserManagement);
    safeAddEventListener('refreshUsersBtn', 'click', loadUsers);
    safeAddEventListener('closeEditUserBtn', 'click', closeEditUser);
    safeAddEventListener('cancelEditUserBtn', 'click', closeEditUser);
    safeAddEventListener('saveEditUserBtn', 'click', saveEditUser);
    safeAddEventListener('cancelSettingsBtn', 'click', closeSettings);
    safeAddEventListener('saveSettingsBtn', 'click', saveSettings);
    safeAddEventListener('closeDetailBtn', 'click', closeDetail);
    safeAddEventListener('clearLogBtn', 'click', clearLog);
    safeAddEventListener('mockModeToggle', 'change', toggleMockMode);
    safeAddEventListener('filterFavoritesBtn', 'click', toggleFavoritesFilter);
    
    // 用户认证相关事件
    safeAddEventListener('loginBtn', 'click', openAuthModal);
    safeAddEventListener('logoutBtn', 'click', logout);
    safeAddEventListener('closeAuthBtn', 'click', closeAuthModal);
    safeAddEventListener('loginTabBtn', 'click', () => switchAuthTab('login'));
    safeAddEventListener('registerTabBtn', 'click', () => switchAuthTab('register'));
    safeAddEventListener('submitLoginBtn', 'click', submitLogin);
    safeAddEventListener('submitRegisterBtn', 'click', submitRegister);
    safeAddEventListener('refreshCaptchaBtn', 'click', loadCaptcha);
    
    // 回车键提交
    const loginPasswordInput = document.getElementById('loginPassword');
    if (loginPasswordInput) {
        loginPasswordInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') submitLogin();
        });
    }
    
    const registerPasswordConfirmInput = document.getElementById('registerPasswordConfirm');
    if (registerPasswordConfirmInput) {
        registerPasswordConfirmInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') submitRegister();
        });
    }
    
    // 排序表头事件
    document.querySelectorAll('.sortable').forEach(th => {
        th.addEventListener('click', function() {
            const column = this.getAttribute('data-sort');
            if (!column) return;
            
            // 切换排序方向
            if (sortState.column === column) {
                sortState.direction = sortState.direction === 'asc' ? 'desc' : 'asc';
            } else {
                sortState.column = column;
                sortState.direction = 'asc';
            }
            
            // 更新表头样式
            document.querySelectorAll('.sortable').forEach(h => {
                h.classList.remove('sort-asc', 'sort-desc');
            });
            this.classList.add(`sort-${sortState.direction}`);
            
            // 重新显示（会自动应用排序）
            displayFunds(allFundsData);
        });
    });
    
    // 点击模态框外部关闭
    const settingsModal = document.getElementById('settingsModal');
    if (settingsModal) {
        settingsModal.addEventListener('click', function(e) {
            if (e.target === this) {
                closeSettings();
            }
        });
    }
    
    // #region agent log
    fetch('http://127.0.0.1:7243/ingest/c359bf7a-79f8-4b93-af0b-f5a5dba44447',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:initEventListeners:success',message:'事件监听器初始化完成',data:{},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'2'})}).catch(()=>{});
    // #endregion
}

// 加载配置
async function loadConfig() {
    try {
        const response = await fetch('/api/config');
        const result = await response.json();
        if (result.success) {
            const config = result.data;
            updateInterval = config.update_interval || 60; // 默认60秒
            if (document.getElementById('mockModeToggle')) {
                document.getElementById('mockModeToggle').checked = config.use_mock_data;
            }
            populateSettingsForm(config);
        }
    } catch (error) {
        log('加载配置失败: ' + error.message, 'error');
    }
}

// 填充设置表单
async function populateSettingsForm(config) {
    document.getElementById('buyCommission').value = (config.trade_fees.buy_commission * 100).toFixed(4);
    document.getElementById('sellCommission').value = (config.trade_fees.sell_commission * 100).toFixed(4);
    document.getElementById('subscribeFee').value = (config.trade_fees.subscribe_fee * 100).toFixed(2);
    document.getElementById('redeemFee').value = (config.trade_fees.redeem_fee * 100).toFixed(2);
    document.getElementById('stampTax').value = (config.trade_fees.stamp_tax * 100).toFixed(4);
    document.getElementById('minProfitRate').value = (config.arbitrage_threshold.min_profit_rate * 100).toFixed(2);
    document.getElementById('minPriceDiff').value = (config.arbitrage_threshold.min_price_diff * 100).toFixed(2);
    document.getElementById('updateInterval').value = config.update_interval;
}

// 填充数据源配置
async function populateDataSources(dataSources, containerId = 'dataSourcesContainer') {
    const container = document.getElementById(containerId);
    if (!dataSources) {
        container.innerHTML = '<p class="placeholder">数据源配置未找到</p>';
        return;
    }
    
    // 获取数据源状态
    let statusData = {};
    try {
        const statusResponse = await fetch('/api/data-sources/status');
        const statusResult = await statusResponse.json();
        if (statusResult.success) {
            statusData = statusResult.data;
        }
    } catch (error) {
        console.error('获取数据源状态失败:', error);
    }
    
    let html = '';
    
    // 价格数据源
    html += '<div class="data-source-group"><h4>价格数据源</h4>';
    if (dataSources.price_sources) {
        const sorted = Object.entries(dataSources.price_sources).sort((a, b) => a[1].priority - b[1].priority);
        sorted.forEach(([key, source]) => {
            const status = statusData.price_sources?.[key] || {installed: true, available: true};
            html += createDataSourceRow(key, source, status, 'price_sources');
        });
    }
    html += '</div>';
    
    // 净值数据源
    html += '<div class="data-source-group"><h4>净值数据源</h4>';
    if (dataSources.nav_sources) {
        const sorted = Object.entries(dataSources.nav_sources).sort((a, b) => a[1].priority - b[1].priority);
        sorted.forEach(([key, source]) => {
            const status = statusData.nav_sources?.[key] || {installed: true, available: true};
            html += createDataSourceRow(key, source, status, 'nav_sources');
        });
    }
    html += '</div>';
    
    // 基金列表数据源
    html += '<div class="data-source-group"><h4>基金列表数据源</h4>';
    if (dataSources.fund_list_sources) {
        const sorted = Object.entries(dataSources.fund_list_sources).sort((a, b) => a[1].priority - b[1].priority);
        sorted.forEach(([key, source]) => {
            const status = statusData.fund_list_sources?.[key] || {installed: true, available: true};
            html += createDataSourceRow(key, source, status, 'fund_list_sources', source.token);
        });
    }
    html += '</div>';
    
    // 中文名称数据源
    html += '<div class="data-source-group"><h4>中文名称数据源</h4>';
    if (dataSources.name_sources) {
        const sorted = Object.entries(dataSources.name_sources).sort((a, b) => a[1].priority - b[1].priority);
        sorted.forEach(([key, source]) => {
            const status = statusData.name_sources?.[key] || {installed: true, available: true};
            html += createDataSourceRow(key, source, status, 'name_sources');
        });
    }
    html += '</div>';
    
    // 限购信息数据源
    html += '<div class="data-source-group"><h4>限购信息数据源</h4>';
    if (dataSources.purchase_limit_sources) {
        const sorted = Object.entries(dataSources.purchase_limit_sources).sort((a, b) => a[1].priority - b[1].priority);
        sorted.forEach(([key, source]) => {
            const status = statusData.purchase_limit_sources?.[key] || {installed: true, available: true};
            html += createDataSourceRow(key, source, status, 'purchase_limit_sources');
        });
    }
    html += '</div>';
    
    container.innerHTML = html;
}

// 创建数据源配置行
function createDataSourceRow(key, source, status, category, token = null) {
    const installedClass = status.installed ? 'installed' : 'not-installed';
    const statusText = status.installed ? (status.available ? '可用' : '不可用') : '未安装';
    
    let html = `<div class="data-source-item">
        <div class="data-source-header">
            <label class="switch">
                <input type="checkbox" class="data-source-enabled" 
                    data-category="${category}" 
                    data-key="${key}" 
                    ${source.enabled ? 'checked' : ''}
                    ${!status.installed ? 'disabled' : ''}>
                <span class="slider"></span>
            </label>
            <span class="data-source-name">${source.name}</span>
            <span class="data-source-status ${installedClass}">${statusText}</span>
            <span class="data-source-priority">优先级: 
                <input type="number" class="data-source-priority-input" 
                    data-category="${category}" 
                    data-key="${key}" 
                    value="${source.priority}" 
                    min="1" 
                    max="100" 
                    style="width: 50px; margin-left: 5px;">
            </span>
        </div>`;
    
    // 如果有关键配置（如token），显示输入框
    if (token !== null && key === 'tushare') {
        html += `<div class="data-source-config" style="margin-top: 5px; margin-left: 30px;">
            <label>Token:</label>
            <input type="text" class="data-source-token-input" 
                data-category="${category}" 
                data-key="${key}" 
                value="${token || ''}" 
                placeholder="Tushare Token"
                style="width: 400px; margin-left: 5px;">
        </div>`;
    }
    
    html += '</div>';
    return html;
}

// 加载基金列表
async function loadFunds() {
    // #region agent log
    fetch('http://127.0.0.1:7243/ingest/c359bf7a-79f8-4b93-af0b-f5a5dba44447',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:loadFunds:entry',message:'加载基金列表开始',data:{},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'1'})}).catch(()=>{});
    // #endregion
    
    const tbody = document.getElementById('fundsTableBody');
    
    // #region agent log
    fetch('http://127.0.0.1:7243/ingest/c359bf7a-79f8-4b93-af0b-f5a5dba44447',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:loadFunds:check_tbody',message:'检查表格元素',data:{tbodyExists:!!tbody},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'1'})}).catch(()=>{});
    // #endregion
    
    if (!tbody) {
        // #region agent log
        fetch('http://127.0.0.1:7243/ingest/c359bf7a-79f8-4b93-af0b-f5a5dba44447',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:loadFunds:tbody_missing',message:'表格元素不存在',data:{},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'1'})}).catch(()=>{});
        // #endregion
        console.error('基金表格元素不存在');
        return;
    }
    
    tbody.innerHTML = '<tr><td colspan="10" class="loading">正在加载数据...</td></tr>';
    
    try {
        // 获取基金代码列表
        const fundsResponse = await fetch('/api/funds');
        const fundsResult = await fundsResponse.json();
        
        // #region agent log
        fetch('http://127.0.0.1:7243/ingest/c359bf7a-79f8-4b93-af0b-f5a5dba44447',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:loadFunds:after_funds_api',message:'获取基金列表API返回',data:{success:fundsResult.success,funds_count:fundsResult.funds?Object.keys(fundsResult.funds).length:0},timestamp:Date.now(),sessionId:'debug-session'})}).catch(()=>{});
        // #endregion
        
        if (!fundsResult.success) {
            throw new Error('获取基金列表失败');
        }
        
        const fundCodes = Object.keys(fundsResult.funds);
        
        // #region agent log
        fetch('http://127.0.0.1:7243/ingest/c359bf7a-79f8-4b93-af0b-f5a5dba44447',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:loadFunds:before_batch',message:'准备批量获取基金信息',data:{fund_codes_count:fundCodes.length},timestamp:Date.now(),sessionId:'debug-session'})}).catch(()=>{});
        // #endregion
        
        // 分批加载基金信息（每批50只，避免超时）
        const batchSize = 50;
        const batches = [];
        for (let i = 0; i < fundCodes.length; i += batchSize) {
            batches.push(fundCodes.slice(i, i + batchSize));
        }
        
        // #region agent log
        fetch('http://127.0.0.1:7243/ingest/c359bf7a-79f8-4b93-af0b-f5a5dba44447',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:loadFunds:batch_info',message:'分批加载信息',data:{total_funds:fundCodes.length,batch_size:batchSize,total_batches:batches.length},timestamp:Date.now(),sessionId:'debug-session'})}).catch(()=>{});
        // #endregion
        
        tbody.innerHTML = `<tr><td colspan="10" class="loading">正在加载数据... (0/${fundCodes.length})</td></tr>`;
        
        let allResults = [];
        let processedCount = 0;
        
        // 逐批加载
        for (let batchIndex = 0; batchIndex < batches.length; batchIndex++) {
            const batch = batches[batchIndex];
            
            // 更新加载提示
            tbody.innerHTML = `<tr><td colspan="10" class="loading">正在加载数据... (${processedCount}/${fundCodes.length}) - 批次 ${batchIndex + 1}/${batches.length}</td></tr>`;
            
            try {
                // 创建超时控制器（每批120秒）
                const controller = new AbortController();
                const timeoutId = setTimeout(() => {
                    controller.abort();
                }, 120000); // 每批120秒超时
                
                const response = await fetch('/api/funds/batch', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ codes: batch }),
                    signal: controller.signal
                });
                
                clearTimeout(timeoutId);
                
                const result = await response.json();
                
                // #region agent log
                fetch('http://127.0.0.1:7243/ingest/c359bf7a-79f8-4b93-af0b-f5a5dba44447',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:loadFunds:batch_result',message:'批次处理结果',data:{batch_index:batchIndex+1,total_batches:batches.length,success:result.success,data_count:result.data?result.data.length:0,requested_count:batch.length,count:result.count||0},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'B'})}).catch(()=>{});
                // #endregion
                
                if (result.success && result.data) {
                    const beforeCount = allResults.length;
                    allResults = allResults.concat(result.data);
                    const afterCount = allResults.length;
                    processedCount += batch.length;
                    
                    // #region agent log
                    fetch('http://127.0.0.1:7243/ingest/c359bf7a-79f8-4b93-af0b-f5a5dba44447',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:loadFunds:batch_merged',message:'批次数据合并',data:{batch_index:batchIndex+1,requested:batch.length,returned:result.data.length,before_merge:beforeCount,after_merge:afterCount,processed_count:processedCount},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'B'})}).catch(()=>{});
                    // #endregion
                    
                    if (result.data.length < batch.length) {
                        log(`批次 ${batchIndex + 1}: 请求 ${batch.length} 只，实际返回 ${result.data.length} 只`, 'warning');
                    }
                } else {
                    // #region agent log
                    fetch('http://127.0.0.1:7243/ingest/c359bf7a-79f8-4b93-af0b-f5a5dba44447',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:loadFunds:batch_failed',message:'批次加载失败',data:{batch_index:batchIndex+1,error:result.message||'未知错误'},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'B'})}).catch(()=>{});
                    // #endregion
                    log(`批次 ${batchIndex + 1} 加载失败: ${result.message || '未知错误'}`, 'warning');
                }
            } catch (fetchError) {
                if (fetchError.name === 'AbortError') {
                    log(`批次 ${batchIndex + 1} 超时，跳过`, 'warning');
                } else {
                    log(`批次 ${batchIndex + 1} 加载失败: ${fetchError.message}`, 'error');
                }
                // 继续处理下一批，不中断
            }
        }
        
        // 所有批次处理完成，显示结果
        // #region agent log
        fetch('http://127.0.0.1:7243/ingest/c359bf7a-79f8-4b93-af0b-f5a5dba44447',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:loadFunds:all_batches_complete',message:'所有批次处理完成',data:{total_requested:fundCodes.length,actual_loaded:allResults.length,processed_count:processedCount,total_batches:batches.length},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'B'})}).catch(()=>{});
        // #endregion
        
        if (allResults.length > 0) {
            displayFunds(allResults);
            if (allResults.length < fundCodes.length) {
                const missing = fundCodes.length - allResults.length;
                const percentage = ((allResults.length / fundCodes.length) * 100).toFixed(1);
                log(`部分加载: ${allResults.length}/${fundCodes.length} 只基金数据 (${percentage}%，缺失 ${missing} 只)`, 'warning');
            } else {
                log(`成功加载 ${allResults.length}/${fundCodes.length} 只基金数据`, 'success');
            }
            updateLastUpdateTime();
            
            // 异步获取限购信息（不阻塞显示，后台更新）
            updatePurchaseLimitsAsync(allResults.map(f => f.fund_code));
        } else {
            throw new Error('未能加载任何基金数据');
        }
        
        return; // 提前返回，避免执行下面的代码
    } catch (error) {
        // #region agent log
        fetch('http://127.0.0.1:7243/ingest/c359bf7a-79f8-4b93-af0b-f5a5dba44447',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:loadFunds:error',message:'加载基金失败',data:{error:error.message,error_type:error.name},timestamp:Date.now(),sessionId:'debug-session'})}).catch(()=>{});
        // #endregion
        
        tbody.innerHTML = `<tr><td colspan="10" class="loading" style="color: #f44336;">加载失败: ${error.message}</td></tr>`;
        log('加载基金数据失败: ' + error.message, 'error');
    }
}

// 存储所有基金数据（用于筛选和排序）
let allFundsData = [];
// 排序状态：{column: 'fund_code', direction: 'asc'|'desc'}
let sortState = { column: null, direction: 'asc' };

// 显示基金列表
function displayFunds(funds) {
    allFundsData = funds; // 保存所有基金数据
    
    const tbody = document.getElementById('fundsTableBody');
    
    if (funds.length === 0) {
        tbody.innerHTML = '<tr><td colspan="11" class="loading">暂无数据</td></tr>';
        return;
    }
    
    // 应用自选筛选
    let filteredFunds = funds;
    if (showFavoritesOnly) {
        filteredFunds = funds.filter(fund => favoriteFunds.has(fund.fund_code));
    }
    
    // 更新统计信息
    updateStats(filteredFunds);
    
    // 应用排序
    let sortedFunds = filteredFunds;
    if (sortState.column) {
        sortedFunds = sortFunds(filteredFunds, sortState.column, sortState.direction);
    }
    
    tbody.innerHTML = sortedFunds.map(fund => {
        const isOpportunity = fund.has_opportunity;
        const rowClass = isOpportunity ? 'opportunity' : '';
        const statusClass = isOpportunity ? 'status-opportunity' : 'status-none';
        const statusText = isOpportunity ? '有机会' : '无机会';
        const typeClass = fund.arbitrage_type === '溢价套利' ? 'type-premium' : 'type-discount';
        const profitClass = fund.profit_rate >= 0 ? 'positive' : 'negative';
        const profitSign = fund.profit_rate >= 0 ? '+' : '';
        
        // 格式化限购信息
        let purchaseLimitDisplay = '<span style="color: #4CAF50;">不限</span>';
        if (fund.purchase_limit && fund.purchase_limit.is_limited && fund.purchase_limit.limit_amount) {
            const amount = fund.purchase_limit.limit_amount;
            const display = amount >= 10000 ? 
                (amount / 10000).toFixed(1) + '万' : 
                amount.toFixed(0) + '元';
            purchaseLimitDisplay = `<span style="color: #f44336;">${display}</span>`;
        }
        
        const isFavorite = favoriteFunds.has(fund.fund_code);
        const starIcon = isFavorite ? '⭐' : '☆';
        const starClass = isFavorite ? 'favorite-star active' : 'favorite-star';
        
        return `
            <tr class="${rowClass}" data-code="${fund.fund_code}">
                <td>
                    <span class="${starClass}" data-code="${fund.fund_code}" style="cursor: pointer; font-size: 18px; user-select: none;" title="${isFavorite ? '取消自选' : '加入自选'}">${starIcon}</span>
                </td>
                <td><strong>${fund.fund_code}</strong></td>
                <td>${fund.fund_name || '--'}</td>
                <td>${fund.price.toFixed(4)}</td>
                <td>${fund.nav.toFixed(4)}</td>
                <td class="${fund.price_diff_pct >= 0 ? 'positive' : 'negative'}">${fund.price_diff_pct >= 0 ? '+' : ''}${fund.price_diff_pct.toFixed(2)}%</td>
                <td><span class="arbitrage-type ${typeClass}">${fund.arbitrage_type}</span></td>
                <td class="profit-rate ${profitClass}">${profitSign}${fund.profit_rate.toFixed(2)}%</td>
                <td style="font-size: 12px; white-space: nowrap;">${purchaseLimitDisplay}</td>
                <td><span class="status-badge ${statusClass}">${statusText}</span></td>
                <td>
                    <button class="btn btn-small btn-secondary" onclick="showDetail('${fund.fund_code}')" style="margin-right: 5px;">详情</button>
                    <button class="btn btn-small btn-primary" onclick="openRecordArbitrageModal('${fund.fund_code}', '${(fund.fund_name || '').replace(/'/g, "\\'")}', '${fund.arbitrage_type}', ${fund.price}, ${fund.nav})" title="记录套利交易">记录</button>
                </td>
            </tr>
        `;
    }).join('');
    
    // 添加行点击事件
    tbody.querySelectorAll('tr[data-code]').forEach(row => {
        row.addEventListener('click', function(e) {
            if (e.target.tagName !== 'BUTTON' && !e.target.classList.contains('favorite-star')) {
                const code = this.getAttribute('data-code');
                showDetail(code);
            }
        });
    });
    
    // 添加自选星标点击事件
    tbody.querySelectorAll('.favorite-star').forEach(star => {
        star.addEventListener('click', function(e) {
            e.stopPropagation(); // 阻止事件冒泡
            const code = this.getAttribute('data-code');
            toggleFavorite(code);
        });
    });
}

// 排序基金
function sortFunds(funds, column, direction) {
    const sorted = [...funds].sort((a, b) => {
        let aVal, bVal;
        
        switch(column) {
            case 'fund_code':
                aVal = a.fund_code || '';
                bVal = b.fund_code || '';
                return aVal.localeCompare(bVal);
            case 'fund_name':
                aVal = (a.fund_name || '').toLowerCase();
                bVal = (b.fund_name || '').toLowerCase();
                return aVal.localeCompare(bVal);
            case 'fund_type':
                aVal = getFundType(a);
                bVal = getFundType(b);
                return aVal.localeCompare(bVal);
            case 'price':
                aVal = a.price || 0;
                bVal = b.price || 0;
                return aVal - bVal;
            case 'nav':
                aVal = a.nav || 0;
                bVal = b.nav || 0;
                return aVal - bVal;
            case 'price_diff_pct':
                aVal = a.price_diff_pct || 0;
                bVal = b.price_diff_pct || 0;
                return aVal - bVal;
            case 'arbitrage_type':
                aVal = (a.arbitrage_type || '').toLowerCase();
                bVal = (b.arbitrage_type || '').toLowerCase();
                return aVal.localeCompare(bVal);
            case 'profit_rate':
                aVal = a.profit_rate || 0;
                bVal = b.profit_rate || 0;
                return aVal - bVal;
            case 'purchase_limit':
                // 排序逻辑：不限购排在前面（值为-1），限购的按限购金额排序
                aVal = a.purchase_limit && a.purchase_limit.is_limited ? (a.purchase_limit.limit_amount || 0) : -1;
                bVal = b.purchase_limit && b.purchase_limit.is_limited ? (b.purchase_limit.limit_amount || 0) : -1;
                return aVal - bVal;
            case 'has_opportunity':
                aVal = a.has_opportunity ? 1 : 0;
                bVal = b.has_opportunity ? 1 : 0;
                return aVal - bVal;
            default:
                return 0;
        }
    });
    
    return direction === 'desc' ? sorted.reverse() : sorted;
}

// 显示基金详情
async function showDetail(fundCode) {
    const panel = document.getElementById('detailPanel');
    const content = document.getElementById('detailContent');
    const title = document.getElementById('detailTitle');
    
    panel.classList.add('active');
    content.innerHTML = '<p class="loading">加载中...</p>';
    
    try {
        const response = await fetch(`/api/fund/${fundCode}`);
        const result = await response.json();
        
        if (result.success) {
            const fund = result.data;
            title.textContent = `${fund.fund_code} ${fund.fund_name || ''}`;
            
            content.innerHTML = `
                <div class="detail-item">
                    <label>场内价格</label>
                    <value>${fund.price.toFixed(4)} 元</value>
                </div>
                <div class="detail-item">
                    <label>场外净值</label>
                    <value>${fund.nav.toFixed(4)} 元</value>
                </div>
                <div class="detail-item">
                    <label>溢价率</label>
                    <value style="color: ${fund.price_diff_pct >= 0 ? '#4CAF50' : '#f44336'};">
                        ${fund.price_diff_pct >= 0 ? '+' : ''}${fund.price_diff_pct.toFixed(2)}%
                    </value>
                </div>
                <div class="detail-item">
                    <label>套利类型</label>
                    <value>${fund.arbitrage_type}</value>
                </div>
                <div class="detail-item">
                    <label>操作方式</label>
                    <value>${fund.operation}</value>
                </div>
                <div class="detail-item">
                    <label>总成本率</label>
                    <value>${fund.total_cost_rate.toFixed(2)}%</value>
                </div>
                <div class="detail-item">
                    <label>预期收益率</label>
                    <value style="color: ${fund.profit_rate >= 0 ? '#4CAF50' : '#f44336'}; font-size: 20px;">
                        ${fund.profit_rate >= 0 ? '+' : ''}${fund.profit_rate.toFixed(2)}%
                    </value>
                </div>
                <div class="detail-item">
                    <label>投入1万元净收益</label>
                    <value style="color: ${fund.net_profit_10k >= 0 ? '#4CAF50' : '#f44336'}; font-size: 18px;">
                        ${fund.net_profit_10k >= 0 ? '+' : ''}${fund.net_profit_10k.toFixed(2)} 元
                    </value>
                </div>
                <div class="detail-item">
                    <label>套利状态</label>
                    <value>
                        <span class="status-badge ${fund.has_opportunity ? 'status-opportunity' : 'status-none'}">
                            ${fund.has_opportunity ? '有套利机会' : '套利机会不足'}
                        </span>
                    </value>
                </div>
                <div class="detail-item">
                    <label>更新时间</label>
                    <value>${fund.update_time || '--'}</value>
                </div>
            `;
            
            log(`查看基金详情: ${fundCode}`, 'info');
        } else {
            content.innerHTML = `<p class="placeholder" style="color: #f44336;">${result.message}</p>`;
        }
    } catch (error) {
        content.innerHTML = `<p class="placeholder" style="color: #f44336;">加载失败: ${error.message}</p>`;
        log('加载基金详情失败: ' + error.message, 'error');
    }
}

// 关闭详情面板
function closeDetail() {
    document.getElementById('detailPanel').classList.remove('active');
}

// 更新统计信息
function updateStats(funds) {
    document.getElementById('fundCount').textContent = funds.length;
    
    const opportunities = funds.filter(f => f.has_opportunity).length;
    document.getElementById('opportunityCount').textContent = opportunities;
    
    // 更新自选基金数量
    const favoriteCount = funds.filter(f => favoriteFunds.has(f.fund_code)).length;
    document.getElementById('favoriteCount').textContent = favoriteCount;
    
    const now = new Date();
    document.getElementById('lastUpdate').textContent = now.toLocaleTimeString('zh-CN');
}

// 更新最后更新时间
function updateLastUpdateTime() {
    const now = new Date();
    const timeStr = now.toLocaleTimeString('zh-CN');
    document.getElementById('lastUpdate').textContent = timeStr;
}

// 切换自动刷新
function toggleAutoRefresh() {
    const btn = document.getElementById('autoRefreshBtn');
    
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
        btn.textContent = '自动刷新';
        btn.classList.remove('btn-primary');
        btn.classList.add('btn-secondary');
        log('已停止自动刷新', 'info');
    } else {
        autoRefreshInterval = setInterval(loadFunds, updateInterval * 1000);
        btn.textContent = '停止刷新';
        btn.classList.remove('btn-secondary');
        btn.classList.add('btn-primary');
        log(`已开启自动刷新 (间隔: ${updateInterval}秒)`, 'success');
    }
}

// 打开设置
function openSettings() {
    if (!checkLogin()) {
        requireLogin();
        return;
    }
    document.getElementById('settingsModal').classList.add('active');
}

// 关闭设置
function closeSettings() {
    document.getElementById('settingsModal').classList.remove('active');
}

// 保存设置
async function saveSettings() {
    const tradeFees = {
        buy_commission: parseFloat(document.getElementById('buyCommission').value) / 100,
        sell_commission: parseFloat(document.getElementById('sellCommission').value) / 100,
        subscribe_fee: parseFloat(document.getElementById('subscribeFee').value) / 100,
        redeem_fee: parseFloat(document.getElementById('redeemFee').value) / 100,
        stamp_tax: parseFloat(document.getElementById('stampTax').value) / 100
    };
    
    const arbitrageThreshold = {
        min_profit_rate: parseFloat(document.getElementById('minProfitRate').value) / 100,
        // 将百分比转换回元（假设基于1元净值）
        min_price_diff: parseFloat(document.getElementById('minPriceDiff').value) / 100
    };
    
    updateInterval = parseInt(document.getElementById('updateInterval').value);
    
    try {
        const response = await fetch('/api/config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                trade_fees: tradeFees,
                arbitrage_threshold: arbitrageThreshold,
                data_sources: {
                    update_interval: updateInterval
                }
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            log('设置保存成功', 'success');
            closeSettings();
            
            // 如果正在自动刷新，重新设置间隔
            if (autoRefreshInterval) {
                toggleAutoRefresh();
                toggleAutoRefresh();
            }
        } else {
            // 检查是否是登录问题
            if (result.requires_login || response.status === 401) {
                alert('请先登录: ' + (result.message || '未登录'));
                closeSettings();
                if (typeof openAuthModal === 'function') {
                    openAuthModal();
                }
            } else {
                throw new Error(result.message);
            }
        }
    } catch (error) {
        log('保存设置失败: ' + error.message, 'error');
        alert('保存设置失败: ' + error.message);
    }
}

// ==================== 数据源配置相关函数（仅管理员） ====================

// 打开数据源配置
async function openDataSourceConfig() {
    if (!checkLogin()) {
        requireLogin();
        return;
    }
    
    // 检查是否为管理员
    if (!currentUser || currentUser.role !== 'admin') {
        alert('此功能需要管理员权限');
        return;
    }
    
    // 加载数据源配置
    try {
        const response = await fetch('/api/data-sources/config');
        const result = await response.json();
        if (result.success) {
            const config = result.data;
            document.getElementById('dataSourceUpdateInterval').value = config.update_interval;
            await populateDataSources(config.data_sources, 'dataSourceConfigContainer');
        }
    } catch (error) {
        log('加载数据源配置失败: ' + error.message, 'error');
    }
    
    document.getElementById('dataSourceConfigModal').classList.add('active');
}

// 关闭数据源配置
function closeDataSourceConfig() {
    document.getElementById('dataSourceConfigModal').classList.remove('active');
}

// 保存数据源配置
async function saveDataSourceConfig() {
    if (!checkLogin()) {
        requireLogin();
        return;
    }
    
    // 检查是否为管理员
    if (!currentUser || currentUser.role !== 'admin') {
        alert('此功能需要管理员权限');
        return;
    }
    
    const updateInterval = parseInt(document.getElementById('dataSourceUpdateInterval').value);
    
    // 收集数据源配置
    const dataSources = {
        update_interval: updateInterval,
        price_sources: {},
        nav_sources: {},
        fund_list_sources: {},
        name_sources: {},
        purchase_limit_sources: {}
    };
    
    // 收集所有数据源配置（从数据源配置模态框）
    document.querySelectorAll('#dataSourceConfigModal .data-source-enabled').forEach(checkbox => {
        const category = checkbox.getAttribute('data-category');
        const key = checkbox.getAttribute('data-key');
        const priorityInput = document.querySelector(`#dataSourceConfigModal .data-source-priority-input[data-category="${category}"][data-key="${key}"]`);
        const priority = priorityInput ? parseInt(priorityInput.value) : 1;
        
        if (!dataSources[category]) {
            dataSources[category] = {};
        }
        
        dataSources[category][key] = {
            enabled: checkbox.checked,
            priority: priority
        };
        
        // 如果有token输入框，也收集
        const tokenInput = document.querySelector(`#dataSourceConfigModal .data-source-token-input[data-category="${category}"][data-key="${key}"]`);
        if (tokenInput) {
            dataSources[category][key].token = tokenInput.value;
        }
    });
    
    try {
        const response = await fetch('/api/data-sources/config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                data_sources: dataSources
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            log('数据源配置保存成功', 'success');
            closeDataSourceConfig();
            
            // 如果正在自动刷新，重新设置间隔
            if (autoRefreshInterval) {
                toggleAutoRefresh();
                toggleAutoRefresh();
            }
        } else {
            // 检查是否是权限问题
            if (result.requires_admin || response.status === 403) {
                alert('需要管理员权限: ' + (result.message || '权限不足'));
                closeDataSourceConfig();
            } else {
                throw new Error(result.message);
            }
        }
    } catch (error) {
        log('保存数据源配置失败: ' + error.message, 'error');
        alert('保存数据源配置失败: ' + error.message);
    }
}

// ==================== 用户管理相关函数（仅管理员） ====================

let currentEditUsername = '';

// 打开用户管理
async function openUserManagement() {
    // #region agent log
    fetch('http://127.0.0.1:7243/ingest/c359bf7a-79f8-4b93-af0b-f5a5dba44447',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:openUserManagement:entry',message:'打开用户管理',data:{},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'5'})}).catch(()=>{});
    // #endregion
    
    if (!checkLogin()) {
        // #region agent log
        fetch('http://127.0.0.1:7243/ingest/c359bf7a-79f8-4b93-af0b-f5a5dba44447',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:openUserManagement:not_logged_in',message:'未登录',data:{},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'5'})}).catch(()=>{});
        // #endregion
        requireLogin();
        return;
    }
    
    // 检查是否为管理员
    if (!currentUser || currentUser.role !== 'admin') {
        // #region agent log
        fetch('http://127.0.0.1:7243/ingest/c359bf7a-79f8-4b93-af0b-f5a5dba44447',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:openUserManagement:not_admin',message:'不是管理员',data:{currentUserRole:currentUser?currentUser.role:'null'},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'5'})}).catch(()=>{});
        // #endregion
        alert('此功能需要管理员权限');
        return;
    }
    
    const modal = document.getElementById('userManagementModal');
    // #region agent log
    fetch('http://127.0.0.1:7243/ingest/c359bf7a-79f8-4b93-af0b-f5a5dba44447',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:openUserManagement:check_modal',message:'检查用户管理模态框',data:{modalExists:!!modal},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'5'})}).catch(()=>{});
    // #endregion
    
    if (modal) {
        modal.classList.add('active');
        await loadUsers();
        // #region agent log
        fetch('http://127.0.0.1:7243/ingest/c359bf7a-79f8-4b93-af0b-f5a5dba44447',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:openUserManagement:success',message:'用户管理模态框已打开',data:{},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'5'})}).catch(()=>{});
        // #endregion
    } else {
        // #region agent log
        fetch('http://127.0.0.1:7243/ingest/c359bf7a-79f8-4b93-af0b-f5a5dba44447',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:openUserManagement:modal_missing',message:'用户管理模态框元素不存在',data:{},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'5'})}).catch(()=>{});
        // #endregion
        console.error('用户管理模态框元素不存在');
        alert('用户管理模态框元素不存在');
    }
}

// 关闭用户管理
function closeUserManagement() {
    document.getElementById('userManagementModal').classList.remove('active');
}

// 加载用户列表
async function loadUsers() {
    try {
        const response = await fetch('/api/users');
        const result = await response.json();
        if (result.success) {
            displayUsers(result.users);
        } else {
            document.getElementById('userManagementBody').innerHTML = 
                '<tr><td colspan="6" class="loading">加载失败: ' + (result.message || '未知错误') + '</td></tr>';
        }
    } catch (error) {
        document.getElementById('userManagementBody').innerHTML = 
            '<tr><td colspan="6" class="loading">加载失败: ' + error.message + '</td></tr>';
    }
}

// 显示用户列表
function displayUsers(users) {
    const tbody = document.getElementById('userManagementBody');
    
    if (users.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="loading">暂无用户</td></tr>';
        return;
    }
    
    tbody.innerHTML = users.map(user => {
        const roleText = user.role === 'admin' ? '管理员' : '普通用户';
        const roleClass = user.role === 'admin' ? 'status-badge' : '';
        const createdDate = user.created_at ? new Date(user.created_at).toLocaleDateString('zh-CN') : '--';
        const lastLoginDate = user.last_login ? new Date(user.last_login).toLocaleDateString('zh-CN') : '--';
        const currentUsername = currentUser ? currentUser.username : '';
        const isCurrentUser = user.username === currentUsername;
        
        return `
            <tr>
                <td style="padding: 10px;">${user.username}</td>
                <td style="padding: 10px;">${user.email || '--'}</td>
                <td style="padding: 10px;"><span class="${roleClass}">${roleText}</span></td>
                <td style="padding: 10px;">${createdDate}</td>
                <td style="padding: 10px;">${lastLoginDate}</td>
                <td style="padding: 10px;">
                    <button class="btn btn-small btn-secondary" onclick="editUser('${user.username}', '${(user.email || '').replace(/'/g, "\\'")}', '${user.role}')" style="margin-right: 5px;">编辑</button>
                    ${!isCurrentUser ? `<button class="btn btn-small btn-danger" onclick="deleteUserConfirm('${user.username}')">删除</button>` : '<span style="color: #999;">当前用户</span>'}
                </td>
            </tr>
        `;
    }).join('');
}

// 编辑用户
function editUser(username, email, role) {
    currentEditUsername = username;
    document.getElementById('editUsername').value = username;
    document.getElementById('editEmail').value = email || '';
    document.getElementById('editRole').value = role || 'user';
    document.getElementById('editPassword').value = '';
    document.getElementById('editUserError').style.display = 'none';
    document.getElementById('editUserModal').classList.add('active');
}

// 关闭编辑用户
function closeEditUser() {
    document.getElementById('editUserModal').classList.remove('active');
    currentEditUsername = '';
}

// 保存用户编辑
async function saveEditUser() {
    const email = document.getElementById('editEmail').value.trim();
    const role = document.getElementById('editRole').value;
    const password = document.getElementById('editPassword').value;
    const errorDiv = document.getElementById('editUserError');
    
    errorDiv.style.display = 'none';
    
    // 验证密码
    if (password && password.length < 6) {
        errorDiv.textContent = '密码至少需要6个字符';
        errorDiv.style.display = 'block';
        return;
    }
    
    try {
        const updateData = {
            email: email || null,
            role: role
        };
        
        if (password) {
            updateData.password = password;
        }
        
        const response = await fetch(`/api/users/${currentEditUsername}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(updateData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            log('用户信息已更新', 'success');
            closeEditUser();
            await loadUsers();
            // 如果更新的是当前用户，重新加载用户信息
            if (currentEditUsername === currentUser.username) {
                await checkAuthStatus();
            }
        } else {
            errorDiv.textContent = result.message || '更新失败';
            errorDiv.style.display = 'block';
        }
    } catch (error) {
        errorDiv.textContent = '更新失败: ' + error.message;
        errorDiv.style.display = 'block';
    }
}

// 删除用户确认
function deleteUserConfirm(username) {
    if (confirm(`确定要删除用户 "${username}" 吗？此操作不可恢复！`)) {
        deleteUser(username);
    }
}

// 删除用户
async function deleteUser(username) {
    try {
        const response = await fetch(`/api/users/${username}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            log('用户已删除', 'success');
            await loadUsers();
        } else {
            alert('删除失败: ' + (result.message || '未知错误'));
        }
    } catch (error) {
        alert('删除失败: ' + error.message);
    }
}

// 切换模拟数据模式
// 异步更新限购信息（不阻塞主流程）
async function updatePurchaseLimitsAsync(fundCodes) {
    if (!fundCodes || fundCodes.length === 0) return;
    
    try {
        // #region agent log
        fetch('http://127.0.0.1:7243/ingest/c359bf7a-79f8-4b93-af0b-f5a5dba44447',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:updatePurchaseLimitsAsync:entry',message:'开始异步获取限购信息',data:{fund_codes_count:fundCodes.length},timestamp:Date.now(),sessionId:'debug-session'})}).catch(()=>{});
        // #endregion
        
        // 分批获取限购信息（每批100只）
        const batchSize = 100;
        for (let i = 0; i < fundCodes.length; i += batchSize) {
            const batch = fundCodes.slice(i, i + batchSize);
            try {
                const response = await fetch('/api/funds/purchase-limits', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ codes: batch })
                });
                const result = await response.json();
                
                if (result.success && result.limits) {
                    // 更新已显示的基金数据
                    if (typeof allFundsData !== 'undefined' && allFundsData.length > 0) {
                        const fundsToUpdate = allFundsData.filter(f => batch.includes(f.fund_code));
                        fundsToUpdate.forEach(fund => {
                            if (result.limits[fund.fund_code]) {
                                fund.purchase_limit = result.limits[fund.fund_code];
                            }
                        });
                        
                        // 重新显示更新后的数据（只更新一次，避免频繁刷新）
                        if (i === 0 || i + batchSize >= fundCodes.length) {
                            displayFunds(allFundsData);
                        }
                    }
                }
            } catch (error) {
                // 单批失败不影响其他批次
                console.error(`批量 ${Math.floor(i / batchSize) + 1} 限购信息获取失败:`, error);
            }
        }
        
        // 最终更新显示
        if (typeof allFundsData !== 'undefined' && allFundsData.length > 0) {
            displayFunds(allFundsData);
        }
        log(`限购信息更新完成`, 'info');
    } catch (error) {
        console.error('异步获取限购信息失败:', error);
        // 不显示错误给用户，因为这是后台操作
    }
}

async function toggleMockMode() {
    const checked = document.getElementById('mockModeToggle').checked;
    
    try {
        const response = await fetch('/api/mode', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ mock: checked })
        });
        
        const result = await response.json();
        
        if (result.success) {
            log(result.message, 'success');
            loadFunds();
        } else {
            throw new Error(result.message);
        }
    } catch (error) {
        log('切换模式失败: ' + error.message, 'error');
        document.getElementById('mockModeToggle').checked = !checked;
    }
}

// 日志功能
function log(message, type = 'info') {
    const logContent = document.getElementById('logContent');
    const time = new Date().toLocaleTimeString('zh-CN');
    const entry = document.createElement('div');
    entry.className = `log-entry ${type}`;
    entry.textContent = `[${time}] ${message}`;
    logContent.appendChild(entry);
    logContent.scrollTop = logContent.scrollHeight;
}

// 清空日志
function clearLog() {
    document.getElementById('logContent').innerHTML = '';
}

// 发现LOF基金
async function discoverFunds() {
    const btn = document.getElementById('discoverBtn');
    const originalText = btn.textContent;
    btn.disabled = true;
    btn.textContent = '发现中...';
    
    try {
        const response = await fetch('/api/funds/discover');
        const result = await response.json();
        
        if (result.success) {
            if (result.funds && Object.keys(result.funds).length > 0) {
                // 更新基金列表
                log(`发现 ${result.count} 只LOF基金`, 'success');
                
                // 重新加载基金数据
                await loadFunds();
                
                alert(`成功发现 ${result.count} 只LOF基金！已更新基金列表。`);
            } else {
                log('未发现新的LOF基金', 'warning');
                alert('未发现新的LOF基金，请稍后再试。');
            }
        } else {
            throw new Error(result.message || '发现基金失败');
        }
    } catch (error) {
        log('发现基金失败: ' + error.message, 'error');
        alert('发现基金失败: ' + error.message);
    } finally {
        btn.disabled = false;
        btn.textContent = originalText;
    }
}

// 加载自选基金列表
async function loadFavoriteFunds() {
    if (!checkLogin()) {
        favoriteFunds = new Set();
        return;
    }
    
    try {
        const response = await fetch('/api/user/favorites');
        const result = await response.json();
        if (result.success && result.favorites) {
            favoriteFunds = new Set(result.favorites);
        } else {
            favoriteFunds = new Set();
        }
    } catch (error) {
        console.error('加载自选基金失败:', error);
        favoriteFunds = new Set();
    }
}

// 保存自选基金列表
async function saveFavoriteFunds() {
    if (!checkLogin()) {
        return;
    }
    
    try {
        const codes = Array.from(favoriteFunds);
        const response = await fetch('/api/user/favorites', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ favorites: codes })
        });
        const result = await response.json();
        if (!result.success) {
            console.error('保存自选基金失败:', result.message);
        }
    } catch (error) {
        console.error('保存自选基金失败:', error);
    }
}

// 检查是否已登录
function checkLogin() {
    return currentUser !== null;
}

// 提示需要登录
function requireLogin() {
    // 直接弹出登录窗口，不显示alert
    openAuthModal();
}

// 切换自选状态
function toggleFavorite(fundCode) {
    if (!checkLogin()) {
        requireLogin();
        return;
    }
    
    if (favoriteFunds.has(fundCode)) {
        favoriteFunds.delete(fundCode);
    } else {
        favoriteFunds.add(fundCode);
    }
    saveFavoriteFunds();
    displayFunds(allFundsData); // 重新显示以更新星标状态
}

// 切换自选筛选
function toggleFavoritesFilter() {
    if (!checkLogin()) {
        requireLogin();
        return;
    }
    
    showFavoritesOnly = !showFavoritesOnly;
    const btn = document.getElementById('filterFavoritesBtn');
    if (showFavoritesOnly) {
        btn.textContent = '显示全部';
        btn.classList.add('active');
    } else {
        btn.textContent = '只看自选';
        btn.classList.remove('active');
    }
    displayFunds(allFundsData); // 重新显示以应用筛选
}

// ==================== 用户认证相关函数 ====================

// 检查登录状态
async function checkAuthStatus() {
    try {
        const response = await fetch('/api/auth/current');
        const result = await response.json();
        
        if (result.success && result.user) {
            currentUser = result.user;
            updateUserUI(true);
            // 登录后加载用户的自选基金
            await loadFavoriteFunds();
            // 登录后重新加载用户设置
            await loadConfig();
            // 重新显示基金列表以更新自选状态
            if (allFundsData && allFundsData.length > 0) {
                displayFunds(allFundsData);
            }
        } else {
            currentUser = null;
            favoriteFunds = new Set(); // 未登录时清空自选
            updateUserUI(false);
            // 停止通知检查
            if (notificationCheckInterval) {
                clearInterval(notificationCheckInterval);
                notificationCheckInterval = null;
            }
        }
    } catch (error) {
        console.error('检查登录状态失败:', error);
        currentUser = null;
        updateUserUI(false);
        // 停止通知检查
        if (notificationCheckInterval) {
            clearInterval(notificationCheckInterval);
            notificationCheckInterval = null;
        }
    }
}

// 更新用户UI显示
function updateUserUI(isLoggedIn) {
    const userInfo = document.getElementById('userInfo');
    const loginBtn = document.getElementById('loginBtn');
    const usernameDisplay = document.getElementById('usernameDisplay');
    
    if (isLoggedIn && currentUser) {
        userInfo.style.display = 'flex';
        loginBtn.style.display = 'none';
        usernameDisplay.textContent = `欢迎, ${currentUser.username}`;
        // 加载未读通知数量
        loadUnreadNotificationCount();
    } else {
        userInfo.style.display = 'none';
        loginBtn.style.display = 'block';
        // 隐藏通知容器
        const notificationContainer = document.getElementById('notificationContainer');
        if (notificationContainer) {
            notificationContainer.style.display = 'none';
        }
    }
    
    // 更新按钮状态（根据登录状态启用/禁用）
    updateFeatureButtons(isLoggedIn);
}

// 更新功能按钮状态
function updateFeatureButtons(isLoggedIn) {
    const filterFavoritesBtn = document.getElementById('filterFavoritesBtn');
    const arbitrageRecordsBtn = document.getElementById('arbitrageRecordsBtn');
    const settingsBtn = document.getElementById('settingsBtn');
    const dataSourceConfigBtn = document.getElementById('dataSourceConfigBtn');
    
    // 不禁用按钮，让用户点击时直接弹出登录窗口
    // 只更新提示信息
    if (filterFavoritesBtn) {
        if (!isLoggedIn) {
            filterFavoritesBtn.title = '需要登录（点击将弹出登录窗口）';
        } else {
            filterFavoritesBtn.title = '';
        }
    }
    
    if (arbitrageRecordsBtn) {
        if (!isLoggedIn) {
            arbitrageRecordsBtn.title = '需要登录（点击将弹出登录窗口）';
        } else {
            arbitrageRecordsBtn.title = '';
        }
    }
    
    if (settingsBtn) {
        if (!isLoggedIn) {
            settingsBtn.title = '需要登录（点击将弹出登录窗口）';
        } else {
            settingsBtn.title = '';
        }
    }
    
    // 数据源配置按钮：只有管理员可见
    if (dataSourceConfigBtn) {
        const isAdmin = isLoggedIn && currentUser && currentUser.role === 'admin';
        if (isAdmin) {
            dataSourceConfigBtn.style.display = 'inline-block';
            dataSourceConfigBtn.title = '';
        } else {
            dataSourceConfigBtn.style.display = 'none';
        }
    }
    
    // 用户管理按钮：只有管理员可见
    const userManagementBtn = document.getElementById('userManagementBtn');
    if (userManagementBtn) {
        const isAdmin = isLoggedIn && currentUser && currentUser.role === 'admin';
        if (isAdmin) {
            userManagementBtn.style.display = 'inline-block';
            userManagementBtn.title = '';
        } else {
            userManagementBtn.style.display = 'none';
        }
    }
    
    // 所有套利记录按钮：只有管理员可见
    const adminArbitrageRecordsBtn = document.getElementById('adminArbitrageRecordsBtn');
    if (adminArbitrageRecordsBtn) {
        const isAdmin = isLoggedIn && currentUser && currentUser.role === 'admin';
        if (isAdmin) {
            adminArbitrageRecordsBtn.style.display = 'inline-block';
            adminArbitrageRecordsBtn.title = '';
        } else {
            adminArbitrageRecordsBtn.style.display = 'none';
        }
    }
}

// 打开认证模态框
function openAuthModal() {
    // #region agent log
    fetch('http://127.0.0.1:7243/ingest/c359bf7a-79f8-4b93-af0b-f5a5dba44447',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:openAuthModal:entry',message:'打开登录模态框',data:{},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'2'})}).catch(()=>{});
    // #endregion
    
    const modal = document.getElementById('authModal');
    // #region agent log
    fetch('http://127.0.0.1:7243/ingest/c359bf7a-79f8-4b93-af0b-f5a5dba44447',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:openAuthModal:check',message:'检查登录模态框元素',data:{modalExists:!!modal},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'2'})}).catch(()=>{});
    // #endregion
    
    if (modal) {
        modal.classList.add('active');
        switchAuthTab('login');
        // #region agent log
        fetch('http://127.0.0.1:7243/ingest/c359bf7a-79f8-4b93-af0b-f5a5dba44447',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:openAuthModal:success',message:'登录模态框已打开',data:{},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'2'})}).catch(()=>{});
        // #endregion
    } else {
        // #region agent log
        fetch('http://127.0.0.1:7243/ingest/c359bf7a-79f8-4b93-af0b-f5a5dba44447',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:openAuthModal:error',message:'登录模态框元素不存在',data:{},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'2'})}).catch(()=>{});
        // #endregion
        console.error('登录模态框元素不存在');
        alert('登录模态框元素不存在');
    }
}

// 关闭认证模态框
function closeAuthModal() {
    const modal = document.getElementById('authModal');
    modal.classList.remove('active');
    // 清空表单
    document.getElementById('loginUsername').value = '';
    document.getElementById('loginPassword').value = '';
    document.getElementById('registerUsername').value = '';
    document.getElementById('registerPassword').value = '';
    document.getElementById('registerPasswordConfirm').value = '';
    document.getElementById('registerEmail').value = '';
    document.getElementById('loginError').style.display = 'none';
    document.getElementById('registerError').style.display = 'none';
}

// 切换登录/注册标签
function switchAuthTab(tab) {
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    const loginTabBtn = document.getElementById('loginTabBtn');
    const registerTabBtn = document.getElementById('registerTabBtn');
    const authModalTitle = document.getElementById('authModalTitle');
    
    if (tab === 'login') {
        loginForm.style.display = 'block';
        registerForm.style.display = 'none';
        loginTabBtn.classList.add('active');
        loginTabBtn.style.borderBottom = '2px solid #007bff';
        loginTabBtn.style.color = '#333';
        registerTabBtn.classList.remove('active');
        registerTabBtn.style.borderBottom = 'none';
        registerTabBtn.style.color = '#666';
        authModalTitle.textContent = '登录';
    } else {
        // 切换到注册标签时加载验证码
        loadCaptcha();
        loginForm.style.display = 'none';
        registerForm.style.display = 'block';
        registerTabBtn.classList.add('active');
        registerTabBtn.style.borderBottom = '2px solid #007bff';
        registerTabBtn.style.color = '#333';
        loginTabBtn.classList.remove('active');
        loginTabBtn.style.borderBottom = 'none';
        loginTabBtn.style.color = '#666';
        authModalTitle.textContent = '注册';
    }
    
    // 清空错误信息
    document.getElementById('loginError').style.display = 'none';
    document.getElementById('registerError').style.display = 'none';
}

// 提交登录
async function submitLogin() {
    // #region agent log
    fetch('http://127.0.0.1:7243/ingest/c359bf7a-79f8-4b93-af0b-f5a5dba44447',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:submitLogin:entry',message:'提交登录开始',data:{},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'3'})}).catch(()=>{});
    // #endregion
    
    const usernameInput = document.getElementById('loginUsername');
    const passwordInput = document.getElementById('loginPassword');
    const errorDiv = document.getElementById('loginError');
    
    // #region agent log
    fetch('http://127.0.0.1:7243/ingest/c359bf7a-79f8-4b93-af0b-f5a5dba44447',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:submitLogin:check_elements',message:'检查登录表单元素',data:{usernameInputExists:!!usernameInput,passwordInputExists:!!passwordInput,errorDivExists:!!errorDiv},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'3'})}).catch(()=>{});
    // #endregion
    
    if (!usernameInput || !passwordInput || !errorDiv) {
        // #region agent log
        fetch('http://127.0.0.1:7243/ingest/c359bf7a-79f8-4b93-af0b-f5a5dba44447',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:submitLogin:missing_elements',message:'登录表单元素缺失',data:{},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'3'})}).catch(()=>{});
        // #endregion
        alert('登录表单元素不存在');
        return;
    }
    
    const username = usernameInput.value.trim();
    const password = passwordInput.value;
    
    if (!username || !password) {
        // #region agent log
        fetch('http://127.0.0.1:7243/ingest/c359bf7a-79f8-4b93-af0b-f5a5dba44447',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:submitLogin:validation_failed',message:'登录验证失败',data:{hasUsername:!!username,hasPassword:!!password},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'3'})}).catch(()=>{});
        // #endregion
        errorDiv.textContent = '请输入用户名和密码';
        errorDiv.style.display = 'block';
        return;
    }
    
    try {
        // #region agent log
        fetch('http://127.0.0.1:7243/ingest/c359bf7a-79f8-4b93-af0b-f5a5dba44447',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:submitLogin:before_fetch',message:'发送登录请求前',data:{username:username,passwordLength:password.length},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'3'})}).catch(()=>{});
        // #endregion
        
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });
        
        const result = await response.json();
        
        if (result.success) {
            currentUser = result.user;
            updateUserUI(true);
            closeAuthModal();
            log('登录成功', 'success');
            // 登录后加载用户的自选基金
            await loadFavoriteFunds();
            // 登录后重新加载用户设置
            await loadConfig();
            // 登录后加载未读通知数量
            await loadUnreadNotificationCount();
            // 重新显示基金列表以更新自选状态
            if (allFundsData && allFundsData.length > 0) {
                displayFunds(allFundsData);
            }
        } else {
            errorDiv.textContent = result.message || '登录失败';
            errorDiv.style.display = 'block';
        }
    } catch (error) {
        errorDiv.textContent = '登录失败: ' + error.message;
        errorDiv.style.display = 'block';
    }
}

// 加载验证码
async function loadCaptcha() {
    try {
        const response = await fetch('/api/auth/captcha');
        const result = await response.json();
        if (result.success) {
            document.getElementById('captchaQuestion').textContent = result.question;
        } else {
            console.error('加载验证码失败:', result.message);
        }
    } catch (error) {
        console.error('加载验证码失败:', error);
    }
}

// 提交注册
async function submitRegister() {
    // #region agent log
    fetch('http://127.0.0.1:7243/ingest/c359bf7a-79f8-4b93-af0b-f5a5dba44447',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:submitRegister:entry',message:'开始注册',data:{},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'3'})}).catch(()=>{});
    // #endregion
    
    const username = document.getElementById('registerUsername').value.trim();
    const password = document.getElementById('registerPassword').value;
    const passwordConfirm = document.getElementById('registerPasswordConfirm').value;
    const email = document.getElementById('registerEmail').value.trim();
    const captchaAnswer = document.getElementById('registerCaptcha').value.trim();
    const errorDiv = document.getElementById('registerError');
    
    // #region agent log
    fetch('http://127.0.0.1:7243/ingest/c359bf7a-79f8-4b93-af0b-f5a5dba44447',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:submitRegister:input',message:'获取输入值',data:{username:username,passwordLength:password.length,passwordConfirmLength:passwordConfirm.length,email:email},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'1,2'})}).catch(()=>{});
    // #endregion
    
    // 验证
    if (!username || !password || !passwordConfirm) {
        // #region agent log
        fetch('http://127.0.0.1:7243/ingest/c359bf7a-79f8-4b93-af0b-f5a5dba44447',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:submitRegister:validation_failed',message:'必填项验证失败',data:{hasUsername:!!username,hasPassword:!!password,hasPasswordConfirm:!!passwordConfirm},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'2'})}).catch(()=>{});
        // #endregion
        errorDiv.textContent = '请填写所有必填项';
        errorDiv.style.display = 'block';
        return;
    }
    
    if (password !== passwordConfirm) {
        // #region agent log
        fetch('http://127.0.0.1:7243/ingest/c359bf7a-79f8-4b93-af0b-f5a5dba44447',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:submitRegister:password_mismatch',message:'密码不一致',data:{},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'2'})}).catch(()=>{});
        // #endregion
        errorDiv.textContent = '两次输入的密码不一致';
        errorDiv.style.display = 'block';
        return;
    }
    
    if (!captchaAnswer) {
        errorDiv.textContent = '请输入验证码';
        errorDiv.style.display = 'block';
        return;
    }
    
    try {
        // #region agent log
        fetch('http://127.0.0.1:7243/ingest/c359bf7a-79f8-4b93-af0b-f5a5dba44447',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:submitRegister:before_fetch',message:'发送注册请求前',data:{username:username,passwordLength:password.length},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'3'})}).catch(()=>{});
        // #endregion
        
        const response = await fetch('/api/auth/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                username, 
                password, 
                email: email || null,
                captcha_answer: captchaAnswer
            })
        });
        
        // #region agent log
        fetch('http://127.0.0.1:7243/ingest/c359bf7a-79f8-4b93-af0b-f5a5dba44447',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:submitRegister:response_received',message:'收到响应',data:{status:response.status,statusText:response.statusText,ok:response.ok},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'3,4'})}).catch(()=>{});
        // #endregion
        
        const result = await response.json();
        
        // #region agent log
        fetch('http://127.0.0.1:7243/ingest/c359bf7a-79f8-4b93-af0b-f5a5dba44447',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:submitRegister:result_parsed',message:'解析响应结果',data:{success:result.success,message:result.message},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'4,5'})}).catch(()=>{});
        // #endregion
        
        if (result.success) {
            // #region agent log
            fetch('http://127.0.0.1:7243/ingest/c359bf7a-79f8-4b93-af0b-f5a5dba44447',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:submitRegister:success',message:'注册成功',data:{username:username},timestamp:Date.now(),sessionId:'debug-session'})}).catch(()=>{});
            // #endregion
            log('注册成功，请登录', 'success');
            // 切换到登录标签
            switchAuthTab('login');
            document.getElementById('loginUsername').value = username;
        } else {
            // #region agent log
            fetch('http://127.0.0.1:7243/ingest/c359bf7a-79f8-4b93-af0b-f5a5dba44447',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:submitRegister:failed',message:'注册失败',data:{message:result.message,username:username},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'1,2,5'})}).catch(()=>{});
            // #endregion
            errorDiv.textContent = result.message || '注册失败';
            errorDiv.style.display = 'block';
        }
    } catch (error) {
        // #region agent log
        fetch('http://127.0.0.1:7243/ingest/c359bf7a-79f8-4b93-af0b-f5a5dba44447',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:submitRegister:exception',message:'注册异常',data:{error:error.message,stack:error.stack},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'3,4'})}).catch(()=>{});
        // #endregion
        errorDiv.textContent = '注册失败: ' + error.message;
        errorDiv.style.display = 'block';
    }
}

// 登出
async function logout() {
    try {
        const response = await fetch('/api/auth/logout', {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.success) {
            currentUser = null;
            updateUserUI(false);
            // 停止通知检查
            if (notificationCheckInterval) {
                clearInterval(notificationCheckInterval);
                notificationCheckInterval = null;
            }
            log('已登出', 'info');
        } else {
            alert('登出失败: ' + result.message);
        }
    } catch (error) {
        alert('登出失败: ' + error.message);
    }
}

// ==================== 管理员套利记录查看功能 ====================

// 打开管理员套利记录查看
async function openAdminArbitrageRecords() {
    // #region agent log
    fetch('http://127.0.0.1:7243/ingest/c359bf7a-79f8-4b93-af0b-f5a5dba44447',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:openAdminArbitrageRecords:entry',message:'打开管理员套利记录查看',data:{},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'2'})}).catch(()=>{});
    // #endregion
    
    if (!checkLogin()) {
        // #region agent log
        fetch('http://127.0.0.1:7243/ingest/c359bf7a-79f8-4b93-af0b-f5a5dba44447',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:openAdminArbitrageRecords:not_logged_in',message:'未登录',data:{},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'2'})}).catch(()=>{});
        // #endregion
        requireLogin();
        return;
    }
    
    // 检查是否为管理员
    if (!currentUser || currentUser.role !== 'admin') {
        // #region agent log
        fetch('http://127.0.0.1:7243/ingest/c359bf7a-79f8-4b93-af0b-f5a5dba44447',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:openAdminArbitrageRecords:not_admin',message:'不是管理员',data:{currentUserRole:currentUser?currentUser.role:'null'},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'2'})}).catch(()=>{});
        // #endregion
        alert('此功能需要管理员权限');
        return;
    }
    
    const modal = document.getElementById('adminArbitrageRecordsModal');
    // #region agent log
    fetch('http://127.0.0.1:7243/ingest/c359bf7a-79f8-4b93-af0b-f5a5dba44447',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:openAdminArbitrageRecords:check_modal',message:'检查管理员套利记录模态框',data:{modalExists:!!modal},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'2'})}).catch(()=>{});
    // #endregion
    
    if (!modal) {
        // #region agent log
        fetch('http://127.0.0.1:7243/ingest/c359bf7a-79f8-4b93-af0b-f5a5dba44447',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:openAdminArbitrageRecords:modal_missing',message:'管理员套利记录模态框元素不存在',data:{},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'2'})}).catch(()=>{});
        // #endregion
        console.error('管理员套利记录模态框元素不存在');
        alert('管理员套利记录模态框元素不存在');
        return;
    }
    
    try {
        modal.classList.add('active');
        // #region agent log
        fetch('http://127.0.0.1:7243/ingest/c359bf7a-79f8-4b93-af0b-f5a5dba44447',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:openAdminArbitrageRecords:before_load',message:'开始加载数据',data:{},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'2'})}).catch(()=>{});
        // #endregion
        await loadAdminArbitrageStatistics();
        await loadAdminArbitrageRecords();
        // #region agent log
        fetch('http://127.0.0.1:7243/ingest/c359bf7a-79f8-4b93-af0b-f5a5dba44447',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:openAdminArbitrageRecords:success',message:'管理员套利记录模态框已打开',data:{},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'2'})}).catch(()=>{});
        // #endregion
    } catch (error) {
        // #region agent log
        fetch('http://127.0.0.1:7243/ingest/c359bf7a-79f8-4b93-af0b-f5a5dba44447',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:openAdminArbitrageRecords:error',message:'打开管理员套利记录时出错',data:{error:error.message,stack:error.stack},timestamp:Date.now(),sessionId:'debug-session',hypothesisId:'2'})}).catch(()=>{});
        // #endregion
        console.error('打开管理员套利记录失败:', error);
        alert('打开管理员套利记录失败: ' + error.message);
    }
}

// 关闭管理员套利记录查看
function closeAdminArbitrageRecords() {
    document.getElementById('adminArbitrageRecordsModal').classList.remove('active');
}

// 加载管理员套利记录统计
async function loadAdminArbitrageStatistics() {
    try {
        const response = await fetch('/api/admin/arbitrage/statistics');
        const result = await response.json();
        if (result.success) {
            displayAdminArbitrageStatistics(result.statistics);
        } else {
            document.getElementById('adminArbitrageStatsContent').innerHTML = 
                '<div style="color: red;">加载统计信息失败: ' + (result.message || '未知错误') + '</div>';
        }
    } catch (error) {
        document.getElementById('adminArbitrageStatsContent').innerHTML = 
            '<div style="color: red;">加载统计信息失败: ' + error.message + '</div>';
    }
}

// 显示管理员套利记录统计
function displayAdminArbitrageStatistics(stats) {
    const statsContent = document.getElementById('adminArbitrageStatsContent');
    
    let html = `
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 15px;">
            <div>
                <strong>总记录数:</strong> ${stats.total_records}
            </div>
            <div>
                <strong>已完成:</strong> ${stats.total_completed}
            </div>
            <div>
                <strong>进行中:</strong> ${stats.total_in_progress}
            </div>
            <div>
                <strong>已取消:</strong> ${stats.total_cancelled}
            </div>
            <div>
                <strong>总盈亏:</strong> <span style="color: ${stats.total_profit >= 0 ? '#28a745' : '#dc3545'}">${stats.total_profit.toFixed(2)}</span>
            </div>
            <div>
                <strong>总金额:</strong> ${stats.total_amount.toFixed(2)}
            </div>
            <div>
                <strong>整体盈亏率:</strong> <span style="color: ${stats.overall_profit_rate >= 0 ? '#28a745' : '#dc3545'}">${stats.overall_profit_rate.toFixed(2)}%</span>
            </div>
        </div>
    `;
    
    if (Object.keys(stats.user_statistics).length > 0) {
        html += '<h4 style="margin-top: 15px; margin-bottom: 10px;">按用户统计:</h4>';
        html += '<div style="overflow-x: auto;"><table style="width: 100%; border-collapse: collapse; font-size: 12px;">';
        html += '<thead><tr style="background: #e9ecef;"><th style="padding: 8px; text-align: left;">用户名</th><th style="padding: 8px; text-align: right;">记录数</th><th style="padding: 8px; text-align: right;">已完成</th><th style="padding: 8px; text-align: right;">总盈亏</th><th style="padding: 8px; text-align: right;">盈亏率</th></tr></thead><tbody>';
        
        for (const [username, userStats] of Object.entries(stats.user_statistics)) {
            html += `
                <tr>
                    <td style="padding: 8px;">${username}</td>
                    <td style="padding: 8px; text-align: right;">${userStats.total_records}</td>
                    <td style="padding: 8px; text-align: right;">${userStats.completed}</td>
                    <td style="padding: 8px; text-align: right; color: ${userStats.total_profit >= 0 ? '#28a745' : '#dc3545'}">${userStats.total_profit.toFixed(2)}</td>
                    <td style="padding: 8px; text-align: right; color: ${userStats.profit_rate >= 0 ? '#28a745' : '#dc3545'}">${userStats.profit_rate.toFixed(2)}%</td>
                </tr>
            `;
        }
        
        html += '</tbody></table></div>';
    }
    
    statsContent.innerHTML = html;
}

// 加载管理员套利记录
async function loadAdminArbitrageRecords() {
    try {
        const statusFilter = document.getElementById('adminArbitrageStatusFilter').value;
        const fundCodeFilter = document.getElementById('adminArbitrageFundCodeFilter').value.trim();
        
        let url = '/api/admin/arbitrage/records?';
        if (statusFilter) url += `status=${statusFilter}&`;
        if (fundCodeFilter) url += `fund_code=${encodeURIComponent(fundCodeFilter)}&`;
        
        const response = await fetch(url);
        const result = await response.json();
        if (result.success) {
            displayAdminArbitrageRecords(result.records);
        } else {
            document.getElementById('adminArbitrageRecordsBody').innerHTML = 
                '<tr><td colspan="10" class="loading">加载失败: ' + (result.message || '未知错误') + '</td></tr>';
        }
    } catch (error) {
        document.getElementById('adminArbitrageRecordsBody').innerHTML = 
            '<tr><td colspan="10" class="loading">加载失败: ' + error.message + '</td></tr>';
    }
}

// 显示管理员套利记录
function displayAdminArbitrageRecords(records) {
    const tbody = document.getElementById('adminArbitrageRecordsBody');
    
    if (records.length === 0) {
        tbody.innerHTML = '<tr><td colspan="10" class="loading">暂无记录</td></tr>';
        return;
    }
    
    tbody.innerHTML = records.map(record => {
        const arbitrageTypeText = record.arbitrage_type === 'premium' ? '溢价套利' : '折价套利';
        const statusText = {
            'completed': '已完成',
            'in_progress': '进行中',
            'cancelled': '已取消',
            'pending': '待执行'
        }[record.status] || record.status;
        const statusClass = {
            'completed': 'status-badge',
            'in_progress': '',
            'cancelled': '',
            'pending': ''
        }[record.status] || '';
        
        const initialAmount = record.initial_operation?.amount || 0;
        const finalAmount = record.final_operation?.amount || null;
        const profit = record.profit !== null && record.profit !== undefined ? record.profit : null;
        const profitRate = record.profit_rate !== null && record.profit_rate !== undefined ? record.profit_rate : null;
        
        const createdDate = record.created_at ? new Date(record.created_at).toLocaleString('zh-CN') : '--';
        
        return `
            <tr>
                <td style="padding: 8px;">${record.username || '--'}</td>
                <td style="padding: 8px;">${record.fund_code || '--'}</td>
                <td style="padding: 8px;">${record.fund_name || '--'}</td>
                <td style="padding: 8px;">${arbitrageTypeText}</td>
                <td style="padding: 8px;"><span class="${statusClass}">${statusText}</span></td>
                <td style="padding: 8px; text-align: right;">${initialAmount.toFixed(2)}</td>
                <td style="padding: 8px; text-align: right;">${finalAmount !== null ? finalAmount.toFixed(2) : '--'}</td>
                <td style="padding: 8px; text-align: right; color: ${profit !== null ? (profit >= 0 ? '#28a745' : '#dc3545') : '#666'}">${profit !== null ? profit.toFixed(2) : '--'}</td>
                <td style="padding: 8px; text-align: right; color: ${profitRate !== null ? (profitRate >= 0 ? '#28a745' : '#dc3545') : '#666'}">${profitRate !== null ? profitRate.toFixed(2) + '%' : '--'}</td>
                <td style="padding: 8px;">${createdDate}</td>
            </tr>
        `;
    }).join('');
}

// 应用筛选
function applyAdminArbitrageFilter() {
    loadAdminArbitrageRecords();
}

// ==================== 通知相关功能 ====================

// 打开通知列表
async function openNotifications() {
    if (!checkLogin()) {
        requireLogin();
        return;
    }
    
    document.getElementById('notificationModal').classList.add('active');
    await loadNotifications();
}

// 关闭通知列表
function closeNotifications() {
    document.getElementById('notificationModal').classList.remove('active');
}

// 加载通知列表
async function loadNotifications() {
    try {
        const response = await fetch('/api/notifications');
        const result = await response.json();
        if (result.success) {
            displayNotifications(result.notifications);
        } else {
            document.getElementById('notificationsList').innerHTML = 
                '<div style="color: red;">加载失败: ' + (result.message || '未知错误') + '</div>';
        }
    } catch (error) {
        document.getElementById('notificationsList').innerHTML = 
            '<div style="color: red;">加载失败: ' + error.message + '</div>';
    }
}

// 显示通知列表
function displayNotifications(notifications) {
    const container = document.getElementById('notificationsList');
    
    if (notifications.length === 0) {
        container.innerHTML = '<div class="loading">暂无通知</div>';
        return;
    }
    
    container.innerHTML = notifications.map(notification => {
        const isRead = notification.read;
        const readClass = isRead ? 'style="opacity: 0.6;"' : 'style="font-weight: bold;"';
        const typeIcon = {
            'arbitrage_opportunity': '💰',
            'arbitrage_completed': '✅',
            'arbitrage_sell': '📈',
            'system': '🔔',
            'user': '👤'
        }[notification.type] || '📬';
        
        const createdDate = notification.created_at ? 
            new Date(notification.created_at).toLocaleString('zh-CN') : '--';
        
        return `
            <div class="notification-item" ${readClass} style="padding: 15px; border-bottom: 1px solid #eee; cursor: pointer;" 
                 onclick="handleNotificationClick('${notification.id}', ${!isRead})">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div style="flex: 1;">
                        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 5px;">
                            <span style="font-size: 18px;">${typeIcon}</span>
                            <strong>${notification.title}</strong>
                            ${!isRead ? '<span style="background: #007bff; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px; margin-left: 5px;">未读</span>' : ''}
                        </div>
                        <div style="color: #666; margin-left: 26px; margin-bottom: 5px;">${notification.content}</div>
                        <div style="color: #999; font-size: 12px; margin-left: 26px;">${createdDate}</div>
                    </div>
                    <button class="btn btn-small btn-secondary" onclick="event.stopPropagation(); deleteNotification('${notification.id}')" style="margin-left: 10px;">删除</button>
                </div>
            </div>
        `;
    }).join('');
}

// 处理通知点击
async function handleNotificationClick(notificationId, isUnread) {
    if (isUnread) {
        await markNotificationRead(notificationId);
    }
    // 可以在这里添加跳转到相关页面的逻辑
}

// 标记通知为已读
async function markNotificationRead(notificationId) {
    try {
        const response = await fetch(`/api/notifications/${notificationId}/read`, {
            method: 'POST'
        });
        const result = await response.json();
        if (result.success) {
            await loadNotifications();
            await loadUnreadNotificationCount();
        }
    } catch (error) {
        console.error('标记通知已读失败:', error);
    }
}

// 删除通知
async function deleteNotification(notificationId) {
    if (!confirm('确定要删除这条通知吗？')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/notifications/${notificationId}`, {
            method: 'DELETE'
        });
        const result = await response.json();
        if (result.success) {
            await loadNotifications();
            await loadUnreadNotificationCount();
        } else {
            alert('删除失败: ' + (result.message || '未知错误'));
        }
    } catch (error) {
        alert('删除失败: ' + error.message);
    }
}

// 标记所有通知为已读
async function markAllNotificationsRead() {
    try {
        const response = await fetch('/api/notifications/read-all', {
            method: 'POST'
        });
        const result = await response.json();
        if (result.success) {
            await loadNotifications();
            await loadUnreadNotificationCount();
        } else {
            alert('操作失败: ' + (result.message || '未知错误'));
        }
    } catch (error) {
        alert('操作失败: ' + error.message);
    }
}

// 删除所有已读通知
async function deleteAllReadNotifications() {
    if (!confirm('确定要删除所有已读通知吗？')) {
        return;
    }
    
    try {
        const response = await fetch('/api/notifications/delete-read', {
            method: 'POST'
        });
        const result = await response.json();
        if (result.success) {
            await loadNotifications();
            await loadUnreadNotificationCount();
        } else {
            alert('操作失败: ' + (result.message || '未知错误'));
        }
    } catch (error) {
        alert('操作失败: ' + error.message);
    }
}

// 加载未读通知数量
async function loadUnreadNotificationCount() {
    if (!checkLogin()) {
        const notificationContainer = document.getElementById('notificationContainer');
        if (notificationContainer) {
            notificationContainer.style.display = 'none';
        }
        return;
    }
    
    try {
        const response = await fetch('/api/notifications/unread-count');
        const result = await response.json();
        if (result.success) {
            updateNotificationBadge(result.count);
        }
    } catch (error) {
        console.error('加载未读通知数量失败:', error);
    }
}

// 更新通知徽章
function updateNotificationBadge(count) {
    const notificationContainer = document.getElementById('notificationContainer');
    const notificationBadge = document.getElementById('notificationBadge');
    
    if (notificationContainer) {
        notificationContainer.style.display = 'inline-block';
    }
    
    if (notificationBadge) {
        if (count > 0) {
            notificationBadge.textContent = count > 99 ? '99+' : count;
            notificationBadge.style.display = 'block';
        } else {
            notificationBadge.style.display = 'none';
        }
    }
}

// 开始定期检查通知
function startNotificationCheck() {
    // 每30秒检查一次未读通知数量
    if (notificationCheckInterval) {
        clearInterval(notificationCheckInterval);
    }
    notificationCheckInterval = setInterval(() => {
        if (checkLogin()) {
            loadUnreadNotificationCount();
        }
    }, 30000); // 30秒
}

// 点击模态框外部关闭
window.addEventListener('click', function(event) {
    const authModal = document.getElementById('authModal');
    if (event.target === authModal) {
        closeAuthModal();
    }
});
