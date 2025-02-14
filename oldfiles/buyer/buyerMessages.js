import { selectedFiles, displaySelectedFiles } from '../common/fileHandling.js';

export async function sendMessage() {
    const input = document.getElementById('messageInput');
    const message = input.value;
    
    if (!message && selectedFiles.length === 0) return;
    
    const formData = new FormData();
    formData.append('message', message);
    
    // Append all selected files
    selectedFiles.forEach(file => {
        formData.append('file', file);
    });
    
    const endpoint = `/${role}/send_message`;
    try {
        await fetch(endpoint, {
            method: 'POST',
            body: formData
        });
        
        // Clear input and files after successful send
        input.value = '';
        selectedFiles = [];
        displaySelectedFiles(); // Update UI to show no files
        document.getElementById('fileInput').value = ''; // Reset file input
    } catch (error) {
        console.error('Error sending message:', error);
    }
}