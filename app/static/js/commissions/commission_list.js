document.getElementById('searchInput').addEventListener('keyup', filterTable);
document.getElementById('statusFilter').addEventListener('change', filterTable);
document.getElementById('periodFilter').addEventListener('change', filterTable);

function filterTable() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const statusFilter = document.getElementById('statusFilter').value;
    
    const rows = document.querySelectorAll('.table-row');
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        const status = row.querySelector('.status-badge').textContent;
        
        const matchesSearch = text.includes(searchTerm);
        const matchesStatus = !statusFilter || status === statusFilter;
        
        row.style.display = (matchesSearch && matchesStatus) ? '' : 'none';
    });
}

