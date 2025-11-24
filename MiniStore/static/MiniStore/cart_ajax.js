// MiniStore/static/MiniStore/cart_ajax.js

document.addEventListener('DOMContentLoaded', function() {
    // Select all forms that target the cart_add URL
    // NOTE: The form's action attribute must contain '/cart/add/'
    const addToCartForms = document.querySelectorAll('form[action*="/cart/add/"]'); 

    if (addToCartForms.length > 0) {
        addToCartForms.forEach(form => {
            form.addEventListener('submit', function(e) {
                e.preventDefault(); // Stop the default browser submission (page reload)

                const url = form.action;
                const method = form.method;
                const formData = new FormData(form);

                // Find the CSRF token from the form data
                const csrftoken = formData.get('csrfmiddlewaretoken');

                // Send the AJAX Request using Fetch API
                fetch(url, {
                    method: method,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest', // Crucial for Django to detect AJAX
                        'X-CSRFToken': csrftoken || '', // Send the CSRF token
                    },
                    body: formData,
                })
                .then(response => {
                    // Check if the response is valid JSON
                    if (!response.ok) {
                         throw new Error(`Server responded with status: ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.success) {
                        // 1. Update the Cart Count Span
                        const cartCountSpan = document.querySelector('.cart-count');
                        if (cartCountSpan) {
                            cartCountSpan.textContent = data.cart_count;
                        }
                        
                        // 2. Optional: Add a visual notification (e.g., alert or pop-up)
                        console.log(`Cart updated! Total items: ${data.cart_count}`);
                        // You can replace the console log with a subtle visual cue for the user
                    } else {
                        alert('Failed to add item to cart. Try refreshing the page.');
                    }
                })
                .catch(error => {
                    console.error('AJAX Error:', error);
                    alert('There was a network or server error.');
                });
            });
        });
    }
});