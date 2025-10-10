/* 物料分类页面专用JavaScript */

/**
 * 物料分类相关功能
 */
const MaterialCategorization = {
    // 分类结果数据
    categorizedData: [],
    
    // 预定义分类体系
    categorySystem: {
        '医用耗材': {
            '一次性耗材': ['注射器', '输液器', '导尿管', '吸氧管', '手术刀片'],
            '植入材料': ['支架', '钉板', '填充材料', '缝合材料'],
            '敷料用品': ['纱布', '绷带', '胶带', '创可贴', '敷贴']
        },
        '医疗设备': {
            '诊断设备': ['X光机', 'CT', 'MRI', '超声', '心电图机'],
            '治疗设备': ['呼吸机', '透析机', '激光设备', '手术器械'],
            '监护设备': ['心电监护', '血氧监护', '血压监护', '体温监护']
        },
        '药品试剂': {
            '西药': ['抗生素', '止痛药', '心血管药', '消化药', '呼吸药'],
            '中药': ['中成药', '中药饮片', '中药提取物'],
            '试剂': ['检验试剂', '诊断试剂', '生化试剂', '免疫试剂']
        }
    },
    
    // 当前分类状态
    status: {
        isCategorizing: false,
        currentMethod: 'ai',
        progress: 0
    },
    
    // 初始化页面
    init: function() {
        this.bindEvents();
        this.loadSessionData();
        this.initCategorizationInterface();
        this.displayCategorySystem();
    },
    
    // 绑定事件
    bindEvents: function() {
        // 开始分类按钮
        const categorizeBtn = document.querySelector('#startCategorizationBtn');
        if (categorizeBtn) {
            categorizeBtn.addEventListener('click', () => {
                this.startCategorization();
            });
        }
        
        // 分类方法选择
        const methodSelect = document.querySelector('#categorizationMethod');
        if (methodSelect) {
            methodSelect.addEventListener('change', (e) => {
                this.status.currentMethod = e.target.value;
                this.updateCategorizationConfig();
            });
        }
        
        // 手动分类按钮
        const manualBtn = document.querySelector('#manualCategorizeBtn');
        if (manualBtn) {
            manualBtn.addEventListener('click', () => {
                this.showManualCategorization();
            });
        }
        
        // 下一步按钮
        const nextBtn = document.querySelector('#nextBtn');
        if (nextBtn) {
            nextBtn.addEventListener('click', () => {
                this.proceedToDecision();
            });
        }
        
        // 重新分类按钮
        const recategorizeBtn = document.querySelector('#recategorizeBtn');
        if (recategorizeBtn) {
            recategorizeBtn.addEventListener('click', () => {
                this.startCategorization();
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
        const matchingResults = data.matching_results || {};
        const matches = matchingResults.matches || [];
        
        summaryContainer.innerHTML = `
            <div class="card">
                <div class="card-header">
                    <h6 class="mb-0">处理进度</h6>
                </div>
                <div class="card-body">
                    <div class="progress-steps">
                        <div class="step completed">
                            <i class="fas fa-upload"></i>
                            <span>文件上传</span>
                        </div>
                        <div class="step completed">
                            <i class="fas fa-extract"></i>
                            <span>参数提取</span>
                        </div>
                        <div class="step completed">
                            <i class="fas fa-search"></i>
                            <span>物料匹配</span>
                        </div>
                        <div class="step active">
                            <i class="fas fa-layer-group"></i>
                            <span>物料分类</span>
                        </div>
                        <div class="step">
                            <i class="fas fa-decision"></i>
                            <span>决策支持</span>
                        </div>
                    </div>
                    
                    <div class="mt-4 row">
                        <div class="col-md-3">
                            <div class="summary-stat">
                                <div class="stat-number">${data.row_count || 0}</div>
                                <div class="stat-label">数据行数</div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="summary-stat">
                                <div class="stat-number">${matches.length || 0}</div>
                                <div class="stat-label">匹配结果</div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="summary-stat">
                                <div class="stat-number">${matches.filter(m => m.confirmed).length || 0}</div>
                                <div class="stat-label">已确认</div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="summary-stat">
                                <div class="stat-number">0</div>
                                <div class="stat-label">已分类</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    },
    
    // 显示分类体系
    displayCategorySystem: function() {
        const systemContainer = document.querySelector('#categorySystem');
        if (!systemContainer) return;
        
        systemContainer.innerHTML = `
            <div class="card">
                <div class="card-header">
                    <h6 class="mb-0">分类体系</h6>
                </div>
                <div class="card-body">
                    <div class="category-tree">
                        ${Object.entries(this.categorySystem).map(([level1, level2Data]) => `
                            <div class="category-level-1">
                                <h6 class="category-title">
                                    <i class="fas fa-folder-open text-primary me-2"></i>
                                    ${level1}
                                </h6>
                                <div class="category-level-2">
                                    ${Object.entries(level2Data).map(([level2, items]) => `
                                        <div class="category-group">
                                            <div class="category-subtitle">
                                                <i class="fas fa-folder text-success me-2"></i>
                                                ${level2}
                                            </div>
                                            <div class="category-items">
                                                ${items.map(item => `
                                                    <span class="category-item">${item}</span>
                                                `).join('')}
                                            </div>
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
    },
    
    // 初始化分类界面
    initCategorizationInterface: function() {
        const interfaceContainer = document.querySelector('#categorizationInterface');
        if (!interfaceContainer) return;
        
        interfaceContainer.innerHTML = `
            <div class="card">
                <div class="card-header">
                    <h6 class="mb-0">分类配置</h6>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-6">
                            <label class="form-label">分类方法</label>
                            <select class="form-select" id="categorizationMethod">
                                <option value="ai">AI智能分类（推荐）</option>
                                <option value="rule">规则基础分类</option>
                                <option value="hybrid">混合分类</option>
                                <option value="manual">手动分类</option>
                            </select>
                            <div class="form-text">
                                AI智能分类提供最准确的分类结果
                            </div>
                        </div>
                        <div class="col-md-6">
                            <label class="form-label">分类详细程度</label>
                            <select class="form-select" id="categorizationDepth">
                                <option value="2">二级分类</option>
                                <option value="3" selected>三级分类（推荐）</option>
                                <option value="4">四级分类</option>
                            </select>
                            <div class="form-text">
                                分类层级越深，分类越精确
                            </div>
                        </div>
                    </div>
                    
                    <div class="mt-4 text-center">
                        <button type="button" class="btn btn-primary btn-lg me-2" id="startCategorizationBtn">
                            <i class="fas fa-play me-2"></i>
                            开始分类
                        </button>
                        <button type="button" class="btn btn-outline-secondary btn-lg" id="manualCategorizeBtn">
                            <i class="fas fa-edit me-2"></i>
                            手动分类
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        // 重新绑定事件
        this.bindEvents();
    },
    
    // 更新分类配置
    updateCategorizationConfig: function() {
        console.log('分类配置更新:', {
            method: this.status.currentMethod
        });
    },
    
    // 开始分类
    startCategorization: async function() {
        if (this.status.isCategorizing) {
            showNotification('分类正在进行中，请稍候', 'info');
            return;
        }
        
        const sessionId = getSessionId();
        if (!sessionId) {
            showNotification('会话ID不存在', 'warning');
            return;
        }
        
        this.status.isCategorizing = true;
        this.status.progress = 0;
        
        try {
            // 显示分类进度
            this.showCategorizationProgress();
            showNotification('开始物料分类，请稍候...', 'info');
            
            const depth = document.querySelector('#categorizationDepth')?.value || '3';
            
            const response = await safeRequest(MMP.API.CATEGORIZE, {
                method: 'POST',
                body: JSON.stringify({
                    session_id: sessionId,
                    categorization_method: this.status.currentMethod,
                    depth: parseInt(depth),
                    category_system: this.categorySystem
                })
            });
            
            if (response.success) {
                this.categorizedData = response.data.categories || [];
                this.displayCategorizationResults(response.data);
                showNotification(`分类完成！成功分类 ${this.categorizedData.length} 项物料`, 'success');
                
                // 保存结果到会话
                MMP.session.data.categorization_results = response.data;
                saveSessionToLocal();
            } else {
                showNotification(`分类失败: ${response.message}`, 'danger');
                this.displayCategorizationError(response.message);
            }
        } catch (error) {
            console.error('分类错误:', error);
            showNotification('分类过程中出现错误', 'danger');
            this.displayCategorizationError(error.message);
        } finally {
            this.status.isCategorizing = false;
            this.hideCategorizationProgress();
        }
    },
    
    // 显示分类进度
    showCategorizationProgress: function() {
        const progressContainer = document.querySelector('#categorizationProgress') || 
                                document.createElement('div');
        progressContainer.id = 'categorizationProgress';
        
        if (!progressContainer.parentElement) {
            const container = document.querySelector('.container');
            container.appendChild(progressContainer);
        }
        
        progressContainer.innerHTML = `
            <div class="card mb-4">
                <div class="card-body">
                    <h6 class="mb-3">正在进行物料分类...</h6>
                    <div class="progress mb-2">
                        <div class="progress-bar progress-bar-striped progress-bar-animated" 
                             role="progressbar" style="width: 0%" id="categorizeProgressBar">
                        </div>
                    </div>
                    <div class="d-flex justify-content-between align-items-center">
                        <span class="text-muted" id="categorizeProgressText">准备中...</span>
                        <span class="text-muted" id="categorizeProgressPercent">0%</span>
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
            { percent: 15, text: '加载分类模型...' },
            { percent: 30, text: '分析物料特征...' },
            { percent: 50, text: '应用分类规则...' },
            { percent: 70, text: '计算分类置信度...' },
            { percent: 85, text: '验证分类结果...' },
            { percent: 100, text: '分类完成！' }
        ];
        
        let currentStage = 0;
        const updateProgress = () => {
            if (currentStage >= stages.length || !this.status.isCategorizing) return;
            
            const stage = stages[currentStage];
            const progressBar = document.querySelector('#categorizeProgressBar');
            const progressText = document.querySelector('#categorizeProgressText');
            const progressPercent = document.querySelector('#categorizeProgressPercent');
            
            if (progressBar && progressText && progressPercent) {
                progressBar.style.width = `${stage.percent}%`;
                progressText.textContent = stage.text;
                progressPercent.textContent = `${stage.percent}%`;
            }
            
            currentStage++;
            
            if (currentStage < stages.length && this.status.isCategorizing) {
                setTimeout(updateProgress, 600 + Math.random() * 800);
            }
        };
        
        updateProgress();
    },
    
    // 隐藏分类进度
    hideCategorizationProgress: function() {
        const progressContainer = document.querySelector('#categorizationProgress');
        if (progressContainer) {
            progressContainer.remove();
        }
    },
    
    // 显示分类结果
    displayCategorizationResults: function(data) {
        const resultsContainer = document.querySelector('#categorizationResults');
        if (!resultsContainer) return;
        
        const categories = data.categories || [];
        const statistics = data.statistics || {};
        
        resultsContainer.innerHTML = `
            <div class="card">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <h6 class="mb-0">分类结果</h6>
                    <div class="btn-group btn-group-sm">
                        <button type="button" class="btn btn-outline-primary" onclick="MaterialCategorization.exportCategories()">
                            导出分类
                        </button>
                        <button type="button" class="btn btn-outline-secondary" onclick="MaterialCategorization.startCategorization()">
                            重新分类
                        </button>
                    </div>
                </div>
                <div class="card-body">
                    ${categories.length > 0 ? `
                        <!-- 分类统计 -->
                        <div class="row mb-4">
                            <div class="col-md-3">
                                <div class="stat-card">
                                    <div class="stat-number">${statistics.total_items || categories.length}</div>
                                    <div class="stat-label">总物料数</div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="stat-card">
                                    <div class="stat-number">${statistics.category_count || 0}</div>
                                    <div class="stat-label">分类数量</div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="stat-card">
                                    <div class="stat-number">${Math.round((statistics.avg_confidence || 0) * 100)}%</div>
                                    <div class="stat-label">平均置信度</div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="stat-card">
                                    <div class="stat-number">${statistics.processing_time || 0}s</div>
                                    <div class="stat-label">处理时间</div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- 分类结果表格 -->
                        <div class="table-responsive">
                            ${this.renderCategorizationTable(categories)}
                        </div>
                        
                        <!-- 分类分布图表 -->
                        <div class="mt-4">
                            ${this.renderCategoryDistribution(categories)}
                        </div>
                    ` : `
                        <div class="alert alert-warning">
                            <h6>分类失败</h6>
                            <p>无法对物料进行自动分类，可能的原因：</p>
                            <ul>
                                <li>物料信息不完整</li>
                                <li>物料类型不在预定义分类体系中</li>
                                <li>分类规则需要调整</li>
                            </ul>
                            <div class="mt-3">
                                <button type="button" class="btn btn-primary me-2" onclick="MaterialCategorization.showManualCategorization()">
                                    手动分类
                                </button>
                                <button type="button" class="btn btn-secondary" onclick="MaterialCategorization.proceedToDecision()">
                                    跳过分类
                                </button>
                            </div>
                        </div>
                    `}
                </div>
            </div>
        `;
        
        // 显示下一步按钮
        if (categories.length > 0) {
            this.showNextButton();
        }
    },
    
    // 渲染分类结果表格
    renderCategorizationTable: function(categories) {
        return `
            <table class="table table-striped data-table">
                <thead>
                    <tr>
                        <th data-sortable>物料名称</th>
                        <th data-sortable>一级分类</th>
                        <th data-sortable>二级分类</th>
                        <th data-sortable>三级分类</th>
                        <th data-sortable>置信度</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody>
                    ${categories.map((item, index) => `
                        <tr data-category-id="${index}">
                            <td>
                                <div class="material-info">
                                    <strong>${item.material_name || '未知'}</strong>
                                    ${item.specification ? `<br><small class="text-muted">${item.specification}</small>` : ''}
                                </div>
                            </td>
                            <td>
                                <span class="category-badge level-1">${item.category_level_1 || '-'}</span>
                            </td>
                            <td>
                                <span class="category-badge level-2">${item.category_level_2 || '-'}</span>
                            </td>
                            <td>
                                <span class="category-badge level-3">${item.category_level_3 || '-'}</span>
                            </td>
                            <td>
                                <div class="confidence-score">
                                    <div class="progress">
                                        <div class="progress-bar ${this.getConfidenceClass(item.confidence)}" 
                                             style="width: ${(item.confidence || 0) * 100}%">
                                        </div>
                                    </div>
                                    <span class="confidence-text">${Math.round((item.confidence || 0) * 100)}%</span>
                                </div>
                            </td>
                            <td>
                                <div class="btn-group btn-group-sm">
                                    <button type="button" class="btn btn-outline-primary" 
                                            onclick="MaterialCategorization.editCategory(${index})">
                                        编辑
                                    </button>
                                    <button type="button" class="btn btn-outline-success"
                                            onclick="MaterialCategorization.confirmCategory(${index})">
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
    
    // 渲染分类分布图
    renderCategoryDistribution: function(categories) {
        const distribution = {};
        categories.forEach(item => {
            const level1 = item.category_level_1 || '未分类';
            distribution[level1] = (distribution[level1] || 0) + 1;
        });
        
        return `
            <div class="card">
                <div class="card-header">
                    <h6 class="mb-0">分类分布</h6>
                </div>
                <div class="card-body">
                    <div class="row">
                        ${Object.entries(distribution).map(([category, count]) => {
                            const percentage = Math.round((count / categories.length) * 100);
                            return `
                                <div class="col-md-4 mb-3">
                                    <div class="distribution-item">
                                        <div class="distribution-label">${category}</div>
                                        <div class="distribution-bar">
                                            <div class="progress">
                                                <div class="progress-bar bg-primary" 
                                                     style="width: ${percentage}%"></div>
                                            </div>
                                            <span class="distribution-text">${count} (${percentage}%)</span>
                                        </div>
                                    </div>
                                </div>
                            `;
                        }).join('')}
                    </div>
                </div>
            </div>
        `;
    },
    
    // 获取置信度颜色类
    getConfidenceClass: function(confidence) {
        if (confidence >= 0.8) return 'bg-success';
        if (confidence >= 0.6) return 'bg-warning';
        return 'bg-danger';
    },
    
    // 编辑分类
    editCategory: function(categoryIndex) {
        const item = this.categorizedData[categoryIndex];
        if (!item) return;
        
        const categoryOptions = this.buildCategoryOptions();
        
        showModal('editCategoryModal', {
            title: '编辑分类',
            body: `
                <div class="edit-category-form">
                    <div class="mb-3">
                        <label class="form-label">物料名称</label>
                        <input type="text" class="form-control" value="${item.material_name || ''}" readonly>
                    </div>
                    
                    <div class="mb-3">
                        <label class="form-label">一级分类</label>
                        <select class="form-select" id="editLevel1" onchange="MaterialCategorization.updateSubCategories(1)">
                            <option value="">请选择一级分类</option>
                            ${Object.keys(this.categorySystem).map(level1 => `
                                <option value="${level1}" ${item.category_level_1 === level1 ? 'selected' : ''}>
                                    ${level1}
                                </option>
                            `).join('')}
                        </select>
                    </div>
                    
                    <div class="mb-3">
                        <label class="form-label">二级分类</label>
                        <select class="form-select" id="editLevel2" onchange="MaterialCategorization.updateSubCategories(2)">
                            <option value="">请先选择一级分类</option>
                        </select>
                    </div>
                    
                    <div class="mb-3">
                        <label class="form-label">三级分类</label>
                        <select class="form-select" id="editLevel3">
                            <option value="">请先选择二级分类</option>
                        </select>
                    </div>
                    
                    <div class="mt-3 text-end">
                        <button type="button" class="btn btn-secondary me-2" data-dismiss="modal">
                            取消
                        </button>
                        <button type="button" class="btn btn-primary" 
                                onclick="MaterialCategorization.saveEditedCategory(${categoryIndex})">
                            保存
                        </button>
                    </div>
                </div>
            `
        });
        
        // 初始化下级分类选项
        this.updateSubCategories(1);
        if (item.category_level_2) {
            setTimeout(() => {
                document.querySelector('#editLevel2').value = item.category_level_2;
                this.updateSubCategories(2);
                if (item.category_level_3) {
                    setTimeout(() => {
                        document.querySelector('#editLevel3').value = item.category_level_3;
                    }, 100);
                }
            }, 100);
        }
    },
    
    // 更新子分类选项
    updateSubCategories: function(level) {
        if (level === 1) {
            const level1Select = document.querySelector('#editLevel1');
            const level2Select = document.querySelector('#editLevel2');
            const level3Select = document.querySelector('#editLevel3');
            
            if (!level1Select || !level2Select || !level3Select) return;
            
            const selectedLevel1 = level1Select.value;
            
            // 清空下级选项
            level2Select.innerHTML = '<option value="">请选择二级分类</option>';
            level3Select.innerHTML = '<option value="">请先选择二级分类</option>';
            
            if (selectedLevel1 && this.categorySystem[selectedLevel1]) {
                Object.keys(this.categorySystem[selectedLevel1]).forEach(level2 => {
                    const option = document.createElement('option');
                    option.value = level2;
                    option.textContent = level2;
                    level2Select.appendChild(option);
                });
            }
        } else if (level === 2) {
            const level1Select = document.querySelector('#editLevel1');
            const level2Select = document.querySelector('#editLevel2');
            const level3Select = document.querySelector('#editLevel3');
            
            if (!level1Select || !level2Select || !level3Select) return;
            
            const selectedLevel1 = level1Select.value;
            const selectedLevel2 = level2Select.value;
            
            // 清空三级分类选项
            level3Select.innerHTML = '<option value="">请选择三级分类</option>';
            
            if (selectedLevel1 && selectedLevel2 && 
                this.categorySystem[selectedLevel1] && 
                this.categorySystem[selectedLevel1][selectedLevel2]) {
                
                this.categorySystem[selectedLevel1][selectedLevel2].forEach(level3 => {
                    const option = document.createElement('option');
                    option.value = level3;
                    option.textContent = level3;
                    level3Select.appendChild(option);
                });
            }
        }
    },
    
    // 保存编辑的分类
    saveEditedCategory: function(categoryIndex) {
        const level1 = document.querySelector('#editLevel1')?.value;
        const level2 = document.querySelector('#editLevel2')?.value;
        const level3 = document.querySelector('#editLevel3')?.value;
        
        if (!level1) {
            showNotification('请至少选择一级分类', 'warning');
            return;
        }
        
        // 更新分类数据
        this.categorizedData[categoryIndex].category_level_1 = level1;
        this.categorizedData[categoryIndex].category_level_2 = level2;
        this.categorizedData[categoryIndex].category_level_3 = level3;
        this.categorizedData[categoryIndex].confidence = 1.0; // 手动编辑设为最高置信度
        this.categorizedData[categoryIndex].edited = true;
        
        // 更新UI
        this.displayCategorizationResults({ categories: this.categorizedData });
        hideModal('editCategoryModal');
        
        showNotification('分类已更新', 'success');
        
        // 保存到会话
        saveSessionToLocal();
    },
    
    // 确认分类
    confirmCategory: function(categoryIndex) {
        const item = this.categorizedData[categoryIndex];
        if (!item) return;
        
        item.confirmed = true;
        
        // 更新UI
        const row = document.querySelector(`tr[data-category-id="${categoryIndex}"]`);
        if (row) {
            row.classList.add('table-success');
            const confirmBtn = row.querySelector('button[onclick*="confirmCategory"]');
            if (confirmBtn) {
                confirmBtn.textContent = '已确认';
                confirmBtn.disabled = true;
                confirmBtn.classList.remove('btn-outline-success');
                confirmBtn.classList.add('btn-success');
            }
        }
        
        showNotification('分类已确认', 'success', 2000);
        
        // 保存到会话
        saveSessionToLocal();
    },
    
    // 显示手动分类界面
    showManualCategorization: function() {
        showModal('manualCategorizeModal', {
            title: '手动分类',
            body: `
                <div class="manual-categorization">
                    <p>手动分类功能允许您直接为每个物料指定分类。</p>
                    <div class="alert alert-info">
                        <i class="fas fa-info-circle me-2"></i>
                        此功能正在开发中，敬请期待！
                    </div>
                    <div class="mt-3 text-end">
                        <button type="button" class="btn btn-secondary" data-dismiss="modal">
                            关闭
                        </button>
                    </div>
                </div>
            `
        });
    },
    
    // 显示分类错误
    displayCategorizationError: function(errorMessage) {
        const resultsContainer = document.querySelector('#categorizationResults');
        if (!resultsContainer) return;
        
        resultsContainer.innerHTML = `
            <div class="card">
                <div class="card-header bg-danger text-white">
                    <h6 class="mb-0">分类失败</h6>
                </div>
                <div class="card-body">
                    <div class="alert alert-danger">
                        <h6>错误信息:</h6>
                        <p>${errorMessage}</p>
                    </div>
                    <div class="d-flex gap-2">
                        <button type="button" class="btn btn-primary" onclick="MaterialCategorization.startCategorization()">
                            重新分类
                        </button>
                        <button type="button" class="btn btn-secondary" onclick="window.location.href='/matching?session_id=${getSessionId()}'">
                            返回上一步
                        </button>
                    </div>
                </div>
            </div>
        `;
    },
    
    // 导出分类结果
    exportCategories: function() {
        if (this.categorizedData.length === 0) {
            showNotification('没有可导出的分类结果', 'warning');
            return;
        }
        
        const csvData = this.convertCategoriesToCSV(this.categorizedData);
        const blob = new Blob([csvData], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        
        if (link.download !== undefined) {
            const url = URL.createObjectURL(blob);
            link.setAttribute('href', url);
            link.setAttribute('download', `categorization_results_${Date.now()}.csv`);
            link.style.visibility = 'hidden';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
        
        showNotification('分类结果已导出', 'success');
    },
    
    // 转换为CSV格式
    convertCategoriesToCSV: function(data) {
        const headers = ['物料名称', '规格', '制造商', '一级分类', '二级分类', '三级分类', '置信度', '确认状态'];
        const rows = data.map(item => [
            item.material_name || '',
            item.specification || '',
            item.manufacturer || '',
            item.category_level_1 || '',
            item.category_level_2 || '',
            item.category_level_3 || '',
            Math.round((item.confidence || 0) * 100) + '%',
            item.confirmed ? '已确认' : '未确认'
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
                    <h6>物料分类完成</h6>
                    <p class="text-muted">点击下方按钮进入决策支持阶段</p>
                    <button type="button" class="btn btn-primary btn-lg" onclick="MaterialCategorization.proceedToDecision()">
                        <i class="fas fa-arrow-right me-2"></i>
                        进入决策支持
                    </button>
                </div>
            </div>
        `;
    },
    
    // 继续到决策阶段
    proceedToDecision: function() {
        const sessionId = getSessionId();
        if (!sessionId) {
            showNotification('会话信息丢失', 'danger');
            return;
        }
        
        showNotification('正在跳转到决策支持...', 'info');
        setTimeout(() => {
            window.location.href = `/decision?session_id=${sessionId}`;
        }, 1000);
    }
};

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    if (window.location.pathname.includes('categorize')) {
        MaterialCategorization.init();
    }
});

// 导出到全局
window.MaterialCategorization = MaterialCategorization;