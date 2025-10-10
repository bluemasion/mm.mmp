/* 物料匹配页面专用JavaScript */

/**
 * 物料匹配相关功能
 */
const MaterialMatching = {
    // 匹配结果数据
    matchingResults: [],
    
    // 匹配配置
    config: {
        similarity_threshold: 0.8,
        max_results: 10,
        matching_methods: ['fuzzy', 'semantic', 'hybrid']
    },
    
    // 当前匹配状态
    status: {
        isMatching: false,
        currentMethod: 'hybrid',
        progress: 0
    },
    
    // 初始化页面
    init: function() {
        this.bindEvents();
        this.loadSessionData();
        this.initMatchingInterface();
    },
    
    // 绑定事件
    bindEvents: function() {
        // 开始匹配按钮
        const matchBtn = document.querySelector('#startMatchingBtn');
        if (matchBtn) {
            matchBtn.addEventListener('click', () => {
                this.startMatching();
            });
        }
        
        // 匹配方法选择
        const methodSelect = document.querySelector('#matchingMethod');
        if (methodSelect) {
            methodSelect.addEventListener('change', (e) => {
                this.status.currentMethod = e.target.value;
                this.updateMatchingConfig();
            });
        }
        
        // 相似度阈值调整
        const thresholdSlider = document.querySelector('#similarityThreshold');
        if (thresholdSlider) {
            thresholdSlider.addEventListener('input', (e) => {
                this.config.similarity_threshold = parseFloat(e.target.value);
                this.updateThresholdDisplay(e.target.value);
            });
        }
        
        // 下一步按钮
        const nextBtn = document.querySelector('#nextBtn');
        if (nextBtn) {
            nextBtn.addEventListener('click', () => {
                this.proceedToCategorization();
            });
        }
        
        // 重新匹配按钮
        const rematchBtn = document.querySelector('#rematchBtn');
        if (rematchBtn) {
            rematchBtn.addEventListener('click', () => {
                this.startMatching();
            });
        }
    },
    
    // 加载会话数据
    loadSessionData: function() {
        const sessionId = getSessionId();
        if (!sessionId || !loadSessionFromLocal(sessionId)) {
            showNotification('未找到会话数据，请重新开始', 'warning');
            setTimeout(() => {
                window.location.href = '/';
            }, 2000);
            return;
        }
        
        this.displaySessionSummary();
    },
    
    // 显示会话摘要
    displaySessionSummary: function() {
        const summaryContainer = document.querySelector('#sessionSummary');
        if (!summaryContainer || !MMP.session.data) return;
        
        const data = MMP.session.data;
        const extractedParams = data.extracted_params || {};
        
        summaryContainer.innerHTML = `
            <div class="card">
                <div class="card-header">
                    <h6 class="mb-0">会话摘要</h6>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-4">
                            <div class="summary-item">
                                <div class="summary-label">文件名</div>
                                <div class="summary-value">${data.filename || '未知'}</div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="summary-item">
                                <div class="summary-label">数据行数</div>
                                <div class="summary-value">${data.row_count || 0}</div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="summary-item">
                                <div class="summary-label">提取参数</div>
                                <div class="summary-value">${Object.keys(extractedParams).length}</div>
                            </div>
                        </div>
                    </div>
                    
                    ${Object.keys(extractedParams).length > 0 ? `
                        <div class="mt-3">
                            <h6>已提取的参数:</h6>
                            <div class="d-flex flex-wrap gap-2">
                                ${Object.entries(extractedParams).map(([key, values]) => {
                                    const sampleValue = Array.isArray(values) ? values[0] : values;
                                    return `
                                        <div class="param-badge">
                                            <strong>${key}:</strong> ${sampleValue || '空'}
                                        </div>
                                    `;
                                }).join('')}
                            </div>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    },
    
    // 初始化匹配界面
    initMatchingInterface: function() {
        const interfaceContainer = document.querySelector('#matchingInterface');
        if (!interfaceContainer) return;
        
        interfaceContainer.innerHTML = `
            <div class="card">
                <div class="card-header">
                    <h6 class="mb-0">物料匹配配置</h6>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-6">
                            <label class="form-label">匹配方法</label>
                            <select class="form-select" id="matchingMethod">
                                <option value="hybrid">混合匹配（推荐）</option>
                                <option value="fuzzy">模糊匹配</option>
                                <option value="semantic">语义匹配</option>
                            </select>
                            <div class="form-text">
                                混合匹配结合多种算法，提供最佳匹配效果
                            </div>
                        </div>
                        <div class="col-md-6">
                            <label class="form-label">
                                相似度阈值: <span id="thresholdValue">${this.config.similarity_threshold}</span>
                            </label>
                            <input type="range" class="form-range" id="similarityThreshold" 
                                   min="0.5" max="1.0" step="0.05" value="${this.config.similarity_threshold}">
                            <div class="form-text">
                                设置匹配的最低相似度要求
                            </div>
                        </div>
                    </div>
                    
                    <div class="mt-4 text-center">
                        <button type="button" class="btn btn-primary btn-lg" id="startMatchingBtn">
                            <i class="fas fa-play me-2"></i>
                            开始匹配
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        // 重新绑定事件
        this.bindEvents();
    },
    
    // 更新阈值显示
    updateThresholdDisplay: function(value) {
        const display = document.querySelector('#thresholdValue');
        if (display) {
            display.textContent = value;
        }
    },
    
    // 更新匹配配置
    updateMatchingConfig: function() {
        console.log('匹配配置更新:', {
            method: this.status.currentMethod,
            threshold: this.config.similarity_threshold
        });
    },
    
    // 开始匹配
    startMatching: async function() {
        if (this.status.isMatching) {
            showNotification('匹配正在进行中，请稍候', 'info');
            return;
        }
        
        const sessionId = getSessionId();
        if (!sessionId) {
            showNotification('会话ID不存在', 'warning');
            return;
        }
        
        this.status.isMatching = true;
        this.status.progress = 0;
        
        try {
            // 显示匹配进度
            this.showMatchingProgress();
            showNotification('开始物料匹配，请稍候...', 'info');
            
            const response = await safeRequest(MMP.API.MATCH, {
                method: 'POST',
                body: JSON.stringify({
                    session_id: sessionId,
                    matching_method: this.status.currentMethod,
                    similarity_threshold: this.config.similarity_threshold,
                    max_results: this.config.max_results
                })
            });
            
            if (response.success) {
                this.matchingResults = response.data.matches || [];
                this.displayMatchingResults(response.data);
                showNotification(`匹配完成！找到 ${this.matchingResults.length} 个匹配结果`, 'success');
                
                // 保存结果到会话
                MMP.session.data.matching_results = response.data;
                saveSessionToLocal();
            } else {
                showNotification(`匹配失败: ${response.message}`, 'danger');
                this.displayMatchingError(response.message);
            }
        } catch (error) {
            console.error('匹配错误:', error);
            showNotification('匹配过程中出现错误', 'danger');
            this.displayMatchingError(error.message);
        } finally {
            this.status.isMatching = false;
            this.hideMatchingProgress();
        }
    },
    
    // 显示匹配进度
    showMatchingProgress: function() {
        const progressContainer = document.querySelector('#matchingProgress') || 
                                document.createElement('div');
        progressContainer.id = 'matchingProgress';
        
        if (!progressContainer.parentElement) {
            const container = document.querySelector('.container');
            container.appendChild(progressContainer);
        }
        
        progressContainer.innerHTML = `
            <div class="card mb-4">
                <div class="card-body">
                    <h6 class="mb-3">正在进行物料匹配...</h6>
                    <div class="progress mb-2">
                        <div class="progress-bar progress-bar-striped progress-bar-animated" 
                             role="progressbar" style="width: 0%" id="matchProgressBar">
                        </div>
                    </div>
                    <div class="d-flex justify-content-between align-items-center">
                        <span class="text-muted" id="matchProgressText">准备中...</span>
                        <span class="text-muted" id="matchProgressPercent">0%</span>
                    </div>
                </div>
            </div>
        `;
        
        // 模拟进度更新
        this.simulateProgress();
    },
    
    // 模拟进度更新
    simulateProgress: function() {
        const stages = [
            { percent: 20, text: '加载物料数据库...' },
            { percent: 40, text: '分析输入数据...' },
            { percent: 60, text: '计算相似度...' },
            { percent: 80, text: '排序匹配结果...' },
            { percent: 100, text: '匹配完成！' }
        ];
        
        let currentStage = 0;
        const updateProgress = () => {
            if (currentStage >= stages.length || !this.status.isMatching) return;
            
            const stage = stages[currentStage];
            const progressBar = document.querySelector('#matchProgressBar');
            const progressText = document.querySelector('#matchProgressText');
            const progressPercent = document.querySelector('#matchProgressPercent');
            
            if (progressBar && progressText && progressPercent) {
                progressBar.style.width = `${stage.percent}%`;
                progressText.textContent = stage.text;
                progressPercent.textContent = `${stage.percent}%`;
            }
            
            currentStage++;
            
            if (currentStage < stages.length && this.status.isMatching) {
                setTimeout(updateProgress, 800 + Math.random() * 1200);
            }
        };
        
        updateProgress();
    },
    
    // 隐藏匹配进度
    hideMatchingProgress: function() {
        const progressContainer = document.querySelector('#matchingProgress');
        if (progressContainer) {
            progressContainer.remove();
        }
    },
    
    // 显示匹配结果
    displayMatchingResults: function(data) {
        const resultsContainer = document.querySelector('#matchingResults');
        if (!resultsContainer) return;
        
        const matches = data.matches || [];
        const statistics = data.statistics || {};
        
        resultsContainer.innerHTML = `
            <div class="card">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <h6 class="mb-0">匹配结果</h6>
                    <div class="btn-group btn-group-sm">
                        <button type="button" class="btn btn-outline-primary" onclick="MaterialMatching.exportResults()">
                            导出结果
                        </button>
                        <button type="button" class="btn btn-outline-secondary" onclick="MaterialMatching.startMatching()">
                            重新匹配
                        </button>
                    </div>
                </div>
                <div class="card-body">
                    ${matches.length > 0 ? `
                        <!-- 匹配统计 -->
                        <div class="row mb-4">
                            <div class="col-md-3">
                                <div class="stat-card">
                                    <div class="stat-number">${statistics.total_matches || matches.length}</div>
                                    <div class="stat-label">总匹配数</div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="stat-card">
                                    <div class="stat-number">${statistics.high_confidence || 0}</div>
                                    <div class="stat-label">高置信度</div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="stat-card">
                                    <div class="stat-number">${Math.round((statistics.avg_similarity || 0) * 100)}%</div>
                                    <div class="stat-label">平均相似度</div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="stat-card">
                                    <div class="stat-number">${statistics.processing_time || 0}s</div>
                                    <div class="stat-label">处理时间</div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- 匹配结果表格 -->
                        <div class="table-responsive">
                            ${this.renderMatchingTable(matches)}
                        </div>
                    ` : `
                        <div class="alert alert-warning">
                            <h6>未找到匹配结果</h6>
                            <p>可能的原因：</p>
                            <ul>
                                <li>相似度阈值设置过高</li>
                                <li>输入数据与数据库中的物料差异较大</li>
                                <li>物料数据库中没有相关物料</li>
                            </ul>
                            <div class="mt-3">
                                <button type="button" class="btn btn-primary me-2" onclick="MaterialMatching.adjustThresholdAndRetry()">
                                    降低阈值重试
                                </button>
                                <button type="button" class="btn btn-secondary" onclick="MaterialMatching.proceedToCategorization()">
                                    跳过匹配
                                </button>
                            </div>
                        </div>
                    `}
                </div>
            </div>
        `;
        
        // 显示下一步按钮
        if (matches.length > 0) {
            this.showNextButton();
        }
    },
    
    // 渲染匹配结果表格
    renderMatchingTable: function(matches) {
        return `
            <table class="table table-striped data-table">
                <thead>
                    <tr>
                        <th data-sortable>物料名称</th>
                        <th data-sortable>规格</th>
                        <th data-sortable>制造商</th>
                        <th data-sortable>相似度</th>
                        <th data-sortable>匹配类型</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody>
                    ${matches.map((match, index) => `
                        <tr data-match-id="${index}">
                            <td>
                                <div class="material-name">
                                    ${match.material_name || '未知'}
                                </div>
                                ${match.original_name ? `
                                    <small class="text-muted">原始: ${match.original_name}</small>
                                ` : ''}
                            </td>
                            <td>${match.specification || '-'}</td>
                            <td>${match.manufacturer || '-'}</td>
                            <td>
                                <div class="similarity-score">
                                    <div class="progress">
                                        <div class="progress-bar ${this.getSimilarityClass(match.similarity)}" 
                                             style="width: ${(match.similarity || 0) * 100}%">
                                        </div>
                                    </div>
                                    <span class="similarity-text">${Math.round((match.similarity || 0) * 100)}%</span>
                                </div>
                            </td>
                            <td>
                                <span class="badge ${this.getMatchTypeBadge(match.match_type)}">
                                    ${match.match_type || 'unknown'}
                                </span>
                            </td>
                            <td>
                                <div class="btn-group btn-group-sm">
                                    <button type="button" class="btn btn-outline-primary" 
                                            onclick="MaterialMatching.viewMatchDetails(${index})">
                                        详情
                                    </button>
                                    <button type="button" class="btn btn-outline-success"
                                            onclick="MaterialMatching.confirmMatch(${index})">
                                        确认
                                    </button>
                                </div>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    },
    
    // 获取相似度颜色类
    getSimilarityClass: function(similarity) {
        if (similarity >= 0.9) return 'bg-success';
        if (similarity >= 0.7) return 'bg-warning';
        return 'bg-danger';
    },
    
    // 获取匹配类型徽章类
    getMatchTypeBadge: function(matchType) {
        switch (matchType) {
            case 'exact': return 'bg-success';
            case 'fuzzy': return 'bg-primary';
            case 'semantic': return 'bg-info';
            case 'hybrid': return 'bg-warning';
            default: return 'bg-secondary';
        }
    },
    
    // 查看匹配详情
    viewMatchDetails: function(matchIndex) {
        const match = this.matchingResults[matchIndex];
        if (!match) return;
        
        showModal('matchDetailModal', {
            title: '匹配详情',
            body: `
                <div class="match-details">
                    <div class="row">
                        <div class="col-md-6">
                            <h6>原始数据</h6>
                            <div class="detail-item">
                                <strong>物料名称:</strong> ${match.original_name || '未知'}
                            </div>
                            <div class="detail-item">
                                <strong>规格:</strong> ${match.original_spec || '-'}
                            </div>
                            <div class="detail-item">
                                <strong>制造商:</strong> ${match.original_manufacturer || '-'}
                            </div>
                        </div>
                        <div class="col-md-6">
                            <h6>匹配结果</h6>
                            <div class="detail-item">
                                <strong>物料名称:</strong> ${match.material_name || '未知'}
                            </div>
                            <div class="detail-item">
                                <strong>规格:</strong> ${match.specification || '-'}
                            </div>
                            <div class="detail-item">
                                <strong>制造商:</strong> ${match.manufacturer || '-'}
                            </div>
                        </div>
                    </div>
                    
                    <div class="mt-3">
                        <h6>匹配信息</h6>
                        <div class="row">
                            <div class="col-md-4">
                                <div class="detail-item">
                                    <strong>相似度:</strong> ${Math.round((match.similarity || 0) * 100)}%
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="detail-item">
                                    <strong>匹配方法:</strong> ${match.match_type || 'unknown'}
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="detail-item">
                                    <strong>置信度:</strong> ${Math.round((match.confidence || 0) * 100)}%
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    ${match.match_reasons ? `
                        <div class="mt-3">
                            <h6>匹配原因</h6>
                            <ul class="list-unstyled">
                                ${match.match_reasons.map(reason => `
                                    <li><i class="fas fa-check-circle text-success me-2"></i>${reason}</li>
                                `).join('')}
                            </ul>
                        </div>
                    ` : ''}
                </div>
            `
        });
    },
    
    // 确认匹配
    confirmMatch: function(matchIndex) {
        const match = this.matchingResults[matchIndex];
        if (!match) return;
        
        match.confirmed = true;
        
        // 更新UI
        const row = document.querySelector(`tr[data-match-id="${matchIndex}"]`);
        if (row) {
            row.classList.add('table-success');
            const confirmBtn = row.querySelector('button[onclick*="confirmMatch"]');
            if (confirmBtn) {
                confirmBtn.textContent = '已确认';
                confirmBtn.disabled = true;
                confirmBtn.classList.remove('btn-outline-success');
                confirmBtn.classList.add('btn-success');
            }
        }
        
        showNotification('匹配已确认', 'success', 2000);
        
        // 保存到会话
        saveSessionToLocal();
    },
    
    // 调整阈值并重试
    adjustThresholdAndRetry: function() {
        this.config.similarity_threshold = Math.max(0.5, this.config.similarity_threshold - 0.1);
        
        const thresholdSlider = document.querySelector('#similarityThreshold');
        if (thresholdSlider) {
            thresholdSlider.value = this.config.similarity_threshold;
            this.updateThresholdDisplay(this.config.similarity_threshold);
        }
        
        showNotification(`已将阈值调整为 ${this.config.similarity_threshold}，重新匹配中...`, 'info');
        this.startMatching();
    },
    
    // 显示匹配错误
    displayMatchingError: function(errorMessage) {
        const resultsContainer = document.querySelector('#matchingResults');
        if (!resultsContainer) return;
        
        resultsContainer.innerHTML = `
            <div class="card">
                <div class="card-header bg-danger text-white">
                    <h6 class="mb-0">匹配失败</h6>
                </div>
                <div class="card-body">
                    <div class="alert alert-danger">
                        <h6>错误信息:</h6>
                        <p>${errorMessage}</p>
                    </div>
                    <div class="d-flex gap-2">
                        <button type="button" class="btn btn-primary" onclick="MaterialMatching.startMatching()">
                            重新匹配
                        </button>
                        <button type="button" class="btn btn-secondary" onclick="window.location.href='/extract_parameters?session_id=${getSessionId()}'">
                            返回上一步
                        </button>
                    </div>
                </div>
            </div>
        `;
    },
    
    // 导出匹配结果
    exportResults: function() {
        if (this.matchingResults.length === 0) {
            showNotification('没有可导出的结果', 'warning');
            return;
        }
        
        const csvData = this.convertToCSV(this.matchingResults);
        const blob = new Blob([csvData], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        
        if (link.download !== undefined) {
            const url = URL.createObjectURL(blob);
            link.setAttribute('href', url);
            link.setAttribute('download', `matching_results_${Date.now()}.csv`);
            link.style.visibility = 'hidden';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
        
        showNotification('匹配结果已导出', 'success');
    },
    
    // 转换为CSV格式
    convertToCSV: function(data) {
        const headers = ['物料名称', '规格', '制造商', '相似度', '匹配类型', '确认状态'];
        const rows = data.map(match => [
            match.material_name || '',
            match.specification || '',
            match.manufacturer || '',
            Math.round((match.similarity || 0) * 100) + '%',
            match.match_type || '',
            match.confirmed ? '已确认' : '未确认'
        ]);
        
        return [headers, ...rows].map(row => 
            row.map(field => `"${field}"`).join(',')
        ).join('\n');
    },
    
    // 显示下一步按钮
    showNextButton: function() {
        let nextContainer = document.querySelector('#nextStepContainer');
        if (!nextContainer) {
            nextContainer = document.createElement('div');
            nextContainer.id = 'nextStepContainer';
            nextContainer.className = 'mt-4 text-center';
            document.querySelector('.container').appendChild(nextContainer);
        }
        
        nextContainer.innerHTML = `
            <div class="card">
                <div class="card-body">
                    <h6>物料匹配完成</h6>
                    <p class="text-muted">点击下方按钮继续进行物料分类</p>
                    <button type="button" class="btn btn-primary btn-lg" onclick="MaterialMatching.proceedToCategorization()">
                        <i class="fas fa-arrow-right me-2"></i>
                        进入物料分类
                    </button>
                </div>
            </div>
        `;
    },
    
    // 继续到分类阶段
    proceedToCategorization: function() {
        const sessionId = getSessionId();
        if (!sessionId) {
            showNotification('会话信息丢失', 'danger');
            return;
        }
        
        showNotification('正在跳转到物料分类...', 'info');
        setTimeout(() => {
            window.location.href = `/categorize?session_id=${sessionId}`;
        }, 1000);
    }
};

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    if (window.location.pathname.includes('matching')) {
        MaterialMatching.init();
    }
});

// 导出到全局
window.MaterialMatching = MaterialMatching;