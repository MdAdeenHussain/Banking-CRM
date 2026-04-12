document.getElementById('searchInput').addEventListener('keyup', filterEmployees);
document.getElementById('roleFilter').addEventListener('change', filterEmployees);
document.getElementById('statusFilter').addEventListener('change', filterEmployees);

function filterEmployees() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const roleFilter = document.getElementById('roleFilter').value;
    const statusFilter = document.getElementById('statusFilter').value;
    
    const cards = document.querySelectorAll('.employee-card');
    cards.forEach(card => {
        const text = card.textContent.toLowerCase();
        const matchesSearch = text.includes(searchTerm);
        const matchesRole = !roleFilter || text.includes(roleFilter);
        const matchesStatus = !statusFilter || card.querySelector('.status-badge').textContent.includes(statusFilter);
        
        card.style.display = (matchesSearch && matchesRole && matchesStatus) ? '' : 'none';
    });
}

