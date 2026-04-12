function showTab(tabName) {
    // Hide all tabs
    const tabs = document.querySelectorAll('.tab-content');
    tabs.forEach(tab => tab.classList.remove('active'));

    // Remove active from all buttons
    const buttons = document.querySelectorAll('.tab-button');
    buttons.forEach(btn => btn.classList.remove('active'));

    // Show selected tab
    document.getElementById(tabName).classList.add('active');

    // Add active to clicked button
    event.target.classList.add('active');
}

function openModal(modalName) {
    // Placeholder for modal functionality
    console.log('Opening modal:', modalName);
}

function deleteDoc(docId) {
    if (confirm('Are you sure you want to delete this document?')) {
        console.log('Deleting document:', docId);
    }
}

