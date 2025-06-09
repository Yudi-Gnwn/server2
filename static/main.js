document.addEventListener('DOMContentLoaded', function() {
    // Add smooth fade-in animation to cards
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        setTimeout(() => {
            card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, 100);
    });

    // Add click animation to buttons
    const buttons = document.querySelectorAll('button, .btn');
    buttons.forEach(button => {
        button.addEventListener('click', function(e) {
            this.style.transform = 'scale(0.95)';
            setTimeout(() => {
                this.style.transform = 'scale(1)';
            }, 100);
        });
    });

    // Flash messages fade out
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.5s ease';
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 500);
        }, 3000);
    });

    // Form validation
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;

            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    isValid = false;
                    field.classList.add('error');
                    
                    const errorMessage = document.createElement('div');
                    errorMessage.classList.add('error-message');
                    errorMessage.textContent = 'This field is required';
                    
                    if (!field.nextElementSibling?.classList.contains('error-message')) {
                        field.parentNode.insertBefore(errorMessage, field.nextSibling);
                    }
                }
            });

            if (!isValid) {
                e.preventDefault();
            }
        });
    });

    // Initialize Socket.IO connection
    const socket = io({
        transports: ['websocket'],
        upgrade: false,
        reconnection: true,
        reconnectionAttempts: 5
    });

    // Handle connection events
    socket.on('connect', () => {
        console.log('Connected to server');
    });

    socket.on('connect_error', (error) => {
        console.error('Connection error:', error);
    });

    socket.on('disconnect', (reason) => {
        console.log('Disconnected:', reason);
    });

    // Handle vote updates
    socket.on('vote_update', function(data) {
        console.log('Vote update received:', data);
        
        // Update vote counts for both options
        if (data.counts) {
            document.getElementById('count-a').textContent = data.counts.A;
            document.getElementById('count-b').textContent = data.counts.B;
            
            // Calculate and update percentages
            const totalVotes = data.counts.A + data.counts.B;
            const percentA = totalVotes > 0 ? (data.counts.A / totalVotes * 100).toFixed(1) : '0.0';
            const percentB = totalVotes > 0 ? (data.counts.B / totalVotes * 100).toFixed(1) : '0.0';
            
            document.getElementById('percent-a').textContent = percentA + '%';
            document.getElementById('percent-b').textContent = percentB + '%';
            
            // Update progress bars
            document.getElementById('progress-a').style.width = percentA + '%';
            document.getElementById('progress-b').style.width = percentB + '%';
        }
    });

    // Handle form submission
    const voteForm = document.getElementById('vote-form');
    if (voteForm) {
        voteForm.addEventListener('submit', function(e) {
            const selectedOption = document.querySelector('input[name="option"]:checked');
            if (!selectedOption) {
                e.preventDefault();
                alert('Please select an option to vote.');
            }
        });
    }

    // Add visual feedback for vote buttons
    const voteButtons = document.querySelectorAll('.vote-option');
    voteButtons.forEach(button => {
        button.addEventListener('change', function() {
            voteButtons.forEach(btn => {
                btn.parentElement.classList.remove('selected');
            });
            if (this.checked) {
                this.parentElement.classList.add('selected');
            }
        });
    });
});
