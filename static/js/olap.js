// MarketMind OLAP Analytics Controller
document.addEventListener('DOMContentLoaded', function() {
  let olapChart = null;

  // Elements
  const rollupBtns = document.querySelectorAll('#rollupLevelGroup button');
  const drilldownCatSelect = document.getElementById('drilldownCategorySelect');
  const execDrilldownBtn = document.getElementById('execDrilldownBtn');
  const sliceCatSelect = document.getElementById('sliceCategorySelect');
  const execSliceBtn = document.getElementById('execSliceBtn');
  const diceCatSelect = document.getElementById('diceCatSelect');
  const diceCountrySelect = document.getElementById('diceCountrySelect');
  const diceQuarterSelect = document.getElementById('diceQuarterSelect');
  const execDiceBtn = document.getElementById('execDiceBtn');
  const refreshPivotBtn = document.getElementById('refreshPivotBtn');

  const sqlInspector = document.getElementById('sqlQueryText');
  const sqlTag = document.getElementById('sqlOperationTag');
  const chartTitle = document.getElementById('olapChartTitle');
  const chartSubtitle = document.getElementById('olapChartSubtitle');
  const chartBadge = document.getElementById('olapChartBadge');
  const tableHead = document.getElementById('olapTableHead');
  const tableBody = document.getElementById('olapTableBody');
  const rowCountBadge = document.getElementById('olapRowCountBadge');

  // Initial Load: Rollup Monthly
  executeRollup('monthly');

  // Roll-up Level Buttons
  rollupBtns.forEach(btn => {
    btn.addEventListener('click', function() {
      rollupBtns.forEach(b => b.classList.remove('active'));
      this.classList.add('active');
      executeRollup(this.getAttribute('data-level'));
    });
  });

  // Drill-down Button
  execDrilldownBtn.addEventListener('click', function() {
    executeDrilldown(drilldownCatSelect.value);
  });

  // Slice Button
  execSliceBtn.addEventListener('click', function() {
    executeSlice(sliceCatSelect.value);
  });

  // Dice Button
  execDiceBtn.addEventListener('click', executeDice);

  // Pivot Button & Tab
  refreshPivotBtn.addEventListener('click', executePivot);
  document.getElementById('pivot-tab').addEventListener('shown.bs.tab', executePivot);
  document.getElementById('rollup-tab').addEventListener('shown.bs.tab', () => executeRollup('monthly'));

  // 1. ROLL-UP EXECUTION
  function executeRollup(level) {
    sqlTag.textContent = `ROLL-UP (${level.toUpperCase()})`;
    chartTitle.textContent = `Roll-Up: ${level.toUpperCase()} Sales`;
    chartSubtitle.textContent = `Aggregating sales measures to the ${level} grain.`;
    chartBadge.textContent = 'Temporal Roll-up';

    fetch(`/api/olap/rollup?hierarchy=${level}`)
      .then(res => res.json())
      .then(res => {
        if (res.success && res.data) {
          const d = res.data;
          sqlInspector.textContent = d.sql_query;
          renderGenericGrid(d.rows);
          renderChart(
            d.rows.map(r => r.Period),
            d.rows.map(r => r.Revenue),
            level === 'daily' ? 'bar' : 'line',
            'Revenue (₹)'
          );
        }
      });
  }

  // 2. DRILL-DOWN EXECUTION
  function executeDrilldown(category) {
    sqlTag.textContent = `DRILL-DOWN (${category})`;
    chartTitle.textContent = `Drill-Down: ${category} Products`;
    chartSubtitle.textContent = `De-aggregating category totals down to individual catalog SKUs.`;
    chartBadge.textContent = 'Product SKU Grain';

    fetch(`/api/olap/drilldown?dimension=category_to_product&filter_value=${encodeURIComponent(category)}`)
      .then(res => res.json())
      .then(res => {
        if (res.success && res.data) {
          const d = res.data;
          sqlInspector.textContent = d.sql_query;
          renderGenericGrid(d.rows);
          renderChart(
            d.rows.map(r => r.ItemName),
            d.rows.map(r => r.Revenue),
            'bar',
            'Revenue (₹)'
          );
        }
      });
  }

  // 3. SLICE EXECUTION
  function executeSlice(category) {
    sqlTag.textContent = `SLICE (Category = '${category}')`;
    chartTitle.textContent = `Slice: ${category} Sub-Plane`;
    chartSubtitle.textContent = `Fixed single dimension slice across time.`;
    chartBadge.textContent = '2D Slice';

    fetch(`/api/olap/slice?slice_type=category&slice_value=${encodeURIComponent(category)}`)
      .then(res => res.json())
      .then(res => {
        if (res.success && res.data) {
          const d = res.data;
          sqlInspector.textContent = d.sql_query;
          renderGenericGrid(d.rows);
          renderChart(
            d.rows.map(r => r.Period),
            d.rows.map(r => r.Revenue),
            'line',
            `${category} Revenue (₹)`
          );
        }
      });
  }

  // 4. DICE EXECUTION
  function executeDice() {
    const cats = diceCatSelect.value === 'all' ? [] : [diceCatSelect.value];
    const countries = diceCountrySelect.value === 'all' ? [] : [diceCountrySelect.value];
    const quarters = diceQuarterSelect.value === 'all' ? [] : [diceQuarterSelect.value];

    sqlTag.textContent = `DICE (Multi-D Sub-Cube)`;
    chartTitle.textContent = `Dice: Multi-Dimensional Sub-Cube`;
    chartSubtitle.textContent = `Intersecting Category, State, and Quarter constraints.`;
    chartBadge.textContent = 'Sub-Cube';

    fetch('/api/olap/dice', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        categories: cats,
        countries: countries,
        quarters: quarters
      })
    })
    .then(res => res.json())
    .then(res => {
      if (res.success && res.data) {
        const d = res.data;
        sqlInspector.textContent = d.sql_query;
        renderGenericGrid(d.rows);
        renderChart(
          d.rows.slice(0, 10).map(r => `${r.Category} (${r.Country} ${r.Quarter})`),
          d.rows.slice(0, 10).map(r => r.Revenue),
          'bar',
          'Sub-Cube Revenue (₹)'
        );
      }
    });
  }

  // 5. PIVOT EXECUTION
  function executePivot() {
    sqlTag.textContent = `PIVOT MATRIX (Category x Quarter)`;
    chartTitle.textContent = `Pivot: Category vs Quarter Matrix`;
    chartSubtitle.textContent = `Cross-tabulation matrix of revenues.`;
    chartBadge.textContent = 'Pivot Matrix';

    fetch('/api/olap/pivot')
      .then(res => res.json())
      .then(res => {
        if (res.success && res.data) {
          const d = res.data;
          sqlInspector.textContent = `
-- OLAP PIVOT OPERATION
-- Aggregates FactSales grouped by DimProduct.Category and DimDate.Quarter
-- Rotates results into cross-tabulated matrix:
SELECT Category, Quarter, SUM(TotalAmount) AS Revenue
FROM FactSales f
JOIN DimProduct p ON f.ProductKey = p.ProductKey
JOIN DimDate d ON f.DateKey = d.DateKey
GROUP BY p.Category, d.Quarter;
          `.trim();
          renderPivotGrid(d.columns, d.rows);

          // Render chart comparing categories
          const categories = d.rows.map(r => r.Category);
          const totals = d.rows.map(r => r.Total);
          renderChart(categories, totals, 'bar', 'Total Revenue (₹)');
        }
      });
  }

  // Chart Renderer
  function renderChart(labels, values, type = 'line', label = 'Revenue') {
    const ctx = document.getElementById('olapChartCanvas').getContext('2d');
    if (olapChart) olapChart.destroy();

    const isLine = type === 'line';
    const gradient = ctx.createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, 'rgba(67, 56, 202, 0.3)');
    gradient.addColorStop(1, 'rgba(67, 56, 202, 0.0)');

    olapChart = new Chart(ctx, {
      type: type,
      data: {
        labels: labels,
        datasets: [{
          label: label,
          data: values,
          borderColor: '#4338ca',
          backgroundColor: isLine ? gradient : '#0ea5e9',
          fill: isLine,
          tension: 0.3,
          borderWidth: 2,
          borderRadius: isLine ? 0 : 5
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: function(c) {
                const val = isLine ? c.parsed.y : c.parsed.y || c.parsed.x;
                return ` ${label}: ${MarketMind.formatCurrency(val)}`;
              }
            }
          }
        },
        scales: {
          x: { grid: { display: false } },
          y: {
            beginAtZero: true,
            ticks: {
              callback: function(v) { return '₹' + v.toLocaleString('en-IN'); }
            }
          }
        }
      }
    });
  }

  // Generic Grid Renderer
  function renderGenericGrid(rows) {
    if (!rows || rows.length === 0) {
      tableHead.innerHTML = '<tr><th>Result</th></tr>';
      tableBody.innerHTML = '<tr><td class="text-center py-4 text-muted">No records found matching criteria.</td></tr>';
      rowCountBadge.textContent = '0 Rows';
      return;
    }

    rowCountBadge.textContent = `${rows.length} Rows`;
    const cols = Object.keys(rows[0]);

    // Headers
    let headHtml = '<tr>';
    cols.forEach(c => {
      headHtml += `<th>${c}</th>`;
    });
    headHtml += '</tr>';
    tableHead.innerHTML = headHtml;

    // Body
    let bodyHtml = '';
    rows.forEach(r => {
      bodyHtml += '<tr>';
      cols.forEach(c => {
        let val = r[c];
        if (c.toLowerCase().includes('revenue') || c.toLowerCase().includes('price') || c.toLowerCase().includes('value')) {
          val = `<span class="fw-bold text-success">${MarketMind.formatCurrency(val)}</span>`;
        }
        bodyHtml += `<td>${val}</td>`;
      });
      bodyHtml += '</tr>';
    });
    tableBody.innerHTML = bodyHtml;
  }

  // Pivot Table Grid Renderer
  function renderPivotGrid(columns, rows) {
    rowCountBadge.textContent = `${rows.length} Categories`;
    let headHtml = '<tr>';
    columns.forEach(c => {
      headHtml += `<th>${c}</th>`;
    });
    headHtml += '</tr>';
    tableHead.innerHTML = headHtml;

    let bodyHtml = '';
    rows.forEach(r => {
      bodyHtml += '<tr>';
      columns.forEach(c => {
        let val = r[c];
        if (c !== 'Category') {
          val = `<span class="fw-bold text-success">${MarketMind.formatCurrency(val)}</span>`;
        } else {
          val = `<strong>${val}</strong>`;
        }
        bodyHtml += `<td>${val}</td>`;
      });
      bodyHtml += '</tr>';
    });
    tableBody.innerHTML = bodyHtml;
  }
});
