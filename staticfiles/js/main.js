// Store Management System - Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Confirm delete actions
    const deleteButtons = document.querySelectorAll('[data-confirm]');
    deleteButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            const message = this.getAttribute('data-confirm') || 'Are you sure you want to delete this item?';
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });

    // Auto-calculate totals in invoice form
    const quantityInputs = document.querySelectorAll('.item-quantity');
    const priceInputs = document.querySelectorAll('.item-price');

    function updateTotals() {
        let grandTotal = 0;
        document.querySelectorAll('.invoice-item-row').forEach(function(row) {
            const quantity = parseFloat(row.querySelector('.item-quantity')?.value) || 0;
            const price = parseFloat(row.querySelector('.item-price')?.value) || 0;
            const total = quantity * price;
            const totalField = row.querySelector('.item-total');
            if (totalField) {
                totalField.value = total.toFixed(2);
            }
            grandTotal += total;
        });
        const grandTotalField = document.getElementById('grand-total');
        if (grandTotalField) {
            grandTotalField.textContent = grandTotal.toFixed(2);
        }
    }

    quantityInputs.forEach(input => input.addEventListener('input', updateTotals));
    priceInputs.forEach(input => input.addEventListener('input', updateTotals));
});
