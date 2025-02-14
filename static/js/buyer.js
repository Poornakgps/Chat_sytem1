let selectedFiles = [];
const role = document.location.pathname.includes('/seller') ? 'seller' : 'buyer';

let ws = new WebSocket(`ws://${window.location.host}/ws/buyer`);

ws.onopen = function() {
    console.log(`Connected as ${role}`);
    loadChatHistory();
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    displayMessage(data);
};


ws.onclose = function() {
    console.log('Connection closed. Attempting to reconnect...');
    setTimeout(() => {
        ws = new WebSocket(`ws://${window.location.host}/ws/${role}`);
        ws.onopen = function() {
            console.log(`Reconnected as ${role}`);
            loadChatHistory();
        };
    }, 3000);
};
function displayMessage(data) {
    const messagesDiv = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    
    if (data.type === 'bargain') {
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


async function removeFile(fileName, container) {
    if (!container.closest(`.${role}-message`)) return;
    
    if (confirm('Are you sure you want to remove this file?')) {
        try {
            const response = await fetch('/remove_file', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    file_name: fileName,
                    sender: role
                })
            });
            
            if (response.ok) {
                container.remove();
            }
        } catch (error) {
            console.error('Error removing file:', error);
        }
    }
}
async function confirmPayment(chatId) {
    try {
        const formData = new FormData();
        formData.append('chat_id', chatId);
        
        await fetch('/seller/confirm_payment', {
            method: 'POST',
            body: formData
        });
    } catch (error) {
        console.error('Error confirming payment:', error);
    }
}
async function sendMessage() {
    const input = document.getElementById('messageInput');
    const message = input.value;
    
    if (!message && selectedFiles.length === 0) return;
    
    const formData = new FormData();
    formData.append('message', message);
    
    selectedFiles.forEach(file => {
        formData.append('files', file);  // 🔹 FIX: Use 'files' instead of 'file'
    });

    const endpoint = `/${role}/send_message`;
    try {
        await fetch(endpoint, {
            method: 'POST',
            body: formData
        });

        input.value = '';
        selectedFiles = [];
        displaySelectedFiles();
        document.getElementById('fileInput').value = '';
    } catch (error) {
        console.error('Error sending message:', error);
    }
}

async function sendBargainRequest() {
    const amount = document.getElementById('bargainAmount').value;
    
    const formData = new FormData();
    formData.append('amount', amount);
    
    await fetch('/buyer/bargain', {
        method: 'POST',
        body: formData
    });
    
    document.getElementById('bargainAmount').value = '';
}

function handleFileSelect() {
    const fileInput = document.getElementById('fileInput');
    selectedFiles = [...Array.from(fileInput.files)];
    displaySelectedFiles();
}

function displaySelectedFiles() {
    const selectedFilesDiv = document.getElementById('selectedFiles');
    selectedFilesDiv.innerHTML = '';
    
    selectedFiles.forEach((file, index) => {
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item';
        fileItem.innerHTML = `
            ${file.name}
            <span class="remove-file" onclick="removeSelectedFile(${index})">×</span>
        `;
        selectedFilesDiv.appendChild(fileItem);
    });
}
        
function removeSelectedFile(index) {
    selectedFiles.splice(index, 1);
    displaySelectedFiles();
}

async function removeAttachment(fileName, element) {
    if (!confirm('Are you sure you want to remove this attachment?')) return;
    
    try {
        const response = await fetch('/remove_file', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                file_name: fileName,
                sender: '${role}'
            })
        });
        
        if (response.ok) {
            element.closest('.attachment').remove();
        }
    } catch (error) {
        console.error('Error removing attachment:', error);
    }
}
window.addEventListener('DOMContentLoaded', loadChatHistory);

async function loadChatHistory() {
    const messagesDiv = document.getElementById('chatMessages');
    messagesDiv.innerHTML = '';
    
    try {
        const response = await fetch(`/${role}/chat_history?role=${role}`);
        if (response.ok) {
            const data = await response.json();
            if (Array.isArray(data.history)) {
                data.history.forEach(msg => {
                    if (msg.is_bargain) {
                        displayBargainMessage({
                            type: 'bargain',
                            amount: msg.bargain_amount
                        });
                    } else if (msg.bargain_status) {
                        displayBargainResponse({
                            type: msg.bargain_status,
                            amount: msg.bargain_amount,
                            qr_code: msg.payment_qr_code,
                            approved: msg.bargain_status === 'approved'
                        });
                    } else {
                        displayMessage({
                            sender: msg.sender,
                            message: msg.message,
                            file_name: msg.file_name
                        });
                    }
                });
                
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

function displayBargainMessage(data) {
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

function displayBargainResponse(data) {
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

async function clearChat() {
    if (!confirm('Are you sure you want to clear the chat history? This cannot be undone.')) {
        return;
    }
    
    try {
        const response = await fetch(`/${role}/clear_chat`, {
            method: 'POST',
            headers: {
                'Accept': 'application/json'
            }
        });
        
        if (response.ok) {
            await loadChatHistory();
        } else {
            throw new Error('Failed to clear chat history');
        }
    } catch (error) {
        console.error('Error clearing chat history:', error);
        alert('Failed to clear chat history. Please try again.');
    }
}