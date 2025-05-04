// dashboard.js - JavaScript for the portfolio dashboard page

document.addEventListener('DOMContentLoaded', function () {
    // Check if we're on the dashboard page
    const dashboardPage = document.getElementById('portfolioValueChart');
    if (!dashboardPage) return;

    console.log('Dashboard page detected, initializing...');

    // Initialize charts
    initializeCharts();

    // Add debug button
    const debugButton = document.createElement('button');
    debugButton.innerText = 'Debug Charts';
    debugButton.className = 'btn btn-sm btn-outline-secondary mt-2';
    debugButton.style.position = 'fixed';
    debugButton.style.bottom = '10px';
    debugButton.style.right = '10px';
    debugButton.style.zIndex = '9999';
    debugButton.onclick = debugChartData;
    document.body.appendChild(debugButton);

    // Load initial data
    updatePerformance();
    updateHistoricalPerformance();
    setTimeout(debugChartData, 1000);
    updateRiskAnalysis();
    updateRecommendations();
    updateNews();

    // Set up periodic updates
    setInterval(() => {
        updatePerformance();
        updateHistoricalPerformance();
        updateRiskAnalysis();
        updateRecommendations();
        updateNews();
    }, 300000);

    // Set up event listeners for modals
    setupModalHandlers();
});

function setupModalHandlers() {
    // Stock add modal
    const addStockSubmitButton = document.getElementById('add-stock-submit');
    if (addStockSubmitButton) {
        addStockSubmitButton.addEventListener('click', async () => {
            const symbol = document.getElementById('symbol').value;
            const quantity = document.getElementById('quantity').value;
            const purchasePrice = document.getElementById('purchase-price').value;
            const purchaseDate = document.getElementById('purchase-date').value;

            // Validate required fields
            if (!symbol || !quantity) {
                alert('Stock symbol and quantity are required.');
                return;
            }

            try {
                const response = await fetch('/portfolio/add_stock', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        symbol: symbol.toUpperCase(),
                        quantity: parseInt(quantity),
                        purchase_price: purchasePrice ? parseFloat(purchasePrice) : null,
                        purchase_date: purchaseDate || null
                    })
                });

                if (response.ok) {
                    // Close the modal
                    const modal = bootstrap.Modal.getInstance(document.getElementById('addStockModal'));
                    modal.hide();

                    // Reset the form
                    document.getElementById('add-stock-form').reset();

                    // Update performance data
                    updatePerformance();
                } else {
                    const errorData = await response.json();
                    alert(`Error adding stock: ${errorData.message || 'Unknown error'}`);
                }
            } catch (error) {
                console.error('Error:', error);
                alert('Error adding stock to portfolio');
            }
        });
    }

    // Settings modal
    const settingsModal = document.getElementById('settingsModal');
    if (settingsModal) {
        settingsModal.addEventListener('show.bs.modal', loadUserSettings);
    }

    // Settings form
    const settingsForm = document.getElementById('settings-form');
    if (settingsForm) {
        settingsForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            //Getting Selected Sectors
            let selectedSectors = '';
            const sectorChecks = document.querySelectorAll('.sector-check:checked');
            if (sectorChecks && sectorChecks.length > 0) {
                selectedSectors = Array.from(sectorChecks).map(check => check.value).join(',');
            }

            const settings = {
                risk_tolerance: document.getElementById('risk_tolerance').value,
                default_chart_period: document.getElementById('default_chart_period').value,
                enable_notifications: document.getElementById('enable_notifications').checked,
                investment_goal: document.getElementById('investment_goal')?.value || 'Growth',
                time_horizon: document.getElementById('time_horizon')?.value || 'Long-term',
                preferred_sectors: selectedSectors,
                tax_consideration: document.getElementById('tax_consideration')?.checked || false
            };

            console.log("Submitting settings", settings);

            try {
                const response = await fetch('/settings/preferences', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(settings)
                });

                if (response.ok) {
                    alert('Settings saved successfully!');
                    const modal = bootstrap.Modal.getInstance(document.getElementById('settingsModal'));
                    if (modal) modal.hide();
                } else {
                    alert('Failed to save settings. Please try again.');
                }
            } catch (error) {
                console.error('Error saving settings:', error);
                alert('An error occurred while saving settings.');
            }
        });
    }

    // Sell stock modal
    const sellStockSubmitButton = document.getElementById('sell-stock-submit');
    if (sellStockSubmitButton) {
        sellStockSubmitButton.addEventListener('click', async () => {
            const symbol = document.getElementById('sell-symbol').value;
            const currentShares = parseFloat(document.getElementById('current-shares').value);
            const sellQuantity = parseFloat(document.getElementById('sell-quantity').value);
            const sellPrice = document.getElementById('sell-price').value;
            const sellDate = document.getElementById('sell-date').value;

            // Validate required fields
            if (isNaN(sellQuantity) || sellQuantity <= 0 || sellQuantity < 0.001) {
                alert('Please enter a valid quantity to sell(minimum 0.001).');
                return;
            }

            if (sellQuantity > currentShares) {
                alert(`You cannot sell more than your current holdings (${currentShares} shares).`);
                return;
            }

            // If selling all shares, use the original remove endpoint
            if (Math.abs(sellQuantity - currentShares) < 0.0001) {
                sellAllShares(symbol);

                // Close the modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('sellStockModal'));
                modal.hide();
                return;
            }

            // Otherwise, use the partial sell endpoint
            try {
                const response = await fetch('/portfolio/sell_shares', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        symbol: symbol,
                        quantity: parseFloat(sellQuantity),
                        sell_price: sellPrice ? parseFloat(sellPrice) : null,
                        sell_date: sellDate || null
                    })
                });

                if (response.ok) {
                    // Close the modal
                    const modal = bootstrap.Modal.getInstance(document.getElementById('sellStockModal'));
                    modal.hide();

                    // Reset the form
                    document.getElementById('sell-stock-form').reset();

                    // Update performance data
                    updatePerformance();
                } else {
                    const errorData = await response.json();
                    alert(`Error selling shares: ${errorData.message || 'Unknown error'}`);
                }
            } catch (error) {
                console.error('Error:', error);
                alert('Error selling shares');
            }
        });
    }
}

