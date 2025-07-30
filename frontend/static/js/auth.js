document.addEventListener("DOMContentLoaded", function () {
  // Toggle password visibility
  const togglePasswordButtons = document.querySelectorAll(".toggle-password");
  togglePasswordButtons.forEach((button) => {
    button.addEventListener("click", function () {
      const input = this.parentElement.querySelector("input");
      const icon = this.querySelector("i");

      if (input.type === "password") {
        input.type = "text";
        icon.classList.remove("fa-eye");
        icon.classList.add("fa-eye-slash");
      } else {
        input.type = "password";
        icon.classList.remove("fa-eye-slash");
        icon.classList.add("fa-eye");
      }
    });
  });

  // Password strength indicator
  const passwordInput = document.getElementById("password");
  if (passwordInput) {
    passwordInput.addEventListener("input", function () {
      const strengthMeter =
        this.closest(".form-group").querySelector(".strength-meter");
      const strengthText =
        this.closest(".form-group").querySelector(".strength-text");
      const sections = strengthMeter.querySelectorAll(".strength-section");

      const password = this.value;
      let strength = 0;

      if (password.length > 0) strength++;
      if (password.length >= 8) strength++;
      if (/[A-Z]/.test(password) && /[a-z]/.test(password)) strength++;
      if (/\d/.test(password)) strength++;
      if (/[^A-Za-z0-9]/.test(password)) strength++;

      sections.forEach((section, index) => {
        if (index < strength) {
          section.style.backgroundColor = getStrengthColor(strength);
          section.style.transform = "scaleY(1.5)";
          setTimeout(() => {
            section.style.transform = "scaleY(1)";
          }, 300);
        } else {
          section.style.backgroundColor = "#e9ecef";
        }
      });

      strengthText.textContent = getStrengthText(strength);
      strengthText.style.color = getStrengthColor(strength);
    });
  }

  function getStrengthColor(strength) {
    if (strength <= 2) return "#f72585";
    if (strength <= 4) return "#f8961e";
    return "#4cc9f0";
  }

  function getStrengthText(strength) {
    if (strength <= 2) return "Weak";
    if (strength <= 4) return "Medium";
    return "Strong";
  }

  // Form validation
  const registerForm = document.getElementById("registerForm");
  if (registerForm) {
    registerForm.addEventListener("submit", function (e) {
      const password = document.getElementById("password");
      const confirmPassword = document.getElementById("confirm_password");

      if (password.value !== confirmPassword.value) {
        e.preventDefault();
        confirmPassword.style.borderColor = "#f72585";
        confirmPassword.style.boxShadow = "0 0 0 3px rgba(247, 37, 133, 0.2)";

        let errorMsg = document.createElement("div");
        errorMsg.className = "alert alert-danger";
        errorMsg.textContent = "Passwords do not match!";
        errorMsg.style.marginTop = "10px";
        errorMsg.style.animation = "slideIn 0.5s ease-out";

        confirmPassword.parentElement.parentElement.appendChild(errorMsg);

        setTimeout(() => {
          errorMsg.style.animation = "slideIn 0.5s ease-out reverse";
          setTimeout(() => {
            errorMsg.remove();
          }, 500);
        }, 3000);

        confirmPassword.focus();
      }
    });
  }

  // Button ripple effect
  const buttons = document.querySelectorAll(".btn");
  buttons.forEach((button) => {
    button.addEventListener("click", function (e) {
      const existingRipples = this.querySelectorAll(".ripple");
      existingRipples.forEach((ripple) => ripple.remove());

      const ripple = document.createElement("span");
      ripple.className = "ripple";

      const rect = this.getBoundingClientRect();
      const size = Math.max(rect.width, rect.height);
      ripple.style.width = ripple.style.height = `${size}px`;
      ripple.style.left = `${e.clientX - rect.left - size / 2}px`;
      ripple.style.top = `${e.clientY - rect.top - size / 2}px`;

      this.appendChild(ripple);

      setTimeout(() => {
        ripple.remove();
      }, 1000);
    });
  });

  // Social icon hover
  const socialIcons = document.querySelectorAll(".social-icon");
  socialIcons.forEach((icon) => {
    icon.addEventListener("mouseenter", function () {
      this.style.transform = "translateY(-5px) scale(1.1)";
    });

    icon.addEventListener("mouseleave", function () {
      this.style.transform = "translateY(0) scale(1)";
    });
  });

  // Image prediction logic
  const uploadInput = document.getElementById("imageUpload");
  const previewImage = document.getElementById("previewImage");
  const predictionBox = document.getElementById("predictionResult");

  if (uploadInput) {
    uploadInput.addEventListener("change", function () {
      const file = uploadInput.files[0];
      if (!file) return;

      const reader = new FileReader();
      reader.onload = function (e) {
        previewImage.src = e.target.result;
        previewImage.style.display = "block";

        fetch("/predict", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ image: e.target.result }),
        })
          .then((res) => res.json())
          .then((data) => {
            predictionBox.textContent =
              "Emotions: " +
              (data.emotions ? data.emotions.join(", ") : "Unknown");
          })
          .catch(() => {
            predictionBox.textContent = "Prediction failed.";
          });
      };
      reader.readAsDataURL(file);
    });
  }
});
