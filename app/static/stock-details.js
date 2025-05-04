document.addEventListener('DOMContentLoaded', function () {
    //Extracting the symbol from the URL
    const pathParts = window.location.pathname.split('/');
    const symbol = pathParts[pathParts.length - 1];

    console.log('Loading stock details for:', symbol);

    const modalElement = document.getElementById('addToPortfolioModal');

    if (modalElement) {
        // When the modal is completely hidden, make sure no child elements have focus
        modalElement.addEventListener('hidden.bs.modal', function () {
            // Return focus to the button that opened the modal
            document.getElementById('add-to-portfolio-btn').focus();
        });
    }

    //Setting up Price Chart
    setupPriceChart(symbol);


    //Setting up tab change listeners
    document.querySelectorAll('.nav-link').forEach(tab => {
        tab.addEventListener('click', function () {
            const target = this.textContent.trim().toLowerCase();

            if (target === 'financials') {
                loadFinancials(symbol);
            } else if (target === 'analysis') {
                loadAnalysis(symbol);
            } else if (target === 'news') {
                loadNews(symbol);
            }
        });
    });

    //Loading forecast and similar stocks
    loadForecast(symbol);
    loadSimilarStocks(symbol);

    //Add to Portfolio Button
    document.getElementById('add-to-portfolio-btn').addEventListener('click', function () {
        const modal = new bootstrap.Modal(document.getElementById('addToPortfolioModal'));
        modal.show();
    });

    //Add to Portfolio form submission
    document.getElementById('add-to-portfolio-form').addEventListener('submit', function (e) {
        e.preventDefault();
        addToPortfolio(symbol);
    });
});


function showToastNotification(message, type = 'info') {
    // Clear any existing identical toast messages first
    const existingToasts = document.querySelectorAll('.toast');
    existingToasts.forEach(existingToast => {
        const existingMessage = existingToast.querySelector('.toast-body')?.textContent?.trim();
        if (existingMessage === message.trim()) {
            const bsToast = bootstrap.Toast.getInstance(existingToast);
            if (bsToast) bsToast.dispose();
            existingToast.remove();
        }
    });

    // Create toast container if it doesn't exist
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }

    // Creating  a unique ID for this toast
    const toastId = 'toast-' + Date.now();

    // Setting the appropriate background color based on type
    let bgClass = 'bg-info';
    if (type === 'success') bgClass = 'bg-success';
    if (type === 'error') bgClass = 'bg-danger';
    if (type === 'warning') bgClass = 'bg-warning';

    // Creating the toast HTML
    const toastHtml = `
        <div id="${toastId}" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header ${bgClass} text-white">
                <strong class="me-auto">Financial Assistant</strong>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        </div>
    `;

    // Adding the toast to the container
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);

    // Initialize and show the toast
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, {
        autohide: true,
        delay: 5000
    });

    toast.show();

    // Removing the toast element after it's hidden
    toastElement.addEventListener('hidden.bs.toast', function () {
        toastElement.remove();
    });
}

async function setupPriceChart(symbol) {
    try {
        if (window.stockChart) {
            window.stockChart.destroy();
            window.stockChart = null;
        }

        // Get the active period button
        const activePeriodBtn = document.querySelector('.period-btn.active');
        const period = activePeriodBtn ? activePeriodBtn.getAttribute('data-period') : '1m';

        // Fetch historical data
        const response = await fetch(`/market/stock_history/${symbol}?period=${period}`);
        const data = await response.json();

        if (data.error) {
            console.error('Error fetching stock history:', data.error);
            return;
        }

        //Drawing the chart with Chart.js
        const canvas = document.getElementById('stock-chart')
        if (!canvas) {
            console.error('Canvas element not found');
            return;
        }
        const ctx = canvas.getContext('2d');
        window.stockChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.dates,
                datasets: [{
                    label: symbol,
                    data: data.prices,
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: `${symbol} Price History`
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        ticks: {
                            callback: function (value) {
                                return '$' + value.toFixed(2);
                            }
                        }
                    }
                }
            }
        });

        //Setting up period button handlers
        document.querySelectorAll('.period-btn').forEach(btn => {
            //Removing any existing event listeners first
            btn.removeEventListener('click', periodButtonHandler);
            btn.addEventListener('click', periodButtonHandler);
        });
    } catch (error) {
        console.error('Error setting up price chart:', error);
    }
}

