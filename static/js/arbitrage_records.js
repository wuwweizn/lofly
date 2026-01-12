// 套利记录相关功能
let currentRecordFundCode = '';
let currentRecordFundName = '';
let currentRecordArbitrageType = '';
let currentRecordId = '';
let tradeFees = null; // 交易费率配置

// 加载交易费率配置
async function loadTradeFees() {
    if (tradeFees) return tradeFees;
    
    try {
        const response = await fetch('/api/config');
        const result = await response.json();
        if (result.success && result.data.trade_fees) {
            tradeFees = result.data.trade_fees;
            return tradeFees;
        }
    } catch (error) {
        console.error('加载费率配置失败:', error);
    }
    
    // 默认费率
    tradeFees = {
        subscribe_fee: 0.0015,  // 申购费率 0.15%
        buy_commission: 0.0003,  // 买入佣金 0.03%
        sell_commission: 0.0003, // 卖出佣金 0.03%
        redeem_fee: 0.0015,      // 赎回费率 0.15%
        stamp_tax: 0.001         // 印花税 0.1%
    };
    return tradeFees;
}

// 计算份额（根据金额和价格）
function calculateShares(amount, price, arbitrageType) {
    if (!amount || !price || amount <= 0 || price <= 0) {
        return 0;
    }
    
    if (!tradeFees) {
        loadTradeFees();
        // 如果费率还没加载，使用默认值
        const defaultFees = {
            subscribe_fee: 0.0015,
            buy_commission: 0.0003
        };
        if (arbitrageType === 'premium') {
            // 溢价套利：场外申购，份额 = 金额 * (1 - 申购费率) / 净值
            return amount * (1 - defaultFees.subscribe_fee) / price;
        } else {
            // 折价套利：场内买入，份额 = 金额 * (1 - 买入佣金) / 价格
            return amount * (1 - defaultFees.buy_commission) / price;
        }
    }
    
    if (arbitrageType === 'premium') {
        // 溢价套利：场外申购，份额 = 金额 * (1 - 申购费率) / 净值
        return amount * (1 - tradeFees.subscribe_fee) / price;
    } else {
        // 折价套利：场内买入，份额 = 金额 * (1 - 买入佣金) / 价格
        return amount * (1 - tradeFees.buy_commission) / price;
    }
}

