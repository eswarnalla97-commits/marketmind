// ============================================================================
// MarketMind — Admin Dashboard Controller (2026 Edition)
// Handles sidebar collapse, AJAX CRUD modals, order viewers & system settings.
// ============================================================================

document.addEventListener('DOMContentLoaded', function() {
  // 1. Sidebar Collapse & Responsive Toggle
  const sidebar = document.getElementById('adminSidebar');
  const sidebarToggleBtn = document.getElementById('sidebarToggleBtn');
  const sidebarBackdrop = document.getElementById('sidebarBackdrop');

  if (sidebarToggleBtn && sidebar) {
    sidebarToggleBtn.addEventListener('click', function() {
      if (window.innerWidth < 992) {
        sidebar.classList.toggle('show-mobile');
        if (sidebarBackdrop) sidebarBackdrop.classList.toggle('show');
      } else {
        sidebar.classList.toggle('collapsed');
        localStorage.setItem('marketmind_admin_sidebar_collapsed', sidebar.classList.contains('collapsed') ? 'true' : 'false');
      }
    });
  }

  if (sidebarBackdrop) {
    sidebarBackdrop.addEventListener('click', function() {
      if (sidebar) sidebar.classList.remove('show-mobile');
      sidebarBackdrop.classList.remove('show');
    });
  }

  // Restore sidebar state from localStorage on desktop
  if (window.innerWidth >= 992 && sidebar) {
    const isCollapsed = localStorage.getItem('marketmind_admin_sidebar_collapsed') === 'true';
    if (isCollapsed) {
      sidebar.classList.add('collapsed');
    }
  }

  // 2. Global AJAX Form Interceptor Helper
  window.AdminApp = {
    handleResponse: function(res, successMsg, callback) {
      if (res.success) {
        MarketMind.showToast('Success', res.message || successMsg, 'success');
        if (callback) callback(res);
        else setTimeout(() => window.location.reload(), 700);
      } else {
        MarketMind.showToast('Error', res.message || res.error || 'Operation failed', 'error');
      }
    },

    // User Operations
    saveUser: function(formEl) {
      const formData = new FormData(formEl);
      const data = Object.fromEntries(formData.entries());
      const submitBtn = formEl.querySelector('button[type="submit"]');
      MarketMind.setLoading(submitBtn, true, 'Saving User...');

      fetch('/api/admin/users', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      })
      .then(r => r.json())
      .then(res => {
        MarketMind.setLoading(submitBtn, false);
        AdminApp.handleResponse(res, 'User created successfully');
      })
      .catch(err => {
        MarketMind.setLoading(submitBtn, false);
        MarketMind.showToast('Network Error', err.message, 'error');
      });
    },

    updateUser: function(userId, formEl) {
      const formData = new FormData(formEl);
      const data = Object.fromEntries(formData.entries());
      const submitBtn = formEl.querySelector('button[type="submit"]');
      MarketMind.setLoading(submitBtn, true, 'Updating...');

      fetch(`/api/admin/users/${userId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      })
      .then(r => r.json())
      .then(res => {
        MarketMind.setLoading(submitBtn, false);
        AdminApp.handleResponse(res, 'User updated successfully');
      })
      .catch(err => {
        MarketMind.setLoading(submitBtn, false);
        MarketMind.showToast('Network Error', err.message, 'error');
      });
    },

    toggleUserStatus: function(userId) {
      if (!confirm('Are you sure you want to toggle the active status of this user?')) return;
      fetch(`/api/admin/users/${userId}/toggle-status`, { method: 'POST' })
        .then(r => r.json())
        .then(res => AdminApp.handleResponse(res, 'Status updated'));
    },

    deleteUser: function(userId, username) {
      if (!confirm(`Are you sure you want to delete user account "${username}"? This cannot be undone.`)) return;
      fetch(`/api/admin/users/${userId}`, { method: 'DELETE' })
        .then(r => r.json())
        .then(res => AdminApp.handleResponse(res, 'User deleted'));
    },

    // Order Operations
    viewOrderDetails: function(orderKey) {
      fetch(`/api/admin/orders/${orderKey}`)
        .then(r => r.json())
        .then(res => {
          if (res.success && res.data) {
            const d = res.data;
            const modalEl = document.getElementById('orderDetailsModal');
            if (!modalEl) return;

            document.getElementById('modalOrderInvoice').textContent = d.order.InvoiceNo;
            document.getElementById('modalOrderDate').textContent = d.order.OrderDate;
            document.getElementById('modalOrderCustomer').textContent = `${d.order.CustomerName} (${d.order.CustomerID})`;
            document.getElementById('modalOrderCountry').textContent = d.order.Country;
            document.getElementById('modalOrderStatus').textContent = d.order.OrderStatus;
            document.getElementById('modalOrderTotal').textContent = MarketMind.formatCurrency(d.total_calculated);

            const tbody = document.getElementById('modalOrderItemsBody');
            tbody.innerHTML = '';
            d.items.forEach(item => {
              const tr = document.createElement('tr');
              tr.innerHTML = `
                <td><code>${item.ProductID}</code></td>
                <td><strong>${item.ProductName}</strong></td>
                <td><span class="badge bg-light text-dark border">${item.Category}</span></td>
                <td class="text-center">${item.Quantity}</td>
                <td class="text-end">${MarketMind.formatCurrency(item.UnitPrice)}</td>
                <td class="text-end fw-bold text-primary">${MarketMind.formatCurrency(item.TotalAmount)}</td>
              `;
              tbody.appendChild(tr);
            });

            const bsModal = new bootstrap.Modal(modalEl);
            bsModal.show();
          }
        });
    },

    updateOrderStatus: function(orderKey, statusSelect) {
      const newStatus = statusSelect.value;
      fetch(`/api/admin/orders/${orderKey}/status`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus })
      })
      .then(r => r.json())
      .then(res => AdminApp.handleResponse(res, `Order updated to ${newStatus}`));
    },

    deleteOrder: function(orderKey, invoiceNo) {
      if (!confirm(`Are you sure you want to delete order ${invoiceNo} and its related sales records?`)) return;
      fetch(`/api/admin/orders/${orderKey}`, { method: 'DELETE' })
        .then(r => r.json())
        .then(res => AdminApp.handleResponse(res, 'Order deleted successfully'));
    },

    // Product Operations
    saveProduct: function(formEl) {
      const formData = new FormData(formEl);
      const data = Object.fromEntries(formData.entries());
      const submitBtn = formEl.querySelector('button[type="submit"]');
      MarketMind.setLoading(submitBtn, true, 'Adding SKU...');

      fetch('/api/admin/products', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      })
      .then(r => r.json())
      .then(res => {
        MarketMind.setLoading(submitBtn, false);
        AdminApp.handleResponse(res, 'Product SKU created');
      })
      .catch(err => {
        MarketMind.setLoading(submitBtn, false);
        MarketMind.showToast('Network Error', err.message, 'error');
      });
    },

    updateProduct: function(prodKey, formEl) {
      const formData = new FormData(formEl);
      const data = Object.fromEntries(formData.entries());
      const submitBtn = formEl.querySelector('button[type="submit"]');
      MarketMind.setLoading(submitBtn, true, 'Updating SKU...');

      fetch(`/api/admin/products/${prodKey}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      })
      .then(r => r.json())
      .then(res => {
        MarketMind.setLoading(submitBtn, false);
        AdminApp.handleResponse(res, 'Product SKU updated');
      })
      .catch(err => {
        MarketMind.setLoading(submitBtn, false);
        MarketMind.showToast('Network Error', err.message, 'error');
      });
    },

    deleteProduct: function(prodKey, prodName) {
      if (!confirm(`Are you sure you want to delete product "${prodName}"?`)) return;
      fetch(`/api/admin/products/${prodKey}`, { method: 'DELETE' })
        .then(r => r.json())
        .then(res => AdminApp.handleResponse(res, 'Product SKU deleted'));
    },

    // Staging Operations
    approveStaging: function(stagingId) {
      fetch(`/api/admin/staging/${stagingId}/approve`, { method: 'POST' })
        .then(r => r.json())
        .then(res => AdminApp.handleResponse(res, 'Staging record approved and loaded into warehouse'));
    },

    rejectStaging: function(stagingId) {
      const reason = prompt('Please enter rejection reason:', 'Invalid price or duplicate record');
      if (reason === null) return;
      fetch(`/api/admin/staging/${stagingId}/reject`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason: reason })
      })
      .then(r => r.json())
      .then(res => AdminApp.handleResponse(res, 'Staging record marked as Rejected'));
    },

    clearStaging: function(status = 'all') {
      if (!confirm(`Clear ${status} records from the staging area?`)) return;
      fetch('/api/admin/staging/clear', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: status })
      })
      .then(r => r.json())
      .then(res => AdminApp.handleResponse(res, 'Staging records cleared'));
    },

    triggerETL: function(btn) {
      MarketMind.setLoading(btn, true, 'Executing ETL Pipeline...');
      fetch('/api/admin/run-etl', { method: 'POST' })
        .then(r => r.json())
        .then(res => {
          MarketMind.setLoading(btn, false);
          AdminApp.handleResponse(res, 'ETL Pipeline batch completed successfully');
        })
        .catch(err => {
          MarketMind.setLoading(btn, false);
          MarketMind.showToast('Error', err.message, 'error');
        });
    },

    // Feedback Operations
    updateFeedbackStatus: function(fbId, newStatus) {
      fetch(`/api/admin/feedback/${fbId}/status`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus })
      })
      .then(r => r.json())
      .then(res => AdminApp.handleResponse(res, `Feedback marked as ${newStatus}`));
    },

    deleteFeedback: function(fbId) {
      if (!confirm('Are you sure you want to delete this feedback submission?')) return;
      fetch(`/api/admin/feedback/${fbId}`, { method: 'DELETE' })
        .then(r => r.json())
        .then(res => AdminApp.handleResponse(res, 'Feedback submission deleted'));
    },

    // Profile & Settings Operations
    updateProfile: function(formEl) {
      const formData = new FormData(formEl);
      const data = Object.fromEntries(formData.entries());
      const submitBtn = formEl.querySelector('button[type="submit"]');
      MarketMind.setLoading(submitBtn, true, 'Saving Profile...');

      fetch('/api/admin/profile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      })
      .then(r => r.json())
      .then(res => {
        MarketMind.setLoading(submitBtn, false);
        AdminApp.handleResponse(res, 'Profile details updated');
      });
    },

    changePassword: function(formEl) {
      const formData = new FormData(formEl);
      const data = Object.fromEntries(formData.entries());

      if (data.new_password !== data.confirm_password) {
        MarketMind.showToast('Validation Error', 'New passwords do not match.', 'warning');
        return;
      }

      const submitBtn = formEl.querySelector('button[type="submit"]');
      MarketMind.setLoading(submitBtn, true, 'Updating Password...');

      fetch('/api/admin/change-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      })
      .then(r => r.json())
      .then(res => {
        MarketMind.setLoading(submitBtn, false);
        AdminApp.handleResponse(res, 'Password changed successfully', () => {
          formEl.reset();
        });
      });
    },

    updateSettings: function(formEl) {
      const formData = new FormData(formEl);
      const data = Object.fromEntries(formData.entries());
      const submitBtn = formEl.querySelector('button[type="submit"]');
      MarketMind.setLoading(submitBtn, true, 'Applying Settings...');

      fetch('/api/admin/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      })
      .then(r => r.json())
      .then(res => {
        MarketMind.setLoading(submitBtn, false);
        AdminApp.handleResponse(res, 'System settings saved');
      });
    }
  };
});
