document.addEventListener('DOMContentLoaded', function() {
    // Toggle password visibility
    const togglePasswordButtons = document.querySelectorAll('.toggle-password');
    togglePasswordButtons.forEach(button => {
        button.addEventListener('click', function() {
            const input = this.parentElement.querySelector('input');
            const icon = this.querySelector('i');
            
            if (input.type === 'password') {
                input.type = 'text';
                icon.classList.remove('fa-eye');
                icon.classList.add('fa-eye-slash');
            } else {
                input.type = 'password';
                icon.classList.remove('fa-eye-slash');
                icon.classList.add('fa-eye');
            }
        });
    });

    // Password strength indicator
    const passwordInput = document.getElementById('password');
    if (passwordInput) {
        passwordInput.addEventListener('input', function() {
            const strengthMeter = this.closest('.form-group').querySelector('.strength-meter');
            const strengthText = this.closest('.form-group').querySelector('.strength-text');
            const sections = strengthMeter.querySelectorAll('.strength-section');
            
            const password = this.value;
            let strength = 0;
            
            // Check password strength
            if (password.length > 0) strength++;
            if (password.length >= 8) strength++;
            if (/[A-Z]/.test(password) && /[a-z]/.test(password)) strength++;
            if (/\d/.test(password)) strength++;
            if (/[^A-Za-z0-9]/.test(password)) strength++;
            
            // Update UI
            sections.forEach((section, index) => {
                if (index < strength) {
                    section.style.backgroundColor = getStrengthColor(strength);
                    section.style.transform = 'scaleY(1.5)';
                    setTimeout(() => {
                        section.style.transform = 'scaleY(1)';
                    }, 300);
                } else {
                    section.style.backgroundColor = '#e9ecef';
                }
            });
            
            strengthText.textContent = getStrengthText(strength);
            strengthText.style.color = getStrengthColor(strength);
        });
    }
    
    function getStrengthColor(strength) {
        if (strength <= 2) return '#f72585'; // Weak (red)
        if (strength <= 4) return '#f8961e'; // Medium (orange)
        return '#4cc9f0'; // Strong (blue)
    }
    
    function getStrengthText(strength) {
        if (strength <= 2) return 'Weak';
        if (strength <= 4) return 'Medium';
        return 'Strong';
    }
    
    // Form validation
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', function(e) {
            const password = document.getElementById('password');
            const confirmPassword = document.getElementById('confirm_password');
            
            if (password.value !== confirmPassword.value) {
                e.preventDefault();
                // Add animation to highlight error
                confirmPassword.style.borderColor = '#f72585';
                confirmPassword.style.boxShadow = '0 0 0 3px rgba(247, 37, 133, 0.2)';
                
                // Create error message
                let errorMsg = document.createElement('div');
                errorMsg.className = 'alert alert-danger';
                errorMsg.textContent = 'Passwords do not match!';
                errorMsg.style.marginTop = '10px';
                errorMsg.style.animation = 'slideIn 0.5s ease-out';
                
                // Insert after confirm password field
                confirmPassword.parentElement.parentElement.appendChild(errorMsg);
                
                // Remove error after 3 seconds
                setTimeout(() => {
                    errorMsg.style.animation = 'slideIn 0.5s ease-out reverse';
                    setTimeout(() => {
                        errorMsg.remove();
                    }, 500);
                }, 3000);
                
                confirmPassword.focus();
            }
        });
    }

    // Add ripple effect to buttons
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
        button.addEventListener('click', function(e) {
            // Remove any existing ripples
            const existingRipples = this.querySelectorAll('.ripple');
            existingRipples.forEach(ripple => ripple.remove());
            
            // Create new ripple
            const ripple = document.createElement('span');
            ripple.className = 'ripple';
            
            // Position ripple
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            ripple.style.width = ripple.style.height = `${size}px`;
            ripple.style.left = `${e.clientX - rect.left - size/2}px`;
            ripple.style.top = `${e.clientY - rect.top - size/2}px`;
            
            this.appendChild(ripple);
            
            // Remove ripple after animation
            setTimeout(() => {
                ripple.remove();
            }, 1000);
        });
    });

    // Add hover effect to social icons
    const socialIcons = document.querySelectorAll('.social-icon');
    socialIcons.forEach(icon => {
        icon.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px) scale(1.1)';
        });
        
        icon.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });
    });
});