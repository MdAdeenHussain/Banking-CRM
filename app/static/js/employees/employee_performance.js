document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', function() {
        document.querySelectorAll('.leaderboard-content').forEach(c => c.classList.remove('active'));
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        
        const content = document.getElementById(this.textContent.trim().split('\n')[0].trim().toLowerCase());
        if (content) content.classList.add('active');
        this.classList.add('active');
    });
});

function switchLeaderboard(type) {
    document.querySelectorAll('.leaderboard-content').forEach(c => c.classList.remove('active'));
    document.getElementById(type).classList.add('active');
}

function dismissAlert(btn) {
    btn.closest('.alert-item').style.display = 'none';
}

