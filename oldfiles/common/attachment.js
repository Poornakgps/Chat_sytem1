import {role} from '../index.js';

export async function removeAttachment(fileName, element) {
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