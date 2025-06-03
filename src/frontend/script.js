/**
 * OpenShift Service Mesh Inventory Demo - Frontend JavaScript
 * Handles UI interactions and API communication through the service mesh
 */

class InventoryApp {
    constructor() {
        this.apiBase = '/api';
        this.currentPage = 1;
        this.totalPages = 1;
        this.searchTerm = '';
        this.isLoading = false;
        
        // Initialize the application
        this.init();
    }

    /**
     * Initialize the application
     */
    init() {
        this.bindEvents();
        this.loadInventory();
        this.updateMeshStatus();
        
        // Set focus on first input
        document.getElementById('item-code').focus();
    }

    /**
     * Bind event listeners
     */
    bindEvents() {
        // Form submission
        document.getElementById('add-item-form').addEventListener('submit', this.handleAddItem.bind(this));
        
        // Search functionality
        document.getElementById('search-btn').addEventListener('click', this.handleSearch.bind(this));
        document.getElementById('search-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.handleSearch();
            }
        });
        
        // Refresh button
        document.getElementById('refresh-btn').addEventListener('click', this.handleRefresh.bind(this));
        
        // Pagination
        document.getElementById('prev-page').addEventListener('click', this.handlePrevPage.bind(this));
        document.getElementById('next-page').addEventListener('click', this.handleNextPage.bind(this));
        
        // Auto-format item code input
        document.getElementById('item-code').addEventListener('input', this.formatItemCode.bind(this));
        
        // Auto-refresh every 30 seconds
        setInterval(() => {
            if (!this.isLoading) {
                this.loadInventory(false); // Silent refresh
            }
        }, 30000);
    }

    /**
     * Format item code input (uppercase, max length)
     */
    formatItemCode(event) {
        const input = event.target;
        let value = input.value.toUpperCase().replace(/[^A-Z0-9]/g, '');
        if (value.length > 6) {
            value = value.substring(0, 6);
        }
        input.value = value;
    }

    /**
     * Update service mesh status indicator
     */
    updateMeshStatus() {
        const statusElement = document.getElementById('meshStatus');
        if (statusElement) {
            statusElement.classList.add('fade-in');
        }
    }

    /**
     * Handle form submission for adding new item
     */
    async handleAddItem(event) {
        event.preventDefault();
        
        if (this.isLoading) return;
        
        const form = event.target;
        const formData = new FormData(form);
        
        const item = {
            code: document.getElementById('item-code').value.trim().toUpperCase(),
            name: document.getElementById('item-name').value.trim(),
            quantity: parseInt(document.getElementById('item-quantity').value)
        };

        // Client-side validation
        if (!this.validateItem(item)) {
            return;
        }

        try {
            this.setLoadingState(true);
            this.updateButtonState(true);
            
            const response = await fetch(`${this.apiBase}/inventory`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Service-Mesh': 'true'
                },
                body: JSON.stringify(item)
            });

            const result = await response.json();

            if (response.ok) {
                this.showMessage('✅ Item added successfully! Traffic flowed through Service Mesh.', 'success');
                form.reset();
                document.getElementById('item-code').focus();
                await this.loadInventory();
                
                // Show mesh traffic indication
                this.highlightMeshTraffic();
            } else {
                this.showMessage(`❌ ${result.error || 'Failed to add item'}`, 'error');
            }
        } catch (error) {
            console.error('Error adding item:', error);
            this.showMessage('🚨 Network error. Check Service Mesh connectivity.', 'error');
        } finally {
            this.setLoadingState(false);
            this.updateButtonState(false);
        }
    }

    /**
     * Validate item data on client side
     */
    validateItem(item) {
        if (!item.code || !item.name || isNaN(item.quantity)) {
            this.showMessage('❌ Please fill in all fields correctly', 'error');
            return false;
        }

        if (item.code.length !== 6) {
            this.showMessage('❌ Item code must be exactly 6 characters', 'error');
            return false;
        }

        if (!/^[A-Z]/.test(item.code)) {
            this.showMessage('❌ Item code must start with a letter', 'error');
            return false;
        }

        if (!/^[A-Z0-9]+$/.test(item.code)) {
            this.showMessage('❌ Item code can only contain letters and numbers', 'error');
            return false;
        }

        if (item.quantity < 0) {
            this.showMessage('❌ Quantity cannot be negative', 'error');
            return false;
        }

        return true;
    }

    /**
     * Handle search functionality
     */
    async handleSearch() {
        this.searchTerm = document.getElementById('search-input').value.trim();
        this.currentPage = 1;
        await this.loadInventory();
    }

    /**
     * Handle refresh button
     */
    async handleRefresh() {
        this.searchTerm = '';
        document.getElementById('search-input').value = '';
        this.currentPage = 1;
        await this.loadInventory();
    }

    /**
     * Handle pagination - previous page
     */
    async handlePrevPage() {
        if (this.currentPage > 1) {
            this.currentPage--;
            await this.loadInventory();
        }
    }

    /**
     * Handle pagination - next page
     */
    async handleNextPage() {
        if (this.currentPage < this.totalPages) {
            this.currentPage++;
            await this.loadInventory();
        }
    }

    /**
     * Load inventory data from API
     */
    async loadInventory(showLoading = true) {
        if (this.isLoading) return;
        
        try {
            this.setLoadingState(true);
            
            if (showLoading) {
                this.showLoadingState();
            }

            // Build query parameters
            const params = new URLSearchParams({
                page: this.currentPage,
                per_page: 20
            });
            
            if (this.searchTerm) {
                params.append('search', this.searchTerm);
            }

            const response = await fetch(`${this.apiBase}/inventory?${params}`, {
                headers: {
                    'X-Service-Mesh': 'true'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            this.renderInventory(data);
            
            if (showLoading) {
                this.highlightMeshTraffic();
            }
            
        } catch (error) {
            console.error('Error loading inventory:', error);
            this.showErrorState('Failed to load inventory through Service Mesh');
        } finally {
            this.setLoadingState(false);
        }
    }

    /**
     * Render inventory data
     */
    renderInventory(data) {
        const items = data.items || [];
        const pagination = data.pagination || {};
        
        this.totalPages = pagination.pages || 1;
        this.currentPage = pagination.page || 1;

        const loadingDiv = document.getElementById('loading');
        const inventoryContainer = document.getElementById('inventory-container');
        const emptyState = document.getElementById('empty-state');
        const tbody = document.getElementById('inventory-tbody');

        // Hide loading
        loadingDiv.style.display = 'none';

        if (items.length === 0) {
            inventoryContainer.style.display = 'none';
            emptyState.style.display = 'block';
            emptyState.classList.add('fade-in');
            return;
        }

        // Show inventory container
        emptyState.style.display = 'none';
        inventoryContainer.style.display = 'block';
        inventoryContainer.classList.add('fade-in');

        // Update item count
        const itemCount = document.getElementById('item-count');
        if (itemCount) {
            const total = pagination.total || items.length;
            itemCount.textContent = `${total} item${total !== 1 ? 's' : ''}`;
        }

        // Render table rows
        tbody.innerHTML = '';
        items.forEach(item => {
            const row = this.createItemRow(item);
            tbody.appendChild(row);
        });

        // Update pagination
        this.updatePagination(pagination);
    }

    /**
     * Create table row for an item
     */
    createItemRow(item) {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><span class="item-code">${this.escapeHtml(item.code)}</span></td>
            <td>${this.escapeHtml(item.name)}</td>
            <td><span class="quantity">${item.quantity}</span></td>
            <td>${this.formatDate(item.created_at)}</td>
            <td class="actions">
                <button class="btn-small btn-edit" onclick="app.editItem(${item.id})">Edit</button>
                <button class="btn-small btn-delete" onclick="app.deleteItem(${item.id}, '${this.escapeHtml(item.code)}')">Delete</button>
            </td>
        `;
        return row;
    }

    /**
     * Update pagination controls
     */
    updatePagination(pagination) {
        const paginationDiv = document.getElementById('pagination');
        const prevBtn = document.getElementById('prev-page');
        const nextBtn = document.getElementById('next-page');
        const pageInfo = document.getElementById('page-info');

        if (pagination.pages > 1) {
            paginationDiv.style.display = 'flex';
            
            prevBtn.disabled = pagination.page <= 1;
            nextBtn.disabled = pagination.page >= pagination.pages;
            
            pageInfo.textContent = `Page ${pagination.page} of ${pagination.pages}`;
        } else {
            paginationDiv.style.display = 'none';
        }
    }

    /**
     * Show loading state
     */
    showLoadingState() {
        document.getElementById('loading').style.display = 'block';
        document.getElementById('inventory-container').style.display = 'none';
        document.getElementById('empty-state').style.display = 'none';
    }

    /**
     * Show error state
     */
    showErrorState(message) {
        document.getElementById('loading').innerHTML = `
            <div style="color: var(--error-color);">
                <strong>❌ ${message}</strong><br>
                <small>Check Service Mesh configuration and try again</small>
            </div>
        `;
    }

    /**
     * Set loading state for operations
     */
    setLoadingState(loading) {
        this.isLoading = loading;
    }

    /**
     * Update button state during operations
     */
    updateButtonState(loading) {
        const btn = document.querySelector('#add-item-form button[type="submit"]');
        const btnText = btn.querySelector('.btn-text');
        const btnLoader = btn.querySelector('.btn-loader');
        
        if (loading) {
            btn.disabled = true;
            btnText.style.display = 'none';
            btnLoader.style.display = 'inline';
        } else {
            btn.disabled = false;
            btnText.style.display = 'inline';
            btnLoader.style.display = 'none';
        }
    }

    /**
     * Highlight service mesh traffic
     */
    highlightMeshTraffic() {
        const meshIndicator = document.querySelector('.mesh-indicator');
        if (meshIndicator) {
            meshIndicator.style.background = '#ff9800';
            meshIndicator.textContent = 'Traffic Active';
            
            setTimeout(() => {
                meshIndicator.style.background = 'var(--success-color)';
                meshIndicator.textContent = 'via Service Mesh';
            }, 2000);
        }
    }

    /**
     * Show message to user
     */
    showMessage(message, type) {
        const messageDiv = document.getElementById('message');
        messageDiv.textContent = message;
        messageDiv.className = `message ${type}`;
        messageDiv.style.display = 'block';
        messageDiv.classList.add('fade-in');
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            messageDiv.style.display = 'none';
            messageDiv.classList.remove('fade-in');
        }, 5000);
        
        // Scroll to message
        messageDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    /**
     * Edit item (placeholder for future functionality)
     */
    async editItem(itemId) {
        this.showMessage('🔧 Edit functionality coming soon!', 'warning');
    }

    /**
     * Delete item
     */
    async deleteItem(itemId, itemCode) {
        if (!confirm(`Are you sure you want to delete item "${itemCode}"?`)) {
            return;
        }

        try {
            this.setLoadingState(true);
            
            const response = await fetch(`${this.apiBase}/inventory/${itemId}`, {
                method: 'DELETE',
                headers: {
                    'X-Service-Mesh': 'true'
                }
            });

            if (response.ok) {
                this.showMessage(`✅ Item "${itemCode}" deleted successfully!`, 'success');
                await this.loadInventory();
                this.highlightMeshTraffic();
            } else {
                const error = await response.json();
                this.showMessage(`❌ ${error.error || 'Failed to delete item'}`, 'error');
            }
        } catch (error) {
            console.error('Error deleting item:', error);
            this.showMessage('🚨 Network error during deletion', 'error');
        } finally {
            this.setLoadingState(false);
        }
    }

    /**
     * Utility: Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Utility: Format date for display
     */
    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new InventoryApp();
    
    // Add some visual feedback for Service Mesh
    console.log('🌐 OpenShift Service Mesh Inventory Demo Loaded');
    console.log('📊 All API traffic flows through Istio service mesh with mTLS encryption');
    console.log('🔍 Monitor traffic in Kiali: https://kiali-istio-system.apps.oxcart.zambruhni.com');
});

// Add keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // Ctrl/Cmd + K to focus search
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        document.getElementById('search-input').focus();
    }
    
    // Ctrl/Cmd + N to focus new item form
    if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
        e.preventDefault();
        document.getElementById('item-code').focus();
    }
    
    // Escape to clear search
    if (e.key === 'Escape') {
        const searchInput = document.getElementById('search-input');
        if (searchInput === document.activeElement) {
            searchInput.value = '';
            searchInput.blur();
        }
    }
});

// Service Worker registration for PWA capabilities (optional)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
            .then(() => console.log('Service Worker registered'))
            .catch(() => console.log('Service Worker registration failed'));
    });
}