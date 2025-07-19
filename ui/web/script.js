// ui/web/script.js

let currentStreamingBubble = null;
let statusBubble = null;

// 等待整个窗口加载完成
window.addEventListener('load', () => {
    // 初始化状态
    showListeningStatus();
    
    // 初始化字体大小和窗口缩放功能
    initControls();
});

// 显示偷听状态
function showListeningStatus() {
    const container = document.getElementById('chat-container');
    
    // 移除之前的状态气泡
    if (statusBubble) {
        statusBubble.remove();
    }
    
    statusBubble = document.createElement('div');
    statusBubble.classList.add('bubble', 'status', 'listening');
    statusBubble.textContent = 'AI杠精偷听中... (点击关闭)';
    
    // 添加点击事件来关闭窗口
    statusBubble.addEventListener('click', () => {
        // 调用暴露给JS的Python API
        pywebview.api.destroy();
    });
    
    container.appendChild(statusBubble);
    scrollToBottom();
}

// 隐藏偷听状态
function hideListeningStatus() {
    if (statusBubble) {
        statusBubble.remove();
        statusBubble = null;
    }
}

// 添加用户消息（听到的内容）
function addUserMessage(text) {
    hideListeningStatus();
    
    const container = document.getElementById('chat-container');
    const bubble = document.createElement('div');
    bubble.classList.add('bubble', 'user');
    
    const textNode = document.createTextNode(text);
    bubble.appendChild(textNode);
    
    container.appendChild(bubble);
    scrollToBottom();
    
    // 清理旧消息，保持窗口整洁
    cleanupOldMessages();
}

// 开始AI流式回复
function startAIResponse() {
    const container = document.getElementById('chat-container');
    
    currentStreamingBubble = document.createElement('div');
    currentStreamingBubble.classList.add('bubble', 'ai', 'streaming');
    
    container.appendChild(currentStreamingBubble);
    scrollToBottom();
    
    return currentStreamingBubble;
}

// 追加AI回复内容（流式传输）
function appendAIResponse(text) {
    if (currentStreamingBubble) {
        // 移除光标效果，添加文本，然后重新添加光标效果
        currentStreamingBubble.classList.remove('streaming');
        currentStreamingBubble.textContent += text;
        currentStreamingBubble.classList.add('streaming');
        
        scrollToBottom();
    }
}

// 完成AI回复
function finishAIResponse() {
    if (currentStreamingBubble) {
        currentStreamingBubble.classList.remove('streaming');
        currentStreamingBubble = null;
        
        // 回复完成后，重新显示偷听状态
        setTimeout(() => {
            showListeningStatus();
        }, 1000);
        
        // 清理旧消息
        cleanupOldMessages();
    }
}

// 兼容旧的addMessage函数
function addMessage(role, text) {
    if (role === 'status') {
        if (text.includes('偷听中')) {
            showListeningStatus();
        }
    } else if (role === 'user') {
        addUserMessage(text);
    } else if (role === 'ai') {
        startAIResponse();
        appendAIResponse(text);
        finishAIResponse();
    }
}

// 自动滚动到底部
function scrollToBottom() {
    const container = document.getElementById('chat-container');
    container.scrollTop = container.scrollHeight;
}

// 清理旧消息，保持最近的几条
function cleanupOldMessages() {
    const container = document.getElementById('chat-container');
    const bubbles = container.querySelectorAll('.bubble:not(.status)');
    
    // 保留最近的6条消息（3对对话）
    const maxMessages = 6;
    if (bubbles.length > maxMessages) {
        for (let i = 0; i < bubbles.length - maxMessages; i++) {
            bubbles[i].style.animation = 'slideOut 0.3s ease-in';
            setTimeout(() => {
                if (bubbles[i].parentNode) {
                    bubbles[i].remove();
                }
            }, 300);
        }
    }
}

// 添加滑出动画
const style = document.createElement('style');
style.textContent = `
@keyframes slideOut {
    from {
        opacity: 1;
        transform: translateY(0);
        height: auto;
        margin-bottom: 6px;
    }
    to {
        opacity: 0;
        transform: translateY(-10px);
        height: 0;
        margin-bottom: 0;
    }
}
`;
document.head.appendChild(style);

// 错误处理
window.addEventListener('error', (e) => {
    console.error('JavaScript错误:', e.error);
});

// 初始化控制按钮
function initControls() {
    const decreaseFontBtn = document.getElementById('decrease-font');
    const increaseFontBtn = document.getElementById('increase-font');
    const resizeHandle = document.querySelector('.resize-handle');
    
    // 字体大小控制
    decreaseFontBtn.addEventListener('click', () => changeFontSize(-1));
    increaseFontBtn.addEventListener('click', () => changeFontSize(1));
    
    // 窗口缩放控制
    let isResizing = false;
    let lastX, lastY;

    resizeHandle.addEventListener('mousedown', (e) => {
        isResizing = true;
        lastX = e.screenX;
        lastY = e.screenY;
        document.body.style.cursor = 'nwse-resize';
        e.preventDefault(); // 防止拖动时选中文本
    });

    window.addEventListener('mousemove', (e) => {
        if (!isResizing) return;
        
        const deltaX = e.screenX - lastX;
        const deltaY = e.screenY - lastY;
        
        pywebview.api.resize(deltaX, deltaY);
        
        lastX = e.screenX;
        lastY = e.screenY;
    });

    window.addEventListener('mouseup', () => {
        if (isResizing) {
            isResizing = false;
            document.body.style.cursor = 'default'; // 恢复鼠标样式
        }
    });
}

// 改变字体大小
function changeFontSize(step) {
    const root = document.documentElement;
    const currentSize = parseFloat(getComputedStyle(root).getPropertyValue('--base-font-size'));
    const newSize = Math.max(10, Math.min(20, currentSize + step)); // 限制字体大小在10px到20px之间
    root.style.setProperty('--base-font-size', `${newSize}px`);
}