// Initialize Charts
function initializeCharts() {
    const valueCtx = document.getElementById('portfolioValueChart');
    const returnsCtx = document.getElementById('returnsChart');
    const pieCtx = document.getElementById('portfolio-chart');

    if (!valueCtx || !returnsCtx) {
        console.warn('Chart canvas elements not found');
        return;
    }

    window.portfolioValueChart = new Chart(valueCtx.getContext('2d'), {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Portfolio Value',
                data: [],
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Portfolio Value Over Time'
                }
            }
        }
    });

    window.returnsChart = new Chart(returnsCtx.getContext('2d'), {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Portfolio Returns',
                data: [],
                borderColor: 'rgb(153, 102, 255)',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Portfolio Returns Over Time'
                }
            }
        }
    });
    if (pieCtx) {
        window.portfolioChart = new Chart(pieCtx.getContext('2d'), {
            type: 'pie',
            data: {
                labels: [],
                datasets: [{
                    data: [],
                    backgroundColor: [
                        '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF',
                        '#FF9F40', '#8AC249', '#EA5545', '#87BC45', '#27AEEF'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right'
                    },
                    title: {
                        display: true,
                        text: 'Portfolio Composition'
                    }
                }
            }
        });
    }

    return {portfolioValueChart, returnsChart, portfolioChart: window.portfolioChart};
}

// Performance Update Function
async function updatePerformance() {
    try {
        const response = await fetch('/portfolio/performance');
        const data = await response.json();

        // Update summary values
        updateElementContent('total-value', `$${data.total_value.toFixed(2)}`);
        updateElementContent('total-return', `$${data.total_return.toFixed(2)}`);
        updateElementContent('return-percentage', `${data.total_return_percentage.toFixed(2)}%`);
        updateElementContent('total-stocks', data.holdings.length);

        // Update performance table
        const performanceTable = document.getElementById('performance-table');
        if (!performanceTable) return;

        performanceTable.innerHTML = '';

        data.holdings.forEach(holding => {
            const row = document.createElement('tr');
            const returnClass = holding.gain_loss >= 0 ? 'text-success' : 'text-danger';

            row.innerHTML = `
                <td>${holding.symbol}</td>
                <td>${holding.quantity}</td>
                <td>$${holding.purchase_price.toFixed(2)}</td>
                <td>$${holding.current_price.toFixed(2)}</td>
                <td>$${holding.current_value.toFixed(2)}</td>
                <td class="${returnClass}">$${holding.gain_loss.toFixed(2)}</td>
                <td class="${returnClass}">${holding.gain_loss_percentage.toFixed(2)}%</td>
                <td>
                    <div class="dropdown">
                        <button class="btn btn-sm btn-outline-secondary dropdown-toggle" type="button" data-bs-toggle="dropdown" aria-expanded="false">
                            Actions
                        </button>
                        <ul class="dropdown-menu">
                            <li><a class="dropdown-item text-warning" href="#" onclick="removeStock('${holding.symbol}', ${holding.quantity}); return false;">
                                <i class="bi bi-currency-dollar"></i> Sell Stock
                            </a></li>
                            <li><hr class="dropdown-divider"></li>
                            <li><a class="dropdown-item text-danger" href="#" onclick="sellAllShares('${holding.symbol}'); return false;">
                                <i class="bi bi-trash"></i> Remove All
                            </a></li>
                        </ul>
                    </div>
                </td>
            `;
            performanceTable.appendChild(row);
        });

        updateCharts(data);

    } catch (error) {
        console.error('Error updating performance:', error);
    }
}

