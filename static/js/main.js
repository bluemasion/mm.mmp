/* MMP物料主数据管理智能应用 - 主JavaScript文件 */

/* ========================================
   全局变量和配置
   ======================================== */
const MMP = {
    // API端点配置
    API: {
        BASE_URL: '',
        UPLOAD: '/api/upload',
        EXTRACT: '/api/extract_parameters',
        MATCH: '/api/match',
        CATEGORIZE: '/api/categorize',
        DECISION: '/api/decision',
        DEBUG_SESSION: '/api/debug/session'
    },
    
    // 当前会话信息
    session: {
        id: null,
        status: null,
        data: {}
    },
    
    // 配置选项
    config: {
        maxFileSize: 50 * 1024 * 1024, // 50MB
        allowedTypes: ['.xlsx', '.xls', '.csv'],
        debugMode: false
    }
};

/* ========================================
   工具函数
   ======================================== */

/**
 * 显示通知消息
 */
function showNotification(message, type = 'info', duration = 3000) {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} notification`;
    notification.innerHTML = `
        <span>${message}</span>
        <button type="button" class="btn-close" onclick="this.parentElement.remove()"></button>
    `;
    
    // 添加到页面顶部
    const container = document.querySelector('.container') || document.body;
    container.insertBefore(notification, container.firstChild);
    
    // 自动消失
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, duration);
}

/**
 * 显示加载状态
 */
function showLoading(element, text = '处理中...') {
    if (typeof element === 'string') {
        element = document.querySelector(element);
    }
    
    if (element) {
        element.innerHTML = `
            <div class="d-flex align-items-center justify-content-center p-4">
                <div class="spinner-border text-primary me-3" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <span>${text}</span>
            </div>
        `;
    }
}

/**
 * 隐藏加载状态
 */
function hideLoading(element) {
    if (typeof element === 'string') {
        element = document.querySelector(element);
    }
    
    if (element && element.querySelector('.spinner-border')) {
        element.innerHTML = '';
    }
}

/**
 * 格式化文件大小
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * 验证文件类型
 */
function validateFileType(filename) {
    const ext = '.' + filename.split('.').pop().toLowerCase();
    return MMP.config.allowedTypes.includes(ext);
}

/**
 * 生成UUID
 */
function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

/**
 * 安全的AJAX请求
 */
async function safeRequest(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            return await response.json();
        } else {
            return await response.text();
        }
    } catch (error) {
        console.error('请求失败:', error);
        showNotification(`请求失败: ${error.message}`, 'danger');
        throw error;
    }
}

/* ========================================
   文件上传功能
   ======================================== */

/**
 * 初始化文件上传
 */
function initFileUpload() {
    const uploadArea = document.querySelector('.file-upload-area');
    const fileInput = document.querySelector('#fileInput');
    
    if (!uploadArea || !fileInput) return;
    
    // 点击上传区域触发文件选择
    uploadArea.addEventListener('click', () => {
        fileInput.click();
    });
    
    // 拖拽上传
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });
    
    uploadArea.addEventListener('dragleave', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileSelect(files[0]);
        }
    });
    
    // 文件选择处理
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileSelect(e.target.files[0]);
        }
    });
}

/**
 * 处理文件选择
 */
function handleFileSelect(file) {
    // 验证文件类型
    if (!validateFileType(file.name)) {
        showNotification(
            `不支持的文件类型。请选择 ${MMP.config.allowedTypes.join(', ')} 格式的文件。`,
            'warning'
        );
        return;
    }
    
    // 验证文件大小
    if (file.size > MMP.config.maxFileSize) {
        showNotification(
            `文件过大。最大支持 ${formatFileSize(MMP.config.maxFileSize)} 的文件。`,
            'warning'
        );
        return;
    }
    
    // 显示文件信息
    displayFileInfo(file);
    
    // 上传文件
    uploadFile(file);
}

/**
 * 显示文件信息
 */
function displayFileInfo(file) {
    const infoContainer = document.querySelector('#fileInfo');
    if (!infoContainer) return;
    
    infoContainer.innerHTML = `
        <div class="card">
            <div class="card-body">
                <h6 class="card-title">已选择文件</h6>
                <p class="card-text">
                    <strong>文件名:</strong> ${file.name}<br>
                    <strong>大小:</strong> ${formatFileSize(file.size)}<br>
                    <strong>类型:</strong> ${file.type || '未知'}
                </p>
                <div class="progress" id="uploadProgress">
                    <div class="progress-bar" role="progressbar" style="width: 0%">0%</div>
                </div>
            </div>
        </div>
    `;
}

/**
 * 上传文件
 */
async function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    // 生成会话ID
    MMP.session.id = generateUUID();
    formData.append('session_id', MMP.session.id);
    
    try {
        showNotification('开始上传文件...', 'info');
        
        const response = await fetch(MMP.API.UPLOAD, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification('文件上传成功！', 'success');
            MMP.session.data = result.data;
            
            // 跳转到参数提取页面
            setTimeout(() => {
                window.location.href = `/extract_parameters?session_id=${MMP.session.id}`;
            }, 1500);
        } else {
            showNotification(`上传失败: ${result.message}`, 'danger');
        }
    } catch (error) {
        console.error('上传失败:', error);
        showNotification('文件上传失败，请重试。', 'danger');
    }
}

/* ========================================
   数据表格功能
   ======================================== */

/**
 * 初始化数据表格
 */
function initDataTable() {
    const tables = document.querySelectorAll('.data-table');
    
    tables.forEach(table => {
        // 添加排序功能
        const headers = table.querySelectorAll('th[data-sortable]');
        headers.forEach(header => {
            header.style.cursor = 'pointer';
            header.addEventListener('click', () => {
                sortTable(table, header);
            });
        });
        
        // 添加搜索功能
        const searchInput = table.parentElement.querySelector('.table-search');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                filterTable(table, e.target.value);
            });
        }
    });
}

/**
 * 表格排序
 */
function sortTable(table, header) {
    const columnIndex = Array.from(header.parentElement.children).indexOf(header);
    const rows = Array.from(table.querySelectorAll('tbody tr'));
    const isAscending = header.classList.contains('sort-asc');
    
    // 清除其他列的排序标记
    header.parentElement.querySelectorAll('th').forEach(th => {
        th.classList.remove('sort-asc', 'sort-desc');
    });
    
    // 设置当前列的排序标记
    header.classList.add(isAscending ? 'sort-desc' : 'sort-asc');
    
    // 排序行
    rows.sort((a, b) => {
        const aValue = a.children[columnIndex].textContent.trim();
        const bValue = b.children[columnIndex].textContent.trim();
        
        if (isAscending) {
            return bValue.localeCompare(aValue, 'zh-CN', { numeric: true });
        } else {
            return aValue.localeCompare(bValue, 'zh-CN', { numeric: true });
        }
    });
    
    // 重新插入排序后的行
    const tbody = table.querySelector('tbody');
    rows.forEach(row => tbody.appendChild(row));
}

/**
 * 表格过滤
 */
function filterTable(table, searchTerm) {
    const rows = table.querySelectorAll('tbody tr');
    const term = searchTerm.toLowerCase();
    
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(term) ? '' : 'none';
    });
}

/* ========================================
   模态框功能
   ======================================== */

/**
 * 显示模态框
 */
function showModal(modalId, options = {}) {
    const modal = document.getElementById(modalId);
    if (!modal) return;
    
    modal.classList.add('show');
    document.body.style.overflow = 'hidden';
    
    // 设置标题和内容
    if (options.title) {
        const titleElement = modal.querySelector('.modal-title');
        if (titleElement) titleElement.textContent = options.title;
    }
    
    if (options.body) {
        const bodyElement = modal.querySelector('.modal-body');
        if (bodyElement) bodyElement.innerHTML = options.body;
    }
    
    // 添加关闭事件
    const closeButtons = modal.querySelectorAll('[data-dismiss="modal"]');
    closeButtons.forEach(btn => {
        btn.onclick = () => hideModal(modalId);
    });
    
    // 点击背景关闭
    modal.onclick = (e) => {
        if (e.target === modal) {
            hideModal(modalId);
        }
    };
}

/**
 * 隐藏模态框
 */
function hideModal(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) return;
    
    modal.classList.remove('show');
    document.body.style.overflow = '';
}

/* ========================================
   会话管理
   ======================================== */

/**
 * 获取URL参数中的会话ID
 */
function getSessionId() {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('session_id') || MMP.session.id;
}

/**
 * 保存会话数据到本地存储
 */
function saveSessionToLocal() {
    if (MMP.session.id) {
        localStorage.setItem(`mmp_session_${MMP.session.id}`, JSON.stringify(MMP.session));
    }
}

/**
 * 从本地存储加载会话数据
 */
function loadSessionFromLocal(sessionId) {
    const sessionData = localStorage.getItem(`mmp_session_${sessionId}`);
    if (sessionData) {
        MMP.session = JSON.parse(sessionData);
        return true;
    }
    return false;
}

/**
 * 调试会话信息
 */
async function debugSession(sessionId = null) {
    if (!sessionId) sessionId = getSessionId();
    if (!sessionId) {
        showNotification('没有找到会话ID', 'warning');
        return;
    }
    
    try {
        const response = await safeRequest(`${MMP.API.DEBUG_SESSION}?session_id=${sessionId}`);
        console.log('会话调试信息:', response);
        
        // 显示调试信息
        showModal('debugModal', {
            title: '会话调试信息',
            body: `<pre>${JSON.stringify(response, null, 2)}</pre>`
        });
    } catch (error) {
        showNotification('获取调试信息失败', 'danger');
    }
}

/* ========================================
   页面初始化
   ======================================== */

/**
 * 页面加载完成后初始化
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('MMP系统加载完成');
    
    // 初始化各种功能
    initFileUpload();
    initDataTable();
    
    // 设置会话ID
    const sessionId = getSessionId();
    if (sessionId) {
        MMP.session.id = sessionId;
        loadSessionFromLocal(sessionId);
    }
    
    // 添加调试功能（开发模式）
    if (MMP.config.debugMode) {
        console.log('调试模式已启用');
        
        // 添加调试按钮
        const debugBtn = document.createElement('button');
        debugBtn.textContent = 'Debug';
        debugBtn.className = 'btn btn-sm btn-secondary position-fixed';
        debugBtn.style.cssText = 'top: 10px; right: 10px; z-index: 9999;';
        debugBtn.onclick = () => debugSession();
        document.body.appendChild(debugBtn);
    }
    
    // 全局错误处理
    window.addEventListener('error', (e) => {
        console.error('页面错误:', e.error);
        if (MMP.config.debugMode) {
            showNotification(`页面错误: ${e.message}`, 'danger');
        }
    });
    
    // 添加页面动画
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        card.style.animationDelay = `${index * 0.1}s`;
        card.classList.add('slide-in-up');
    });
    
    console.log('MMP系统初始化完成');
});

/* ========================================
   导出供外部使用的函数
   ======================================== */
window.MMP = MMP;
window.showNotification = showNotification;
window.showModal = showModal;
window.hideModal = hideModal;
window.debugSession = debugSession;