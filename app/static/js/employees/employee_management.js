document.getElementById('searchInput').addEventListener('keyup', filterTable);

function filterTable() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const rows = document.querySelectorAll('.table-row');
    
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(searchTerm) ? '' : 'none';
    });
}

function viewEmployee(empId) {
    window.location.href = `/employees/detail/${empId}`;
}

function editEmployee(empId) {
    window.location.href = `/employees/edit/${empId}`;
}

function toggleStatus(empId) {
    if (confirm('Toggle this employee\'s status?')) {
        console.log('Toggling status for:', empId);
    }
}

function deleteEmployee(empId) {
    if (confirm('Are you sure you want to delete this employee?')) {
        console.log('Deleting employee:', empId);
    }
}

function toggleSelectAll() {
    const isChecked = document.getElementById('selectAll').checked;
    document.querySelectorAll('input[type="checkbox"]').forEach(cb => {
        cb.checked = isChecked;
    });
}

function bulkAction(action) {
    console.log('Bulk action:', action);
}