//Update Charts Function
function updateCharts(data) {
    // Update line charts (portfolioValueChart and returnsChart)
    if (window.portfolioValueChart && window.returnsChart && data.historical_data && data.historical_data.length > 0) {
        const dates = data.historical_data.map(item => item.date);
        const values = data.historical_data.map(item => item.value);
        const returns = data.historical_data.map(item => item.return_percentage);

        // Update portfolio value chart
        window.portfolioValueChart.data.labels = dates;
        window.portfolioValueChart.data.datasets[0].data = values;
        window.portfolioValueChart.update();

        // Update returns chart
        window.returnsChart.data.labels = dates;
        window.returnsChart.data.datasets[0].data = returns;
        window.returnsChart.update();
    } else if (data.historical_data && data.historical_data.length > 0) {
        console.log('Charts not initialized or no historical data available');
    }

    // Original code for portfolio composition pie chart
    if (window.portfolioChart) {
        // Update existing chart
        window.portfolioChart.data.labels = data.holdings.map(holding => holding.symbol);
        window.portfolioChart.data.datasets[0].data = data.holdings.map(holding => holding.current_value);
        window.portfolioChart.update();
    } else if (document.getElementById('portfolio-chart')) {
        // Create new chart using Chart.js (assuming Chart.js is included)
        const ctx = document.getElementById('portfolio-chart').getContext('2d');
        window.portfolioChart = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: data.holdings.map(holding => holding.symbol),
                datasets: [{
                    data: data.holdings.map(holding => holding.current_value),
                    backgroundColor: [
                        '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF',
                        '#FF9F40', '#8AC249', '#EA5545', '#87BC45', '#27AEEF'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right'
                    },
                    title: {
                        display: true,
                        text: 'Portfolio Composition'
                    }
                }
            }
        });
    }
}

async function debugChartData() {
    console.log("Fetching and debugging historical performance data...");

    try {
        const response = await fetch('/portfolio/historical_performance');
        const data = await response.json();

        console.log("Historical performance data:", data);
        console.log("Dates:", data.dates);
        console.log("Values:", data.values);
        console.log("Returns:", data.returns);

        // Check if we have valid data
        if (!data.dates || data.dates.length === 0) {
            console.error("No historical dates available");

            // Create sample data if none exists
            console.log("Creating sample data for charts");

            const today = new Date();
            const sampleDates = [];
            const sampleValues = [];
            const sampleReturns = [];

            // Generate 30 days of sample data
            for (let i = 29; i >= 0; i--) {
                const date = new Date();
                date.setDate(today.getDate() - i);
                sampleDates.push(date.toISOString().split('T')[0]);

                // Generate some random values between 9000 and 11000
                const baseValue = 10000;
                const randomVariation = Math.random() * 2000 - 1000; // -1000 to +1000
                const value = baseValue + randomVariation;
                sampleValues.push(value);

                // Calculate sample returns
                const initialValue = sampleValues[0];
                const returnPct = ((value / initialValue) - 1) * 100;
                sampleReturns.push(returnPct);
            }

            // Update charts with sample data
            if (window.portfolioValueChart) {
                window.portfolioValueChart.data.labels = sampleDates;
                window.portfolioValueChart.data.datasets[0].data = sampleValues;
                window.portfolioValueChart.update();
            }

            if (window.returnsChart) {
                window.returnsChart.data.labels = sampleDates;
                window.returnsChart.data.datasets[0].data = sampleReturns;
                window.returnsChart.update();
            }

            console.log("Charts updated with sample data");
            return;
        }

        // If we have real data, use it
        console.log("Updating charts with real data");
        if (window.portfolioValueChart) {
            window.portfolioValueChart.data.labels = data.dates;
            window.portfolioValueChart.data.datasets[0].data = data.values;
            window.portfolioValueChart.update();
        }

        if (window.returnsChart) {
            window.returnsChart.data.labels = data.dates;
            window.returnsChart.data.datasets[0].data = data.returns;
            window.returnsChart.update();
        }

    } catch (error) {
        console.error("Error during chart debugging:", error);
    }
}

