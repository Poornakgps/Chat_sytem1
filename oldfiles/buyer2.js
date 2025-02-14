import { sendBargainRequest } from './buyer/bargainRequest.js';
import { sendMessage } from './buyer/buyerMessages.js';
import { handleFileSelect, displaySelectedFiles, removeSelectedFile, removeFile } from './common/fileHandling.js';
import { clearChat } from './common/chatHistory.js';
import { initializeWebSocket } from './websocket.js';
import { role } from './index.js';

window.addEventListener('DOMContentLoaded', () => {
    initializeWebSocket(role);
});

window.sendBargainRequest = sendBargainRequest;
window.sendMessage = sendMessage;
window.handleFileSelect = handleFileSelect;
window.displaySelectedFiles = displaySelectedFiles;
window.removeSelectedFile = removeSelectedFile;
window.removeFile = removeFile;
window.clearChat = clearChat;