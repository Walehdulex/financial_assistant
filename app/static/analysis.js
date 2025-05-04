document.addEventListener('DOMContentLoaded', function () {
    // Check if we're on the analysis page
    const analysisPage = document.getElementById('analysisTabContent');
    if (!analysisPage) return;

    console.log('Analysis page detected, initializing...');

    // Set up tab change listeners
    document.querySelectorAll('.nav-link').forEach(tab => {
        tab.addEventListener('click', function () {
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

function attachLearnButtonListeners() {
    document.querySelectorAll('.learn-more-btn').forEach(button => {
        button.addEventListener('click', function() {
            const target = this.getAttribute('data-bs-target');
            // Toggle the educational content
            const eduContent = document.querySelector(target);
            if (eduContent) {
                // Bootstrap 5 collapse API
                const bsCollapse = new bootstrap.Collapse(eduContent);
                bsCollapse.toggle();
            }
        });
    });
}

// Loads recommendation data and updates the recommendations container
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
                switch (rec.type) {
                    case 'buy':
                        iconClass = 'bi-graph-up-arrow text-success';
                        break;
                    case 'sell':
                        iconClass = 'bi-graph-down-arrow text-danger';
                        break;
                    case 'diversification':
                        iconClass = 'bi-diagram-3';
                        break;
                    case 'sector':
                        iconClass = 'bi-pie-chart';
                        break;
                    case 'concentration':
                        iconClass = 'bi-exclamation-triangle text-warning';
                        break;
                    case 'goal':
                        iconClass = 'bi-bullseye';
                        break;
                    case 'tax':
                        iconClass = 'bi-cash-coin';
                        break;
                    default:
                        iconClass = 'bi-info-circle';
                }

                let confidenceHtml = '';
                if (rec.confidence) {
                    confidenceHtml = `
                        <div class="progress mt-2" style="height: 5px;">
                            <div class="progress-bar" role="progressbar" style="width: ${rec.confidence * 100}%" 
                                 aria-valuenow="${rec.confidence * 100}" aria-valuemin="0" aria-valuemax="100"></div>
                        </div>
                        <small class="text-muted">Confidence: ${(rec.confidence * 100).toFixed(0)}%</small>
                    `;
                }

                let symbolBadge = rec.symbol ? `<span class="badge bg-secondary me-2">${rec.symbol}</span>` : '';

                // Apply button for actionable recommendations
                let actionButtons = '';
                if (rec.type === 'buy' && rec.symbol) {
                    actionButtons = `
                        <button class="btn btn-sm btn-success action-btn" data-action="buy" data-symbol="${rec.symbol}">
                            <i class="bi bi-plus-circle"></i> Add to Portfolio
                        </button>
                        <button class="btn btn-sm btn-outline-primary show-impact-btn" data-rec-id="${rec.type}-${rec.symbol || 'general'}">
                            <i class="bi bi-eye"></i> Show Impact
                        </button>
                    `;
                } else if (rec.type === 'sell' && rec.symbol) {
                    actionButtons = `
                        <button class="btn btn-sm btn-warning action-btn" data-action="sell" data-symbol="${rec.symbol}">
                            <i class="bi bi-dash-circle"></i> Sell Position
                        </button>
                        <button class="btn btn-sm btn-outline-primary show-impact-btn" data-rec-id="${rec.type}-${rec.symbol || 'general'}">
                            <i class="bi bi-eye"></i> Show Impact
                        </button>
                    `;
                } else if (rec.type === 'diversification' || rec.type === 'sector') {
                    actionButtons = `
                        <button class="btn btn-sm btn-info action-btn" data-action="search" data-sector="${rec.sector || ''}">
                            <i class="bi bi-search"></i> Find Stocks
                        </button>
                        <button class="btn btn-sm btn-outline-primary show-impact-btn" data-rec-id="${rec.type}-${rec.sector || 'general'}">
                            <i class="bi bi-eye"></i> Show Impact
                        </button>
                    `;
                } else {
                    actionButtons = `
                        <button class="btn btn-sm btn-outline-primary show-impact-btn" data-rec-id="${rec.type}-${rec.symbol || rec.sector || 'general'}">
                            <i class="bi bi-eye"></i> Show Impact
                        </button>
                    `;
                }

                let educationalContent = '';
                if (rec.type === 'diversification') {
                    educationalContent = `
                        <div class="educational-tip collapse" id="edu-tip-${rec.type}-${rec.id || 'gen'}">
                            <div class="card bg-light mt-2">
                                <div class="card-body">
                                    <h6><i class="bi bi-lightbulb"></i> Learning Corner</h6>
                                    <p>Diversification is a risk management strategy that mixes a variety of investments within a portfolio.</p>
                                    <p>A well-diversified portfolio typically includes:</p>
                                    <ul>
                                        <li>Investments across different asset classes (stocks, bonds, alternatives)</li>
                                        <li>Exposure to multiple sectors and industries</li>
                                        <li>A mix of company sizes (large, mid, and small cap)</li>
                                    </ul>
                                    <a href="/education/guides/diversification" class="btn btn-sm btn-outline-primary read-more-link">Read More</a>
                                </div>
                            </div>
                        </div>
                    `;
                } else if (rec.type === 'sector') {
                    educationalContent = `
                        <div class="educational-tip collapse" id="edu-tip-${rec.type}-${rec.id || 'gen'}">
                            <div class="card bg-light mt-2">
                                <div class="card-body">
                                    <h6><i class="bi bi-lightbulb"></i> Learning Corner</h6>
                                    <p>Sector allocation influences both risk and return in your portfolio.</p>
                                    <p>The ${rec.sector} sector is known for:</p>
                                    <ul>
                                        <li>${getSectorDescription(rec.sector)}</li>
                                    </ul>
                                    <a href="/education/guides/diversification" class="btn btn-sm btn-outline-primary read-more-link">Read More</a>
                                </div>
                            </div>
                        </div>
                    `;
                } else if (rec.type === 'buy') {
                    educationalContent = `
                        <div class="educational-tip collapse" id="edu-tip-${rec.type}-${rec.id || 'gen'}">
                            <div class="card bg-light mt-2">
                                <div class="card-body">
                                    <h6><i class="bi bi-lightbulb"></i> Learning Corner</h6>
                                    <p>Increasing your position in a stock can enhance returns when you have high conviction about its future performance.</p>
                                    <p>When adding to a position, consider:</p>
                                    <ul>
                                        <li>The impact on your overall portfolio diversification</li>
                                        <li>Averaging in over time rather than all at once</li>
                                        <li>Setting a maximum allocation limit for any single position</li>
                                    </ul>
                                    <a href="/education/guides/buy" class="btn btn-sm btn-outline-primary read-more-link">Read More</a>
                                </div>
                            </div>
                        </div>
                    `;
                } else if (rec.type === 'sell') {
                    educationalContent = `
                        <div class="educational-tip collapse" id="edu-tip-${rec.type}-${rec.id || 'gen'}">
                            <div class="card bg-light mt-2">
                                <div class="card-body">
                                    <h6><i class="bi bi-lightbulb"></i> Learning Corner</h6>
                                    <p>Selling a position can help you manage risk, take profits, or reallocate to better opportunities.</p>
                                    <p>Important considerations when selling include:</p>
                                    <ul>
                                        <li>Tax implications of realized gains or losses</li>
                                        <li>Impact on your overall portfolio diversification</li>
                                        <li>Avoiding emotional decisions during market volatility</li>
                                    </ul>
                                    <a href="/education/guides/diversification" class="btn btn-sm btn-outline-primary read-more-link">Read More</a>
                                </div>
                            </div>
                        </div>
                    `;
                } else if (rec.type === 'concentration') {
                    educationalContent = `
                        <div class="educational-tip collapse" id="edu-tip-${rec.type}-${rec.id || 'gen'}">
                            <div class="card bg-light mt-2">
                                <div class="card-body">
                                    <h6><i class="bi bi-lightbulb"></i> Learning Corner</h6>
                                    <p>Concentration risk occurs when too much of your portfolio is allocated to a single stock, sector, or asset class.</p>
                                    <p>Managing concentration risk:</p>
                                    <ul>
                                        <li>Consider limiting individual positions to 5-10% of your portfolio</li>
                                        <li>Regularly rebalance to maintain target allocations</li>
                                        <li>Diversify across different sectors and asset classes</li>
                                    </ul>
                                    <a href="/education/guides/risk-management" class="btn btn-sm btn-outline-primary read-more-link">Read More</a>
                                </div>
                            </div>
                        </div>
                    `;
                } else if (rec.type === 'goal') {
                    educationalContent = `
                        <div class="educational-tip collapse" id="edu-tip-${rec.type}-${rec.id || 'gen'}">
                            <div class="card bg-light mt-2">
                                <div class="card-body">
                                    <h6><i class="bi bi-lightbulb"></i> Learning Corner</h6>
                                    <p>Aligning your portfolio with your investment goals is critical for long-term success.</p>
                                    <p>Key goal-based considerations:</p>
                                    <ul>
                                        <li>Short-term goals (1-3 years) typically require more conservative investments</li>
                                        <li>Long-term goals (10+ years) allow for more growth-oriented strategies</li>
                                        <li>Regular reviews ensure your portfolio stays aligned with changing goals</li>
                                    </ul>
                                    <a href="/education/guides/risk-management" class="btn btn-sm btn-outline-primary read-more-link">Read More</a>
                                </div>
                            </div>
                        </div>
                    `;
                } else if (rec.type === 'tax') {
                    educationalContent = `
                        <div class="educational-tip collapse" id="edu-tip-${rec.type}-${rec.id || 'gen'}">
                            <div class="card bg-light mt-2">
                                <div class="card-body">
                                    <h6><i class="bi bi-lightbulb"></i> Learning Corner</h6>
                                    <p>Tax-efficient investing can significantly improve your after-tax returns over time.</p>
                                    <p>Common tax strategies include:</p>
                                    <ul>
                                        <li>Tax-loss harvesting to offset capital gains</li>
                                        <li>Holding investments for over a year to qualify for long-term capital gains rates</li>
                                        <li>Using tax-advantaged accounts for appropriate investments</li>
                                    </ul>
                                    <a href="/education/guides/tax-strategies" class="btn btn-sm btn-outline-primary read-more-link">Read More</a>
                                </div>
                            </div>
                        </div>
                    `;
                } else {
                    // Default educational content for other recommendation types
                    educationalContent = `
                        <div class="educational-tip collapse" id="edu-tip-${rec.type}-${rec.id || 'gen'}">
                            <div class="card bg-light mt-2">
                                <div class="card-body">
                                    <h6><i class="bi bi-lightbulb"></i> Learning Corner</h6>
                                    <p>Regular portfolio reviews and adjustments are essential for long-term investment success.</p>
                                    <p>Consider reviewing your investment strategy at least quarterly or when your financial situation changes.</p>
                                    <a href="/education/guides/portfolio-management" class="btn btn-sm btn-outline-primary read-more-link">Read More</a>
                                </div>
                            </div>
                        </div>
                    `;
                }

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
                        
                        <!-- Action buttons should be here, OUTSIDE the collapse div -->
                        <div class="d-flex justify-content-between align-items-center mt-3">
                            <div class="action-buttons">
                                ${actionButtons}
                            </div>
                           
                            <button class="btn btn-sm btn-link text-info learn-more-btn"
                                    data-bs-toggle="collapse"
                                    data-bs-target="#edu-tip-${rec.type}-${rec.id || 'gen'}"
                                    aria-expanded="false">
                                <i class="bi bi-info-circle"></i> Learn
                            </button>
                        </div>
                    </div>
                        
                        <!-- Impact visualization in a collapsible section -->
                        <div class="impact-visualization collapse mt-3" id="impact-${rec.type}-${rec.symbol || rec.sector || 'general'}">
                            <div class="card bg-light">
                                <div class="card-body">
                                    <h6 class="card-subtitle mb-2">Potential Impact</h6>
                                    <div class="impact-content">
                                        <div class="text-center">
                                            <div class="spinner-border spinner-border-sm" role="status">
                                                <span class="visually-hidden">Loading...</span>
                                            </div>
                                            <p class="mt-2">Calculating potential impact...</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Educational content -->
                        ${educationalContent}
                        
                        <!-- Feedback section -->
                        <div class="text-end mt-2">
                            <button class="btn btn-sm btn-link text-muted feedback-toggle"
                                    data-bs-toggle="collapse"
                                    data-bs-target="#feedback-${rec.type}-${rec.symbol || rec.sector || 'general'}"
                                    aria-expanded="false">
                                Rate this recommendation
                            </button>
                        </div>
                        
                        <div class="collapse mt-2" id="feedback-${rec.type}-${rec.symbol || rec.sector || 'general'}">
                            <div class="card card-body bg-light">
                                <h6>Was this recommendation helpful?</h6>
                                <div class="rating mb-2">
                                    <span class="rating-star" data-rating="5">★</span>
                                    <span class="rating-star" data-rating="4">★</span>
                                    <span class="rating-star" data-rating="3">★</span>
                                    <span class="rating-star" data-rating="2">★</span>
                                    <span class="rating-star" data-rating="1">★</span>
                                </div>
                                <div class="form-check mb-2">
                                    <input class="form-check-input was-followed" type="checkbox" value="" id="followed-${rec.type}-${rec.symbol || rec.sector || 'general'}">
                                    <label class="form-check-label" for="followed-${rec.type}-${rec.symbol || rec.sector || 'general'}">
                                        I followed this recommendation
                                    </label>
                                </div>
                                <div class="mb-2">
                                    <textarea class="form-control feedback-comment" placeholder="Additional comments (optional)"></textarea>
                                </div>
                                <button class="btn btn-sm btn-primary submit-feedback"
                                        data-type="${rec.type}"
                                        data-action="${rec.action}">
                                    Submit Feedback
                                </button>
                            </div>
                        </div>
                    </div>
                  `;
                container.appendChild(card);
            });

            // Event listeners for star ratings
            document.querySelectorAll('.rating-star').forEach(star => {
                star.addEventListener('click', function () {
                    const rating = parseInt(this.getAttribute('data-rating'));
                    const ratingContainer = this.closest('.rating');

                    // Reset all stars
                    ratingContainer.querySelectorAll('.rating-star').forEach(s => {
                        s.classList.remove('active');
                    });

                    // Set active stars
                    for (let i = 1; i <= 5; i++) {
                        const s = ratingContainer.querySelector(`.rating-star[data-rating="${i}"]`);
                        if (i <= rating) {
                            s.classList.add('active');
                        }
                    }

                    // Store the rating as a data attribute
                    ratingContainer.setAttribute('data-user-rating', rating);
                });
            });

            // Event listeners for submitting feedback
            document.querySelectorAll('.submit-feedback').forEach(button => {
                button.addEventListener('click', async function () {
                    const type = this.getAttribute('data-type');
                    const action = this.getAttribute('data-action');
                    const feedbackContainer = this.closest('.collapse');

                    const rating = parseInt(feedbackContainer.querySelector('.rating').getAttribute('data-user-rating') || 0);
                    const wasFollowed = feedbackContainer.querySelector('.was-followed').checked;
                    const comment = feedbackContainer.querySelector('.feedback-comment').value;

                    if (!rating) {
                        showToastNotification('Please select a rating', 'warning');
                        return;
                    }

                    try {
                        const response = await fetch('/portfolio/recommendation-feedback', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({
                                recommendation_type: type,
                                recommendation_action: action,
                                rating: rating,
                                was_followed: wasFollowed,
                                comment: comment
                            })
                        });

                        if (response.ok) {
                            showToastNotification('Thank you for your feedback!', 'success');

                            // Closing the feedback form using Bootstrap's Collapse API instead of clicking an element
                            const bsCollapse = bootstrap.Collapse.getInstance(feedbackContainer)
                            if (bsCollapse) {
                                bsCollapse.hide();
                            }

                            // Find the toggle button if it exists and update it
                            const toggleButton = document.querySelector(`[data-bs-target="#${feedbackContainer.id}"]`);
                            if (toggleButton) {
                                toggleButton.disabled = true;
                                toggleButton.textContent = 'Feedback submitted';
                            }
                        } else {
                            showToastNotification('Failed to submit feedback', 'error');
                        }
                    } catch (error) {
                        console.error('Error submitting feedback:', error);
                        showToastNotification('An error occurred', 'error');
                    }
                });
            });

            // Event listeners for applying recommendations
            document.querySelectorAll('.apply-recommendation').forEach(button => {
                button.addEventListener('click', function () {
                    const type = this.getAttribute('data-type');
                    const symbol = this.getAttribute('data-symbol');

                    if (type === 'buy') {
                        // Open add stock modal
                        const symbolField = document.getElementById('symbol');

                        if (symbolField) {
                            symbolField.value = symbol;
                            const addModal = new bootstrap.Modal(document.getElementById('addStockModal'));
                            addModal.show();
                        } else {
                            // Element not found - redirect to dashboard with param
                            window.location.href = `/portfolio/dashboard?action=buy&symbol=${symbol}`;
                        }
                    } else if (type === 'sell') {
                        // Open sell stock modal
                        if (typeof removeStock === 'function') {
                            removeStock(symbol);
                        } else {
                            // Function not available - redirect
                            window.location.href = `/portfolio/dashboard?action=sell&symbol=${symbol}`;
                        }
                    }
                });
            });
            // Event listeners for action buttons
            attachActionButtonListeners();

            // event listeners for impact visualization
            attachImpactButtonListeners();
            //Button Listeners
            attachFeedbackButtonListeners();
            //Learn Button Listener
            attachLearnButtonListeners();
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

function destroyCharts(section) {
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

        // Destroying existing charts on the tab
        destroyCharts('forecasts');

        // Show loading state
        showLoading('forecasts-container', 'Generating price forecasts...');

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
            try {
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
            } catch (symbolError) {
                console.error(`Error processing forecast for ${symbol}:`, symbolError);
            }
        }

        container.appendChild(row);

        // Initialize charts after DOM is updated
        chartInstances['forecasts'] = chartInstances['forecasts'] || {};

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
                                    label: function (context) {
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
                                    callback: function (value) {
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

    // Appending warning without clearing existing content
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

    switch (tabId) {
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
    switch (priority) {
        case 'high':
            return 'danger';
        case 'medium':
            return 'warning';
        case 'low':
            return 'info';
        default:
            return 'secondary';
    }
}

function getRiskClass(riskLevel) {
    switch (riskLevel.toLowerCase()) {
        case 'high':
            return 'danger';
        case 'medium':
            return 'warning';
        case 'low':
            return 'success';
        default:
            return 'secondary';
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

function attachActionButtonListeners() {
    document.querySelectorAll('.action-btn').forEach(button => {
        button.addEventListener('click', function() {
            const action = this.getAttribute('data-action');
            const symbol = this.getAttribute('data-symbol');
            const sector = this.getAttribute('data-sector');

            if (action === 'buy' && symbol) {
                createBuyModal(symbol);
            } else if (action === 'sell' && symbol) {
                createSellModal(symbol);
            } else if (action === 'search' && sector) {
                // Searching for stocks in the specified sector
                searchStocksInSector(sector);
            }
        });
    });
}


function createBuyModal(symbol) {
    // Removing any existing modal
    const existingModal = document.getElementById('dynamicStockModal');
    if (existingModal) {
        existingModal.remove();
    }

     // Creating modal for HTML
    const modalHtml = `
        <div class="modal fade" id="dynamicStockModal" tabindex="-1" aria-hidden="true">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header bg-success text-white">
                        <h5 class="modal-title">Add ${symbol} to Portfolio</h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <form id="dynamic-stock-form">
                            <input type="hidden" id="dynamic-symbol" value="${symbol}">
                            <div class="mb-3">
                                <label for="dynamic-quantity" class="form-label">Quantity</label>
                                <input type="number" class="form-control" id="dynamic-quantity" min="0.001" step="0.001" value="1" required>
                                <small class="text-muted">Fractional shares supported (min: 0.001)</small>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-success" id="dynamic-submit">Add to Portfolio</button>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Adding modal to body
    document.body.insertAdjacentHTML('beforeend', modalHtml);

    // Set up submit handler
    document.getElementById('dynamic-submit').addEventListener('click', function() {
        const modalSymbol = document.getElementById('dynamic-symbol').value;
        const quantity = parseFloat(document.getElementById('dynamic-quantity').value);

        if (isNaN(quantity) || quantity <= 0 || quantity < 0.001) {
            showToastNotification('Please enter a valid quantity (minimum 0.001).', 'warning');
            return;
        }

        // Calling my  API to add stock
        addStockToPortfolio(modalSymbol, quantity);
    });

    // Showing modal
    const modal = new bootstrap.Modal(document.getElementById('dynamicStockModal'));
    modal.show();
}

function createSellModal(symbol) {
    // Getting current holdings info first
    fetch(`/portfolio/holdings?symbol=${symbol}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showToastNotification(data.error, 'error');
                return;
            }

            const holding = data.holding;
            if (!holding) {
                showToastNotification(`You don't own any shares of ${symbol}.`, 'warning');
                return;
            }

            // Removing any existing modal
            const existingModal = document.getElementById('dynamicSellModal');
            if (existingModal) {
                existingModal.remove();
            }

            // Creating the  modal HTML
            const modalHtml = `
                <div class="modal fade" id="dynamicSellModal" tabindex="-1" aria-hidden="true">
                    <div class="modal-dialog">
                        <div class="modal-content">
                            <div class="modal-header bg-warning text-white">
                                <h5 class="modal-title">Sell ${symbol} Shares</h5>
                                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                            </div>
                            <div class="modal-body">
                                <form id="dynamic-sell-form">
                                    <input type="hidden" id="sell-symbol" value="${symbol}">
                                    
                                    <div class="mb-3">
                                        <label for="current-shares" class="form-label">Current Shares</label>
                                        <input type="number" class="form-control" id="current-shares" value="${holding.quantity}" disabled readonly>
                                    </div>
                                    
                                    <div class="mb-3">
                                        <label for="sell-quantity" class="form-label">Quantity to Sell</label>
                                        <input type="number" class="form-control" id="sell-quantity" min="0.001" max="${holding.quantity}" step="0.001" value="${holding.quantity}" required>
                                        <small class="text-muted">Enter the number of shares you want to sell (min: 0.001)</small>
                                    </div>
                                </form>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                                <button type="button" class="btn btn-warning" id="dynamic-sell-submit">Sell Shares</button>
                            </div>
                        </div>
                    </div>
                </div>
            `;

            // Adding modal to body
            document.body.insertAdjacentHTML('beforeend', modalHtml);

            // Setting up submit handler
            document.getElementById('dynamic-sell-submit').addEventListener('click', function() {
                const sellSymbol = document.getElementById('sell-symbol').value;
                const currentShares = parseFloat(document.getElementById('current-shares').value);
                const sellQuantity = parseFloat(document.getElementById('sell-quantity').value);

                if (isNaN(sellQuantity) || sellQuantity <= 0 || sellQuantity < 0.001) {
                    showToastNotification('Please enter a valid quantity to sell (minimum 0.001).', 'warning');
                    return;
                }

                if (sellQuantity > currentShares) {
                    showToastNotification(`You cannot sell more than your current holdings (${currentShares} shares).`, 'warning');
                    return;
                }

                // Selling shares
                sellShares(sellSymbol, sellQuantity);
            });

            // Showing modal
            const modal = new bootstrap.Modal(document.getElementById('dynamicSellModal'));
            modal.show();
        })
        .catch(error => {
            console.error('Error getting holding info:', error);
            showToastNotification('Error getting current holdings information.', 'error');
        });
}

async function addStockToPortfolio(symbol, quantity) {
    try {
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
            // Closing the modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('dynamicStockModal'));
            if (modal) {
                modal.hide();

                // Ensuring modal backdrop is removed
                setTimeout(() => {
                    if (document.querySelector('.modal-backdrop')) {
                        document.querySelector('.modal-backdrop').remove();
                    }
                    document.body.classList.remove('modal-open');
                    document.body.style.overflow = '';
                    document.body.style.paddingRight = '';
                }, 300);
            }

            // Showing success message
            showToastNotification(`Successfully added ${quantity} shares of ${symbol} to your portfolio!`, 'success');

            // Refreshing recommendations to reflect the change
            setTimeout(() => {
                loadRecommendations();
            }, 1000);
        } else {
            showToastNotification(`Error: ${result.error || 'Failed to add stock to portfolio'}`, 'error');
        }
    } catch (error) {
        console.error('Error adding stock to portfolio:', error);
        showToastNotification('An error occurred while adding the stock to your portfolio.', 'error');
    }
}

async function sellShares(symbol, quantity) {
    try {
        const response = await fetch('/portfolio/sell_shares', {
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
            // Closing modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('dynamicSellModal'));
            if (modal) {
                modal.hide();

                // EnsurIng the  modal backdrop is removed
                setTimeout(() => {
                    if (document.querySelector('.modal-backdrop')) {
                        document.querySelector('.modal-backdrop').remove();
                    }
                    document.body.classList.remove('modal-open');
                    document.body.style.overflow = '';
                    document.body.style.paddingRight = '';
                }, 300);
            }

            // Showing success message
            showToastNotification(`Successfully sold ${quantity} shares of ${symbol}.`, 'success');

            // Refreshing recommendations to reflect the change
            setTimeout(() => {
                loadRecommendations();
            }, 1000);
        } else {
            showToastNotification(`Error: ${result.message || 'Failed to sell shares'}`, 'error');
        }
    } catch (error) {
        console.error('Error selling shares:', error);
        showToastNotification('An error occurred while selling shares.', 'error');
    }
}

function searchStocksInSector(sector) {
    // redirecting with the sector as a filter
    if (!sector) {
        showToastNotification('Please specify a sector to search for stocks.', 'warning');
        return;
    }

    // Redirecting to my market page with sector filter
    window.location.href = `/market/overview?sector=${encodeURIComponent(sector)}`;
}

//Impact Visuialization Part of the Script
function attachImpactButtonListeners() {
    document.querySelectorAll('.show-impact-btn').forEach(button => {
        button.addEventListener('click', function() {
            const recId = this.getAttribute('data-rec-id');
            const impactElement = document.getElementById(`impact-${recId}`);

            if (impactElement) {
                // Toggling the impact visualization
                const wasCollapsed = impactElement.classList.contains('show');

                // If it was hidden and is now being shown, load the impact data
                if (!wasCollapsed) {
                    loadImpactVisualization(recId, impactElement.querySelector('.impact-content'));
                }

                // Toggling the collapse
                new bootstrap.Collapse(impactElement).toggle();

                // Update button text
                if (wasCollapsed) {
                    this.innerHTML = '<i class="bi bi-eye"></i> Show Impact';
                } else {
                    this.innerHTML = '<i class="bi bi-eye-slash"></i> Hide Impact';
                }
            }
        });
    });
}

function loadImpactVisualization(recId, container) {
    if (!container) return;

    // Extracting  recommendation type and symbol/sector from recId
    const [type, identifier] = recId.split('-');

    // Creating Different visualization based on recommendation type
    if (type === 'buy' || type === 'sell') {
        visualizeStockImpact(type, identifier, container);
    } else if (type === 'diversification') {
        visualizeDiversificationImpact(container);
    } else if (type === 'sector') {
        visualizeSectorAllocationImpact(identifier, container);
    } else {
        // Generic impact for other recommendation types
        visualizeGenericImpact(type, container);
    }
}

async function visualizeStockImpact(actionType, symbol, container) {
    try {
        // Calling my  backend to get impact data
        const response = await fetch(`/portfolio/impact-analysis?type=${actionType}&symbol=${symbol}`);
        const data = await response.json();

        if (data.error) {
            container.innerHTML = `<div class="alert alert-warning">${data.error}</div>`;
            return;
        }

        // Creating impact visualization with current vs projected values
        const currentValue = data.current_value || 0;
        const projectedValue = data.projected_value || 0;
        const valueDiff = projectedValue - currentValue;
        const percentChange = currentValue > 0 ? (valueDiff / currentValue * 100) : 0;

        const changeClass = valueDiff >= 0 ? 'text-success' : 'text-danger';
        const changeIcon = valueDiff >= 0 ? 'bi-arrow-up' : 'bi-arrow-down';

        // Creating risk comparison
        const currentRisk = data.current_risk || { volatility: 0, diversification: 0 };
        const projectedRisk = data.projected_risk || { volatility: 0, diversification: 0 };

        // Creating the visualization with HTML
        container.innerHTML = `
            <div class="row">
                <div class="col-md-6">
                    <h6>Portfolio Value Impact</h6>
                    <div class="d-flex justify-content-between">
                        <div>
                            <small class="text-muted">Current</small>
                            <h5>$${currentValue.toFixed(2)}</h5>
                        </div>
                        <div class="text-center">
                            <small class="text-muted">Change</small>
                            <h5 class="${changeClass}">
                                <i class="bi ${changeIcon}"></i> 
                                ${Math.abs(percentChange).toFixed(2)}%
                            </h5>
                        </div>
                        <div>
                            <small class="text-muted">Projected</small>
                            <h5>$${projectedValue.toFixed(2)}</h5>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <h6>Risk Impact</h6>
                    <div class="row">
                        <div class="col-6">
                            <small class="text-muted">Volatility</small>
                            <div class="d-flex align-items-center">
                                <span class="me-2">${(currentRisk.volatility * 100).toFixed(1)}%</span>
                                <i class="bi bi-arrow-right"></i>
                                <span class="ms-2 ${projectedRisk.volatility < currentRisk.volatility ? 'text-success' : 'text-danger'}">
                                    ${(projectedRisk.volatility * 100).toFixed(1)}%
                                </span>
                            </div>
                        </div>
                        <div class="col-6">
                            <small class="text-muted">Diversification</small>
                            <div class="d-flex align-items-center">
                                <span class="me-2">${(currentRisk.diversification * 100).toFixed(1)}%</span>
                                <i class="bi bi-arrow-right"></i>
                                <span class="ms-2 ${projectedRisk.diversification > currentRisk.diversification ? 'text-success' : 'text-danger'}">
                                    ${(projectedRisk.diversification * 100).toFixed(1)}%
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="mt-3">
                <h6>Projected Allocation</h6>
                <div  style="height: 200px;"
                    <canvas id="impact-allocation-chart-${symbol}" height="200"></canvas>
            </div>
        `;

        setTimeout(() => {
            try {
                const canvasElement = document.getElementById(`impact-allocation-chart-${symbol}`);

                // Check if the element exists and is a canvas
                if (!canvasElement) {
                    console.error(`Canvas element with ID impact-allocation-chart-${symbol} not found`);
                    return;
                }

                if (!(canvasElement instanceof HTMLCanvasElement)) {
                    console.error(`Element with ID impact-allocation-chart-${symbol} is not a canvas element`);
                    return;
                }

                const ctx = canvasElement.getContext('2d');

                new Chart(ctx, {
                    type: 'doughnut',
                    data: {
                        labels: data.projected_allocation.map(item => item.symbol),
                        datasets: [{
                            data: data.projected_allocation.map(item => item.weight * 100),
                            backgroundColor: [
                                '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF',
                                '#FF9F40', '#8AC249', '#EA5545', '#87BC45', '#27AEEF'
                            ]
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: true,
                        plugins: {
                            legend: {
                                position: 'right',
                                labels: {
                                    boxWidth: 12
                                }
                            },
                            tooltip: {
                                callbacks: {
                                    label: function(context) {
                                        return `${context.label}: ${context.raw.toFixed(1)}%`;
                                    }
                                }
                            }
                        }
                    }
                });
            } catch (chartError) {
                console.error('Error creating chart:', chartError);
                const chartContainer = document.getElementById(`impact-allocation-chart-${symbol}`).parentNode;
                chartContainer.innerHTML = '<div class="alert alert-warning">Unable to render chart</div>';
            }
        }, 100); // Small delay to ensure DOM is updated

    } catch (error) {
        console.error('Error visualizing impact:', error);
        container.innerHTML = '<div class="alert alert-danger">Error calculating impact analysis.</div>';
    }
}


// Adding functions for other recommendation types...
function visualizeDiversificationImpact(container) {
    // Similar implementation to visualizeStockImpact but focused on diversification metrics
    container.innerHTML = `
        <div class="alert alert-info">
            <p>Increasing diversification generally reduces portfolio risk while maintaining return potential.</p>
            <p>A well-diversified portfolio typically has:</p>
            <ul>
                <li>8+ different stocks</li>
                <li>Exposure to multiple sectors</li>
                <li>No single position greater than 5-10% of total portfolio</li>
            </ul>
        </div>
    `;
}

function visualizeSectorAllocationImpact(sector, container) {
    try {
        // Creating a simple sector impact visualization for when data isn't available
        container.innerHTML = `
            <div class="alert alert-info">
                <h6 class="mb-3">Sector Allocation Impact</h6>
                <p>Adding exposure to the ${sector} sector would help diversify your portfolio and potentially:</p>
                <ul>
                    <li>Reduce overall portfolio risk through diversification</li>
                    <li>Capture growth opportunities in the ${sector} sector</li>
                    <li>Balance your portfolio against market fluctuations</li>
                </ul>
                <h6 class="mt-3">Recommended ${sector} Stocks</h6>
                <div class="row">
                    ${getSectorStockRecommendations(sector)}
                </div>
            </div>
        `;
    } catch (error) {
        console.error('Error visualizing sector impact:', error);
        container.innerHTML = '<div class="alert alert-danger">Error generating sector impact visualization.</div>';
    }
}

function visualizeGenericImpact(type, container) {
    // Creating a generic impact visualization based on recommendation type
    let content = '';

    switch (type) {
        case 'diversification':
            content = `
                <div class="alert alert-info">
                    <h6>Diversification Impact</h6>
                    <p>Improving diversification typically reduces portfolio volatility while maintaining return potential.</p>
                    <div class="row mt-3">
                        <div class="col-md-6">
                            <h6>Current Portfolio</h6>
                            <div class="progress mb-2" style="height: 20px;">
                                <div class="progress-bar bg-danger" style="width: 70%">High Risk</div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <h6>Projected Portfolio</h6>
                            <div class="progress mb-2" style="height: 20px;">
                                <div class="progress-bar bg-success" style="width: 40%">Lower Risk</div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            break;

        case 'risk':
            content = `
                <div class="alert alert-info">
                    <h6>Risk Reduction Impact</h6>
                    <p>Reducing portfolio risk helps protect against market downturns and volatility.</p>
                    <div class="row mt-3">
                        <div class="col-md-6">
                            <h6>Current Volatility</h6>
                            <div class="progress mb-2" style="height: 20px;">
                                <div class="progress-bar bg-danger" style="width: 75%">25% Annual</div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <h6>Target Volatility</h6>
                            <div class="progress mb-2" style="height: 20px;">
                                <div class="progress-bar bg-success" style="width: 40%">15% Annual</div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            break;

        case 'goal':
            content = `
                <div class="alert alert-info">
                    <h6>Investment Goal Alignment</h6>
                    <p>Aligning your portfolio with your investment goals improves the likelihood of meeting your objectives.</p>
                    <div class="mt-3">
                        <p>Following this recommendation will better align your portfolio with your stated investment goals.</p>
                    </div>
                </div>
            `;
            break;

        case 'tax':
            content = `
                <div class="alert alert-info">
                    <h6>Tax Optimization Impact</h6>
                    <p>Tax optimization strategies can improve your after-tax returns.</p>
                    <div class="mt-3">
                        <p>Tax-loss harvesting and other tax strategies can save an estimated 0.5% to 1.5% annually in tax costs.</p>
                    </div>
                </div>
            `;
            break;

        default:
            content = `
                <div class="alert alert-info">
                    <p>Following this recommendation may improve your portfolio's performance or risk characteristics.</p>
                </div>
            `;
    }

    container.innerHTML = content;
}

// Helper function to suggest stocks in a sector
function getSectorStockRecommendations(sector) {
    const sectorStocks = {
        'Technology': [
            { symbol: 'AAPL', name: 'Apple Inc.' },
            { symbol: 'MSFT', name: 'Microsoft Corp.' },
            { symbol: 'GOOGL', name: 'Alphabet Inc.' }
        ],
        'Healthcare': [
            { symbol: 'JNJ', name: 'Johnson & Johnson' },
            { symbol: 'PFE', name: 'Pfizer Inc.' },
            { symbol: 'UNH', name: 'UnitedHealth Group' }
        ],
        'Financials': [
            { symbol: 'JPM', name: 'JPMorgan Chase' },
            { symbol: 'BAC', name: 'Bank of America' },
            { symbol: 'V', name: 'Visa Inc.' }
        ],
        'Consumer Defensive': [
            { symbol: 'PG', name: 'Procter & Gamble' },
            { symbol: 'KO', name: 'Coca-Cola Company' },
            { symbol: 'WMT', name: 'Walmart Inc.' }
        ],
        'Energy': [
            { symbol: 'XOM', name: 'Exxon Mobil' },
            { symbol: 'CVX', name: 'Chevron Corp.' },
            { symbol: 'COP', name: 'ConocoPhillips' }
        ],
        'Utilities': [
            { symbol: 'NEE', name: 'NextEra Energy' },
            { symbol: 'DUK', name: 'Duke Energy' },
            { symbol: 'SO', name: 'Southern Company' }
        ],
        'Communication Services': [
            { symbol: 'VZ', name: 'Verizon Communications' },
            { symbol: 'T', name: 'AT&T Inc.' },
            { symbol: 'CMCSA', name: 'Comcast Corp.' }
        ],
        'Industrials': [
            { symbol: 'HON', name: 'Honeywell International' },
            { symbol: 'UNP', name: 'Union Pacific' },
            { symbol: 'BA', name: 'Boeing Co.' }
        ],
        'Materials': [
            { symbol: 'LIN', name: 'Linde plc' },
            { symbol: 'ECL', name: 'Ecolab Inc.' },
            { symbol: 'APD', name: 'Air Products & Chemicals' }
        ],
        'Real Estate': [
            { symbol: 'AMT', name: 'American Tower' },
            { symbol: 'PLD', name: 'Prologis Inc.' },
            { symbol: 'CCI', name: 'Crown Castle' }
        ]
    };

    // Use default stocks if the sector isn't found
    const stocks = sectorStocks[sector] || [
        { symbol: 'SPY', name: 'S&P 500 ETF' },
        { symbol: 'VTI', name: 'Vanguard Total Stock Market ETF' },
        { symbol: 'QQQ', name: 'Invesco QQQ Trust' }
    ];

    // Generating HTML for my stock cards
    return stocks.map(stock => `
        <div class="col-md-4 mb-2">
            <div class="card">
                <div class="card-body p-2">
                    <h6 class="mb-0">${stock.symbol}</h6>
                    <small class="text-muted">${stock.name}</small>
                    <div class="mt-1">
                        <button class="btn btn-sm btn-outline-primary action-btn" 
                                data-action="buy" 
                                data-symbol="${stock.symbol}">
<!--                         <i class="bi bi-plus-circle"></i> Add-->
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `).join('');
}



// Feedback button handlers
function attachFeedbackButtonListeners() {
    document.querySelectorAll('.feedback-btn').forEach(button => {
        button.addEventListener('click', function() {
            const recType = this.getAttribute('data-rec-type');
            const recAction = this.getAttribute('data-rec-action');

            openFeedbackModal(recType, recAction);
        });
    });
}

function openFeedbackModal(recType, recAction) {
    //Removing any existing feedback modal
    const existingModal = document.getElementById('feedbackModal');
    if (existingModal) {
        existingModal.remove();
    }

    // Creating modal for HTML
    const modalHtml = `
        <div class="modal fade" id="feedbackModal" tabindex="-1" aria-hidden="true">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header bg-info text-white">
                        <h5 class="modal-title">Rate This Recommendation</h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <p>How helpful was this recommendation?</p>
                        <div class="rating-stars mb-3 text-center">
                            <i class="bi bi-star rating-star fs-3" data-rating="5"></i>
                            <i class="bi bi-star rating-star fs-3" data-rating="4"></i>
                            <i class="bi bi-star rating-star fs-3" data-rating="3"></i>
                            <i class="bi bi-star rating-star fs-3" data-rating="2"></i>
                            <i class="bi bi-star rating-star fs-3" data-rating="1"></i>
                        </div>
                        
                        <div class="form-check mb-3">
                            <input class="form-check-input" type="checkbox" id="followedRecommendation">
                            <label class="form-check-label" for="followedRecommendation">
                                I followed this recommendation
                            </label>
                        </div>
                        
                        <div class="mb-3">
                            <label for="feedbackComment" class="form-label">Additional comments (optional)</label>
                            <textarea class="form-control" id="feedbackComment" rows="3"></textarea>
                        </div>
                        
                        <input type="hidden" id="rec-type" value="${recType}">
                        <input type="hidden" id="rec-action" value="${recAction}">
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-primary" id="submit-feedback">Submit Feedback</button>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Adding modal to body
    document.body.insertAdjacentHTML('beforeend', modalHtml);

    // Set up star rating
    document.querySelectorAll('.rating-star').forEach(star => {
        star.addEventListener('click', function() {
            const rating = parseInt(this.getAttribute('data-rating'));
            document.querySelectorAll('.rating-star').forEach(s => {
                const starRating = parseInt(s.getAttribute('data-rating'));
                if (starRating <= rating) {
                    s.classList.remove('bi-star');
                    s.classList.add('bi-star-fill', 'text-warning');
                } else {
                    s.classList.remove('bi-star-fill', 'text-warning');
                    s.classList.add('bi-star');
                }
            });
            document.getElementById('feedbackModal').setAttribute('data-user-rating', rating);
        });
    });

    // Setting up submit handler
    document.getElementById('submit-feedback').addEventListener('click', function() {
        const modal = document.getElementById('feedbackModal');
        const rating = parseInt(modal.getAttribute('data-user-rating') || 0);
        const wasFollowed = document.getElementById('followedRecommendation').checked;
        const comment = document.getElementById('feedbackComment').value;
        const recType = document.getElementById('rec-type').value;
        const recAction = document.getElementById('rec-action').value;

        if (!rating) {
            showToastNotification('Please select a rating.', 'warning');
            return;
        }

        submitFeedback(recType, recAction, rating, wasFollowed, comment);
    });

    // Showing the  modal
    const modal = new bootstrap.Modal(document.getElementById('feedbackModal'));
    modal.show();
}

async function submitFeedback(recType, recAction, rating, wasFollowed, comment) {
    try {
        const response = await fetch('/portfolio/recommendation-feedback', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                recommendation_type: recType,
                recommendation_action: recAction,
                rating: rating,
                was_followed: wasFollowed,
                comment: comment
            })
        });

        if (response.ok) {
            // Closing modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('feedbackModal'));
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
                }, 300);
            }

            showToastNotification('Thank you for your feedback!', 'success');
        } else {
            const result = await response.json();
            showToastNotification(`Error: ${result.message || 'Failed to submit feedback'}`, 'error');
        }
    } catch (error) {
        console.error('Error submitting feedback:', error);
        showToastNotification('An error occurred while submitting feedback.', 'error');
    }
}

function getSectorDescription(sector) {
    const descriptions = {
        'Technology': 'Higher growth potential with increased volatility, sensitive to innovation cycles',
        'Healthcare': 'Defensive sector with stable demand, influenced by demographics and regulation',
        'Financials': 'Cyclical sector tied to economic conditions and interest rates',
        'Consumer Defensive': 'Stable performance across economic cycles, lower volatility',
        'Energy': 'Cyclical sector influenced by commodity prices and global demand',
        'Utilities': 'Defensive sector with stable dividends, sensitive to interest rates',
        'Communication Services': 'Mix of growth and value companies, evolving from utilities to tech',
        'Industrials': 'Cyclical sector tied to economic expansion and manufacturing',
        'Materials': 'Cyclical sector sensitive to commodity prices and global growth',
        'Real Estate': 'Income-focused sector influenced by interest rates and property trends'
    };

    return descriptions[sector] || 'Unique characteristics and risk/return profile';
}




function showToastNotification(message, type = 'info') {
    const toastId = `toast-${Date.now()}`;
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${getToastColor(type)} border-0 position-fixed bottom-0 end-0 m-3`;
    toast.id = toastId;
    toast.role = 'alert';
    toast.ariaLive = 'assertive';
    toast.ariaAtomic = 'true';
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;

    document.body.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast, { delay: 3000 });
    bsToast.show();

    // Optional cleanup
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

function getToastColor(type) {
    switch (type) {
        case 'success':
            return 'success';
        case 'error':
        case 'danger':
            return 'danger';
        case 'warning':
            return 'warning';
        default:
            return 'primary';
    }
}




