const usernameField = document.querySelector("#usernameField");
const feedbackArea = document.querySelector('.invalid_feedback');
const emailField = document.querySelector('#emailField');
const passwordField = document.querySelector('#passwordField')
const feedbackAreaEmail = document.querySelector('.emailFeedBackArea');
const showPassowordToggle = document.querySelector('.showPasswordToggle')
const submitBtn = document.querySelector('.submit-btn')


const handleToggleInput = (e) => {
    if (showPassowordToggle.textContent === 'SHOW') {
        showPassowordToggle.textContent = 'HIDE';
        passwordField.setAttribute('type', 'text');
    } else {
        showPassowordToggle.textContent = 'SHOW';
        passwordField.setAttribute('type', 'password')
    }
}

showPassowordToggle.addEventListener('click', handleToggleInput);

usernameField.addEventListener("keyup", (e) => {
    const usernameVal = e.target.value;

    usernameField.classList.remove('is-invalid')
    feedbackArea.style.display = 'none';

    if (usernameVal.length > 0) {
        fetch('/authentication/validate-username', {
            body: JSON.stringify({ username: usernameVal }),
            method: 'POST',
        }).then((res) => res.json())
            .then((data) => {
                console.log('data', data);
                if (data.username_error) {
                    usernameField.classList.add('is-invalid')
                    feedbackArea.style.display = 'block';
                    feedbackArea.innerHTML = `<p>${data.username_error}</p>`
                    submitBtn.disabled = true;
                } else {
                    submitBtn.removeAttribute('disabled');
                }
            })
    }
})


emailField.addEventListener("keyup", (e) => {
    const emailVal = e.target.value;

    emailField.classList.remove('is-invalid')
    feedbackAreaEmail.style.display = 'none';

    if (emailVal.length > 0) {
        fetch('/authentication/validate-email', {
            body: JSON.stringify({ email: emailVal }),
            method: 'POST',
        }).then((res) => res.json())
            .then((data) => {
                console.log('data', data);
                if (data.email_error) {
                    emailField.classList.add('is-invalid')
                    feedbackAreaEmail.style.display = 'block';
                    feedbackAreaEmail.innerHTML = `<p>${data.email_error}</p>`
                    submitBtn.disabled = true;
                } else {
                    submitBtn.removeAttribute('disabled');
                }

            })
    }
})