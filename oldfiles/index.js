export const role = document.location.pathname.includes('/seller') ? 'seller' : 'buyer';

import { initializeWebSocket } from './websocket.js';
import { loadChatHistory } from './common/chatHistory.js';

// Initialize when DOM is loaded
window.addEventListener('DOMContentLoaded', () => {
    initializeWebSocket(role);
    loadChatHistory();
});

export function getUserRole() {
    return document.location.pathname.includes('/seller') ? 'seller' : 'buyer';
}