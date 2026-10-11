// MarketMind Reports & Insights Controller
document.addEventListener('DOMContentLoaded', function() {
  loadSalesReport();
  loadProductsReport();
  loadCustomerReport();
  loadMiningReport();

  // 1. Sales Report
  function loadSalesReport() {
    fetch('/api/monthly-revenue')
      .then(res => res.json())
      .then(res => {
        if (res.success && res.data) {
          const tbody = document.getElementById('salesReportBody');
          let html = '';
          res.data.forEach(r => {
            html += `
              <tr>
                <td><code class="text-primary">${r.Period}</code></td>
                <td>${r.MonthName}</td>
                <td>${r.Year}</td>
                <td class="text-end fw-bold">${MarketMind.formatNumber(r.Orders)}</td>
                <td class="text-end">${MarketMind.formatNumber(r.Units)}</td>
                <td class="text-end fw-bold text-success">${MarketMind.formatCurrency(r.Revenue)}</td>
              </tr>
            `;
          });
          tbody.innerHTML = html;
        }
      });
  }

  // 2. Products Report
  function loadProductsReport() {
    fetch('/api/top-products?limit=50')
      .then(res => res.json())
      .then(res => {
        if (res.success && res.data) {
          const tbody = document.getElementById('productsReportBody');
          let html = '';
          res.data.forEach(p => {
            html += `
              <tr>
                <td><code class="text-primary">${p.ProductID}</code></td>
                <td class="fw-semibold text-dark">${p.ProductName}</td>
                <td><span class="badge bg-secondary-subtle text-secondary">${p.Category}</span></td>
                <td class="text-end">${MarketMind.formatCurrency(p.UnitPrice)}</td>
                <td class="text-end fw-bold">${MarketMind.formatNumber(p.UnitsSold)}</td>
                <td class="text-end fw-bold text-success">${MarketMind.formatCurrency(p.TotalRevenue)}</td>
                <td class="text-end text-muted">${MarketMind.formatNumber(p.OrdersCount)}</td>
              </tr>
            `;
          });
          tbody.innerHTML = html;
        }
      });
  }

  // 3. Customer Segments Report
  function loadCustomerReport() {
    fetch('/api/kmeans?k_clusters=4')
      .then(res => res.json())
      .then(data => {
        if (data.success && data.customers) {
          const tbody = document.getElementById('custReportBody');
          let html = '';
          data.customers.slice(0, 50).forEach(c => {
            html += `
              <tr>
                <td><code class="text-primary">${c.customer_id}</code></td>
                <td>${c.country}</td>
                <td class="text-end fw-bold text-success">${MarketMind.formatCurrency(c.monetary)}</td>
                <td class="text-end">${c.frequency}</td>
                <td class="text-end">${MarketMind.formatCurrency(c.aov)}</td>
                <td class="text-end text-muted">${c.recency} days</td>
                <td><span class="badge ${c.badge_class}">${c.segment_name}</span></td>
              </tr>
            `;
          });
          tbody.innerHTML = html;
        }
      });
  }

  // 4. Mining Report
  function loadMiningReport() {
    fetch('/api/apriori?min_support=0.015&min_confidence=0.20')
      .then(res => res.json())
      .then(data => {
        if (data.success && data.rules) {
          const tbody = document.getElementById('miningReportBody');
          if (data.rules.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center py-4 text-muted">No rules generated.</td></tr>';
            return;
          }
          let html = '';
          data.rules.slice(0, 30).forEach(r => {
            let liftBadge = r.lift >= 2.0 ? 'bg-success' : 'bg-primary';
            html += `
              <tr>
                <td class="fw-bold text-dark">${r.antecedents_str}</td>
                <td class="fw-bold text-primary">${r.consequents_str}</td>
                <td class="text-end font-monospace">${r.support_pct}%</td>
                <td class="text-end font-monospace fw-bold">${r.confidence_pct}%</td>
                <td class="text-center"><span class="badge ${liftBadge} badge-lift">${r.lift}x</span></td>
                <td class="small text-muted">${r.explanation}</td>
              </tr>
            `;
          });
          tbody.innerHTML = html;
        }
      });
  }
});