// 打开记录套利模态框
async function openRecordArbitrageModal(fundCode, fundName, arbitrageType, price, nav) {
    // 检查登录状态（currentUser在app.js中定义）
    if (typeof currentUser === 'undefined' || currentUser === null) {
        // 直接弹出登录窗口
        if (typeof openAuthModal === 'function') {
            openAuthModal();
        } else {
            alert('此功能需要登录后才能使用，请先登录。');
        }
        return;
    }
    
    currentRecordFundCode = fundCode;
    currentRecordFundName = fundName;
    currentRecordArbitrageType = arbitrageType === '溢价套利' ? 'premium' : 'discount';
    
    // 加载费率配置
    await loadTradeFees();
    
    document.getElementById('recordFundCode').value = fundCode;
    document.getElementById('recordFundName').value = fundName;
    document.getElementById('recordArbitrageType').value = arbitrageType;
    
    const initialPrice = arbitrageType === '溢价套利' ? nav : price;
    document.getElementById('recordInitialPrice').value = initialPrice.toFixed(4);
    
    // 更新价格标签
    const priceLabel = document.getElementById('recordPriceLabel');
    if (priceLabel) {
        priceLabel.textContent = arbitrageType === '溢价套利' ? '净值' : '价格';
    }
    
    const initialOperation = arbitrageType === '溢价套利' ? '场外申购（按净值）' : '场内买入（按价格）';
    document.getElementById('recordInitialOperation').textContent = initialOperation;
    
    // 设置默认日期为今天
    const today = new Date().toISOString().split('T')[0];
    const dateInput = document.getElementById('recordInitialDate');
    dateInput.value = today;
    
    // 清空其他字段
    document.getElementById('recordInitialShares').value = '';
    document.getElementById('recordInitialAmount').value = '';
    hidePurchaseLimitHint();
    
    // 添加金额输入事件监听，自动计算份额
    const amountInput = document.getElementById('recordInitialAmount');
    const priceInput = document.getElementById('recordInitialPrice');
    const sharesInput = document.getElementById('recordInitialShares');
    
    // 移除旧的事件监听器（如果存在）
    const newAmountInput = amountInput.cloneNode(true);
    amountInput.parentNode.replaceChild(newAmountInput, amountInput);
    const newPriceInput = priceInput.cloneNode(true);
    priceInput.parentNode.replaceChild(newPriceInput, priceInput);
    const newDateInput = dateInput.cloneNode(true);
    dateInput.parentNode.replaceChild(newDateInput, dateInput);
    
    // 添加新的事件监听器
    let checkLimitTimeout = null;
    newAmountInput.addEventListener('input', function() {
        const amount = parseFloat(this.value) || 0;
        const price = parseFloat(document.getElementById('recordInitialPrice').value) || 0;
        if (amount > 0 && price > 0) {
            const shares = calculateShares(amount, price, currentRecordArbitrageType);
            document.getElementById('recordInitialShares').value = shares.toFixed(4);
        } else {
            document.getElementById('recordInitialShares').value = '';
        }
        
        // 只对溢价套利（申购）进行限购验证
        if (currentRecordArbitrageType === 'premium' && amount > 0) {
            // 防抖：延迟500ms后检查，避免频繁请求
            if (checkLimitTimeout) {
                clearTimeout(checkLimitTimeout);
            }
            checkLimitTimeout = setTimeout(() => {
                checkPurchaseLimit(currentRecordFundCode, amount);
            }, 500);
        } else {
            // 非溢价套利，隐藏提示
            hidePurchaseLimitHint();
        }
    });
    
    newPriceInput.addEventListener('input', function() {
        const amount = parseFloat(document.getElementById('recordInitialAmount').value) || 0;
        const price = parseFloat(this.value) || 0;
        if (amount > 0 && price > 0) {
            const shares = calculateShares(amount, price, currentRecordArbitrageType);
            document.getElementById('recordInitialShares').value = shares.toFixed(4);
        } else {
            document.getElementById('recordInitialShares').value = '';
        }
    });
    
    // 日期变化时，如果是溢价套利且有金额，重新检查限购
    newDateInput.addEventListener('change', function() {
        const amount = parseFloat(document.getElementById('recordInitialAmount').value) || 0;
        if (currentRecordArbitrageType === 'premium' && amount > 0) {
            checkPurchaseLimit(currentRecordFundCode, amount);
        }
    });
    
    document.getElementById('recordArbitrageModal').classList.add('active');
}

// 关闭记录套利模态框
function closeRecordArbitrageModal() {
    document.getElementById('recordArbitrageModal').classList.remove('active');
    hidePurchaseLimitHint();
}

