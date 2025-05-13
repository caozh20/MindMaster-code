let isRefresh = false;

const heartbeatInterval = 1000; // 5 秒
let heartbeatTimer;

function sendHeartbeat() {
    const sidMatch = document.cookie.match(/sid=([^;]+)/);
    const sid = sidMatch ? sidMatch[1] : null;

    if (sid) {
        fetch('/heartbeat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ sid: sid }),
        })
        .then(response => response.json())
        .then(data => {
            // console.log('Heartbeat sent:', data);
        })
        .catch(error => {
            console.error('Heartbeat error:', error);
        });
    }
}

function startHeartbeat() {
    sendHeartbeat(); // 立即发送一次
    heartbeatTimer = setInterval(sendHeartbeat, heartbeatInterval);
}

function stopHeartbeat() {
    clearInterval(heartbeatTimer);
}

// 捕捉键盘快捷键刷新
window.addEventListener('keydown', function(e) {
    if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
        isRefresh = true;
    }
    if (e.key === 'F5') {
        isRefresh = true;
    }
});

window.addEventListener('beforeunload', function (e) {
    stopHeartbeat(); // 停止心跳
    const isReload = isPageReload();
    const sidMatch = document.cookie.match(/sid=([^;]+)/);
    const sid = sidMatch ? sidMatch[1] : null;

    if (sid && !userExit) {
        const data = {
            sid: sid,
            action: isRefresh ? 'refresh' : 'close' 
        };
        const jsonData = JSON.stringify(data);
        const blob = new Blob([jsonData], { type: 'application/json' });
        navigator.sendBeacon('/user_leave', blob);
        console.log(`发送 user_leave 请求，sid: ${sid}, action: ${data.action}`);
    }

    userExit = true;
});

function isPageReload() {
    const navigationEntries = performance.getEntriesByType("navigation");
    if (navigationEntries.length > 0) {
        return navigationEntries[0].type === 'reload';
    }
    // 兼容旧浏览器
    return performance.navigation.type === performance.navigation.TYPE_RELOAD;
}

window.addEventListener('load', function () {
    userExit = false;
    isRefresh = false;
    startHeartbeat();
});