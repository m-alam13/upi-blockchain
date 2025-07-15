// const API_BASE_URL = 'http://localhost:8000'; // Update with your backend URL
const API_BASE_URL = `${window.location.protocol}//${window.location.host}`;
class BankAccountManager {
    constructor() {
        this.currentUser = null;
        this.bankAccounts = [];
        this.init();
    }

    async init() {
        await this.loadUserData();
        await this.loadBankAccounts();
        this.setupEventListeners();
    }

    // API Request Helper
    async makeApiRequest(endpoint, method = 'GET', body = null) {
        const headers = {
            'Content-Type': 'application/json',
        };

        const config = {
            method,
            headers,
            credentials: 'include',
        };

        if (body) {
            config.body = JSON.stringify(body);
        }

        try {
            const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Request failed');
            }

            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    // Data Loading Methods
    async loadUserData() {
        this.currentUser = await this.makeApiRequest('/api/users/me');
    }

    async loadBankAccounts() {
        try {
            this.bankAccounts = await this.makeApiRequest('/bank-accounts');
            this.renderBankAccounts();
        } catch (error) {
            this.showError(error.message);
        }
    }

    // Rendering Methods
    renderBankAccounts() {
        const container = document.getElementById('bankAccountsList');
        
        if (this.bankAccounts.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <p>No bank accounts found</p>
                </div>
            `;
            return;
        }

        let html = '';
        this.bankAccounts.forEach(account => {
            html += `
                <div class="bank-account-card" data-account-id="${account.id}">
                    <div class="bank-details-row">
                        <strong>${account.bank_name}</strong>
                        ${account.is_primary ? '<span class="primary-badge">Primary</span>' : ''}
                    </div>
                    <div class="bank-details-row">
                        <span class="bank-details-label">Account Number:</span>
                        <span class="bank-details-value">${account.account_number}</span>
                    </div>
                    <div class="bank-details-row">
                        <span class="bank-details-label">Account Holder:</span>
                        <span class="bank-details-value">${account.account_holder_name || 'N/A'}</span>
                    </div>
                    <div class="bank-details-row">
                        <span class="bank-details-label">VPA:</span>
                        <span class="bank-details-value">${account.vpa}</span>
                    </div>
                    <div class="account-actions">
                        <button class="btn btn-primary check-balance-btn">Check Balance</button>
                        <button class="btn btn-secondary manage-account-btn">Manage</button>
                    </div>
                </div>
            `;
        });

        container.innerHTML = html;
        this.setupAccountActionListeners();
    }

    // Event Handlers
    setupEventListeners() {
        // Tab switching
        document.querySelectorAll('.tab').forEach(tab => {
            tab.addEventListener('click', () => {
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                
                const tabId = tab.getAttribute('data-tab');
                document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                document.getElementById(`${tabId}-tab`).classList.add('active');
            });
        });

        // Add account form
        document.getElementById('addBankAccountForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.createBankAccount();
        });

        // Check balance form
        document.getElementById('checkBalanceForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.checkAccountBalance();
        });

        // Account action buttons
        document.getElementById('setPrimaryBtn').addEventListener('click', async () => {
            await this.setPrimaryAccount();
        });

        document.getElementById('deleteAccountBtn').addEventListener('click', async () => {
            await this.deleteBankAccount();
        });

        // Modal close buttons
        document.querySelectorAll('.close-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.getElementById(e.target.closest('.modal').id).style.display = 'none';
            });
        });

        // Logout
        document.getElementById('logoutBtn').addEventListener('click', (e) => {
            e.preventDefault();
            this.logout();
        });
    }

    setupAccountActionListeners() {
        // Check balance buttons
        document.querySelectorAll('.check-balance-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const accountId = e.target.closest('.bank-account-card').getAttribute('data-account-id');
                document.getElementById('balanceAccountId').value = accountId;
                document.getElementById('checkBalanceModal').style.display = 'flex';
            });
        });

        // Manage account buttons
        document.querySelectorAll('.manage-account-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const accountId = e.target.closest('.bank-account-card').getAttribute('data-account-id');
                const account = this.bankAccounts.find(a => a.id == accountId);
                
                document.getElementById('currentAccountId').value = accountId;
                document.getElementById('accountActionsTitle').textContent = account.bank_name;
                
                // Display account info
                document.getElementById('accountInfoDisplay').innerHTML = `
                    <div class="bank-details-row">
                        <span class="bank-details-label">Account Number:</span>
                        <span class="bank-details-value">${account.account_number}</span>
                    </div>
                    <div class="bank-details-row">
                        <span class="bank-details-label">IFSC Code:</span>
                        <span class="bank-details-value">${account.ifsc_code}</span>
                    </div>
                    <div class="bank-details-row">
                        <span class="bank-details-label">VPA:</span>
                        <span class="bank-details-value">${account.vpa}</span>
                    </div>
                `;
                
                // Disable primary button if already primary
                document.getElementById('setPrimaryBtn').disabled = account.is_primary;
                
                document.getElementById('accountActionsModal').style.display = 'flex';
            });
        });
    }

    // Account Operations
    async createBankAccount() {
        const formData = {
            bank_name: document.getElementById('bankName').value,
            account_holder_name: document.getElementById('accountHolderName').value,
            account_number: document.getElementById('accountNumber').value,
            ifsc_code: document.getElementById('ifscCode').value,
            branch_name: document.getElementById('branchName').value,
            upi_pin: document.getElementById('upiPin').value,
            vpa: document.getElementById('vpa').value || undefined,
            is_primary: document.getElementById('isPrimary').checked,
            balance: 0
        };

        try {
            await this.makeApiRequest('/bank-accounts', 'POST', formData);
            this.showSuccess('Bank account added successfully!');
            document.getElementById('addBankAccountForm').reset();
            await this.loadBankAccounts();
            
            // Switch back to accounts tab
            document.querySelector('.tab[data-tab="accounts"]').click();
        } catch (error) {
            this.showError(error.message);
        }
    }

    async checkAccountBalance() {
        const accountId = document.getElementById('balanceAccountId').value;
        const upiPin = document.getElementById('balanceUpiPin').value;

        try {
            const response = await this.makeApiRequest(
                `/bank-accounts/${accountId}/check-balance`,
                'POST',
                { upi_pin: upiPin }
            );
            
            this.showSuccess(`Current balance: ₹${response.balance.toFixed(2)}`);
            document.getElementById('checkBalanceForm').reset();
            document.getElementById('checkBalanceModal').style.display = 'none';
        } catch (error) {
            this.showError(error.message);
        }
    }

    async setPrimaryAccount() {
        const accountId = document.getElementById('currentAccountId').value;

        try {
            await this.makeApiRequest(
                `/bank-accounts/${accountId}/set-primary`,
                'POST'
            );
            
            this.showSuccess('Primary account updated successfully!');
            document.getElementById('accountActionsModal').style.display = 'none';
            await this.loadBankAccounts();
        } catch (error) {
            this.showError(error.message);
        }
    }

    async deleteBankAccount() {
        const accountId = document.getElementById('currentAccountId').value;

        if (!confirm('Are you sure you want to delete this bank account?')) {
            return;
        }

        try {
            await this.makeApiRequest(
                `/bank-accounts/${accountId}`,
                'DELETE'
            );
            
            this.showSuccess('Bank account deleted successfully!');
            document.getElementById('accountActionsModal').style.display = 'none';
            await this.loadBankAccounts();
        } catch (error) {
            this.showError(error.message);
        }
    }

    async logout() {
        try {
            await this.makeApiRequest('/auth/logout', 'POST');
            window.location.href = '/login';
        } catch (error) {
            this.showError(error.message);
        }
    }

    // UI Helpers
    showSuccess(message) {
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-success';
        alertDiv.textContent = message;
        document.getElementById('alertContainer').appendChild(alertDiv);
        
        setTimeout(() => {
            alertDiv.remove();
        }, 5000);
    }

    showError(message) {
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-danger';
        alertDiv.textContent = message;
        document.getElementById('alertContainer').appendChild(alertDiv);
        
        setTimeout(() => {
            alertDiv.remove();
        }, 5000);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new BankAccountManager();
});