// 检查申购限购
async function checkPurchaseLimit(fundCode, amount) {
    // #region agent log
    fetch('http://127.0.0.1:7243/ingest/c359bf7a-79f8-4b93-af0b-f5a5dba44447',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'arbitrage_records.js:checkPurchaseLimit:entry',message:'开始检查申购限购',data:{fundCode,amount},timestamp:Date.now(),sessionId:'debug-session'})}).catch(()=>{});
    // #endregion
    
    const hintElement = document.getElementById('purchaseLimitHint');
    if (!hintElement) return;
    
    // 获取日期
    const dateInput = document.getElementById('recordInitialDate');
    const date = dateInput ? dateInput.value : null;
    
    try {
        const response = await fetch('/api/arbitrage/check-purchase-limit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                fund_code: fundCode,
                amount: amount,
                date: date
            })
        });
        
        const result = await response.json();
        
        // #region agent log
        fetch('http://127.0.0.1:7243/ingest/c359bf7a-79f8-4b93-af0b-f5a5dba44447',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'arbitrage_records.js:checkPurchaseLimit:result',message:'检查限购结果',data:{success:result.success,is_valid:result.is_valid,message:result.message},timestamp:Date.now(),sessionId:'debug-session'})}).catch(()=>{});
        // #endregion
        
        if (result.success) {
            if (result.is_valid) {
                // 金额有效，显示提示信息（绿色）
                if (result.message) {
                    showPurchaseLimitHint(result.message, 'success');
                } else {
                    hidePurchaseLimitHint();
                }
            } else {
                // 金额无效，显示错误信息（红色）
                showPurchaseLimitHint(result.message, 'error');
            }
        } else {
            // API调用失败，隐藏提示
            hidePurchaseLimitHint();
        }
    } catch (error) {
        // #region agent log
        fetch('http://127.0.0.1:7243/ingest/c359bf7a-79f8-4b93-af0b-f5a5dba44447',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'arbitrage_records.js:checkPurchaseLimit:error',message:'检查限购失败',data:{error:error.message},timestamp:Date.now(),sessionId:'debug-session'})}).catch(()=>{});
        // #endregion
        console.error('检查限购失败:', error);
        hidePurchaseLimitHint();
    }
}

// 显示限购提示
function showPurchaseLimitHint(message, type) {
    const hintElement = document.getElementById('purchaseLimitHint');
    if (!hintElement) return;
    
    hintElement.textContent = message;
    hintElement.style.display = 'block';
    
    if (type === 'error') {
        hintElement.style.backgroundColor = '#ffebee';
        hintElement.style.color = '#c62828';
        hintElement.style.border = '1px solid #ef5350';
    } else {
        hintElement.style.backgroundColor = '#e8f5e9';
        hintElement.style.color = '#2e7d32';
        hintElement.style.border = '1px solid #66bb6a';
    }
}

// 隐藏限购提示
function hidePurchaseLimitHint() {
    const hintElement = document.getElementById('purchaseLimitHint');
    if (hintElement) {
        hintElement.style.display = 'none';
        hintElement.textContent = '';
    }
}

// 保存套利记录
async function saveArbitrageRecord() {
    try {
        const initialPrice = parseFloat(document.getElementById('recordInitialPrice').value);
        const initialAmount = parseFloat(document.getElementById('recordInitialAmount').value);
        const initialDate = document.getElementById('recordInitialDate').value;
        
        if (!initialPrice || !initialAmount || !initialDate) {
            alert('请填写完整信息（价格、金额、日期）');
            return;
        }
        
        // 如果是溢价套利，再次检查限购（防止绕过前端验证）
        if (currentRecordArbitrageType === 'premium') {
            try {
                const response = await fetch('/api/arbitrage/check-purchase-limit', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        fund_code: currentRecordFundCode,
                        amount: initialAmount,
                        date: initialDate
                    })
                });
                
                const result = await response.json();
                if (result.success && !result.is_valid) {
                    alert(result.message);
                    return;
                }
            } catch (error) {
                console.error('检查限购失败:', error);
                // 如果检查失败，仍然允许提交（由后端验证）
            }
        }
        
        // 自动计算份额
        const initialShares = calculateShares(initialAmount, initialPrice, currentRecordArbitrageType);
        
        if (initialShares <= 0) {
            alert('计算份额失败，请检查金额和价格是否正确');
            return;
        }
        
        const response = await fetch('/api/arbitrage/records', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                fund_code: currentRecordFundCode,
                fund_name: currentRecordFundName,
                arbitrage_type: currentRecordArbitrageType,
                initial_price: initialPrice,
                initial_shares: initialShares,
                initial_amount: initialAmount,
                initial_date: initialDate
            })
        });
        
        const result = await response.json();
        if (result.success) {
            alert('套利记录创建成功！');
            closeRecordArbitrageModal();
            if (document.getElementById('arbitrageRecordsModal').classList.contains('active')) {
                loadArbitrageRecords();
            }
        } else {
            // 检查是否是登录问题
            if (result.requires_login || response.status === 401) {
                alert('请先登录: ' + (result.message || '未登录'));
                closeRecordArbitrageModal();
                if (typeof openAuthModal === 'function') {
                    openAuthModal();
            }
        } else {
            alert('创建失败: ' + result.message);
            }
        }
    } catch (error) {
        alert('创建失败: ' + error.message);
    }
}

