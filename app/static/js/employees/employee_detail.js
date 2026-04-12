function showTab(tabName) {
    document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
    document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
    
    document.getElementById(tabName).classList.add('active');
    event.target.classList.add('active');
}

function deactivateEmployee(employeeId) {
    if (confirm('Are you sure you want to deactivate this employee?')) {
        console.log('Deactivating employee:', employeeId);
    }
}

