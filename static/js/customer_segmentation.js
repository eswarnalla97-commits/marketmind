// MarketMind Customer Segmentation Controller
document.addEventListener('DOMContentLoaded', function() {
  const kSelect = document.getElementById('kClustersSelect');
  const reclusterBtn = document.getElementById('reclusterBtn');
  const searchInput = document.getElementById('custSearchInput');
  const cardsContainer = document.getElementById('clusterCardsContainer');
  const tbody = document.getElementById('customerTableBody');

  let allCustomers = [];
  let scatterChart = null;
  let donutChart = null;

  const clusterColors = [
    '#4338ca', '#0ea5e9', '#10b981', '#f59e0b', '#7c3aed', '#ec4899'
  ];

  loadSegmentation();

  reclusterBtn.addEventListener('click', loadSegmentation);
  kSelect.addEventListener('change', loadSegmentation);

  searchInput.addEventListener('input', function() {
    renderCustomerTable(this.value.trim().toLowerCase());
  });

  function loadSegmentation() {
    const k = kSelect.value;
    reclusterBtn.disabled = true;
    reclusterBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin me-1"></i> Running K-Means...';

    fetch(`/api/kmeans?k_clusters=${k}`)
      .then(res => res.json())
      .then(data => {
        reclusterBtn.disabled = false;
        reclusterBtn.innerHTML = '<i class="fa-solid fa-arrows-rotate me-1"></i> Re-Cluster';

        if (data.success) {
          allCustomers = data.customers || [];
          renderClusterCards(data.clusters);
          renderCharts(data);
          renderCustomerTable('');
          MarketMind.showToast("K-Means Completed", `Clustered ${data.total_customers} accounts into ${data.k_clusters} behavioral groups.`, "success");
        } else {
          MarketMind.showToast("Clustering Error", data.message, "danger");
        }
      })
      .catch(err => {
        reclusterBtn.disabled = false;
        reclusterBtn.innerHTML = '<i class="fa-solid fa-arrows-rotate me-1"></i> Re-Cluster';
        MarketMind.showToast("Error", err.toString(), "danger");
      });
  }

  function renderClusterCards(clusters) {
    if (!clusters || clusters.length === 0) {
      cardsContainer.innerHTML = '<div class="col-12 text-center text-muted">No clusters generated.</div>';
      return;
    }

    let html = '';
    const colWidth = clusters.length <= 4 ? (12 / clusters.length) : 4;

    clusters.forEach((c, idx) => {
      const color = clusterColors[idx % clusterColors.length];
      html += `
        <div class="col-lg-${colWidth} col-md-6">
          <div class="mm-card h-100 p-3" style="border-top: 4px solid ${color};">
            <div class="d-flex justify-content-between align-items-start mb-2">
              <div>
                <span class="badge ${c.badge} mb-1">${c.name}</span>
                <div class="text-muted" style="font-size: 0.75rem;">Cluster ID: ${c.cluster_id}</div>
              </div>
              <span class="fw-bold fs-5 text-dark">${c.percentage}%</span>
            </div>
            <p class="text-muted small mb-3" style="min-height: 38px;">${c.description}</p>
            <div class="bg-light p-2 rounded small d-flex flex-column gap-1">
              <div class="d-flex justify-content-between">
                <span class="text-muted">Accounts:</span>
                <strong>${c.customer_count}</strong>
              </div>
              <div class="d-flex justify-content-between">
                <span class="text-muted">Avg Lifetime Spend:</span>
                <strong class="text-success">${MarketMind.formatCurrency(c.avg_spend)}</strong>
              </div>
              <div class="d-flex justify-content-between">
                <span class="text-muted">Avg Order Freq:</span>
                <strong>${c.avg_frequency} orders</strong>
              </div>
              <div class="d-flex justify-content-between">
                <span class="text-muted">Avg Recency:</span>
                <strong>${c.avg_recency} days</strong>
              </div>
              <div class="d-flex justify-content-between">
                <span class="text-muted">Avg Order Value:</span>
                <strong>${MarketMind.formatCurrency(c.avg_aov)}</strong>
              </div>
            </div>
          </div>
        </div>
      `;
    });
    cardsContainer.innerHTML = html;
  }

  function renderCharts(data) {
    // 1. Scatter Chart
    const scatterCtx = document.getElementById('clusterScatterChart').getContext('2d');
    if (scatterChart) scatterChart.destroy();

    const datasets = data.clusters.map((c, idx) => {
      const points = data.scatter_data.filter(p => p.cluster === c.cluster_id);
      return {
        label: c.name,
        data: points.map(p => ({ x: p.x, y: p.y, customer_id: p.customer_id })),
        backgroundColor: clusterColors[idx % clusterColors.length],
        pointRadius: 5,
        pointHoverRadius: 8
      };
    });

    scatterChart = new Chart(scatterCtx, {
      type: 'scatter',
      data: { datasets: datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom',
            labels: { boxWidth: 10, font: { size: 11 } }
          },
          tooltip: {
            callbacks: {
              label: function(ctx) {
                const pt = ctx.raw;
                return [
                  ` Customer: ${pt.customer_id}`,
                  ` Orders: ${pt.x} | Spend: ${MarketMind.formatCurrency(pt.y)}`
                ];
              }
            }
          }
        },
        scales: {
          x: {
            title: { display: true, text: 'Order Frequency (Count)', font: { weight: 'bold' } },
            beginAtZero: true
          },
          y: {
            title: { display: true, text: 'Total Monetary Spend (₹)', font: { weight: 'bold' } },
            beginAtZero: true,
            ticks: {
              callback: function(v) { return '₹' + v.toLocaleString('en-IN'); }
            }
          }
        }
      }
    });

    // 2. Donut Chart
    const donutCtx = document.getElementById('clusterDonutChart').getContext('2d');
    if (donutChart) donutChart.destroy();

    donutChart = new Chart(donutCtx, {
      type: 'doughnut',
      data: {
        labels: data.clusters.map(c => c.name),
        datasets: [{
          data: data.clusters.map(c => c.customer_count),
          backgroundColor: data.clusters.map((_, idx) => clusterColors[idx % clusterColors.length]),
          borderWidth: 2,
          borderColor: '#ffffff'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom',
            labels: { boxWidth: 10, font: { size: 11 } }
          }
        }
      }
    });
  }

  function renderCustomerTable(query) {
    let filtered = allCustomers;
    if (query) {
      filtered = allCustomers.filter(c => 
        c.customer_id.toLowerCase().includes(query) ||
        c.country.toLowerCase().includes(query) ||
        c.segment_name.toLowerCase().includes(query)
      );
    }

    if (filtered.length === 0) {
      tbody.innerHTML = `<tr><td colspan="8" class="text-center py-4 text-muted">No customers matching "${query}".</td></tr>`;
      return;
    }

    let rowsHtml = '';
    // Show up to top 100
    filtered.slice(0, 100).forEach(c => {
      rowsHtml += `
        <tr>
          <td><code class="text-primary fw-bold">${c.customer_id}</code></td>
          <td>${c.country}</td>
          <td class="text-end fw-bold">${c.frequency}</td>
          <td class="text-end fw-bold text-success">${MarketMind.formatCurrency(c.monetary)}</td>
          <td class="text-end">${MarketMind.formatCurrency(c.aov)}</td>
          <td class="text-end text-muted">${c.recency} days</td>
          <td class="text-center"><span class="badge bg-light text-dark border">C${c.cluster_id}</span></td>
          <td><span class="badge ${c.badge_class}">${c.segment_name}</span></td>
        </tr>
      `;
    });
    tbody.innerHTML = rowsHtml;
  }
});
