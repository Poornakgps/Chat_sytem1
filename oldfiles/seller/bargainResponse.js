export async function respondToBargain(approved, amount) {
    const formData = new FormData();
    formData.append('response', approved);
    formData.append('amount', amount);
    
    try {
        await fetch('/seller/bargain_response', {
            method: 'POST',
            body: formData
        });
    } catch (error) {
        console.error('Error responding to bargain:', error);
    }
}

export async function confirmPayment(chatId) {
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
