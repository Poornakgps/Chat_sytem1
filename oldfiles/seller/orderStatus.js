export function handleStatusChange() {
    const status = document.getElementById('orderStatus').value;
    const trackingSection = document.getElementById('trackingSection');
    trackingSection.style.display = status === 'shipped' ? 'block' : 'none';
}

export async function updateStatus() {
    const status = document.getElementById('orderStatus').value;
    const formData = new FormData();
    formData.append('status', status);
    
    if (status === 'shipped') {
        const tracking = document.getElementById('trackingNumber').value;
        formData.append('tracking', tracking);
    }
    
    try {
        await fetch('/seller/update_status', {
            method: 'POST',
            body: formData
        });
    } catch (error) {
        console.error('Error updating status:', error);
    }
}
export function handleStatusChange() {
    const status = document.getElementById('orderStatus').value;
    const trackingSection = document.getElementById('trackingSection');
    trackingSection.style.display = status === 'shipped' ? 'block' : 'none';
}

export async function updateStatus() {
    const status = document.getElementById('orderStatus').value;
    const formData = new FormData();
    formData.append('status', status);
    
    if (status === 'shipped') {
        const tracking = document.getElementById('trackingNumber').value;
        formData.append('tracking', tracking);
    }
    
    await fetch('/seller/update_status', {
        method: 'POST',
        body: formData
    });
}