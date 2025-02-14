import { displayMessage } from './common/messageDisplay.js';
import { loadChatHistory } from './common/chatHistory.js';

let ws;


export const initializeWebSocket = (role) => {
    ws = new WebSocket(`ws://${window.location.host}/ws/${role}`);

    ws.onopen = function () {
        console.log(`Connected as ${role}`);
        setTimeout(loadChatHistory, 100);
    };

    ws.onmessage = function (event) {
        const data = JSON.parse(event.data);
        displayMessage(data);
    };

    ws.onclose = function () {
        console.log('Connection closed. Attempting to reconnect...');
        setTimeout(() => {
            initializeWebSocket(role);
        }, 3000);
    };

    return ws;
};


export const getWebSocket = () => ws;