// 打开套利记录管理界面
async function openArbitrageRecords() {
    // 检查登录状态（currentUser在app.js中定义）
    if (typeof currentUser === 'undefined' || currentUser === null) {
        // 直接弹出登录窗口
        if (typeof openAuthModal === 'function') {
            openAuthModal();
        } else {
            alert('此功能需要登录后才能使用，请先登录。');
        }
        return;
    }
    document.getElementById('arbitrageRecordsModal').classList.add('active');
    await loadArbitrageRecords();
    await loadArbitrageStatistics();
}

// 关闭套利记录管理界面
function closeArbitrageRecords() {
    document.getElementById('arbitrageRecordsModal').classList.remove('active');
}

// 加载套利记录
async function loadArbitrageRecords(status = null) {
    try {
        let url = '/api/arbitrage/records';
        if (status) {
            url += `?status=${status}`;
        }
        
        const response = await fetch(url);
        const result = await response.json();
        
        if (result.success) {
            displayArbitrageRecords(result.records);
        } else {
            // 检查是否是登录问题
            if (result.requires_login || response.status === 401) {
                document.getElementById('arbitrageRecordsBody').innerHTML = 
                    `<tr><td colspan="13" class="loading">请先登录: ${result.message || '未登录'}</td></tr>`;
        } else {
            document.getElementById('arbitrageRecordsBody').innerHTML = 
                `<tr><td colspan="13" class="loading">加载失败: ${result.message}</td></tr>`;
            }
        }
    } catch (error) {
        document.getElementById('arbitrageRecordsBody').innerHTML = 
            `<tr><td colspan="13" class="loading">加载失败: ${error.message}</td></tr>`;
    }
}

// 显示套利记录
function displayArbitrageRecords(records) {
    const tbody = document.getElementById('arbitrageRecordsBody');
    
    if (records.length === 0) {
        tbody.innerHTML = '<tr><td colspan="13" class="loading">暂无记录</td></tr>';
        return;
    }
    
    tbody.innerHTML = records.map(record => {
        const initial = record.initial_operation;
        const final = record.final_operation;
        const status = record.status;
        const profit = record.profit;
        const profitRate = record.profit_rate;
        
        let statusBadge = '';
        let statusClass = '';
        if (status === 'completed') {
            statusBadge = '已完成';
            statusClass = 'status-opportunity';
        } else if (status === 'in_progress') {
            statusBadge = '进行中';
            statusClass = 'status-none';
        } else if (status === 'cancelled') {
            statusBadge = '已取消';
            statusClass = '';
        }
        
        const profitColor = profit !== null && profit > 0 ? '#4CAF50' : (profit !== null && profit < 0 ? '#f44336' : '#666');
        const profitRateColor = profitRate !== null && profitRate > 0 ? '#4CAF50' : (profitRate !== null && profitRate < 0 ? '#f44336' : '#666');
        
        return `
            <tr>
                <td>${record.fund_code}</td>
                <td>${record.arbitrage_type === 'premium' ? '溢价' : '折价'}</td>
                <td>${initial.type === 'subscribe' ? '申购' : '买入'}</td>
                <td>${initial.price.toFixed(4)}</td>
                <td>${initial.shares.toFixed(2)}</td>
                <td>${initial.amount.toFixed(2)}</td>
                <td>${final ? (final.type === 'sell' ? '卖出' : '赎回') : '--'}</td>
                <td>${final ? final.price.toFixed(4) : '--'}</td>
                <td>${final ? final.amount.toFixed(2) : '--'}</td>
                <td style="color: ${profitColor}; font-weight: bold;">${profit !== null ? (profit >= 0 ? '+' : '') + profit.toFixed(2) : '--'}</td>
                <td style="color: ${profitRateColor}; font-weight: bold;">${profitRate !== null ? (profitRate >= 0 ? '+' : '') + profitRate.toFixed(2) + '%' : '--'}</td>
                <td><span class="status-badge ${statusClass}">${statusBadge}</span></td>
                <td>
                    ${status === 'in_progress' ? `<button class="btn btn-small btn-primary" onclick="openCompleteArbitrageModal('${record.id}', '${record.fund_code}', '${record.arbitrage_type}', ${initial.shares})">完成</button>` : ''}
                    <button class="btn btn-small btn-secondary" onclick="deleteArbitrageRecord('${record.id}')" style="margin-left: 5px;">删除</button>
                </td>
            </tr>
        `;
    }).join('');
}

