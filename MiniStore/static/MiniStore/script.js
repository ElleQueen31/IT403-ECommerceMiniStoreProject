// MiniStore/script.js

// Function to handle adding items to cart dynamically
document.addEventListener('DOMContentLoaded', function() {
    
    const cartIcon = document.querySelector('.cart-icon'); // The main cart link/icon
    
    // 1. Target all 'Add to Cart' forms or buttons
    // NOTE: You must update your 'Add to Cart' buttons to submit a form via POST
    const addToCartForms = document.querySelectorAll('form[action*="/cart/add/"]'); 

    if (addToCartForms.length > 0) {
        addToCartForms.forEach(form => {
            form.addEventListener('submit', function(e) {
                e.preventDefault(); // Stop the default page refresh/redirect

                const url = form.action;
                const method = form.method;
                const formData = new FormData(form);

                // Send the AJAX Request
                fetch(url, {
                    method: method,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest', // Identifies request as AJAX
                    },
                    body: formData,
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // 2. Update the Cart Count Span
                        const cartCountSpan = document.querySelector('.cart-count');
                        if (cartCountSpan) {
                            cartCountSpan.textContent = data.cart_count;
                        }
                        
                        // 3. (Optional) Provide Visual Feedback
                        alert('Item added to cart!');
                        // You can also add a visual animation here
                    } else {
                        alert('Failed to add item to cart.');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('An error occurred during network request.');
                });
            });
        });
    }
});