function approveCommission(commissionId) {
    if (confirm('Are you sure you want to approve this commission?')) {
        // Send approval request
        fetch(`/api/commissions/${commissionId}/approve`, { method: 'POST' })
            .then(() => location.reload());
    }
}

function rejectCommission(commissionId) {
    const reason = prompt('Enter rejection reason:');
    if (reason) {
        fetch(`/api/commissions/${commissionId}/reject`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ reason: reason })
        }).then(() => location.reload());
    }
}

function markAsPaid(commissionId) {
    if (confirm('Mark this commission as paid?')) {
        fetch(`/api/commissions/${commissionId}/paid`, { method: 'POST' })
            .then(() => location.reload());
    }
}

