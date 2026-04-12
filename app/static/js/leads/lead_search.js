function switchView(viewName) {
    // Hide all views
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    document.querySelectorAll('.view-btn').forEach(b => b.classList.remove('active'));

    // Show selected view
    document.getElementById(viewName === 'list' ? 'listView' : 'gridView').classList.add('active');
    event.target.classList.add('active');
}

function resetForm() {
    document.getElementById('searchForm').reset();
    document.getElementById('searchForm').submit();
}

