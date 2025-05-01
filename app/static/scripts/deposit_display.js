document.addEventListener('DOMContentLoaded', function() {
    // Only run if the financial modal exists
    if (document.getElementById('financialModal')) {
        // Fetch the maximum deposit amount
        fetch('/api/max-deposit')
            .then(response => response.json())
            .then(data => {
                const maxAmount = data.max.toFixed(2);
                const safeAmount = data.safe.toFixed(2);
                
                // Get the deposit tab content
                const depositTab = document.querySelector('#deposit');
                if (depositTab) {
                    // Create max-deposit notice
                    const notice = document.createElement('div');
                    notice.className = 'alert alert-info mb-3';
                    notice.innerHTML = `<strong>Available balance:</strong> $${maxAmount}`;
                    
                    // Create safe deposit notice
                    const safeNotice = document.createElement('div');
                    safeNotice.className = 'alert alert-warning mb-3';
                    safeNotice.innerHTML = `<strong>Safe deposit amount:</strong> $${safeAmount} <small>(Ensures you stay above your minimum balance goal. If it is 0, you are already below your minimum balance goal.)</small>`;
                    
                    // Add notices at the top of the deposit tab
                    depositTab.insertBefore(safeNotice, depositTab.firstChild);
                    depositTab.insertBefore(notice, depositTab.firstChild);
                    
                    // Set amount input placeholder
                    const amountInput = depositTab.querySelector('input[name="amount"]');
                    if (amountInput) {
                        amountInput.placeholder = `Max: $${maxAmount}`;
                    }
                }
            })
            .catch(error => console.error('Error fetching max deposit:', error));
    }
});