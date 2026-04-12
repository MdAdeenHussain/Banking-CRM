const otpInputs = document.querySelectorAll('.otp-input');
const otpForm = document.getElementById('verifyOtpForm');
const otpCodeInput = document.getElementById('otp_code');

otpInputs.forEach((input, index) => {
    input.addEventListener('input', (e) => {
        if (e.target.value.length === 1 && index < otpInputs.length - 1) {
            otpInputs[index + 1].focus();
        }
    });

    input.addEventListener('keydown', (e) => {
        if (e.key === 'Backspace' && input.value === '' && index > 0) {
            otpInputs[index - 1].focus();
        }
    });
});

otpForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const code = Array.from(otpInputs).map(input => input.value).join('');
    otpCodeInput.value = code;
    otpForm.submit();
});