// 加载套利统计
async function loadArbitrageStatistics() {
    try {
        const response = await fetch('/api/arbitrage/statistics');
        const result = await response.json();
        
        if (result.success) {
            const stats = result.statistics;
            document.getElementById('statsTotalCount').textContent = stats.total_count;
            document.getElementById('statsTotalProfit').textContent = 
                (stats.total_profit >= 0 ? '+' : '') + stats.total_profit.toFixed(2);
            document.getElementById('statsTotalProfit').style.color = stats.total_profit >= 0 ? '#4CAF50' : '#f44336';
            document.getElementById('statsTotalInvestment').textContent = stats.total_investment.toFixed(2);
            document.getElementById('statsTotalReturnRate').textContent = 
                (stats.total_return_rate >= 0 ? '+' : '') + stats.total_return_rate.toFixed(2) + '%';
            document.getElementById('statsTotalReturnRate').style.color = stats.total_return_rate >= 0 ? '#4CAF50' : '#f44336';
            document.getElementById('statsWinRate').textContent = stats.win_rate.toFixed(2) + '%';
            document.getElementById('statsInProgress').textContent = stats.in_progress_count;
        }
    } catch (error) {
        console.error('加载统计失败:', error);
    }
}

// 打开完成套利模态框
async function openCompleteArbitrageModal(recordId, fundCode, arbitrageType, initialShares) {
    // #region agent log
    const startTime = Date.now();
    fetch('http://127.0.0.1:7243/ingest/c359bf7a-79f8-4b93-af0b-f5a5dba44447',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'arbitrage_records.js:openCompleteArbitrageModal:entry',message:'开始打开完成套利模态框',data:{recordId,fundCode,arbitrageType,initialShares},timestamp:Date.now(),sessionId:'debug-session'})}).catch(()=>{});
    // #endregion
    
    currentRecordId = recordId;
    const today = new Date().toISOString().split('T')[0];
    
    // 立即显示模态框，提升用户体验
    document.getElementById('completeArbitrageModal').classList.add('active');
    
    // 更新价格标签
    const priceLabel = document.getElementById('completeFinalPriceLabel');
    if (priceLabel) {
        priceLabel.innerHTML = `最终价格（${arbitrageType === 'premium' ? '场内卖出价格' : '场外赎回净值'}）:`;
    }
    
    // 立即填充已知数据
    document.getElementById('completeFinalDate').value = today;
    if (initialShares) {
        document.getElementById('completeFinalShares').value = parseFloat(initialShares).toFixed(4);
    }
    document.getElementById('completeFinalPrice').value = '';
    document.getElementById('completeFinalAmount').value = '';
    
    // #region agent log
    const uiReadyTime = Date.now();
    fetch('http://127.0.0.1:7243/ingest/c359bf7a-79f8-4b93-af0b-f5a5dba44447',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'arbitrage_records.js:openCompleteArbitrageModal:ui_ready',message:'UI已显示',data:{elapsed_ms:uiReadyTime-startTime},timestamp:Date.now(),sessionId:'debug-session'})}).catch(()=>{});
    // #endregion
    
    // 异步获取当前价格/净值（不阻塞UI显示）
    try {
        // #region agent log
        const fetchStartTime = Date.now();
        fetch('http://127.0.0.1:7243/ingest/c359bf7a-79f8-4b93-af0b-f5a5dba44447',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'arbitrage_records.js:openCompleteArbitrageModal:fetch_start',message:'开始获取基金信息',data:{fundCode},timestamp:Date.now(),sessionId:'debug-session'})}).catch(()=>{});
        // #endregion
        
        const response = await fetch(`/api/fund/${fundCode}`);
        const result = await response.json();
        
        // #region agent log
        const fetchEndTime = Date.now();
        fetch('http://127.0.0.1:7243/ingest/c359bf7a-79f8-4b93-af0b-f5a5dba44447',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'arbitrage_records.js:openCompleteArbitrageModal:fetch_end',message:'获取基金信息完成',data:{success:result.success,fetch_time_ms:fetchEndTime-fetchStartTime},timestamp:Date.now(),sessionId:'debug-session'})}).catch(()=>{});
        // #endregion
        
        if (result.success) {
            const fund = result.data;
            // 溢价套利：获取场内价格（卖出价格）
            // 折价套利：获取场外净值（赎回净值）
            const finalPrice = arbitrageType === 'premium' ? fund.price : fund.nav;
            if (finalPrice && finalPrice > 0) {
                document.getElementById('completeFinalPrice').value = finalPrice.toFixed(4);
                
                // 如果已填充初始份额，自动计算最终金额
                if (initialShares) {
                    const finalPriceValue = parseFloat(finalPrice);
                    const finalSharesValue = parseFloat(initialShares);
                    if (finalPriceValue > 0 && finalSharesValue > 0) {
                        // 确保费率已加载
                        if (!tradeFees) {
                            await loadTradeFees();
                        }
                        
                        // 根据套利类型计算最终金额
                        if (arbitrageType === 'premium') {
                            // 溢价套利：场内卖出，需要扣除卖出费用
                            const sellCost = tradeFees ? (tradeFees.sell_commission + tradeFees.stamp_tax) : 0.0004;
                            const finalAmount = finalSharesValue * finalPriceValue * (1 - sellCost);
                            document.getElementById('completeFinalAmount').value = finalAmount.toFixed(2);
                        } else {
                            // 折价套利：场外赎回，需要扣除赎回费用
                            const redeemCost = tradeFees ? tradeFees.redeem_fee : 0.005;
                            const finalAmount = finalSharesValue * finalPriceValue * (1 - redeemCost);
                            document.getElementById('completeFinalAmount').value = finalAmount.toFixed(2);
                        }
                    }
                }
            }
        } else {
            console.warn('获取基金信息失败:', result.message);
        }
    } catch (error) {
        console.error('获取基金信息失败:', error);
    }
    
    // #region agent log
    const endTime = Date.now();
    fetch('http://127.0.0.1:7243/ingest/c359bf7a-79f8-4b93-af0b-f5a5dba44447',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'arbitrage_records.js:openCompleteArbitrageModal:complete',message:'完成套利模态框打开完成',data:{total_time_ms:endTime-startTime},timestamp:Date.now(),sessionId:'debug-session'})}).catch(()=>{});
    // #endregion
}

