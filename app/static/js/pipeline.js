/**
 * LoanAxis CRM — Pipeline Kanban
 * Uses Sortable.js for drag-and-drop stage updates.
 */
document.addEventListener('DOMContentLoaded', () => {
    // Load Sortable.js dynamically
    if (typeof Sortable === 'undefined') {
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/sortablejs@1.15.6/Sortable.min.js';
        script.onload = initKanban;
        document.head.appendChild(script);
    } else {
        initKanban();
    }

    function initKanban() {
        document.querySelectorAll('.kanban-column-body').forEach(column => {
            new Sortable(column, {
                group: 'leads',
                animation: 200,
                ghostClass: 'sortable-ghost',
                dragClass: 'dragging',
                onEnd: function(evt) {
                    const leadId = evt.item.dataset.leadId;
                    const newStage = evt.to.dataset.stage;
                    if (!leadId || !newStage) return;

                    fetch('/leads/api/stage-update', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ lead_id: leadId, new_stage: newStage }),
                    })
                    .then(r => r.json())
                    .then(data => {
                        if (data.error) {
                            alert('Error: ' + data.error);
                            location.reload();
                        }
                    })
                    .catch(() => location.reload());
                }
            });
        });
    }
});
