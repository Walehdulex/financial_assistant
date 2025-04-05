document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on the analysis page
    const analysisPage = document.getElementById('analysisTabContent');
    if (!analysisPage) return;

    console.log('Analysis page detected, initializing...');

    // Set up tab change listeners
    document.querySelectorAll('.nav-link').forEach(tab => {
        tab.addEventListener('click', function() {
            console.log('Tab clicked:', this.textContent);

            // Get the target from data-bs-target attribute
            const target = this.getAttribute('data-bs-target');

            if (target === '#recommendations') {
                loadRecommendations();
            } else if (target === '#risk') {
                loadRiskAnalysis();
            } else if (target === '#forecasts') {
                loadForecasts();
            }
        });
    });

    // Load the active tab content on page load
    const activeTab = document.querySelector('.nav-link.active');
    if (activeTab) {
        console.log('Active tab on load:', activeTab.textContent);

        const target = activeTab.getAttribute('data-bs-target');
        if (target === '#recommendations') {
            loadRecommendations();
        } else if (target === '#risk') {
            loadRiskAnalysis();
        } else if (target === '#forecasts') {
            loadForecasts();
        }
    } else {
        // Default to recommendations if no active tab
        loadRecommendations();
    }
});

//Loads recommendation data and updates the recommendations container

async function loadRecommendations() {
    try {
        console.log('Loading recommendations...');
        const container = document.getElementById('recommendations-container');
        if (!container) {
            console.error('Recommendations container not found');
            return;
        }

        // Show loading state
        container.innerHTML = `
            <div class="text-center p-5">
                <div class="spinner-border" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-2">Analyzing your portfolio and generating recommendations...</p>
            </div>
        `;

        const response = await fetch('/portfolio/enhanced-recommendations');
        const data = await response.json();
        console.log('Recommendations data received:', data);

        container.innerHTML = '';

        if (data.recommendations && data.recommendations.length > 0) {
            data.recommendations.forEach(rec => {
                const card = document.createElement('div');
                card.className = `card mb-3 border-${getPriorityClass(rec.priority)}`;

                let iconClass = '';
                switch(rec.type) {
                    case 'buy': iconClass = 'bi-graph-up-arrow text-success'; break;
                    case 'sell': iconClass = 'bi-graph-down-arrow text-danger'; break;
                    case 'diversification': iconClass = 'bi-diagram-3'; break;
                    case 'sector': iconClass = 'bi-pie-chart'; break;
                    case 'concentration': iconClass = 'bi-exclamation-triangle text-warning'; break;
                    default: iconClass = 'bi-info-circle';
                }

                let confidenceHtml = '';
                if (rec.confidence) {
                    confidenceHtml = `<div class="progress mt-2" style="height: 5px;">
                        <div class="progress-bar" role="progressbar" style="width: ${rec.confidence * 100}%" 
                             aria-valuenow="${rec.confidence * 100}" aria-valuemin="0" aria-valuemax="100"></div>
                    </div>
                    <small class="text-muted">Confidence: ${(rec.confidence * 100).toFixed(0)}%</small>`;
                }

                let symbolBadge = rec.symbol ? `<span class="badge bg-secondary me-2">${rec.symbol}</span>` : '';

                card.innerHTML = `
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-center">
                            <h5 class="card-title">
                                <i class="bi ${iconClass} me-2"></i>
                                ${symbolBadge}
                                ${rec.action}
                            </h5>
                            <span class="badge bg-${getPriorityClass(rec.priority)}">${rec.priority}</span>
                        </div>
                        <p class="card-text">${rec.reasoning}</p>
                        ${confidenceHtml}
                    </div>
                `;

                container.appendChild(card);
            });
        } else {
            container.innerHTML = '<div class="alert alert-info">No recommendations available at this time.</div>';
        }
    } catch (error) {
        console.error('Error loading recommendations:', error);
        if (container) {
            container.innerHTML = '<div class="alert alert-danger">Error loading recommendations</div>';
        }
    }
}

