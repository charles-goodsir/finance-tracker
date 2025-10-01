// Configuration
const API_BASE_URL = CONFIG.API_BASE_URL
// Global state
let categories = []

// Initialize the app
document.addEventListener('DOMContentLoaded', function () {
  loadCategories()
  setupEventListeners()
})

// Event Listeners
function setupEventListeners() {
  // Transaction form
  document
    .getElementById('transaction-form')
    .addEventListener('submit', handleAddTransaction)

  // CSV form
  document
    .getElementById('csv-form')
    .addEventListener('submit', handleCSVImport)
}

// Tab Management
function showTab(tabName) {
  // Hide all tabs
  document.querySelectorAll('.tab-content').forEach((tab) => {
    tab.classList.remove('active')
  })

  // Remove active class from all buttons
  document.querySelectorAll('.tab-button').forEach((btn) => {
    btn.classList.remove('active')
  })

  // Show selected tab
  document.getElementById(tabName).classList.add('active')

  // Add active class to clicked button
  event.target.classList.add('active')
}

// API Functions
async function apiCall(endpoint, options = {}) {
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    return await response.json()
  } catch (error) {
    console.error('API call failed:', error)
    showStatus('API call failed: ' + error.message, 'error')
    throw error
  }
}

// Dashboard Functions
async function loadDashboard() {
  try {
    showStatus('Loading dashboard...', 'info')

    const user_id = 'test_user'
    const report = await apiCall(`/report?user_id=${user_id}&days=7`)

    document.getElementById('weekly-income').textContent =
      `$${report.income.toFixed(2)}`
    document.getElementById('weekly-expense').textContent =
      `$${Math.abs(report.expense).toFixed(2)}`
    document.getElementById('weekly-net').textContent =
      `$${(report.income + report.expense).toFixed(2)}`

    showStatus('Dashboard loaded successfully!', 'success')
  } catch (error) {
    showStatus('Failed to load dashboard', 'error')
  }
}

// Transaction Functions
async function loadTransactions() {
  try {
    showStatus('Loading transactions...', 'info')

    const user_id = document.getElementById('user-filter').value || 'test_user'
    const limit = document.getElementById('limit-filter').value || 20

    const response = await apiCall(
      `/transactions?user_id=${user_id}&limit=${limit}`
    )

    displayTransactions(response.items)
    showStatus('Transactions loaded successfully!', 'success')
  } catch (error) {
    showStatus('Failed to load transactions', 'error')
  }
}

function displayTransactions(transactions) {
  const container = document.getElementById('transactions-list')

  if (!transactions || transactions.length === 0) {
    container.innerHTML = '<p>No transactions found.</p>'
    return
  }

  container.innerHTML = transactions
    .map(
      (transaction) => `
        <div class="transaction-item">
            <div class="transaction-amount ${transaction.amount >= 0 ? 'positive' : 'negative'}">
                $${transaction.amount.toFixed(2)}
            </div>
            <div class="transaction-details">
                <div class="transaction-description">${transaction.description}</div>
                <div class="transaction-meta">
                    ${transaction.category} • ${new Date(transaction.date).toLocaleDateString()}
                    ${transaction.tags ? ` • ${transaction.tags}` : ''}
                </div>
            </div>
        </div>
    `
    )
    .join('')
}

// Add Transaction Functions
async function handleAddTransaction(event) {
  event.preventDefault()

  try {
    showStatus('Adding transaction...', 'info')

    const formData = {
      user_id: document.getElementById('user-id').value,
      amount: parseFloat(document.getElementById('amount').value),
      category: document.getElementById('category').value,
      description: document.getElementById('description').value,
      type: document.getElementById('type').value,
      tags: document.getElementById('tags').value,
    }

    const response = await apiCall('/transactions', {
      method: 'POST',
      body: JSON.stringify(formData),
    })

    showStatus('Transaction added successfully!', 'success')
    document.getElementById('transaction-form').reset()
    document.getElementById('user-id').value = 'test_user'
  } catch (error) {
    showStatus('Failed to add transaction', 'error')
  }
}

// Category Functions
async function loadCategories() {
  try {
    const response = await apiCall('/categories')
    categories = response.categories
    populateCategorySelect()
    displayCategories()
  } catch (error) {
    showStatus('Failed to load categories', 'error')
  }
}

function populateCategorySelect() {
  const select = document.getElementById('category')
  select.innerHTML = '<option value="">Select Category</option>'

  categories.forEach((category) => {
    const option = document.createElement('option')
    option.value = category.name
    option.textContent = `${category.icon} ${category.name}`
    select.appendChild(option)
  })
}

function displayCategories() {
  const container = document.getElementById('categories-list')

  if (!categories || categories.length === 0) {
    container.innerHTML = '<p>No categories found.</p>'
    return
  }

  container.innerHTML = categories
    .map(
      (category) => `
        <div class="category-item">
            <div>
                <strong>${category.icon} ${category.name}</strong>
                <div style="color: #666; font-size: 0.9rem;">${category.type}</div>
            </div>
            <div style="width: 20px; height: 20px; background: ${category.color}; border-radius: 50%;"></div>
        </div>
    `
    )
    .join('')
}

