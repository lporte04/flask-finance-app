// Show max spendable amount in spending form
document.addEventListener('DOMContentLoaded', function() {
    // Only run if the financial modal exists
    if (document.getElementById('financialModal')) {
        // Fetch the maximum spendable amount
        fetch('/api/max-spend')
            .then(response => response.json())
            .then(data => {
                const maxAmount = data.max.toFixed(2);
                
                // Get the spending tab content
                const spendingTab = document.querySelector('#spending');
                if (spendingTab) {
                    // Create max-spend notice
                    const notice = document.createElement('div');
                    notice.className = 'alert alert-info mb-3';
                    notice.innerHTML = `<strong>Available balance:</strong> $${maxAmount}`;
                    
                    // Add notice at the top of the spending tab
                    spendingTab.insertBefore(notice, spendingTab.firstChild);
                    
                    // Apply placeholder to all existing inputs
                    applyPlaceholders(maxAmount);
                    
                    // Set up an observer to watch for new rows
                    const observer = new MutationObserver(() => {
                        applyPlaceholders(maxAmount);
                    });
                    
                    // Start observing the spending table for added rows
                    const spendingTable = document.querySelector('#spending table tbody');
                    if (spendingTable) {
                        observer.observe(spendingTable, { childList: true, subtree: true });
                    }
                }
            })
            .catch(error => console.error('Error fetching max spend:', error));
    }
});

// Helper function to apply placeholders to all amount inputs
function applyPlaceholders(maxAmount) {
    const amountInputs = document.querySelectorAll('input[name*="spendings-"][name$="-amount"]');
    amountInputs.forEach(input => {
        input.placeholder = `Max: $${maxAmount}`;
    });
}