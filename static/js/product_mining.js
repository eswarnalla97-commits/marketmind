// MarketMind Apriori Association Mining Controller
document.addEventListener('DOMContentLoaded', function() {
  const form = document.getElementById('aprioriForm');
  const minSupportSlider = document.getElementById('minSupport');
  const minConfidenceSlider = document.getElementById('minConfidence');
  const supportValDisplay = document.getElementById('supportValDisplay');
  const confValDisplay = document.getElementById('confValDisplay');
  const sortByMetric = document.getElementById('sortByMetric');
  const categoryFilter = document.getElementById('categoryFilter');
  const runBtn = document.getElementById('runAprioriBtn');

  let scatterChart = null;

  // Sync sliders to badges
  minSupportSlider.addEventListener('input', function() {
    supportValDisplay.textContent = (parseFloat(this.value) * 100).toFixed(1) + '%';
  });

  minConfidenceSlider.addEventListener('input', function() {
    confValDisplay.textContent = (parseFloat(this.value) * 100).toFixed(0) + '%';
  });

  // Run Apriori
  form.addEventListener('submit', function(e) {
    e.preventDefault();
    executeApriori();
  });

  // Initial execution on load
  executeApriori();

  function executeApriori() {
    runBtn.disabled = true;
    runBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin me-1"></i> Mining...';

    const payload = {
      min_support: parseFloat(minSupportSlider.value),
      min_confidence: parseFloat(minConfidenceSlider.value),
      sort_by: sortByMetric.value,
      category: categoryFilter.value
    };

    fetch('/api/apriori', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
    .then(res => res.json())
    .then(data => {
      runBtn.disabled = false;
      runBtn.innerHTML = '<i class="fa-solid fa-play me-1"></i> Run Apriori';

      if (data.success) {
        updateSummaryStats(data);
        renderTopCombos(data.top_combinations);
        renderRulesScatter(data.rules);
        renderRulesTable(data.rules);
        MarketMind.showToast("Mining Complete", data.message, "success");
      } else {
        MarketMind.showToast("Mining Notice", data.message, "warning");
        document.getElementById('associationRulesBody').innerHTML = `
          <tr><td colspan="7" class="text-center py-4 text-muted">${data.message}</td></tr>
        `;
      }
    })
    .catch(err => {
      runBtn.disabled = false;
      runBtn.innerHTML = '<i class="fa-solid fa-play me-1"></i> Run Apriori';
      MarketMind.showToast("Error", err.toString(), "danger");
    });
  }

  function updateSummaryStats(data) {
    const s = data.summary;
    document.getElementById('statBaskets').textContent = MarketMind.formatNumber(s.total_transactions);
    document.getElementById('statItemsets').textContent = MarketMind.formatNumber(s.frequent_itemsets_found);
    document.getElementById('statRules').textContent = MarketMind.formatNumber(s.rules_generated);
    document.getElementById('statMaxLift').textContent = s.max_lift > 0 ? `${s.max_lift}x` : 'N/A';
    document.getElementById('rulesCountBadge').textContent = `${data.rules.length} Rules`;
  }

  function renderTopCombos(combos) {
    const container = document.getElementById('topCombosList');
    if (!combos || combos.length === 0) {
      container.innerHTML = `<div class="p-4 text-center text-muted">No multi-item frequent bundles found at this support threshold.</div>`;
      return;
    }

    let html = '';
    combos.forEach((c, idx) => {
      html += `
        <div class="list-group-item d-flex justify-content-between align-items-center p-3">
          <div>
            <div class="fw-bold text-dark small mb-1">
              <span class="badge bg-light text-dark border me-1">#${idx + 1}</span>
              ${c.items_str}
            </div>
            <div class="text-muted" style="font-size: 0.78rem;">
              Co-purchased in ~${c.transaction_count} orders
            </div>
          </div>
          <span class="badge bg-purple-subtle text-purple border" style="color: #7c3aed; background: rgba(124, 58, 237, 0.1);">
            ${c.support_pct}% Sup
          </span>
        </div>
      `;
    });
    container.innerHTML = html;
  }

  function renderRulesScatter(rules) {
    const ctx = document.getElementById('rulesScatterChart').getContext('2d');
    if (scatterChart) {
      scatterChart.destroy();
    }

    if (!rules || rules.length === 0) {
      return;
    }

    const scatterData = rules.map(r => ({
      x: r.confidence_pct,
      y: r.lift,
      rule: r
    }));

    scatterChart = new Chart(ctx, {
      type: 'scatter',
      data: {
        datasets: [{
          label: 'Association Rules',
          data: scatterData,
          backgroundColor: 'rgba(67, 56, 202, 0.7)',
          borderColor: '#4338ca',
          borderWidth: 1.5,
          pointRadius: 6,
          pointHoverRadius: 9
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: function(ctx) {
                const r = ctx.raw.rule;
                return [
                  ` If Bought: ${r.antecedents_str}`,
                  ` Then Also: ${r.consequents_str}`,
                  ` Lift: ${r.lift}x | Confidence: ${r.confidence_pct}% | Support: ${r.support_pct}%`
                ];
              }
            }
          }
        },
        scales: {
          x: {
            title: {
              display: true,
              text: 'Confidence (%)',
              font: { weight: 'bold' }
            },
            min: 0,
            max: 100
          },
          y: {
            title: {
              display: true,
              text: 'Lift Ratio',
              font: { weight: 'bold' }
            },
            beginAtZero: false
          }
        }
      }
    });
  }

  function renderRulesTable(rules) {
    const tbody = document.getElementById('associationRulesBody');
    if (!rules || rules.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="text-center py-4 text-muted">No rules satisfied the minimum confidence and support thresholds.</td></tr>`;
      return;
    }

    let rowsHtml = '';
    rules.forEach((r, idx) => {
      let liftBadge = 'bg-secondary';
      if (r.lift >= 2.0) liftBadge = 'bg-success';
      else if (r.lift >= 1.2) liftBadge = 'bg-primary';
      else if (r.lift < 1.0) liftBadge = 'bg-warning text-dark';

      rowsHtml += `
        <tr>
          <td><span class="text-muted small">${idx + 1}</span></td>
          <td><span class="fw-bold text-dark">${r.antecedents_str}</span></td>
          <td><span class="fw-bold text-primary">${r.consequents_str}</span></td>
          <td class="text-end font-monospace">${r.support_pct}%</td>
          <td class="text-end font-monospace fw-bold">${r.confidence_pct}%</td>
          <td class="text-center">
            <span class="badge ${liftBadge} badge-lift">${r.lift}x</span>
          </td>
          <td>
            <small class="text-muted"><i class="fa-solid fa-arrow-turn-down text-primary me-1"></i> ${r.explanation}</small>
          </td>
        </tr>
      `;
    });
    tbody.innerHTML = rowsHtml;
  }
});