async function periodButtonHandler() {
    // Update active button
    document.querySelectorAll('.period-btn').forEach(b => b.classList.remove('active'));
    this.classList.add('active');

    // Get new period and update chart
    const newPeriod = this.getAttribute('data-period');
    const symbol = getSymbolFromURL(); // You'll need to implement this
    await updateChartPeriod(symbol, newPeriod);
}

// Helper function to get symbol from URL
function getSymbolFromURL() {
    const pathParts = window.location.pathname.split('/');
    return pathParts[pathParts.length - 1];
}

async function updateChartPeriod(symbol, period) {
    try {
        const response = await fetch(`/market/stock_history/${symbol}?period=${period}`);
        const data = await response.json();

        if (data.error) {
            console.error('Error updating chart period:', data.error);
            return;
        }

        // Update chart data
        window.stockChart.data.labels = data.dates;
        window.stockChart.data.datasets[0].data = data.prices;
        window.stockChart.update();
    } catch (error) {
        console.error('Error updating chart period:', error);
    }
}

async function loadFinancials(symbol) {
    try {
        const container = document.getElementById('financials-container');
        container.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"></div><p>Loading financial data...</p></div>';

        const response = await fetch(`/market/stock/${symbol}/financials`);
        const data = await response.json();

        if (data.error || !data.length) {
            container.innerHTML = '<div class="alert alert-warning">No financial data available for this stock.</div>';
            return;
        }

        //Creating a table with the financial data
        let html = `
            <div class="table-responsive">
                <table class="table table-bordered">
                    <thead>
                        <tr>
                            <th>Fiscal Year</th>
                            <th>Revenue</th>
                            <th>Gross Profit</th>
                            <th>Net Income</th>
                            <th>EPS</th>
                        </tr>
                    </thead>
                    <tbody>
        `;

        data.forEach(year => {
            html += `
                <tr>
                    <td>${year.year}</td>
                    <td>$${formatLargeNumber(year.revenue)}</td>
                    <td>$${formatLargeNumber(year.grossProfit)}</td>
                    <td>$${formatLargeNumber(year.netIncome)}</td>
                    <td>$${year.eps.toFixed(2)}</td>
                </tr>
            `;
        });

        html += `
                    </tbody>
                </table>
            </div>
            <p class="text-muted small">Source: Alpha Vantage</p>
        `;

        container.innerHTML = html;
    } catch (error) {
        console.error('Error loading financials:', error);
        document.getElementById('financials-container').innerHTML =
            '<div class="alert alert-danger">Error loading financial data.</div>';
    }
}

async function loadAnalysis(symbol) {
    try {
        const container = document.getElementById('analysis-container');
        container.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"></div><p>Loading analysis...</p></div>';

        const response = await fetch(`/market/stock/${symbol}/analysis`);
        const data = await response.json();

        if (data.error) {
            container.innerHTML = '<div class="alert alert-warning">No analysis data available for this stock.</div>';
            return;
        }

        //Formating the NA values
        for (const [key, value] of Object.entries(data)) {
            if (value === null || value === undefined) {
                data[key] = 'N/A';
            } else if (typeof value === 'number') {
                data[key] = value.toFixed(2);
            }
        }

        //Creating analysis content
        const html = `
            <div class="row">
                <div class="col-md-6">
                    <h5>Valuation Metrics</h5>
                    <table class="table table-sm">
                        <tr>
                            <td>P/E Ratio</td>
                            <td>${data.pe_ratio}</td>
                        </tr>
                        <tr>
                            <td>PEG Ratio</td>
                            <td>${data.peg_ratio}</td>
                        </tr>
                        <tr>
                            <td>EPS</td>
                            <td>$${data.eps}</td>
                        </tr>
                        <tr>
                            <td>Profit Margin</td>
                            <td>${data.profit_margin}%</td>
                        </tr>
                    </table>
                </div>
                <div class="col-md-6">
                    <h5>Technical & Forecast</h5>
                    <table class="table table-sm">
                        <tr>
                            <td>Beta</td>
                            <td>${data.beta}</td>
                        </tr>
                        <tr>
                            <td>Dividend Yield</td>
                            <td>${data.dividend_yield}%</td>
                        </tr>
                        <tr>
                            <td>Analyst Target Price</td>
                            <td>$${data.target_price}</td>
                        </tr>
                    </table>
                </div>
            </div>
            <div class="alert alert-info mt-3">
                <i class="bi bi-info-circle-fill me-2"></i>
                Based on the P/E ratio and growth metrics, this stock appears to be 
                ${getValuationAssessment(data.pe_ratio, data.peg_ratio)}.
            </div>
        `;

        container.innerHTML = html;
    } catch (error) {
        console.error('Error loading analysis:', error);
        document.getElementById('analysis-container').innerHTML =
            '<div class="alert alert-danger">Error loading analysis data.</div>';
    }
}

