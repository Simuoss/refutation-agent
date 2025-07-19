// ui/web/script.js

// 等待整个窗口加载完成
window.addEventListener('load', () => {
    // 可以在这里调用Python函数通知已加载完成 (未来功能)
});

// 这个函数将由Python调用，用于在UI上添加新消息
function addMessage(role, text) {
    const container = document.getElementById('chat-container');

    // 创建新的消息气泡div
    const bubble = document.createElement('div');
    bubble.classList.add('bubble', role); // 添加 'bubble' 和 'user'/'ai'/'status' 类

    // 防止HTML注入，纯文本显示
    const textNode = document.createTextNode(text);
    bubble.appendChild(textNode);
    
    // 将新气泡添加到容器中
    container.appendChild(bubble);

    // 自动滚动到底部，显示最新消息
    container.scrollTop = container.scrollHeight;
}