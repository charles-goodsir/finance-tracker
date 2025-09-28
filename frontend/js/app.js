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
async function handleCSVImport(event) {
  event.preventDefault()

  try {
    showStatus('Importing CSV...', 'info')

    const fileInput = document.getElementById('csv-file')
    const user_id = document.getElementById('csv-user-id').value

    if (!fileInput.files[0]) {
      showStatus('Please select a CSV file', 'error')
      return
    }

    const formData = new FormData()
    formData.append('file', fileInput.files[0])

    const response = await fetch(
      `${API_BASE_URL}/import/csv?user_id=${user_id}`,
      {
        method: 'POST',
        body: formData,
      }
    )

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const result = await response.json()

    if (result.errors && result.errors.length > 0) {
      showStatus(
        `Import completed with ${result.errors.length} errors`,
        'error'
      )
      console.error('Import errors:', result.errors)
    } else {
      showStatus(
        `Successfully imported ${result.imported_count} transactions!`,
        'success'
      )
    }

    // Reset form
    document.getElementById('csv-form').reset()
    document.getElementById('csv-user-id').value = 'test_user'
  } catch (error) {
    showStatus('Failed to import CSV', 'error')
    console.error('CSV import error:', error)
  }
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