async function updateHistoricalPerformance() {
    try {
        const response = await fetch('/portfolio/historical_performance');
        const data = await response.json();

        //Checking if we have a valid data
        if (!data.dates || data.dates.length === 0) {
            console.log('No historical data available');
            return;
        }

        //Updating portfolio value chart
        if (window.portfolioValueChart) {
            window.portfolioValueChart.data.labels = data.dates;
            window.portfolioValueChart.data.datasets[0].data = data.values;
            window.portfolioValueChart.update();
        }

        //Updating returns chart
        if (window.returnsChart) {
            window.returnsChart.data.labels = data.dates;
            window.returnsChart.data.datasets[0].data = data.returns;
            window.returnsChart.update();
        }

        //Updating pie chart
        if (window.returnsChart) {
            window.returnsChart.data.labels = data.dates;
            window.returnsChart.update();
        }

        console.log('Charts updated with historical data:', data);
    } catch (error) {
        console.error('Error updating charts:', error);
    }
}

// Remove Stock Function
async function removeStock(symbol, totalQuantity) {
    // If quantity is provided, offer partial sale
    if (totalQuantity) {
        // Open sell modal
        const modal = new bootstrap.Modal(document.getElementById('sellStockModal'));
        if (!modal) {
            console.error('Sell stock modal not found');
            return;
        }

        // Set the symbol in the hidden field
        document.getElementById('sell-symbol').value = symbol;

        // Set current shares
        const formattedQuantity = parseFloat(totalQuantity).toFixed(3).replace(/\.?0+$/, '');
        document.getElementById('current-shares').value = totalQuantity;

        // Set default quantity to all shares
        document.getElementById('sell-quantity').value = totalQuantity;
        document.getElementById('sell-quantity').max = totalQuantity;

        // Update modal title
        document.getElementById('sellStockModalLabel').textContent = `Sell ${symbol} Shares`;

        // Show the modal
        modal.show();
    } else {
        // Original full removal behavior
        if (confirm(`Are you sure you want to remove ${symbol} from your portfolio?`)) {
            sellAllShares(symbol);
        }
    }
}

// Function to sell all shares (original removeStock functionality)
async function sellAllShares(symbol) {
    try {
        const response = await fetch(`/portfolio/remove_stock/${symbol}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            updatePerformance();
        } else {
            alert('Error removing stock from portfolio');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error removing stock from portfolio');
    }
}

async function updateRiskAnalysis() {
    try {
        const response = await fetch('/portfolio/risk_analysis');
        const data = await response.json();

        // Updating Risk Metrics
        updateElementContent('risk-level', data.risk_level);
        updateElementContent('volatility', (data.volatility * 100).toFixed(2) + '%');
        updateElementContent('sharpe-ratio', data.sharpe_ratio.toFixed(2));
        updateElementContent('diversification-score', (data.diversification_score * 100).toFixed(2) + '%');

        // Updating Stock Risks table
        const riskTable = document.getElementById('stock-risks-table');
        if (!riskTable) return;

        const tbody = riskTable.getElementsByTagName('tbody')[0];
        if (!tbody) return;

        tbody.innerHTML = '';

        Object.entries(data.individual_stock_risks).forEach(([symbol, risk]) => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${symbol}</td>
                <td>${(risk.volatility * 100).toFixed(2)}%</td>
                <td class="risk-${risk.risk_level.toLowerCase()}">${risk.risk_level}</td>
            `;
            tbody.appendChild(row);
        });
    } catch (error) {
        console.error('Error updating risk analysis:', error);
    }
}