function getValuationAssessment(pe, peg) {
    if (pe === 'N/A' || peg === 'N/A') return 'difficult to assess due to missing data';

    pe = parseFloat(pe);
    peg = parseFloat(peg);

    if (pe < 15 && peg < 1) return 'potentially undervalued';
    if (pe > 30 && peg > 1.5) return 'potentially overvalued';
    return 'reasonably valued relative to earnings and growth';
}

async function loadNews(symbol) {
    try {
        const container = document.getElementById('news-container');
        container.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"></div><p>Loading news articles...</p></div>';

        const response = await fetch(`/market/news?symbol=${symbol}`);
        const data = await response.json();

        if (data.error || !data.news || data.news.length === 0) {
            container.innerHTML = '<div class="alert alert-warning">No news articles found for this stock.</div>';
            return;
        }

        let html = '';

        data.news.forEach(item => {
            const sentimentClass = getSentimentClass(item.sentiment);

            html += `
                <div class="card mb-3">
                    <div class="card-body">
                        <div class="d-flex justify-content-between">
                            <h5 class="card-title">${item.title}</h5>
                            <span class="badge ${sentimentClass}">${item.sentiment}</span>
                        </div>
                        <h6 class="card-subtitle mb-2 text-muted">${item.source} · ${formatDate(item.published_at)}</h6>
                        <p class="card-text">${item.summary}</p>
                        <a href="${item.url}" class="btn btn-sm btn-primary" target="_blank">Read More</a>
                    </div>
                </div>
            `;
        });

        container.innerHTML = html;
    } catch (error) {
        console.error('Error loading news:', error);
        document.getElementById('news-container').innerHTML =
            '<div class="alert alert-danger">Error loading news articles.</div>';
    }
}

async function loadForecast(symbol) {
    try {
        const container = document.getElementById('forecast-container');
        container.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"></div><p>Generating forecast...</p></div>';

        const response = await fetch(`/market/stock/${symbol}/forecast`);
        const data = await response.json();

        if (data.error) {
            container.innerHTML = '<div class="alert alert-warning">Unable to generate forecast for this stock.</div>';
            return;
        }

        const directionClass = data.target_price > data.current_price ? 'text-success' : 'text-danger';
        const directionIcon = data.target_price > data.current_price ? 'bi-arrow-up' : 'bi-arrow-down';
        const percentChange = ((data.target_price - data.current_price) / data.current_price * 100).toFixed(2);

        const html = `
            <div class="text-center mb-3">
                <h5 class="${directionClass}">
                    <i class="bi ${directionIcon}"></i> 
                    ${percentChange}% in 30 days
                </h5>
                <div class="d-flex justify-content-between">
                    <div>
                        <small class="text-muted">Current</small>
                        <h4>$${data.current_price.toFixed(2)}</h4>
                    </div>
                    <div>
                        <small class="text-muted">Target</small>
                        <h4>$${data.target_price.toFixed(2)}</h4>
                    </div>
                </div>
            </div>
            <div class="progress mb-2" style="height: 6px;">
                <div class="progress-bar bg-primary" role="progressbar" style="width: ${data.confidence * 100}%" 
                    aria-valuenow="${data.confidence * 100}" aria-valuemin="0" aria-valuemax="100"></div>
            </div>
            <div class="d-flex justify-content-between">
                <small>Forecast Confidence</small>
                <small>${(data.confidence * 100).toFixed(0)}%</small>
            </div>
        `;

        container.innerHTML = html;
    } catch (error) {
        console.error('Error loading forecast:', error);
        document.getElementById('forecast-container').innerHTML =
            '<div class="alert alert-danger">Error generating forecast.</div>';
    }
}

