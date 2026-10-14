// ============================================================================
// MarketMind Global Utilities — Indian Standards (INR - ₹) & Modern UI Helpers
// ============================================================================

window.MarketMind = {
  formatCurrency: function(val) {
    if (val === null || val === undefined || isNaN(val)) return '₹0.00';
    return '₹' + parseFloat(val).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  },

  formatNumber: function(val) {
    if (val === null || val === undefined || isNaN(val)) return '0';
    return parseInt(val).toLocaleString('en-IN');
  },

  showToast: function(title, message, type = 'info') {
    let container = document.getElementById('mmToastContainer');
    if (!container) {
      container = document.createElement('div');
      container.id = 'mmToastContainer';
      container.className = 'toast-container-fixed';
      document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `mm-toast toast-${type}`;

    let iconClass = 'fa-solid fa-circle-info text-primary';
    if (type === 'success') iconClass = 'fa-solid fa-circle-check text-success';
    else if (type === 'error' || type === 'danger') iconClass = 'fa-solid fa-circle-exclamation text-danger';
    else if (type === 'warning') iconClass = 'fa-solid fa-triangle-exclamation text-warning';

    toast.innerHTML = `
      <div class="fs-5 mt-1"><i class="${iconClass}"></i></div>
      <div class="flex-grow-1">
        <div class="fw-bold text-dark small">${title}</div>
        <div class="text-muted small mt-1" style="font-size: 0.82rem; line-height: 1.4;">${message}</div>
      </div>
      <button type="button" class="btn-close ms-2" style="font-size: 0.7rem;" aria-label="Close"></button>
    `;

    toast.querySelector('.btn-close').addEventListener('click', () => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(30px)';
      setTimeout(() => toast.remove(), 250);
    });

    container.appendChild(toast);

    setTimeout(() => {
      if (toast.parentElement) {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(30px)';
        setTimeout(() => toast.remove(), 250);
      }
    }, 4500);
  },

  setLoading: function(btnElement, isLoading, loadingText = 'Processing...') {
    if (!btnElement) return;
    if (isLoading) {
      btnElement.dataset.originalHtml = btnElement.innerHTML;
      btnElement.disabled = true;
      btnElement.innerHTML = `<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>${loadingText}`;
    } else {
      btnElement.disabled = false;
      if (btnElement.dataset.originalHtml) {
        btnElement.innerHTML = btnElement.dataset.originalHtml;
      }
    }
  }
};
