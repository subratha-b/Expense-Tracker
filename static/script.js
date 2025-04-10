document.addEventListener('DOMContentLoaded', function() {
    // Budget form editing
    document.querySelectorAll('.edit-budget').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const budgetId = this.dataset.id;
            const category = this.dataset.category;
            const amount = this.dataset.amount;
            const month = this.dataset.month;
            const year = this.dataset.year;
            const threshold = this.dataset.threshold;
            
            document.getElementById('category').value = category;
            document.getElementById('amount').value = amount;
            document.getElementById('month').value = month;
            document.getElementById('year').value = year;
            document.getElementById('alert_threshold').value = threshold;
            
            // Scroll to form
            document.querySelector('.budget-form').scrollIntoView({ behavior: 'smooth' });
        });
    });
    
    // Shared expense participants
    const participantsList = document.getElementById('participants-list');
    const addParticipantBtn = document.getElementById('add-participant');
    
    if (addParticipantBtn) {
        addParticipantBtn.addEventListener('click', function() {
            const participantRow = document.createElement('div');
            participantRow.className = 'participant-row';
            
            participantRow.innerHTML = `
                <select name="participants" required>
                    <option value="">Select User</option>
                    {% for user in users %}
                        <option value="{{ user.id }}">{{ user.username }}</option>
                    {% endfor %}
                </select>
                <input type="number" name="amounts" step="0.01" min="0" placeholder="Amount" required>
                <button type="button" class="remove-participant">×</button>
            `;
            
            participantsList.appendChild(participantRow);
            
            // Add remove event
            participantRow.querySelector('.remove-participant').addEventListener('click', function() {
                participantsList.removeChild(participantRow);
            });
        });
    }
    
    // Date picker defaults to today
    const dateInput = document.getElementById('date');
    if (dateInput && !dateInput.value) {
        const today = new Date().toISOString().split('T')[0];
        dateInput.value = today;
    }
    
    // Confirm before deleting
    document.querySelectorAll('.delete').forEach(link => {
        link.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this?')) {
                e.preventDefault();
            }
        });
    });
});