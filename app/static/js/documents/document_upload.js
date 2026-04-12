const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const filePreview = document.getElementById('filePreview');
const filesList = document.getElementById('filesList');

dropZone.addEventListener('click', () => fileInput.click());
dropZone.addEventListener('dragover', handleDragOver);
dropZone.addEventListener('dragleave', handleDragLeave);
dropZone.addEventListener('drop', handleDrop);

fileInput.addEventListener('change', handleFileSelect);

function handleDragOver(e) {
    e.preventDefault();
    dropZone.classList.add('drag-over');
}

function handleDragLeave() {
    dropZone.classList.remove('drag-over');
}

function handleDrop(e) {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
    fileInput.files = e.dataTransfer.files;
    updateFilePreview();
}

function handleFileSelect() {
    updateFilePreview();
}

function updateFilePreview() {
    filesList.innerHTML = '';
    const files = fileInput.files;
    
    if (files.length === 0) {
        filePreview.style.display = 'none';
        return;
    }
    
    filePreview.style.display = 'block';
    
    Array.from(files).forEach((file, index) => {
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item';
        fileItem.innerHTML = `
            <div class="file-info">
                <span class="file-name">${file.name}</span>
                <span class="file-size">${(file.size / 1024).toFixed(2)} KB</span>
            </div>
            <button type="button" class="file-remove" onclick="removeFile(${index})">Remove</button>
        `;
        filesList.appendChild(fileItem);
    });
}

function removeFile(index) {
    const dt = new DataTransfer();
    const files = fileInput.files;
    
    for (let i = 0; i < files.length; i++) {
        if (i !== index) {
            dt.items.add(files[i]);
        }
    }
    
    fileInput.files = dt.files;
    updateFilePreview();
}

function clearFiles() {
    fileInput.value = '';
    filePreview.style.display = 'none';
}

document.getElementById('uploadForm').addEventListener('submit', function(e) {
    if (fileInput.files.length === 0) {
        e.preventDefault();
        alert('Please select a file to upload');
    }
});

