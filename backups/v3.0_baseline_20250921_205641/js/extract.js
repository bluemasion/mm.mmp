/* 参数提取页面专用JavaScript */

/**
 * 参数提取相关功能
 */
const ParameterExtraction = {
    // 当前提取的参数
    extractedParams: {},
    
    // 参数验证规则
    validationRules: {
        materialName: {
            required: true,
            minLength: 2,
            message: '物料名称至少需要2个字符'
        },
        specification: {
            required: false,
            pattern: /^[A-Za-z0-9\s\-\*\/]+$/,
            message: '规格格式不正确'
        },
        manufacturer: {
            required: false,
            minLength: 2,
            message: '制造商名称至少需要2个字符'
        }
    },
    
    // 初始化页面
    init: function() {
        this.bindEvents();
        this.loadSessionData();
        this.startAutoExtraction();
    },
    
    // 绑定事件
    bindEvents: function() {
        // 手动提取按钮
        const extractBtn = document.querySelector('#extractBtn');
        if (extractBtn) {
            extractBtn.addEventListener('click', () => {
                this.extractParameters();
            });
        }
        
        // 参数编辑
        const paramInputs = document.querySelectorAll('.param-input');
        paramInputs.forEach(input => {
            input.addEventListener('change', (e) => {
                this.updateParameter(e.target.name, e.target.value);
            });
        });
        
        // 下一步按钮
        const nextBtn = document.querySelector('#nextBtn');
        if (nextBtn) {
            nextBtn.addEventListener('click', () => {
                this.proceedToMatching();
            });
        }
        
        // 参数验证
        const validateBtn = document.querySelector('#validateBtn');
        if (validateBtn) {
            validateBtn.addEventListener('click', () => {
                this.validateAllParameters();
            });
        }
    },
    
    // 加载会话数据
    loadSessionData: function() {
        const sessionId = getSessionId();
        if (!sessionId) {
            showNotification('未找到会话信息，请重新上传文件', 'warning');
            setTimeout(() => {
                window.location.href = '/';
            }, 2000);
            return;
        }
        
        // 从本地存储或服务器加载数据
        if (loadSessionFromLocal(sessionId)) {
            this.displaySessionInfo();
        } else {
            this.loadSessionFromServer(sessionId);
        }
    },
    
    // 从服务器加载会话
    loadSessionFromServer: async function(sessionId) {
        try {
            showLoading('#sessionInfo', '加载会话数据...');
            
            const response = await safeRequest(`/api/session/${sessionId}`);
            if (response.success) {
                MMP.session.data = response.data;
                this.displaySessionInfo();
                saveSessionToLocal();
            } else {
                showNotification('加载会话数据失败', 'danger');
            }
        } catch (error) {
            showNotification('加载会话数据时出错', 'danger');
        } finally {
            hideLoading('#sessionInfo');
        }
    },
    
    // 显示会话信息
    displaySessionInfo: function() {
        const sessionInfo = document.querySelector('#sessionInfo');
        if (!sessionInfo || !MMP.session.data) return;
        
        const data = MMP.session.data;
        sessionInfo.innerHTML = `
            <div class="card">
                <div class="card-header">
                    <h6 class="mb-0">文件信息</h6>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-6">
                            <p><strong>文件名:</strong> ${data.filename || '未知'}</p>
                            <p><strong>上传时间:</strong> ${new Date(data.upload_time || Date.now()).toLocaleString()}</p>
                        </div>
                        <div class="col-md-6">
                            <p><strong>数据行数:</strong> ${data.row_count || 0}</p>
                            <p><strong>检测到的列:</strong> ${data.columns ? data.columns.length : 0}</p>
                        </div>
                    </div>
                    ${data.columns ? `
                        <div class="mt-3">
                            <h6>检测到的数据列:</h6>
                            <div class="d-flex flex-wrap gap-2">
                                ${data.columns.map(col => `
                                    <span class="badge bg-primary">${col}</span>
                                `).join('')}
                            </div>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    },
    
    // 开始自动参数提取
    startAutoExtraction: function() {
        setTimeout(() => {
            this.extractParameters();
        }, 1000);
    },
    
    // 提取参数
    extractParameters: async function() {
        const sessionId = getSessionId();
        if (!sessionId) {
            showNotification('会话ID不存在', 'warning');
            return;
        }
        
        try {
            showLoading('#extractionResults', '正在提取参数...');
            showNotification('开始参数提取，请稍候...', 'info');
            
            const response = await safeRequest(MMP.API.EXTRACT, {
                method: 'POST',
                body: JSON.stringify({
                    session_id: sessionId,
                    extraction_method: 'auto'
                })
            });
            
            if (response.success) {
                this.extractedParams = response.data.parameters || {};
                this.displayExtractionResults(response.data);
                showNotification('参数提取完成！', 'success');
                
                // 保存到会话
                MMP.session.data.extracted_params = this.extractedParams;
                saveSessionToLocal();
            } else {
                showNotification(`参数提取失败: ${response.message}`, 'danger');
                this.displayExtractionError(response.message);
            }
        } catch (error) {
            console.error('参数提取错误:', error);
            showNotification('参数提取过程中出现错误', 'danger');
            this.displayExtractionError(error.message);
        } finally {
            hideLoading('#extractionResults');
        }
    },
    
    // 显示提取结果
    displayExtractionResults: function(data) {
        const resultsContainer = document.querySelector('#extractionResults');
        if (!resultsContainer) return;
        
        const params = data.parameters || {};
        const stats = data.statistics || {};
        
        resultsContainer.innerHTML = `
            <div class="card">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <h6 class="mb-0">参数提取结果</h6>
                    <button type="button" class="btn btn-sm btn-outline-primary" onclick="ParameterExtraction.validateAllParameters()">
                        验证参数
                    </button>
                </div>
                <div class="card-body">
                    ${Object.keys(params).length > 0 ? `
                        <div class="row">
                            ${this.renderParameterInputs(params)}
                        </div>
                        <div class="mt-4">
                            <h6>提取统计:</h6>
                            <div class="row">
                                <div class="col-md-3">
                                    <div class="stat-card">
                                        <div class="stat-number">${stats.total_records || 0}</div>
                                        <div class="stat-label">总记录数</div>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="stat-card">
                                        <div class="stat-number">${stats.valid_records || 0}</div>
                                        <div class="stat-label">有效记录</div>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="stat-card">
                                        <div class="stat-number">${stats.extracted_fields || 0}</div>
                                        <div class="stat-label">提取字段</div>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="stat-card">
                                        <div class="stat-number">${Math.round((stats.confidence || 0) * 100)}%</div>
                                        <div class="stat-label">置信度</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    ` : `
                        <div class="alert alert-warning">
                            <h6>未能提取到有效参数</h6>
                            <p>可能的原因：</p>
                            <ul>
                                <li>文件格式不符合要求</li>
                                <li>数据列名称不标准</li>
                                <li>文件内容为空或格式错误</li>
                            </ul>
                            <button type="button" class="btn btn-primary btn-sm" onclick="ParameterExtraction.extractParameters()">
                                重新提取
                            </button>
                        </div>
                    `}
                </div>
            </div>
        `;
        
        // 重新绑定事件
        this.bindParameterEvents();
        
        // 显示下一步按钮
        this.showNextButton();
    },
    
    // 渲染参数输入框
    renderParameterInputs: function(params) {
        const paramTypes = {
            'material_name': '物料名称',
            'specification': '规格',
            'manufacturer': '制造商',
            'model': '型号',
            'category': '分类',
            'price': '价格',
            'unit': '单位'
        };
        
        return Object.entries(params).map(([key, values]) => {
            const label = paramTypes[key] || key;
            const sampleValues = Array.isArray(values) ? values.slice(0, 5) : [values];
            
            return `
                <div class="col-md-6 mb-3">
                    <div class="parameter-group">
                        <label class="form-label">${label}</label>
                        <div class="parameter-preview">
                            <div class="sample-values">
                                ${sampleValues.map(val => `
                                    <span class="badge bg-light text-dark">${val || '空值'}</span>
                                `).join('')}
                            </div>
                            <div class="parameter-controls mt-2">
                                <select class="form-select form-select-sm param-mapping" name="${key}">
                                    <option value="">选择映射字段</option>
                                    ${(MMP.session.data.columns || []).map(col => `
                                        <option value="${col}" ${col.toLowerCase().includes(key) ? 'selected' : ''}>
                                            ${col}
                                        </option>
                                    `).join('')}
                                </select>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    },
    
    // 绑定参数事件
    bindParameterEvents: function() {
        const mappingSelects = document.querySelectorAll('.param-mapping');
        mappingSelects.forEach(select => {
            select.addEventListener('change', (e) => {
                this.updateParameterMapping(e.target.name, e.target.value);
            });
        });
    },
    
    // 更新参数映射
    updateParameterMapping: function(paramName, columnName) {
        if (!MMP.session.data.parameter_mappings) {
            MMP.session.data.parameter_mappings = {};
        }
        
        MMP.session.data.parameter_mappings[paramName] = columnName;
        saveSessionToLocal();
        
        showNotification(`${paramName} 已映射到 ${columnName}`, 'info', 2000);
    },
    
    // 显示提取错误
    displayExtractionError: function(errorMessage) {
        const resultsContainer = document.querySelector('#extractionResults');
        if (!resultsContainer) return;
        
        resultsContainer.innerHTML = `
            <div class="card">
                <div class="card-header bg-danger text-white">
                    <h6 class="mb-0">参数提取失败</h6>
                </div>
                <div class="card-body">
                    <div class="alert alert-danger">
                        <h6>错误信息:</h6>
                        <p>${errorMessage}</p>
                    </div>
                    <div class="d-flex gap-2">
                        <button type="button" class="btn btn-primary" onclick="ParameterExtraction.extractParameters()">
                            重新提取
                        </button>
                        <button type="button" class="btn btn-secondary" onclick="window.location.href='/'">
                            返回首页
                        </button>
                    </div>
                </div>
            </div>
        `;
    },
    
    // 验证所有参数
    validateAllParameters: function() {
        const isValid = this.validateParameters(this.extractedParams);
        
        if (isValid) {
            showNotification('所有参数验证通过！', 'success');
            this.showNextButton();
        } else {
            showNotification('参数验证失败，请检查并修正', 'warning');
        }
        
        return isValid;
    },
    
    // 参数验证
    validateParameters: function(params) {
        let isValid = true;
        const errors = [];
        
        Object.entries(this.validationRules).forEach(([paramName, rule]) => {
            const value = params[paramName];
            
            // 必填验证
            if (rule.required && (!value || value.length === 0)) {
                errors.push(`${paramName}: 此字段为必填项`);
                isValid = false;
            }
            
            // 长度验证
            if (value && rule.minLength && value.length < rule.minLength) {
                errors.push(`${paramName}: ${rule.message}`);
                isValid = false;
            }
            
            // 格式验证
            if (value && rule.pattern && !rule.pattern.test(value)) {
                errors.push(`${paramName}: ${rule.message}`);
                isValid = false;
            }
        });
        
        if (errors.length > 0) {
            console.log('参数验证错误:', errors);
        }
        
        return isValid;
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
                    <h6>参数提取完成</h6>
                    <p class="text-muted">点击下方按钮继续进行物料匹配</p>
                    <button type="button" class="btn btn-primary btn-lg" onclick="ParameterExtraction.proceedToMatching()">
                        <i class="fas fa-arrow-right me-2"></i>
                        进入物料匹配
                    </button>
                </div>
            </div>
        `;
    },
    
    // 继续到匹配阶段
    proceedToMatching: function() {
        const sessionId = getSessionId();
        if (!sessionId) {
            showNotification('会话信息丢失', 'danger');
            return;
        }
        
        if (Object.keys(this.extractedParams).length === 0) {
            showNotification('请先完成参数提取', 'warning');
            return;
        }
        
        showNotification('正在跳转到物料匹配...', 'info');
        setTimeout(() => {
            window.location.href = `/matching?session_id=${sessionId}`;
        }, 1000);
    }
};

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    if (window.location.pathname.includes('extract_parameters')) {
        ParameterExtraction.init();
    }
});

// 导出到全局
window.ParameterExtraction = ParameterExtraction;