// 关闭完成套利模态框
function closeCompleteArbitrageModal() {
    document.getElementById('completeArbitrageModal').classList.remove('active');
}

// 完成套利记录
async function completeArbitrageRecord() {
    try {
        const finalPrice = parseFloat(document.getElementById('completeFinalPrice').value);
        const finalShares = document.getElementById('completeFinalShares').value;
        const finalAmount = document.getElementById('completeFinalAmount').value;
        const finalDate = document.getElementById('completeFinalDate').value;
        
        if (!finalPrice || !finalDate) {
            alert('请填写最终价格和日期');
            return;
        }
        
        const data = {
            final_price: finalPrice,
            final_date: finalDate
        };
        
        if (finalShares) {
            data.final_shares = parseFloat(finalShares);
        }
        if (finalAmount) {
            data.final_amount = parseFloat(finalAmount);
        }
        
        const response = await fetch(`/api/arbitrage/records/${currentRecordId}/complete`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        if (result.success) {
            alert('套利记录完成！');
            closeCompleteArbitrageModal();
            await loadArbitrageRecords();
            await loadArbitrageStatistics();
        } else {
            alert('完成失败: ' + result.message);
        }
    } catch (error) {
        alert('完成失败: ' + error.message);
    }
}

// 删除套利记录
async function deleteArbitrageRecord(recordId) {
    if (!confirm('确定要删除这条记录吗？')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/arbitrage/records/${recordId}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        if (result.success) {
            await loadArbitrageRecords();
            await loadArbitrageStatistics();
        } else {
            alert('删除失败: ' + result.message);
        }
    } catch (error) {
        alert('删除失败: ' + error.message);
    }
}

// 绑定套利记录相关事件
document.addEventListener('DOMContentLoaded', function() {
    // 记录套利模态框
    const closeRecordBtn = document.getElementById('closeRecordArbitrageBtn');
    const cancelRecordBtn = document.getElementById('cancelRecordBtn');
    const saveRecordBtn = document.getElementById('saveRecordBtn');
    if (closeRecordBtn) closeRecordBtn.addEventListener('click', closeRecordArbitrageModal);
    if (cancelRecordBtn) cancelRecordBtn.addEventListener('click', closeRecordArbitrageModal);
    if (saveRecordBtn) saveRecordBtn.addEventListener('click', saveArbitrageRecord);
    
    // 套利记录管理模态框
    const closeRecordsBtn = document.getElementById('closeArbitrageRecordsBtn');
    const filterAllBtn = document.getElementById('filterAllBtn');
    const filterCompletedBtn = document.getElementById('filterCompletedBtn');
    const filterInProgressBtn = document.getElementById('filterInProgressBtn');
    if (closeRecordsBtn) closeRecordsBtn.addEventListener('click', closeArbitrageRecords);
    if (filterAllBtn) filterAllBtn.addEventListener('click', () => loadArbitrageRecords());
    if (filterCompletedBtn) filterCompletedBtn.addEventListener('click', () => loadArbitrageRecords('completed'));
    if (filterInProgressBtn) filterInProgressBtn.addEventListener('click', () => loadArbitrageRecords('in_progress'));
    
    // 完成套利模态框
    const closeCompleteBtn = document.getElementById('closeCompleteArbitrageBtn');
    const cancelCompleteBtn = document.getElementById('cancelCompleteBtn');
    const saveCompleteBtn = document.getElementById('saveCompleteBtn');
    if (closeCompleteBtn) closeCompleteBtn.addEventListener('click', closeCompleteArbitrageModal);
    if (cancelCompleteBtn) cancelCompleteBtn.addEventListener('click', closeCompleteArbitrageModal);
    if (saveCompleteBtn) saveCompleteBtn.addEventListener('click', completeArbitrageRecord);
    
    // 点击模态框外部关闭
    const recordModal = document.getElementById('recordArbitrageModal');
    const recordsModal = document.getElementById('arbitrageRecordsModal');
    const completeModal = document.getElementById('completeArbitrageModal');
    if (recordModal) {
        recordModal.addEventListener('click', function(e) {
            if (e.target === this) closeRecordArbitrageModal();
        });
    }
    if (recordsModal) {
        recordsModal.addEventListener('click', function(e) {
            if (e.target === this) closeArbitrageRecords();
        });
    }
    if (completeModal) {
        completeModal.addEventListener('click', function(e) {
            if (e.target === this) closeCompleteArbitrageModal();
        });
    }
});
