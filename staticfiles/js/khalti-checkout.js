class KhaltiPaymentHandler {
    constructor(publicKey, amount, productIdentity, productName) {
        this.config = {
            // Replace with your public key from Khalti
            "publicKey": publicKey,
            "productIdentity": productIdentity,
            "productName": productName,
            "productUrl": window.location.href, // Current page URL
            "amount": amount * 100, // Convert to paisa
            "eventHandler": {
                onSuccess: (payload) => {
                    // Hit merchant api for verification
                    this.verifyPayment(payload);
                },
                onError: (error) => {
                    console.log(error);
                    alert("Payment failed. Please try again.");
                },
                onClose: () => {
                    console.log('Widget is closing');
                }
            },
            // Additional required fields
            "merchant": {
                "name": "EventMaster",
                "logo": "/static/images/logo.png" // Replace with your logo URL
            },
            "paymentPreference": [
                "KHALTI",
                "EBANKING",
                "MOBILE_BANKING",
                "CONNECT_IPS",
                "SCT"
            ],
        };
    }

    initiatePayment() {
        const checkout = new KhaltiCheckout(this.config);
        checkout.show({ amount: this.config.amount });
    }

    async verifyPayment(payload) {
        try {
            const response = await fetch('/tickets/verify-payment/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                body: JSON.stringify(payload)
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                // Show success message
                alert('Payment successful!');
                // Submit the checkout form
                document.getElementById('checkout-form').submit();
            } else {
                alert('Payment verification failed. Please contact support.');
            }
        } catch (error) {
            console.error('Payment verification error:', error);
            alert('Payment verification failed. Please try again.');
        }
    }
}

// Wait for DOM content to be loaded
document.addEventListener('DOMContentLoaded', function() {
    // Wait for Khalti SDK to load
    const khaltiScriptLoad = new Promise((resolve) => {
        if (typeof KhaltiCheckout !== 'undefined') {
            resolve();
        } else {
            const script = document.createElement('script');
            script.src = "https://khalti.s3.ap-south-1.amazonaws.com/KPG/dist/2020.12.22.0.0.0/khalti-checkout.iffe.js";
            script.onload = resolve;
            document.head.appendChild(script);
        }
    });

    // Initialize payment handler when button is clicked
    document.getElementById('confirm-purchase').addEventListener('click', async () => {
        // Wait for Khalti SDK to load if it hasn't already
        await khaltiScriptLoad;
        
        // Remove currency symbol and parse amount
        const totalAmountText = document.getElementById('total-price').textContent;
        const totalAmount = parseFloat(totalAmountText.replace(/[^0-9.]/g, ''));
        
        // Generate a unique order ID
        const orderId = 'ORDER-' + Date.now();
        
        const handler = new KhaltiPaymentHandler(
            'test_public_key_831f3e7517dd4ee9a75e7790178f6f9b', // Replace with your test public key
            totalAmount,
            orderId,
            'Event Tickets Purchase'
        );
        handler.initiatePayment();
    });
});