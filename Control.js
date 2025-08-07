//register
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/; 
    return re.test(String(email).toLowerCase());
}

document.getElementById('registerForm').addEventListener('submit', function(event) {
    const emailInput = document.querySelector('input[name="email"]');
    const email = emailInput.value;
    const messageContainer = document.createElement('div');

    if (!validateEmail(email)) {
        event.preventDefault();
        messageContainer.className = 'alert';
        messageContainer.style.color = '#ff6666';
        messageContainer.innerText = 'البريد الإلكتروني غير صالح.';
        emailInput.parentNode.insertBefore(messageContainer, emailInput.nextSibling);
    }
});

const passwordInput = document.getElementById('password');
const requirements = {
    length: document.getElementById('length'),
    uppercase: document.getElementById('uppercase'),
    number: document.getElementById('number'),
    special: document.getElementById('special')
};

passwordInput.addEventListener('input', function() {
    const password = passwordInput.value;

    const lengthValid = password.length >= 8;
    const uppercaseValid = /[A-Z]/.test(password);
    const numberValid = /[0-9]/.test(password);
    const specialValid = /[!@#$%^&*]/.test(password);

    requirements.length.className = lengthValid ? 'valid' : 'invalid';
    requirements.length.querySelector('.checkmark').style.display = lengthValid ? 'inline' : 'none';

    requirements.uppercase.className = uppercaseValid ? 'valid' : 'invalid';
    requirements.uppercase.querySelector('.checkmark').style.display = uppercaseValid ? 'inline' : 'none';

    requirements.number.className = numberValid ? 'valid' : 'invalid';
    requirements.number.querySelector('.checkmark').style.display = numberValid ? 'inline' : 'none';

    requirements.special.className = specialValid ? 'valid' : 'invalid';
    requirements.special.querySelector('.checkmark').style.display = specialValid ? 'inline' : 'none';
});




//date users

function copyPassword(password) {
    navigator.clipboard.writeText(password).then(function() {
        alert('تم نسخ كلمة المرور إلى الحافظة!');
    }, function(err) {
        alert('فشل في نسخ كلمة المرور: ', err);
    });
}

// بيانات العينة لعدد المشتركين
const dailyData = [5, 3, 4, 7, 6, 8, 10]; // عدد المشتركين في الأيام
const monthlyData = [20, 30, 25, 35, 40, 50, 45]; // عدد المشتركين في الأشهر
const yearlyData = [200, 250, 300, 350, 400, 450, 500]; // عدد المشتركين في السنوات

const dailyCtx = document.getElementById('dailyChart').getContext('2d');
new Chart(dailyCtx, {
    type: 'line',
    data: {
        labels: ['الأحد', 'الإثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت'],
        datasets: [{
            label: 'عدد المشتركين اليومي',
            data: dailyData,
            borderColor: 'rgba(255, 99, 132, 1)',
            fill: false
        }]
    },
    options: {
        responsive: true,
        scales: {
            y: {
                beginAtZero: true
            }
        }
    }
});

const monthlyCtx = document.getElementById('monthlyChart').getContext('2d');
new Chart(monthlyCtx, {
    type: 'bar',
    data: {
        labels: ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو', 'يوليو'],
        datasets: [{
            label: 'عدد المشتركين الشهري',
            data: monthlyData,
            backgroundColor: 'rgba(54, 162, 235, 0.5)',
            borderColor: 'rgba(54, 162, 235, 1)',
            borderWidth: 1
        }]
    },
    options: {
        responsive: true,
        scales: {
            y: {
                beginAtZero: true
            }
        }
    }
});

const yearlyCtx = document.getElementById('yearlyChart').getContext('2d');
new Chart(yearlyCtx, {
    type: 'bar',
    data: {
        labels: ['2021', '2022', '2023', '2024', '2025'],
        datasets: [{
            label: 'عدد المشتركين السنوي',
            data: yearlyData,
            backgroundColor: 'rgba(75, 192, 192, 0.5)',
            borderColor: 'rgba(75, 192, 192, 1)',
            borderWidth: 1
        }]
    },
    options: {
        responsive: true,
        scales: {
            y: {
                beginAtZero: true
            }
        }
    }
});

//contantgroup

const messagesDiv = document.getElementById('messages');

function scrollToBottom() {
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

window.onload = function() {
    scrollToBottom();
};

function refreshMessages() {
    scrollToBottom();
}

setInterval(refreshMessages, 5000);


//courses
function likeCourse(courseId, button) {
    fetch(`/like/${courseId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (response.ok) {
            button.classList.toggle('liked');
            button.textContent = button.classList.contains('liked') ? '❤️' : '🤍'; 
        } else {
            console.error('Failed to like the course');
        }
    })
    .catch(error => console.error('Error:', error));
}


//desktop-index

function toggleHeart(button) {
    if (button.textContent === '🤍') {
        button.textContent = '❤️';
    } else {
        button.textContent = '🤍';
    }
}
function shareCourse(title, description) {
    const shareText = `${title}\n${description}`;
    if (navigator.share) {
        navigator.share({
            title: title,
            text: description,
        })
        .then(() => console.log('تمت المشاركة بنجاح'))
        .catch((error) => console.error('خطأ في المشاركة:', error));
    } else {
        alert(shareText);
    }
}


    function toggleSpecializationPopup(event) {
        const popup = document.getElementById('specializationPopup');
        const isDisplayed = popup.classList.contains('show');
        if (isDisplayed) {
            popup.classList.remove('show');
        } else {
            popup.classList.add('show');
        }

       
        popup.style.top = (event.clientY + 10) + 'px';
        popup.style.left = (event.clientX - 10) + 'px';
    }

    window.onclick = function(event) {
        const popup = document.getElementById('specializationPopup');
        if (event.target !== popup && !popup.contains(event.target) && event.target !== document.querySelector('nav button')) {
            popup.classList.remove('show');
        }
    }
    