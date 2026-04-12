/**
 * Data Tables Module
 * Handles sorting, filtering, pagination, and interactive features
 */

class DataTable {
    constructor(options = {}) {
        this.tableElement = options.element || null;
        this.sortColumn = options.sortColumn || null;
        this.sortDirection = options.sortDirection || 'asc';
        this.filterText = '';
        this.currentPage = 1;
        this.itemsPerPage = options.itemsPerPage || 20;
        this.data = [];
        
        if (this.tableElement) {
            this.init();
        }
    }

    init() {
        this.setupEventListeners();
        this.loadData();
    }

    setupEventListeners() {
        // Sort columns
        this.tableElement.querySelectorAll('th[data-sortable]').forEach(header => {
            header.style.cursor = 'pointer';
            header.addEventListener('click', (e) => {
                const column = e.target.closest('th').getAttribute('data-column');
                this.sortBy(column);
            });
        });

        // Search filter
        const searchInput = document.querySelector('[data-table-search]');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.filterText = e.target.value;
                this.filter();
            });
        }

        // Row click actions
        this.tableElement.querySelectorAll('tbody tr').forEach(row => {
            row.addEventListener('click', function() {
                this.style.boxShadow = 'inset 0 0 0 2px rgba(102, 126, 234, 0.5)';
            });
            row.addEventListener('mouseover', function() {
                this.classList.add('hover');
            });
            row.addEventListener('mouseout', function() {
                this.classList.remove('hover');
            });
        });

        // Bulk actions
        const selectAllCheckbox = document.querySelector('th .select-all-checkbox');
        if (selectAllCheckbox) {
            selectAllCheckbox.addEventListener('change', (e) => {
                this.toggleSelectAll(e.target.checked);
            });
        }
    }

    loadData() {
        const rows = this.tableElement.querySelectorAll('tbody tr');
        this.data = Array.from(rows).map(row => ({
            element: row,
            cells: Array.from(row.querySelectorAll('td')).map(td => td.textContent.trim())
        }));
    }

    sortBy(column) {
        const header = this.tableElement.querySelector(`th[data-column="${column}"]`);
        if (!header) return;

        // Toggle sort direction if clicking same column
        if (this.sortColumn === column) {
            this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
        } else {
            this.sortColumn = column;
            this.sortDirection = 'asc';
        }

        // Update header visual
        this.tableElement.querySelectorAll('th').forEach(h => {
            h.classList.remove('sort-asc', 'sort-desc');
        });
        header.classList.add(`sort-${this.sortDirection}`);

        // Sort the table
        this.performSort();
    }

    performSort() {
        const columnIndex = Array.from(this.tableElement.querySelectorAll('th')).findIndex(
            h => h.getAttribute('data-column') === this.sortColumn
        );

        if (columnIndex === -1) return;

        const rows = Array.from(this.tableElement.querySelectorAll('tbody tr'));
        rows.sort((a, b) => {
            const aVal = a.cells[columnIndex].textContent.trim();
            const bVal = b.cells[columnIndex].textContent.trim();

            // Try to parse as number
            const aNum = parseFloat(aVal);
            const bNum = parseFloat(bVal);

            if (!isNaN(aNum) && !isNaN(bNum)) {
                return this.sortDirection === 'asc' ? aNum - bNum : bNum - aNum;
            }

            // String comparison
            const comparison = aVal.localeCompare(bVal);
            return this.sortDirection === 'asc' ? comparison : -comparison;
        });

        // Reorder in DOM
        const tbody = this.tableElement.querySelector('tbody');
        rows.forEach(row => tbody.appendChild(row));
    }

    filter() {
        const rows = this.tableElement.querySelectorAll('tbody tr');
        const searchTerm = this.filterText.toLowerCase();

        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            const isVisible = text.includes(searchTerm);
            row.style.display = isVisible ? '' : 'none';
            
            if (isVisible && this.filterText) {
                row.classList.add('filtered-match');
                // Highlight matching text
                this.highlightText(row, this.filterText);
            } else {
                row.classList.remove('filtered-match');
                this.clearHighlight(row);
            }
        });
    }

    highlightText(element, text) {
        const walker = document.createTreeWalker(
            element,
            NodeFilter.SHOW_TEXT,
            null
        );

        const nodesToReplace = [];
        let node;
        while (node = walker.nextNode()) {
            if (node.textContent.toLowerCase().includes(text.toLowerCase())) {
                nodesToReplace.push(node);
            }
        }

        nodesToReplace.forEach(node => {
            const regex = new RegExp(`(${text})`, 'gi');
            const span = document.createElement('span');
            span.innerHTML = node.textContent.replace(regex, '<mark>$1</mark>');
            node.parentNode.replaceChild(span, node);
        });
    }

    clearHighlight(element) {
        const marks = element.querySelectorAll('mark');
        marks.forEach(mark => {
            const parent = mark.parentNode;
            while (mark.firstChild) {
                parent.insertBefore(mark.firstChild, mark);
            }
            parent.removeChild(mark);
        });
    }

    toggleSelectAll(checked) {
        this.tableElement.querySelectorAll('tbody .row-checkbox').forEach(checkbox => {
            checkbox.checked = checked;
            checkbox.closest('tr').classList.toggle('selected', checked);
        });
    }

    getSelectedRows() {
        return Array.from(this.tableElement.querySelectorAll('tbody .row-checkbox:checked'))
            .map(checkbox => checkbox.closest('tr'));
    }

    exportToCSV() {
        const rows = this.getSelectedRows().length > 0 
            ? this.getSelectedRows()
            : Array.from(this.tableElement.querySelectorAll('tbody tr'));

        const headers = Array.from(this.tableElement.querySelectorAll('th'))
            .map(h => h.textContent.trim());

        let csv = headers.join(',') + '\n';
        rows.forEach(row => {
            const cells = Array.from(row.querySelectorAll('td'))
                .map(td => '"' + td.textContent.trim().replace(/"/g, '""') + '"');
            csv += cells.join(',') + '\n';
        });

        this.downloadCSV(csv, 'table-export.csv');
    }

    downloadCSV(csv, filename) {
        const link = document.createElement('a');
        link.href = 'data:text/csv;charset=utf-8,' + encodeURIComponent(csv);
        link.download = filename;
        link.click();
    }

    print() {
        const rows = this.getSelectedRows().length > 0 
            ? this.getSelectedRows()
            : Array.from(this.tableElement.querySelectorAll('tbody tr'));

        const printWindow = window.open('', '_blank');
        const headers = Array.from(this.tableElement.querySelectorAll('th'))
            .map(h => `<th>${h.textContent.trim()}</th>`).join('');

        let html = '<table border="1" style="border-collapse: collapse; width: 100%;">';
        html += `<thead><tr>${headers}</tr></thead><tbody>`;
        
        rows.forEach(row => {
            html += '<tr>';
            Array.from(row.querySelectorAll('td')).forEach(td => {
                html += `<td>${td.textContent.trim()}</td>`;
            });
            html += '</tr>';
        });

        html += '</tbody></table>';
        printWindow.document.write(html);
        printWindow.print();
    }
}

// Initialize data tables on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('table[data-table]').forEach(table => {
        new DataTable({
            element: table,
            sortColumn: table.getAttribute('data-sort-column'),
            itemsPerPage: parseInt(table.getAttribute('data-items-per-page')) || 20
        });
    });
});