// CSV Import Functions
async function handleCSVImport() {
  console.log('CSV import function called!') // Debug line
  event.preventDefault()
  const fileInput = document.getElementById('csv-file')
  console.log('File input:', fileInput) // Debug line
  const file = fileInput.files[0]
  console.log('File:', file) // Debug line
  if (!file) {
    showStatus('Please select a CSV file', 'error')
    return
  }

  const formData = new FormData()
  formData.append('file', file)
  formData.append('user_id', 'default')

  try {
    showStatus('Processing CSV with smart classification...', 'info')

    // Use the smart endpoint
    const response = await fetch(`${API_BASE_URL}/import-csv-smart`, {
      method: 'POST',
      body: formData,
    })

    const result = await response.json()

    if (result.status === 'success') {
      showSmartImportResults(result)
    } else {
      showStatus('Error processing CSV', 'error')
    }
  } catch (error) {
    console.error('Error:', error)
    showStatus('Error uploading CSV', 'error')
  }
}

function showSmartImportResults(result) {
  const summary = result.summary
  const transactions = result.transactions

  // Create a modal to show results
  const modal = document.createElement('div')
  modal.className = 'modal'
  modal.style.cssText = `
    position: fixed !important;
    top: 0 !important;
    left: 0 !important;
    width: 100% !important;
    height: 100% !important;
    background-color: rgba(0, 0, 0, 0.5) !important;
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    z-index: 1000 !important;
  `

  modal.innerHTML = `
        <div class="modal-content" style="
          background: white !important;
          padding: 2rem !important;
          border-radius: 12px !important;
          box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3) !important;
          max-width: 600px !important;
          width: 90% !important;
          max-height: 80vh !important;
          overflow-y: auto !important;
        ">
            <h3 style="color: #2d3748 !important; margin-bottom: 1.5rem !important; font-size: 1.5rem !important; border-bottom: 2px solid #e2e8f0 !important; padding-bottom: 0.5rem !important;">Smart Classification Results</h3>
            <div class="summary" style="background: #f7fafc !important; padding: 1rem !important; border-radius: 8px !important; margin-bottom: 1.5rem !important;">
                <p style="margin: 0.5rem 0 !important; font-weight: 500 !important;"><strong>Total:</strong> ${summary.total}</p>
                <p style="margin: 0.5rem 0 !important; font-weight: 500 !important;"><strong>Auto-classified:</strong> ${summary.auto_classified || 0}</p>
                <p style="margin: 0.5rem 0 !important; font-weight: 500 !important;"><strong>Needs review:</strong> ${summary.needs_review || 0}</p>
            </div>
            <div class="transactions-preview" style="margin-bottom: 1.5rem !important;">
                <h4 style="color: #4a5568 !important; margin-bottom: 1rem !important;">Preview (first 5):</h4>
                ${transactions
                  .slice(0, 5)
                  .map(
                    (tx) => `
                    <div class="transaction-preview" style="
                      display: flex !important;
                      align-items: center !important;
                      padding: 0.75rem !important;
                      background: #f8f9fa !important;
                      border-radius: 6px !important;
                      margin-bottom: 0.5rem !important;
                      border-left: 4px solid #4299e1 !important;
                    ">
                        <span>${tx.description}</span> → 
                        <span class="category" style="
                          background: #4299e1 !important;
                          color: white !important;
                          padding: 0.25rem 0.5rem !important;
                          border-radius: 4px !important;
                          font-size: 0.875rem !important;
                          margin: 0 0.5rem !important;
                        ">${tx.category}</span>
                        <span class="confidence" style="
                          color: #38a169 !important;
                          font-weight: 600 !important;
                          font-size: 0.875rem !important;
                        ">(${tx.classification.confidence})</span>
                    </div>
                `
                  )
                  .join('')}
            </div>
            <div class="actions" style="display: flex !important; gap: 1rem !important; justify-content: flex-end !important; margin-top: 1.5rem !important;">
                <button onclick="commitTransactions(${JSON.stringify(transactions).replace(/"/g, '&quot;')})" style="
                  padding: 0.75rem 1.5rem !important;
                  border: none !important;
                  border-radius: 6px !important;
                  font-weight: 600 !important;
                  cursor: pointer !important;
                  background: #48bb78 !important;
                  color: white !important;
                ">Commit All</button>
                <button onclick="this.parentElement.parentElement.parentElement.remove()" style="
                  padding: 0.75rem 1.5rem !important;
                  border: none !important;
                  border-radius: 6px !important;
                  font-weight: 600 !important;
                  cursor: pointer !important;
                  background: #e2e8f0 !important;
                  color: #4a5568 !important;
                ">Cancel</button>
            </div>
        </div>
    `
  document.body.appendChild(modal)
}

async function commitTransactions(transactions) {
  try {
    const response = await fetch(`${API_BASE_URL}/transaction/commit-bulk`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ transactions }),
    })

    const result = await response.json()

    if (result.status === 'ok') {
      showStatus(`Successfully saved ${result.saved} transactions!`, 'success')
      loadTransactions() // Refresh the list
    } else {
      showStatus('Error saving transactions', 'error')
    }
  } catch (error) {
    showStatus('Error committing transactions', 'error')
  }

  // Close modal
  document.querySelector('.modal').remove()
}
function downloadTemplate() {
  const template = `date,amount,description,category,tags
2024-01-15,-25.50,Coffee shop,Food & Dining,coffee work
2024-01-16,1200.00,Salary,Salary,income
2024-01-17,-89.99,Groceries,Food & Dining,groceries
2024-01-18,-15.00,Subway,Transportation,commute`

  const blob = new Blob([template], { type: 'text/csv' })
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'transaction_template.csv'
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  window.URL.revokeObjectURL(url)

  showStatus('Template downloaded!', 'success')
}

// Utility Functions
function showStatus(message, type = 'info') {
  const statusEl = document.getElementById('status-message')
  statusEl.textContent = message
  statusEl.className = `status-message ${type} show`

  setTimeout(() => {
    statusEl.classList.remove('show')
  }, 3000)
}

function formatCurrency(amount) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(amount)
}
