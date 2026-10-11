// MarketMind Dashboard Analytics Controller
document.addEventListener('DOMContentLoaded', function() {
  let monthlyChart = null;
  let categoryChart = null;
  let countryChart = null;

  const filterForm = document.getElementById('dashboardFilterForm');
  const filterCategory = document.getElementById('filterCategory');
  const filterYear = document.getElementById('filterYear');
  const resetBtn = document.getElementById('resetFilterBtn');

  // Load initial data
  loadDashboardData();

  // Form submit handler
  filterForm.addEventListener('submit', function(e) {
    e.preventDefault();
    loadDashboardData();
  });

  resetBtn.addEventListener('click', function() {
    filterCategory.value = 'all';
    filterYear.value = 'all';
    loadDashboardData();
  });

  function loadDashboardData() {
    const category = filterCategory.value;
    const year = filterYear.value;

    fetchKPIs(category, year);
    fetchMonthlyRevenue(category, year);
    fetchCategorySales(year);
    fetchCountrySales();
    fetchTopProducts(category);
  }

  // 1. Fetch & Update KPIs
  function fetchKPIs(category, year) {
    let url = `/api/kpis?category=${encodeURIComponent(category)}&year=${encodeURIComponent(year)}`;
    fetch(url)
      .then(res => res.json())
      .then(res => {
        if (res.success && res.data) {
          const d = res.data;
          document.getElementById('kpiRevenue').textContent = MarketMind.formatCurrency(d.total_revenue);
          document.getElementById('kpiOrders').textContent = MarketMind.formatNumber(d.total_orders);
          document.getElementById('kpiCustomers').textContent = MarketMind.formatNumber(d.total_customers);
          document.getElementById('kpiUnits').textContent = MarketMind.formatNumber(d.total_products_sold);
          document.getElementById('kpiAOV').textContent = MarketMind.formatCurrency(d.average_order_value);
        }
      })
      .catch(err => console.error("Error fetching KPIs:", err));
  }

  // 2. Fetch & Render Monthly Revenue Trend
  function fetchMonthlyRevenue(category, year) {
    let url = `/api/monthly-revenue?category=${encodeURIComponent(category)}&year=${encodeURIComponent(year)}`;
    fetch(url)
      .then(res => res.json())
      .then(res => {
        if (res.success && res.data) {
          renderMonthlyChart(res.data);
        }
      })
      .catch(err => console.error("Error fetching monthly revenue:", err));
  }

  function renderMonthlyChart(data) {
    const ctx = document.getElementById('monthlyRevenueChart').getContext('2d');
    const labels = data.map(d => d.Period);
    const revenues = data.map(d => d.Revenue);
    const orders = data.map(d => d.Orders);

    if (monthlyChart) {
      monthlyChart.destroy();
    }

    const gradient = ctx.createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, 'rgba(67, 56, 202, 0.35)');
    gradient.addColorStop(1, 'rgba(67, 56, 202, 0.0)');

    monthlyChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [{
          label: 'Revenue (₹)',
          data: revenues,
          borderColor: '#4338ca',
          backgroundColor: gradient,
          fill: true,
          tension: 0.35,
          borderWidth: 2.5,
          pointRadius: 4,
          pointBackgroundColor: '#4338ca',
          pointHoverRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: function(context) {
                return ` Revenue: ${MarketMind.formatCurrency(context.parsed.y)}`;
              }
            }
          }
        },
        scales: {
          x: {
            grid: { display: false }
          },
          y: {
            beginAtZero: true,
            ticks: {
              callback: function(val) {
                return '₹' + val.toLocaleString('en-IN');
              }
            }
          }
        }
      }
    });
  }

  // 3. Fetch & Render Category Sales
  function fetchCategorySales(year) {
    let url = `/api/sales-by-category?year=${encodeURIComponent(year)}`;
    fetch(url)
      .then(res => res.json())
      .then(res => {
        if (res.success && res.data) {
          renderCategoryChart(res.data);
        }
      })
      .catch(err => console.error("Error fetching category sales:", err));
  }

  function renderCategoryChart(data) {
    const ctx = document.getElementById('categoryDonutChart').getContext('2d');
    const labels = data.map(d => d.Category);
    const revenues = data.map(d => d.Revenue);

    if (categoryChart) {
      categoryChart.destroy();
    }

    const colors = [
      '#4338ca', '#0ea5e9', '#10b981', '#f59e0b', '#7c3aed', '#ec4899'
    ];

    categoryChart = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: labels,
        datasets: [{
          data: revenues,
          backgroundColor: colors.slice(0, labels.length),
          borderWidth: 2,
          borderColor: '#ffffff',
          hoverOffset: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '70%',
        plugins: {
          legend: {
            position: 'bottom',
            labels: {
              boxWidth: 12,
              font: { size: 11 }
            }
          },
          tooltip: {
            callbacks: {
              label: function(context) {
                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                const pct = ((context.parsed / total) * 100).toFixed(1);
                return ` ${context.label}: ${MarketMind.formatCurrency(context.parsed)} (${pct}%)`;
              }
            }
          }
        }
      }
    });
  }

  // 4. Fetch & Render Geographic Country Sales
  function fetchCountrySales() {
    fetch('/api/sales-by-country')
      .then(res => res.json())
      .then(res => {
        if (res.success && res.data) {
          renderCountryChart(res.data);
        }
      })
      .catch(err => console.error("Error fetching country sales:", err));
  }

  function renderCountryChart(data) {
    const ctx = document.getElementById('countryBarChart').getContext('2d');
    const labels = data.map(d => d.Country);
    const revenues = data.map(d => d.Revenue);

    if (countryChart) {
      countryChart.destroy();
    }

    countryChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: 'Revenue (₹)',
          data: revenues,
          backgroundColor: '#0ea5e9',
          borderRadius: 6,
          borderSkipped: false
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        indexAxis: 'y',
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: function(context) {
                return ` Revenue: ${MarketMind.formatCurrency(context.parsed.x)}`;
              }
            }
          }
        },
        scales: {
          x: {
            beginAtZero: true,
            ticks: {
              callback: function(val) {
                return '₹' + val.toLocaleString('en-IN');
              }
            }
          },
          y: {
            grid: { display: false }
          }
        }
      }
    });
  }

  // 5. Fetch & Render Top Products
  function fetchTopProducts(category) {
    let url = `/api/top-products?limit=10&category=${encodeURIComponent(category)}`;
    fetch(url)
      .then(res => res.json())
      .then(res => {
        if (res.success && res.data) {
          renderTopProductsTable(res.data);
        }
      })
      .catch(err => console.error("Error fetching top products:", err));
  }

  function renderTopProductsTable(products) {
    const tbody = document.getElementById('topProductsBody');
    if (!products || products.length === 0) {
      tbody.innerHTML = `<tr><td colspan="8" class="text-center py-4 text-muted">No products found matching criteria.</td></tr>`;
      return;
    }

    let rowsHtml = '';
    products.forEach((p, idx) => {
      const rankBadge = idx === 0 
        ? `<span class="badge bg-warning text-dark"><i class="fa-solid fa-crown me-1"></i>#1</span>`
        : `<span class="badge bg-light text-dark border">#${idx + 1}</span>`;

      rowsHtml += `
        <tr>
          <td>${rankBadge}</td>
          <td><code class="text-primary fw-bold">${p.ProductID}</code></td>
          <td class="fw-semibold text-dark">${p.ProductName}</td>
          <td><span class="badge bg-secondary-subtle text-secondary">${p.Category}</span></td>
          <td class="text-end">${MarketMind.formatCurrency(p.UnitPrice)}</td>
          <td class="text-end fw-bold">${MarketMind.formatNumber(p.UnitsSold)}</td>
          <td class="text-end fw-bold text-success">${MarketMind.formatCurrency(p.TotalRevenue)}</td>
          <td class="text-end text-muted">${MarketMind.formatNumber(p.OrdersCount)}</td>
        </tr>
      `;
    });
    tbody.innerHTML = rowsHtml;
  }
});
