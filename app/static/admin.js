///3rd version
document.addEventListener('DOMContentLoaded', function() {
    // Check if we've already attached the event listener
    if (window.userActionsAttached) return;
    window.userActionsAttached = true;

    // Use event delegation for user actions
    document.addEventListener('click', function(event) {
        // Edit user
        if (event.target.classList.contains('edit-user')) {
            const userId = event.target.getAttribute('data-user-id');
            window.location.href = `/admin/users/edit/${userId}`;
        }

        // Delete user
        if (event.target.classList.contains('delete-user')) {
            const userId = event.target.getAttribute('data-user-id');
            if (confirm('Are you sure you want to delete this user?')) {
                deleteUser(userId);
            }
        }

        // Add user submit button
        if (event.target.id === 'add-user-submit') {
            const username = document.getElementById('username').value.trim();
            const email = document.getElementById('email').value.trim();
            const password = document.getElementById('password').value;
            const isAdmin = document.getElementById('is-admin').checked;

            if (!username || !email || !password) {
                alert('Please fill in all required fields');
                return;
            }

            addUser(username, email, password, isAdmin);
        }
    });
});


 async function deleteUser(userId) {
    try {
        const response = await fetch(`/admin/users/delete/${userId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const result = await response.json();

        if (result.success) {
            alert('User deleted successfully!');
            window.location.reload();
        } else {
            alert(result.message || 'Failed to delete user');
        }
    } catch (error) {
        console.error('Error deleting user:', error);
        alert('An error occurred while deleting user');
    }
}

async function addUser(username, email, password, isAdmin) {
    try {
        const response = await fetch('/admin/users/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username: username,
                email: email,
                password: password,
                is_admin: isAdmin
            })
        });

        const result = await response.json();

        if (result.success) {
            //Closing the Modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('addUserModal'));
            modal.hide();

            //Reloading the page to show the new User
            alert('User added successfully!');
            window.location.reload();
        } else {
            console.error(result.message || 'Failed to add user');
        }
    } catch (error) {
        console.error('Error adding user:', error);
        alert('An error occurred while adding user');
    }
}

// Function to load portfolio details
async function loadPortfolioDetails() {
    const loadingSpinner = document.getElementById('portfolioLoadingSpinner');
    const contentContainer = document.getElementById('portfolioDetailsContent');

    if (!loadingSpinner || !contentContainer) {
        console.error('Portfolio elements not found');
        return;
    }

    // Show loading spinner, hide content
    loadingSpinner.style.display = 'block';
    contentContainer.style.display = 'none';

    try {
        // Make API call to the admin endpoint
        const response = await fetch('/admin/portfolios/all');

        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const portfolios = await response.json();
        console.log('Received portfolio data:', portfolios);

        // Generate HTML for the portfolios
        let html = `
            <div class="table-responsive">
                <table class="table table-striped table-hover">
                    <thead>
                        <tr>
                            <th>Portfolio Name</th>
                            <th>Value</th>
                            <th>Holdings</th>
                            <th>Created</th>
                        </tr>
                    </thead>
                    <tbody>
        `;

        if (!portfolios || portfolios.length === 0) {
            html += `
                <tr>
                    <td colspan="5" class="text-center">No portfolios found</td>
                </tr>
            `;
        } else {
            portfolios.forEach(portfolio => {
                const portfolioValue = typeof portfolio.value === 'number' ? portfolio.value.toFixed(2) : '0.00';
                html += `
                    <tr>
                        <td>${portfolio.name}</td>
                        <td>$${portfolioValue}</td>
                        <td>${portfolio.holdings_count} stocks</td>
                        <td>${new Date(portfolio.created_at).toLocaleDateString()}</td>                        
                    </tr>
                `;
            });
        }

        html += `
                    </tbody>
                </table>
            </div>
        `;

        // Update the content container with the generated HTML
        contentContainer.innerHTML = html;

        // Hide loading spinner, show content
        loadingSpinner.style.display = 'none';
        contentContainer.style.display = 'block';

    } catch (error) {
        console.error('Error loading portfolio details:', error);

        // Show error message
        contentContainer.innerHTML = `
            <div class="alert alert-danger">
                <i class="bi bi-exclamation-triangle-fill me-2"></i>
                Error loading portfolio details. Please try again later.
            </div>
        `;

        // Hide loading spinner, show content with error
        loadingSpinner.style.display = 'none';
        contentContainer.style.display = 'block';
    }
}

// Add event listener to the button
document.addEventListener('DOMContentLoaded', function() {
    const viewPortfoliosBtn = document.getElementById('viewPortfoliosBtn');
    if (viewPortfoliosBtn) {
        viewPortfoliosBtn.addEventListener('click', loadPortfolioDetails);
    }

    // Also handle the modal open event to load data
    const portfolioModal = document.getElementById('portfolioDetailsModal');
    if (portfolioModal) {
        portfolioModal.addEventListener('show.bs.modal', loadPortfolioDetails);
    }
});