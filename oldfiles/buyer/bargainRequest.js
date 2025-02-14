export async function sendBargainRequest() {
    const amount = document.getElementById('bargainAmount').value;
    
    const formData = new FormData();
    formData.append('amount', amount);
    
    await fetch('/buyer/bargain', {
        method: 'POST',
        body: formData
    });
    
    document.getElementById('bargainAmount').value = '';
}
