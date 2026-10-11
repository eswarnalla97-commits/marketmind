// MarketMind ETL Portal Controller
document.addEventListener('DOMContentLoaded', function() {
  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('csvFileInput');
  const fileStatusBox = document.getElementById('fileStatusBox');
  const selectedFileName = document.getElementById('selectedFileName');
  const selectedFileSize = document.getElementById('selectedFileSize');
  const validationBadge = document.getElementById('validationBadge');
  const validationMsg = document.getElementById('validationMsg');
  const runETLBtn = document.getElementById('runETLBtn');
  const reloadSampleBtn = document.getElementById('reloadSampleBtn');
  const etlResultsCard = document.getElementById('etlResultsCard');
  const refreshErrorsBtn = document.getElementById('refreshErrorsBtn');

  let uploadedFilePath = null;
  let uploadedOriginalName = null;

  // Setup Drag and Drop
  ['dragenter', 'dragover'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropzone.classList.add('dragover');
    }, false);
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropzone.classList.remove('dragover');
    }, false);
  });

  dropzone.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    const files = dt.files;
    if (files.length > 0) {
      handleFileSelected(files[0]);
    }
  });

  fileInput.addEventListener('change', function() {
    if (fileInput.files.length > 0) {
      handleFileSelected(fileInput.files[0]);
    }
  });

  function handleFileSelected(file) {
    if (!file.name.toLowerCase().endsWith('.csv')) {
      MarketMind.showToast("Invalid File", "Please select a valid .csv file.", "warning");
      return;
    }

    fileStatusBox.classList.remove('d-none');
    selectedFileName.textContent = file.name;
    selectedFileSize.textContent = (file.size / 1024).toFixed(1) + ' KB';
    validationBadge.className = 'badge bg-warning text-dark';
    validationBadge.textContent = 'Uploading & Validating...';
    validationMsg.textContent = 'Verifying schema headers...';
    runETLBtn.disabled = true;

    // Send to upload API
    const formData = new FormData();
    formData.append('file', file);

    fetch('/api/upload-csv', {
      method: 'POST',
      body: formData
    })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        uploadedFilePath = data.file_path;
        uploadedOriginalName = data.filename;
        validationBadge.className = 'badge bg-success';
        validationBadge.textContent = 'Schema Validated';
        validationMsg.innerHTML = `<span class="text-success"><i class="fa-solid fa-check me-1"></i> ${data.message} (~${data.info.estimated_rows} rows found)</span>`;
        runETLBtn.disabled = false;
        MarketMind.showToast("CSV Validated", "File schema is compatible with Star Schema.", "success");
      } else {
        uploadedFilePath = null;
        validationBadge.className = 'badge bg-danger';
        validationBadge.textContent = 'Validation Failed';
        validationMsg.innerHTML = `<span class="text-danger"><i class="fa-solid fa-xmark me-1"></i> ${data.message}</span>`;
        runETLBtn.disabled = true;
        MarketMind.showToast("Validation Error", data.message, "danger");
      }
    })
    .catch(err => {
      validationBadge.className = 'badge bg-danger';
      validationBadge.textContent = 'Upload Error';
      validationMsg.textContent = err.toString();
      runETLBtn.disabled = true;
    });
  }

  // Run ETL Pipeline
  runETLBtn.addEventListener('click', function() {
    if (!uploadedFilePath) return;

    runETLBtn.disabled = true;
    runETLBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin me-1"></i> Executing Ingestion & Loading...';

    fetch('/api/run-etl', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        file_path: uploadedFilePath,
        filename: uploadedOriginalName
      })
    })
    .then(res => res.json())
    .then(data => {
      runETLBtn.disabled = false;
      runETLBtn.innerHTML = '<i class="fa-solid fa-play me-1"></i> Run Complete ETL Pipeline';

      if (data.success) {
        // Display results
        etlResultsCard.classList.remove('d-none');
        document.getElementById('etlBatchBadge').textContent = data.batch_id;
        document.getElementById('etlTotalRead').textContent = MarketMind.formatNumber(data.total_records);
        document.getElementById('etlAccepted').textContent = MarketMind.formatNumber(data.accepted_records);
        document.getElementById('etlDuplicates').textContent = MarketMind.formatNumber(data.duplicate_records);
        document.getElementById('etlRejected').textContent = MarketMind.formatNumber(data.rejected_records);

        MarketMind.showToast("ETL Complete", data.message, "success");
        loadETLHistory();
        loadStagingErrors();
      } else {
        MarketMind.showToast("ETL Failure", data.message, "danger");
      }
    })
    .catch(err => {
      runETLBtn.disabled = false;
      runETLBtn.innerHTML = '<i class="fa-solid fa-play me-1"></i> Run Complete ETL Pipeline';
      MarketMind.showToast("Error", err.toString(), "danger");
    });
  });

  // Reload Default Sample Data
  reloadSampleBtn.addEventListener('click', function() {
    if (!confirm("This will execute the ETL pipeline on the bundled sample transactions dataset. Proceed?")) return;

    reloadSampleBtn.disabled = true;
    reloadSampleBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin me-1"></i> Processing...';

    fetch('/api/run-etl', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({})
    })
    .then(res => res.json())
    .then(data => {
      reloadSampleBtn.disabled = false;
      reloadSampleBtn.innerHTML = '<i class="fa-solid fa-rotate-left me-1"></i> Reload Default Sample Data';
      if (data.success) {
        MarketMind.showToast("ETL Seed Completed", data.message, "success");
        loadETLHistory();
        loadStagingErrors();
      } else {
        MarketMind.showToast("Failed", data.message, "danger");
      }
    })
    .catch(err => {
      reloadSampleBtn.disabled = false;
      reloadSampleBtn.innerHTML = '<i class="fa-solid fa-rotate-left me-1"></i> Reload Default Sample Data';
      MarketMind.showToast("Error", err.toString(), "danger");
    });
  });

  // Load ETL History
  function loadETLHistory() {
    fetch('/api/etl-history')
      .then(res => res.json())
      .then(res => {
        if (res.success && res.data) {
          const tbody = document.getElementById('etlHistoryBody');
          let html = '';
          res.data.forEach(h => {
            const statusBadge = h.Status === 'Success' 
              ? '<span class="badge bg-success">Success</span>'
              : (h.Status === 'Partial' ? '<span class="badge bg-warning text-dark">Partial</span>' : '<span class="badge bg-danger">Failed</span>');

            html += `
              <tr>
                <td><code class="text-primary">${h.BatchID}</code></td>
                <td>${h.FileName}</td>
                <td class="fw-bold">${h.TotalRecords}</td>
                <td class="text-success fw-bold">${h.AcceptedRecords}</td>
                <td class="text-danger fw-bold">${h.RejectedRecords}</td>
                <td class="text-warning fw-bold">${h.DuplicateRecords}</td>
                <td>${h.ExecutionTimeSeconds}s</td>
                <td>${statusBadge}</td>
                <td class="text-muted small">${h.CreatedAt}</td>
              </tr>
            `;
          });
          tbody.innerHTML = html;
        }
      });
  }

  // Load Staging Errors
  function loadStagingErrors() {
    fetch('/api/staging-errors')
      .then(res => res.json())
      .then(res => {
        if (res.success && res.data) {
          const tbody = document.getElementById('stagingErrorsBody');
          if (res.data.length === 0) {
            tbody.innerHTML = `<tr><td colspan="8" class="text-center py-4 text-success"><i class="fa-solid fa-circle-check me-1"></i> Clean pipeline! No dirty or rejected records in staging.</td></tr>`;
            return;
          }
          let html = '';
          res.data.forEach(err => {
            const badgeClass = err.ValidationStatus === 'Duplicate' ? 'bg-warning text-dark' : 'bg-danger';
            html += `
              <tr>
                <td>${err.StagingID}</td>
                <td><code class="text-muted small">${err.BatchID}</code></td>
                <td>${err.InvoiceNo || '-'}</td>
                <td>${err.CustomerID || '-'}</td>
                <td>${err.ProductID || '-'}</td>
                <td><span class="badge ${badgeClass}">${err.ValidationStatus}</span></td>
                <td class="text-danger small">${err.ErrorMessage || '-'}</td>
                <td class="text-muted small">${err.ImportedAt}</td>
              </tr>
            `;
          });
          tbody.innerHTML = html;
        }
      });
  }

  if (refreshErrorsBtn) {
    refreshErrorsBtn.addEventListener('click', loadStagingErrors);
  }

  // Initial load of staging errors
  loadStagingErrors();
});