async function loadRiskAnalysis() {
    try {
        console.log('Loading risk analysis...');
        const chartContainer = document.getElementById('riskChart');
        const stockRisksContainer = document.getElementById('stock-risks-container');

        if (!chartContainer || !stockRisksContainer) {
            console.error('Risk analysis elements not found');
            return;
        }

        // Show loading states
        stockRisksContainer.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"></div><p>Loading risk data...</p></div>';

        const response = await fetch('/portfolio/risk_analysis');
        const data = await response.json();
        console.log('Risk analysis data received:', data);

        // Create risk radar chart
        const ctx = chartContainer.getContext('2d');
        new Chart(ctx, {
            type: 'radar',
            data: {
                labels: ['Volatility', 'Sharpe Ratio', 'Diversification', 'Beta', 'Correlation'],
                datasets: [{
                    label: 'Your Portfolio',
                    data: [
                        data.volatility * 100,
                        data.sharpe_ratio,
                        data.diversification_score * 100,
                        data.beta || 1,
                        data.correlation || 0.8
                    ],
                    fill: true,
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    borderColor: 'rgb(54, 162, 235)',
                    pointBackgroundColor: 'rgb(54, 162, 235)',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: 'rgb(54, 162, 235)'
                }]
            },
            options: {
                elements: {
                    line: {
                        borderWidth: 3
                    }
                },
                scales: {
                    r: {
                        angleLines: {
                            display: true
                        },
                        suggestedMin: 0,
                        suggestedMax: 100
                    }
                }
            }
        });

        // Create stock risks table
        stockRisksContainer.innerHTML = '';

        const table = document.createElement('table');
        table.className = 'table table-striped';
        table.innerHTML = `
            <thead>
                <tr>
                    <th>Symbol</th>
                    <th>Volatility</th>
                    <th>Risk Level</th>
                </tr>
            </thead>
            <tbody id="stock-risks-tbody"></tbody>
        `;

        stockRisksContainer.appendChild(table);

        const tbody = document.getElementById('stock-risks-tbody');
        if (!tbody) {
            console.error('Stock risks table body not found');
            return;
        }

        for (const [symbol, risk] of Object.entries(data.individual_stock_risks)) {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${symbol}</td>
                <td>${(risk.volatility * 100).toFixed(2)}%</td>
                <td><span class="badge bg-${getRiskClass(risk.risk_level)}">${risk.risk_level}</span></td>
            `;
            tbody.appendChild(row);
        }
    } catch (error) {
        console.error('Error loading risk analysis:', error);
        const container = document.getElementById('stock-risks-container');
        if (container) {
            container.innerHTML = '<div class="alert alert-danger">Error loading risk analysis data</div>';
        }
    }
}

const chartInstances = {};

function destroyCharts(section){
    if (chartInstances && chartInstances[section]) {
        Object.keys(chartInstances[section]).forEach(chartKey => {
            const chart = chartInstances[section][chartKey];

            if (chart && typeof chart.destroy === 'function') {
                chart.destroy();
            }
        });
        chartInstances[section] = {};
    }
}


async function loadForecasts() {
    try {
        console.log('Loading forecasts...');
        const container = document.getElementById('forecasts-container');
        if (!container) {
            console.error('Forecasts container not found');
            return;
        }

        //Destroying existing charts on the tab
        destroyCharts('forecasts');

        // Show loading state
        showLoading('forecasts-container', 'Generating price forecasts...',);

        const response = await fetch('/portfolio/forecasts');
        if (!response.ok) {
            throw new Error(`Server responded with ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        console.log('Forecasts data received:', data);

        container.innerHTML = '';

        if (!data.forecasts || Object.keys(data.forecasts).length === 0) {
            showNoData('forecasts-container', 'No forecast data available at this time. This could be due to insufficient historical data for your holdings.');
            return;
        }

        const row = document.createElement('div');
        row.className = 'row';

        for (const [symbol, forecast] of Object.entries(data.forecasts)) {
            try{
                // Validating forecast data to prevent UI errors
                if (!forecast.historical_prices || forecast.historical_prices.length === 0 ||
                    !forecast.dates || forecast.dates.length === 0) {
                    console.warn(`Incomplete forecast data for ${symbol}, skipping`);
                    continue;
                }

                const col = document.createElement('div');
                col.className = 'col-md-6 mb-4';

                const directionClass = forecast.predicted_return >= 0 ? 'text-success' : 'text-danger';
                const directionIcon = forecast.predicted_return >= 0 ? 'bi-arrow-up' : 'bi-arrow-down';
                const returnValue = isNaN(forecast.predicted_return) ? 0 : forecast.predicted_return;

                col.innerHTML = `
                    <div class="card">
                        <div class="card-header d-flex justify-content-between align-items-center">
                            <span>${symbol}</span>
                            <span class="${directionClass}">
                                <i class="bi ${directionIcon}"></i> 
                                ${(returnValue * 100).toFixed(2)}%
                            </span>
                        </div>
                        <div class="card-body">
                            <canvas id="forecast-chart-${symbol}"></canvas>
                            <div class="d-flex justify-content-between mt-3">
                                <div>
                                    <small class="text-muted">Current Price</small>
                                    <h5>${isNaN(forecast.current_price) ? 'N/A' : forecast.current_price.toFixed(2)}</h5>
                                </div>
                                <div>
                                    <small class="text-muted">Target Price (30d)</small>
                                    <h5>${isNaN(forecast.target_price) ? 'N/A' : forecast.target_price.toFixed(2)}</h5>
                                </div>
                            </div>
                        </div>
                    </div>
                `;

                row.appendChild(col);
            }catch(symbolError){
                console.error(`Error processing forecast for ${symbol}:`, symbolError);
            }
        }

        container.appendChild(row);

        // Initialize charts after DOM is updated
        chartInstances['forecasts'] = chartInstances['forecasts']|| {};

        for (const [symbol, forecast] of Object.entries(data.forecasts)) {
            try {
                if (!forecast.historical_prices || forecast.historical_prices.length === 0 ||
                    !forecast.dates || forecast.dates.length === 0) {
                    continue;
                }

                const chartCanvas = document.getElementById(`forecast-chart-${symbol}`);
                if (!chartCanvas) {
                    console.error(`Forecast chart canvas for ${symbol} not found`);
                    continue;
                }

                const ctx = chartCanvas.getContext('2d');

                // Making sure all data arrays exist and have values
                const historicalDates = forecast.dates || [];
                const forecastDates = forecast.forecast_dates || [];
                const historicalPrices = forecast.historical_prices || [];
                const forecastPrices = forecast.forecast_prices || [];

                chartInstances['forecasts'][`forecast-chart-${symbol}`] = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: [...historicalDates, ...forecastDates],
                        datasets: [
                            {
                                label: 'Historical',
                                data: [...historicalPrices, ...Array(forecastDates.length).fill(null)],
                                borderColor: 'rgb(75, 192, 192)',
                                backgroundColor: 'rgba(75, 192, 192, 0.5)',
                                tension: 0.1
                            },
                            {
                                label: 'Forecast',
                                data: [...Array(historicalDates.length).fill(null), ...forecastPrices],
                                borderColor: 'rgb(255, 99, 132)',
                                backgroundColor: 'rgba(255, 99, 132, 0.5)',
                                borderDash: [5, 5],
                                tension: 0.1
                            }
                        ]
                    },
                     options: {
                        responsive: true,
                        plugins: {
                            title: {
                                display: true,
                                text: '30-Day Price Forecast'
                            },
                            tooltip: {
                                callbacks: {
                                    label: function(context) {
                                        let label = context.dataset.label || '';
                                        if (label) {
                                            label += ': ';
                                        }
                                        if (context.parsed.y !== null) {
                                            label += new Intl.NumberFormat('en-US', {
                                                style: 'currency',
                                                currency: 'USD'
                                            }).format(context.parsed.y);
                                        }
                                        return label;
                                    }
                                }
                            }
                        },
                        scales: {
                            y: {
                                beginAtZero: false,
                                ticks: {
                                    callback: function(value) {
                                        return '$' + value.toFixed(2);
                                    }
                                }
                            },
                            x: {
                                ticks: {
                                    maxRotation: 45,
                                    minRotation: 45
                                }
                            }
                        }
                    }
                });
        } catch (chartError) {
                console.error(`Error creating chart for ${symbol}:`, chartError);
            }
        }
        // Displaying message for when no forecast charts were created
        if (Object.keys(chartInstances['forecasts'] || {}).length === 0 && Object.keys(data.forecasts).length > 0) {
            console.warn("No forecast charts were created despite having forecast data");
            showWarning('forecasts-container', 'Could not render forecast charts with the available data.');
        }
    } catch (error) {
        console.error('Error loading forecasts:', error);
        showError('forecasts-container', 'Error loading price forecasts. Please try again later.');
    }
}

