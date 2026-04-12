document.getElementById('searchInput').addEventListener('keyup', filterDocuments);

function filterDocuments() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const cards = document.querySelectorAll('.document-card');
    
    cards.forEach(card => {
        const text = card.textContent.toLowerCase();
        card.style.display = text.includes(searchTerm) ? '' : 'none';
    });
}

function deleteDoc(docId) {
    if (confirm('Are you sure you want to delete this document?')) {
        console.log('Deleting document:', docId);
    }
}

