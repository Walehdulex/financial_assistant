// Priority class helper for recommendations 
function getPriorityClass(priority) {
    switch(priority) {
        case 'high': return 'danger';
        case 'medium': return 'warning';
        case 'low': return 'info';
        default: return 'secondary';
    }
}

// Risk level class helper
function getRiskClass(riskLevel) {
    switch (riskLevel.toLowerCase()) {
        case 'high': return 'danger';
        case 'medium': return 'warning';
        case 'low': return 'success';
        default: return 'secondary';
    }
}

// Sentiment class helper for news
function getSentimentClass(sentiment) {
    switch (sentiment.toLowerCase()) {
        case 'bullish': return 'bg-success';
        case 'somewhat-bullish': return 'bg-success text-white';
        case 'bearish': return 'bg-danger';
        case 'somewhat-bearish': return 'bg-danger text-white';
        default: return 'bg-secondary';
    }
}

// Date formatting helper
function formatDate(dateString) {
    if (!dateString) return 'Unknown date';
    const date = new Date(dateString);
    return date.toLocaleDateString();
}

// Volume formatting helper
function formatVolume(volume) {
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

// Helper function to safely get DOM elements
function getElement(id) {
    const element = document.getElementById(id);
    if (!element) {
        console.warn(`Element with ID "${id}" not found in the DOM`);
    }
    return element;
}

// Helper to safely update element content
function updateElementContent(id, content) {
    const element = getElement(id);
    if (element) {
        element.innerHTML = content;
    }
}