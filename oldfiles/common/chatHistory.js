import { displayMessage } from './messageDisplay.js';

import { getUserRole } from '../../static/js/index.js';

import {role} from '../index/js';
export async function loadChatHistory() {
    const messagesDiv = document.getElementById('chatMessages');
    messagesDiv.innerHTML = '';
    
    try {
        const response = await fetch(`/${role}/chat_history?role=${role}`);
        if (response.ok) {
            const data = await response.json();
            if (Array.isArray(data.history)) {
                data.history.forEach(msg => {
                    if (msg.is_bargain) {
                        // Use existing displayBargainMessage function
                        displayBargainMessage({
                            type: 'bargain',
                            amount: msg.bargain_amount
                        });
                    } else if (msg.bargain_status) {
                        // Use existing displayBargainResponse function
                        displayBargainResponse({
                            type: msg.bargain_status,
                            amount: msg.bargain_amount,
                            qr_code: msg.payment_qr_code,
                            approved: msg.bargain_status === 'approved'
                        });
                    } else {
                        // Use existing displayMessage function
                        displayMessage({
                            sender: msg.sender,
                            message: msg.message,
                            file_name: msg.file_name
                        });
                    }
                });
                
                // Scroll to bottom after loading history
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            }
        }
    } catch (error) {
        console.error('Error loading chat history:', error);
        const errorDiv = document.createElement('div');
        errorDiv.className = 'system-message error';
        errorDiv.textContent = 'Failed to load chat history';
        messagesDiv.appendChild(errorDiv);
    }
}

export async function clearChat() {
    const role = getUserRole();
    if (!confirm('Are you sure you want to clear the chat history? This cannot be undone.')) {
        return;
    }
    
    try {
        const response = await fetch(`/${role}/clear_chat`, {
            method: 'POST'
        });
        
        if (response.ok) {
            await loadChatHistory();
        }
    } catch (error) {
        console.error('Error clearing chat history:', error);
    }
}

export function displayBargainMessage(data) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'bargain-request';
    
    if (role === 'seller') {
        messageDiv.innerHTML = `
            <p>Bargain request: $${data.amount}</p>
            <button onclick="respondToBargain(true, ${data.amount})">Accept</button>
            <button onclick="respondToBargain(false, ${data.amount})">Reject</button>
        `;
    } else {
        messageDiv.innerHTML = `
            <p>Bargain request sent: $${data.amount}</p>
            <p>Waiting for seller response...</p>
        `;
    }
    
    document.getElementById('chatMessages').appendChild(messageDiv);
}

export function displayBargainResponse(data) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `bargain-request ${data.approved ? 'bargain-approved' : 'bargain-rejected'}`;
    
    const chatId = data.chat_id || Date.now();
    messageDiv.setAttribute('data-chat-id', chatId);
    
    if (data.approved) {
        messageDiv.innerHTML = `
            <p>Bargain Approved! Final amount: $${data.amount}</p>
            ${data.qr_code ? `
                <div class="payment-section" id="payment-${chatId}">
                    <img src="${data.qr_code}" alt="Payment QR Code" style="width:200px;height:200px;margin:10px auto;display:block;">
                    <p>Please scan the QR code to make the payment</p>
                    ${role === 'seller' ? `<button onclick="confirmPayment(${chatId})">Confirm Payment</button>` : ''}
                </div>
            ` : ''}
        `;
    } else {
        messageDiv.innerHTML = `
            <p>Bargain Rejected</p>
            <p>The seller has rejected your bargain request.</p>
        `;
    }
    
    document.getElementById('chatMessages').appendChild(messageDiv);
}