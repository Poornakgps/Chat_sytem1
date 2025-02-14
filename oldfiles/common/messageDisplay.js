
import {role} from '../../static/js/index.js';
import { loadChatHistory, clearChat, displayBargainMessage, displayBargainResponse } from './chatHistory.js';

export function displayMessage(data) {
    const messagesDiv = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    
    if (data.type === 'bargain') {
        // Only show bargain controls to seller
        if (role === 'seller') {
            messageDiv.className = 'bargain-request';
            messageDiv.innerHTML = `
                <p>New bargain request: $${data.amount}</p>
                <button onclick="respondToBargain(true, ${data.amount})">Accept</button>
                <button onclick="respondToBargain(false, ${data.amount})">Reject</button>
            `;
        } else {
            messageDiv.className = 'bargain-request';
            messageDiv.innerHTML = `
                <p>Bargain request sent: $${data.amount}</p>
                <p>Waiting for seller response...</p>
            `;
        }
    } else if (data.type === 'bargain_response') {
        messageDiv.className = `bargain-request ${data.approved ? 'bargain-approved' : 'bargain-rejected'}`;
        if (data.approved) {
            const chatId = Date.now();
            messageDiv.setAttribute('data-chat-id', chatId);
            messageDiv.innerHTML = `
                <p>Bargain Approved! Final amount: $${data.amount}</p>
                ${data.qr_code ? `
                    <div class="payment-section" id="payment-${chatId}">
                        <img src="${data.qr_code}" alt="Payment QR Code" style="width:200px;height:200px;margin:10px auto;display:block;">
                        <p>Please scan the QR code to make the payment</p>
                        ${role === 'seller' ? 
                            `<button onclick="confirmPayment(${chatId})">Confirm Payment</button>` : ''}
                    </div>
                ` : ''}
            `;
        } else {
            messageDiv.innerHTML = `
                <p>Bargain Rejected</p>
                <p>The seller has rejected your bargain request.</p>
            `;
        }
    } else {
        const isMyMessage = data.sender === role;
        messageDiv.className = `message ${data.sender}-message`;
        
        let messageContent = '';
        if (data.message) {
            messageContent += `<div class="message-content">${data.message}</div>`;
        }
        
        if (data.file_name) {
            messageContent += `
                <div class="file-container">
                    <img src="/static/uploads/${data.file_name}" class="file-preview" alt="Attached file">
                    ${isMyMessage ? `
                        <div class="remove-file" onclick="removeFile('${data.file_name}', this.parentElement)">×</div>
                    ` : ''}
                </div>
            `;
        }
        
        messageDiv.innerHTML = messageContent;
    }
    
    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}