// Update Recommendations
async function updateRecommendations() {
    try {
        const response = await fetch('/portfolio/recommendations');
        const data = await response.json();

        const container = document.getElementById('recommendations-container');
        if (!container) return;

        container.innerHTML = '';

        if (data.recommendations && data.recommendations.length > 0) {
            const recommendationList = document.createElement('div');

            data.recommendations.forEach(rec => {
                const card = document.createElement('div');
                card.className = `card mb-3 border-${getPriorityClass(rec.priority)}`;

                let typeIcon = '';
                switch (rec.type) {
                    case 'diversification':
                        typeIcon = '<i class="bi bi-diagram-3"></i>';
                        break;
                    case 'sector':
                        typeIcon = '<i class="bi bi-pie-chart"></i> ';
                        break;
                    case 'risk':
                        typeIcon = '<i class="bi bi-exclamation-triangle"></i> ';
                        break;
                    case 'rebalance':
                        typeIcon = '<i class="bi bi-arrow-repeat"></i> ';
                        break;
                    case 'stock_specific':
                        typeIcon = '<i class="bi bi-graph-up"></i> ';
                        break;
                }

                card.innerHTML = `
                    <div class="card-body">
                        <h5 class="card-title">${typeIcon}${rec.recommendation}</h5>
                        <p class="card-text text-muted">${rec.reasoning}</p>
                        <span class="badge bg-${getPriorityClass(rec.priority)}">${rec.priority}</span>
                    </div>
                `;

                recommendationList.appendChild(card);
            });

            container.appendChild(recommendationList);
        } else {
            container.innerHTML = '<p class="text-center">No recommendations available at this time.</p>';
        }
    } catch (error) {
        console.error('Error updating recommendations:', error);
        updateElementContent('recommendations-container', '<div class="alert alert-danger">Error loading recommendations.</div>');
    }
}

// News Update Function
async function updateNews() {
    try {
        const response = await fetch('/portfolio/news');
        const data = await response.json();

        const container = document.getElementById('news-container');
        if (!container) return;

        container.innerHTML = '';

        if (data.news && data.news.length > 0) {
            const newsContainer = document.createElement('div');

            data.news.forEach(item => {
                const sentimentClass = getSentimentClass(item.sentiment);

                const newsCard = document.createElement('div');
                newsCard.className = 'card mb-2'
                newsCard.innerHTML = `
                    <div class="card-body">
                        <div class="d-flex justify-content-between">
                            <h5 class="card-title">${item.title}</h5>
                            <span class="badge ${sentimentClass}">${item.sentiment}</span>
                        </div>
                        <h6 class="card-subtitle mb-2 text-muted">${item.source} · ${formatDate(item.published_at)}</h6>
                        <p class="card-text">${item.summary}</p>
                        <div class="d-flex justify-content-between">
                            <span class="badge bg-secondary">${item.symbol}</span>
                            <a href="${item.url}" target="_blank" class="btn btn-sm btn-primary">Read More</a>
                        </div>
                    </div>
                `;

                newsContainer.appendChild(newsCard);
            });

            container.appendChild(newsContainer);
        } else {
            container.innerHTML = '<p class="text-center">No news available at this time.</p>';
        }
    } catch (error) {
        console.error('Error updating news:', error);
        updateElementContent('news-container', '<div class="alert alert-danger">Error loading news.</div>');
    }
}

//User Settings Function
async function loadUserSettings() {
    try {
        const response = await fetch('/settings/preferences');
        const settings = await response.json();

        // Set form values
        if (document.getElementById('risk_tolerance')) {
            document.getElementById('risk_tolerance').value = settings.risk_tolerance || 'Moderate';
        }
        if (document.getElementById('default_chart_period')) {
            document.getElementById('default_chart_period').value = settings.default_chart_period || '1m';
        }
        if (document.getElementById('enable_notifications')) {
            document.getElementById('enable_notifications').checked = settings.enable_notifications || false;
        }
        if (document.getElementById('investment_goal')) {
            document.getElementById('investment_goal').value = settings.investment_goal || 'Growth';
        }
        if (document.getElementById('time_horizon')) {
            document.getElementById('time_horizon').value = settings.time_horizon || 'Long-term';
        }
        if (document.getElementById('tax_consideration')) {
            document.getElementById('tax_consideration').checked = settings.tax_consideration || false;
        }

        // Handling sectors if they exist
        if (settings.preferred_sectors) {
            const sectors = settings.preferred_sectors.split(',');
            sectors.forEach(sector => {
                const checkbox = document.querySelector(`.sector-check[value="${sector}"]`);
                if (checkbox) checkbox.checked = true;
            });
        }
    } catch (error) {
        console.error('Error loading settings:', error);
    }
}

function setupPushNotifications() {
  if ('Notification' in window) {
    Notification.requestPermission().then(function(permission) {
      if (permission === 'granted') {
        // Set up websocket or polling for new notifications
        pollForNewNotifications();
      }
    });
  }
}

function pollForNewNotifications() {
  setInterval(() => {
    fetch('/api/notifications?unread=true&limit=1')
      .then(response => response.json())
      .then(data => {
        if (data.notifications.length > 0 && data.notifications[0].id > lastNotificationId) {
          const notification = data.notifications[0];
          new Notification(notification.title, {
            body: notification.message,
            icon: '/static/img/notification-icon.png'
          });
          lastNotificationId = notification.id;
        }
      });
  }, 30000); // Poll every 30 seconds
}