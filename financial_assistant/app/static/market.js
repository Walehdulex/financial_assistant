console.log("Market.js loaded!");

document.addEventListener('DOMContentLoaded', function() {
    console.log('Market JS loaded at', new Date().toISOString());

    // Look for the market overview header or any unique element
    const marketOverview = document.querySelector('.card-header h3');
    if (marketOverview && marketOverview.textContent.includes('Market Overview')) {
        console.log('Market Overview page detected, initializing...');

        // Load all market data
        loadMarketIndices();
        loadMarketMovers();
        loadMarketNews();

        // Set up search form handler
        const searchForm = document.getElementById('stock-search-form');
        if (searchForm) {
            searchForm.addEventListener('submit', function(e) {
                e.preventDefault();
                const symbol = document.getElementById('stock-symbol').value.trim().toUpperCase();
                if (symbol) {
                    searchStock(symbol);
                }
            });
        }
    }
});

async function loadMarketIndices() {
    try {
        console.log('Loading market indices...');
        const response = await fetch('/market/indices');
        const data = await response.json();
        console.log('Market indices data:', data);

        // Make sure we have valid data
        if (!data || !data.sp500 || !data.nasdaq || !data.dow) {
            console.error('Invalid market indices data structure:', data);
            return;
        }

        // Update S&P 500
        const sp500Price = document.getElementById('sp500-price');
        const sp500Change = document.getElementById('sp500-change');
        if (sp500Price && sp500Change) {
            sp500Price.textContent = data.sp500.price;
            sp500Change.textContent = `${data.sp500.change} (${data.sp500.changePercent}%)`;
            sp500Change.className = parseFloat(data.sp500.change) >= 0 ? 'text-success card-text' : 'text-danger card-text';
        }

        // Update Nasdaq
        const nasdaqPrice = document.getElementById('nasdaq-price');
        const nasdaqChange = document.getElementById('nasdaq-change');
        if (nasdaqPrice && nasdaqChange) {
            nasdaqPrice.textContent = data.nasdaq.price;
            nasdaqChange.textContent = `${data.nasdaq.change} (${data.nasdaq.changePercent}%)`;
            nasdaqChange.className = parseFloat(data.nasdaq.change) >= 0 ? 'text-success card-text' : 'text-danger card-text';
        }

        // Update Dow Jones
        const dowPrice = document.getElementById('dow-price');
        const dowChange = document.getElementById('dow-change');
        if (dowPrice && dowChange) {
            dowPrice.textContent = data.dow.price;
            dowChange.textContent = `${data.dow.change} (${data.dow.changePercent}%)`;
            dowChange.className = parseFloat(data.dow.change) >= 0 ? 'text-success card-text' : 'text-danger card-text';
        }
    } catch (error) {
        console.error('Error loading market indices:', error);
    }
}

async function loadMarketMovers() {
    try {
        console.log('Loading market movers...');
        const response = await fetch('/market/movers');
        const data = await response.json();
        console.log('Market movers data:', data);

        // Update gainers
        updateMoversTable('gainers-container', data.gainers);

        // Update losers
        updateMoversTable('losers-container', data.losers);

        // Update most active
        updateMoversTable('volume-container', data.mostActive);

    } catch (error) {
        console.error('Error loading market movers:', error);
    }
}

function updateMoversTable(containerId, stocks) {
    const container = document.getElementById(containerId);
    if (!container) {
        console.error(`Container ${containerId} not found`);
        return;
    }

    if (!stocks || stocks.length === 0) {
        container.innerHTML = '<p class="text-muted">No data available</p>';
        return;
    }

    const table = document.createElement('table');
    table.className = 'table table-sm table-hover';

    // Create header
    const thead = document.createElement('thead');
    thead.innerHTML = `
        <tr>
            <th>Symbol</th>
            <th>Price</th>
            <th>Change</th>
            <th>% Change</th>
            <th>Volume</th>
        </tr>
    `;
    table.appendChild(thead);

    // Create body
    const tbody = document.createElement('tbody');

    stocks.forEach(stock => {
        const row = document.createElement('tr');
        row.style.cursor = 'pointer';
        row.addEventListener('click', () => window.location.href = `/market/stock/${stock.symbol}`);

        const changeClass = parseFloat(stock.change) >= 0 ? 'text-success' : 'text-danger';

        row.innerHTML = `
            <td>${stock.symbol}</td>
            <td>${stock.price}</td>
            <td class="${changeClass}">${stock.change}</td>
            <td class="${changeClass}">${stock.changePercent}%</td>
            <td>${formatVolume(stock.volume)}</td>
        `;

        tbody.appendChild(row);
    });

    table.appendChild(tbody);
    container.innerHTML = '';
    container.appendChild(table);
}

