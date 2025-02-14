import { handleStatusChange, updateStatus } from './seller/orderStatus.js';
import { respondToBargain, confirmPayment } from './seller/bargainResponse.js';
import { sendMessage } from './seller/sellerMessages.js';
import { handleFileSelect, displaySelectedFiles, removeSelectedFile, removeFile } from './common/fileHandling.js';
import { clearChat } from './common/chatHistory.js';
import { initializeWebSocket } from './websocket.js';
import { role } from './index.js';

window.addEventListener('DOMContentLoaded', () => {
    initializeWebSocket(role);
});

window.handleStatusChange = handleStatusChange;
window.updateStatus = updateStatus;
window.respondToBargain = respondToBargain;
window.confirmPayment = confirmPayment;
window.sendMessage = sendMessage;
window.handleFileSelect = handleFileSelect;
window.displaySelectedFiles = displaySelectedFiles;
window.removeSelectedFile = removeSelectedFile;
window.removeFile = removeFile;
window.clearChat = clearChat;