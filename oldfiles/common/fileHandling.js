

import { role } from '../../static/js/index.js'; // Add this import

export function handleFileSelect() {
    const fileInput = document.getElementById('fileInput');
    selectedFiles = [...Array.from(fileInput.files)];
    displaySelectedFiles();
}


export function displaySelectedFiles() {
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

export function removeSelectedFile(index) {
    selectedFiles.splice(index, 1);
    displaySelectedFiles();
}

export async function removeFile(fileName, container) {
    // Only allow removal if it's the user's own message
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
export let selectedFiles = [];  // Ensure it's an array