function formatVolume(volume) {
    if (!volume) return 'N/A';
    volume = parseFloat(volume);
    if (isNaN(volume)) return 'N/A';

    if (volume >= 1000000000) {
        return (volume / 1000000000).toFixed(2) + 'B';
    } else if (volume >= 1000000) {
        return (volume / 1000000).toFixed(2) + 'M';
    } else if (volume >= 1000) {
        return (volume / 1000).toFixed(2) + 'K';
    } else {
        return volume.toString();
    }
}

async function loadMarketNews() {
    try {
        console.log('Loading market news...');
        const response = await fetch('/market/news');
        const data = await response.json();
        console.log('Market news data:', data);

        const container = document.getElementById('market-news-container');
        if (!container) {
            console.error('Market news container not found');
            return;
        }

        container.innerHTML = '';

        if (!data.news || data.news.length === 0) {
            container.innerHTML = '<p class="text-muted">No news available</p>';
            return;
        }

        const newsList = document.createElement('div');
        newsList.className = 'list-group list-group-flush';

        data.news.slice(0, 5).forEach(item => {
            const newsItem = document.createElement('a');
            newsItem.className = 'list-group-item list-group-item-action flex-column align-items-start p-2';
            newsItem.href = item.url || '#';
            newsItem.target = '_blank';

            const date = item.published_at ? new Date(item.published_at) : new Date();
            const formattedDate = date.toLocaleDateString();

            newsItem.innerHTML = `
                <div class="d-flex w-100 justify-content-between">
                    <h6 class="mb-1">${item.title || 'No title'}</h6>
                </div>
                <p class="mb-1 small">${item.summary || 'No summary available'}</p>
                <small class="text-muted">${item.source || 'Unknown'} | ${formattedDate}</small>
            `;

            newsList.appendChild(newsItem);
        });

        container.appendChild(newsList);
    } catch (error) {
        console.error('Error loading market news:', error);
        const container = document.getElementById('market-news-container');
        if (container) {
            container.innerHTML = '<div class="alert alert-danger">Failed to load market news</div>';
        }
    }
}

async function searchStock(symbol) {
    try {
        console.log(`Searching for stock: ${symbol}`);
        const response = await fetch(`/market/search?symbol=${symbol}`);
        const data = await response.json();
        console.log('Search results:', data);

        const resultContainer = document.getElementById('search-result');
        if (!resultContainer) {
            console.error('Search result container not found');
            return;
        }

        if (data.error) {
            resultContainer.innerHTML = `<div class="alert alert-warning">${data.error}</div>`;
            return;
        }

        const changeClass = parseFloat(data.change) >= 0 ? 'text-success' : 'text-danger';

        resultContainer.innerHTML = `
            <div class="card">
                <div class="card-body">
                    <h5 class="card-title">${data.symbol} - ${data.name}</h5>
                    <h6 class="card-subtitle mb-2 ${changeClass}">
                        ${data.price} ${data.change} (${data.changePercent}%)
                    </h6>
                    <p class="card-text">
                        <small class="text-muted">Last updated: ${new Date(data.lastUpdated).toLocaleString()}</small>
                    </p>
                    <a href="/market/stock/${data.symbol}" class="btn btn-sm btn-primary">View Details</a>
                    <button onclick="addToPortfolio('${data.symbol}')" class="btn btn-sm btn-outline-success">Add to Portfolio</button>
                </div>
            </div>
        `;
    } catch (error) {
        console.error('Error searching stock:', error);
        const resultContainer = document.getElementById('search-result');
        if (resultContainer) {
            resultContainer.innerHTML = '<div class="alert alert-danger">Error searching for stock</div>';
        }
    }
}

function addToPortfolio(symbol) {
    // Create a small form for quantity input
    const form = document.createElement('div');
    form.innerHTML = `
        <div class="form mt-3">
            <div class="input-group">
                <input type="number" class="form-control" id="quick-add-quantity" placeholder="Quantity" min="1" value="1">
                <button class="btn btn-success" id="quick-add-btn">Add</button>
            </div>
        </div>
    `;

    const searchResult = document.getElementById('search-result');
    if (!searchResult) {
        console.error('Search result container not found');
        return;
    }

    searchResult.appendChild(form);

    document.getElementById('quick-add-btn').addEventListener('click', async () => {
        const quantity = document.getElementById('quick-add-quantity').value;

        try {
            const response = await fetch('/portfolio/add_stock', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    symbol: symbol,
                    quantity: parseInt(quantity)
                })
            });

            if (response.ok) {
                searchResult.innerHTML +=
                    '<div class="alert alert-success mt-2">Successfully added to portfolio!</div>';
            } else {
                const errorData = await response.json();
                searchResult.innerHTML +=
                    `<div class="alert alert-danger mt-2">Error: ${errorData.message || 'Failed to add to portfolio'}</div>`;
            }
        } catch (error) {
            console.error('Error adding to portfolio:', error);
            searchResult.innerHTML +=
                '<div class="alert alert-danger mt-2">Error adding to portfolio</div>';
        }
    });
}