function showWarning(containerId, message = 'Warning') {
    const container = document.getElementById(containerId);
    if (!container) return;

    // Append warning without clearing existing content
    const warningDiv = document.createElement('div');
    warningDiv.className = 'alert alert-warning mt-3';
    warningDiv.innerHTML = `
        <i class="bi bi-exclamation-triangle-fill me-2"></i> 
        ${message}
    `;
    container.prepend(warningDiv);
}


function updateActiveTab(tabId) {
    console.log(`Tab ${tabId} became active`);

    switch(tabId) {
        case 'recommendations':
            loadRecommendations();
            break;
        case 'risk':
            loadRiskAnalysis();
            break;
        case 'forecasts':
            loadForecasts();
            break;
        default:
            console.warn(`Unknown tab ID: ${tabId}`);
    }
}

function getPriorityClass(priority) {
    switch(priority) {
        case 'high': return 'danger';
        case 'medium': return 'warning';
        case 'low': return 'info';
        default: return 'secondary';
    }
}

function getRiskClass(riskLevel) {
    switch(riskLevel.toLowerCase()) {
        case 'high': return 'danger';
        case 'medium': return 'warning';
        case 'low': return 'success';
        default: return 'secondary';
    }
}

function showLoading(containerId, message = 'Loading...') {
    const container = document.getElementById(containerId);
    if (!container) return;

    container.innerHTML = `
        <div class="text-center p-5">
            <div class="spinner-border" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-2">${message}</p>
        </div>
    `;
}

function showError(containerId, message = 'An error occurred') {
    const container = document.getElementById(containerId);
    if (!container) return;

    container.innerHTML = `
        <div class="alert alert-danger">
            <i class="bi bi-exclamation-triangle-fill me-2"></i> 
            ${message}
        </div>
    `;
}

function showNoData(containerId, message = 'No data available') {
    const container = document.getElementById(containerId);
    if (!container) return;

    container.innerHTML = `
        <div class="alert alert-info">
            <i class="bi bi-info-circle-fill me-2"></i> 
            ${message}
        </div>
    `;
}