async function loadSimilarStocks(symbol) {
    try {
        const container = document.getElementById('similar-stocks-container');
        container.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"></div><p>Finding similar stocks...</p></div>';

        const response = await fetch(`/market/stock/${symbol}/similar`);
        const data = await response.json();

        if (!data || data.length === 0) {
            container.innerHTML = '<div class="alert alert-warning">No similar stocks found.</div>';
            return;
        }

        let html = '<div class="list-group">';

        data.forEach(stock => {
            const changeClass = stock.change_percent >= 0 ? 'text-success' : 'text-danger';

            html += `
                <a href="/market/stock/${stock.symbol}" class="list-group-item list-group-item-action">
                    <div class="d-flex justify-content-between">
                        <div>
                            <strong>${stock.symbol}</strong> 
                            <small class="text-muted">${stock.name}</small>
                        </div>
                        <div>
                            <span>$${stock.price.toFixed(2)}</span>
                            <span class="${changeClass}">
                                ${stock.change_percent >= 0 ? '▲' : '▼'} 
                                ${Math.abs(stock.change_percent).toFixed(2)}%
                            </span>
                        </div>
                    </div>
                </a>
            `;
        });

        html += '</div>';
        container.innerHTML = html;
    } catch (error) {
        console.error('Error loading similar stocks:', error);
        document.getElementById('similar-stocks-container').innerHTML =
            '<div class="alert alert-danger">Error loading similar stocks.</div>';
    }
}

async function addToPortfolio(symbol) {
    try {
        const quantity = parseFloat(document.getElementById('quantity').value);

        if (isNaN(quantity) || quantity <= 0 || quantity < 0.001) {
            showToastNotification('Please enter a valid quantity.');
            return;
        }

        const response = await fetch('/portfolio/add_stock', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                symbol: symbol,
                quantity: quantity
            })
        });

        const result = await response.json();

        if (response.ok) {
            // Close the modal
            const modalEl = document.getElementById('addToPortfolioModal');
            const modal = bootstrap.Modal.getInstance(modalEl);

            if (modal) {
                modal.hide();

                // Ensuring the modal backdrop is removed
                setTimeout(() => {
                    if (document.querySelector('.modal-backdrop')) {
                        document.querySelector('.modal-backdrop').remove();
                    }
                    document.body.classList.remove('modal-open');
                    document.body.style.overflow = '';
                    document.body.style.paddingRight = '';
                }, 500);
            }

            //Returning Focus to the add button
            setTimeout(() => {
                document.getElementById('add-to-portfolio-btn').focus();
            }, 600);

            // Show success message
            showToastNotification(`Successfully added ${quantity} shares of ${symbol} to your portfolio!`);

            // Reset the form
            document.getElementById('add-to-portfolio-form').reset();
        } else {
            showToastNotification(`Error: ${result.error || 'Failed to add stock to portfolio'}`);
        }
    } catch (error) {
        console.error('Error adding to portfolio:', error);
        showToastNotification('An error occurred while adding the stock to your portfolio.');
    }
}

// Helper functions
function formatLargeNumber(num) {
    if (num >= 1000000000) {
        return (num / 1000000000).toFixed(2) + 'B';
    } else if (num >= 1000000) {
        return (num / 1000000).toFixed(2) + 'M';
    } else {
        return num.toFixed(2);
    }
}

function formatDate(dateString) {
    if (!dateString) return 'Unknown date';
    const date = new Date(dateString);
    return date.toLocaleDateString();
}

function getSentimentClass(sentiment) {
    switch (sentiment.toLowerCase()) {
        case 'bullish':
            return 'bg-success';
        case 'somewhat-bullish':
            return 'bg-success text-white';
        case 'bearish':
            return 'bg-danger';
        case 'somewhat-bearish':
            return 'bg-danger text-white';
        default:
            return 'bg-secondary';
    }
}


