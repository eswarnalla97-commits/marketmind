// MarketMind Global Utilities — Indian Standards (INR - ₹)
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
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 end-0 m-3 shadow-lg`;
    alertDiv.style.zIndex = '9999';
    alertDiv.style.maxWidth = '380px';
    alertDiv.innerHTML = `
      <div class="d-flex align-items-center gap-2">
        <strong>${title}</strong>
      </div>
      <div class="small mt-1">${message}</div>
      <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    document.body.appendChild(alertDiv);
    setTimeout(() => {
      alertDiv.classList.remove('show');
      setTimeout(() => alertDiv.remove(), 250);
    }, 4500);
  }
};
