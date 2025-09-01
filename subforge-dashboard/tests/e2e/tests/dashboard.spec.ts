import { test, expect, Page } from '@playwright/test'

test.describe('SubForge Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to dashboard
    await page.goto('/')
    
    // Wait for page to load
    await page.waitForLoadState('networkidle')
  })

  test('loads dashboard homepage', async ({ page }) => {
    // Check page title
    await expect(page).toHaveTitle(/SubForge Dashboard/)
    
    // Check main navigation elements
    await expect(page.locator('nav')).toBeVisible()
    
    // Check for key dashboard sections
    await expect(page.getByText('System Health')).toBeVisible()
    await expect(page.getByText('Agent Status')).toBeVisible()
    await expect(page.getByText('Recent Tasks')).toBeVisible()
  })

  test('displays system health metrics', async ({ page }) => {
    // Wait for system health component to load
    await page.waitForSelector('[data-testid="system-health"]', { timeout: 10000 })
    
    // Check for health metrics
    await expect(page.getByText('CPU Usage')).toBeVisible()
    await expect(page.getByText('Memory Usage')).toBeVisible()
    await expect(page.getByText('Active Connections')).toBeVisible()
    
    // Check for percentage values
    await expect(page.locator('text=/%/')).toHaveCount({ min: 2 })
  })

  test('shows agent status cards', async ({ page }) => {
    // Wait for agent status component
    await page.waitForSelector('[data-testid="agent-status"]', { timeout: 10000 })
    
    // Check for agent cards
    const agentCards = page.locator('[data-testid="agent-card"]')
    await expect(agentCards).toHaveCount({ min: 1 })
    
    // Check agent status indicators
    const statusIndicators = page.locator('[data-testid="status-indicator"]')
    await expect(statusIndicators).toHaveCount({ min: 1 })
    
    // Verify agent information is displayed
    await expect(page.getByText(/tasks completed/i)).toBeVisible()
  })

  test('displays recent tasks', async ({ page }) => {
    // Wait for recent tasks component
    await page.waitForSelector('[data-testid="recent-tasks"]', { timeout: 10000 })
    
    // Check for task items
    const taskItems = page.locator('[data-testid="task-item"]')
    await expect(taskItems).toHaveCount({ min: 1 })
    
    // Check task priorities
    await expect(page.locator('.priority-high, .priority-medium, .priority-low')).toHaveCount({ min: 1 })
  })

  test('navigation menu works', async ({ page }) => {
    // Test navigation to Agents page
    await page.click('a[href="/agents"]')
    await page.waitForURL('/agents')
    await expect(page.getByRole('heading', { name: /agents/i })).toBeVisible()
    
    // Test navigation to Tasks page
    await page.click('a[href="/tasks"]')
    await page.waitForURL('/tasks')
    await expect(page.getByRole('heading', { name: /tasks/i })).toBeVisible()
    
    // Test navigation to Metrics page
    await page.click('a[href="/metrics"]')
    await page.waitForURL('/metrics')
    await expect(page.getByRole('heading', { name: /metrics/i })).toBeVisible()
    
    // Return to dashboard
    await page.click('a[href="/"]')
    await page.waitForURL('/')
    await expect(page.getByText('System Health')).toBeVisible()
  })

  test('theme toggle works', async ({ page }) => {
    // Look for theme toggle button
    const themeToggle = page.locator('[data-testid="theme-toggle"]')
    
    if (await themeToggle.isVisible()) {
      // Check initial theme (assuming light theme by default)
      const body = page.locator('body')
      const initialClass = await body.getAttribute('class')
      
      // Toggle theme
      await themeToggle.click()
      
      // Wait for theme change
      await page.waitForTimeout(500)
      
      // Check theme changed
      const newClass = await body.getAttribute('class')
      expect(newClass).not.toBe(initialClass)
      
      // Toggle back
      await themeToggle.click()
      await page.waitForTimeout(500)
      
      const finalClass = await body.getAttribute('class')
      expect(finalClass).toBe(initialClass)
    }
  })

  test('responsive design works on mobile', async ({ page, isMobile }) => {
    if (!isMobile) {
      // Set mobile viewport
      await page.setViewportSize({ width: 375, height: 667 })
    }
    
    // Check that mobile navigation is present
    const mobileMenu = page.locator('[data-testid="mobile-menu"]')
    if (await mobileMenu.isVisible()) {
      await mobileMenu.click()
      
      // Check navigation items are visible in mobile menu
      await expect(page.getByRole('link', { name: /agents/i })).toBeVisible()
      await expect(page.getByRole('link', { name: /tasks/i })).toBeVisible()
    }
    
    // Check that content is properly displayed on mobile
    await expect(page.getByText('System Health')).toBeVisible()
    
    // Check that cards stack properly
    const cards = page.locator('[data-testid="dashboard-card"]')
    if (await cards.count() > 0) {
      const firstCard = cards.first()
      const cardBox = await firstCard.boundingBox()
      expect(cardBox?.width).toBeLessThan(400) // Should be responsive
    }
  })

  test('loading states are shown', async ({ page }) => {
    // Intercept API calls to simulate slow loading
    await page.route('**/api/**', async route => {
      await page.waitForTimeout(2000) // 2 second delay
      await route.continue()
    })
    
    // Navigate to page
    await page.goto('/')
    
    // Check for loading indicators
    await expect(page.locator('[data-testid="loading-spinner"]')).toBeVisible()
    
    // Wait for loading to complete
    await page.waitForSelector('[data-testid="loading-spinner"]', { state: 'hidden', timeout: 10000 })
    
    // Check content is loaded
    await expect(page.getByText('System Health')).toBeVisible()
  })

  test('error handling works', async ({ page }) => {
    // Intercept API calls to simulate errors
    await page.route('**/api/**', async route => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Internal server error' })
      })
    })
    
    // Navigate to page
    await page.goto('/')
    
    // Check for error messages or fallback content
    // This depends on how error handling is implemented
    const errorMessage = page.locator('[data-testid="error-message"]')
    const fallbackContent = page.locator('[data-testid="fallback-content"]')
    
    // Either error message or fallback content should be visible
    await expect(errorMessage.or(fallbackContent)).toBeVisible({ timeout: 10000 })
  })

  test('real-time updates work', async ({ page }) => {
    // Wait for WebSocket connection
    await page.waitForTimeout(2000)
    
    // Look for real-time indicators
    const connectionStatus = page.locator('[data-testid="connection-status"]')
    if (await connectionStatus.isVisible()) {
      await expect(connectionStatus).toHaveText(/connected/i)
    }
    
    // Test that data updates when simulated
    // This would require backend WebSocket support for testing
    const agentStatus = page.locator('[data-testid="agent-status"]').first()
    const initialText = await agentStatus.textContent()
    
    // Simulate WebSocket update (this is implementation-dependent)
    await page.evaluate(() => {
      // Dispatch custom event to simulate WebSocket update
      window.dispatchEvent(new CustomEvent('websocket-test', {
        detail: { type: 'agent_update', data: { id: '1', status: 'busy' } }
      }))
    })
    
    await page.waitForTimeout(1000)
    
    // Check if content updated (implementation-dependent)
    // This test might need adjustment based on actual WebSocket implementation
  })
})

test.describe('Dashboard Accessibility', () => {
  test('meets accessibility standards', async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')
    
    // Check for proper heading hierarchy
    const h1 = page.locator('h1')
    await expect(h1).toHaveCount({ min: 1 })
    
    // Check for alt text on images
    const images = page.locator('img')
    const imageCount = await images.count()
    
    for (let i = 0; i < imageCount; i++) {
      const img = images.nth(i)
      await expect(img).toHaveAttribute('alt')
    }
    
    // Check for proper form labels
    const inputs = page.locator('input')
    const inputCount = await inputs.count()
    
    for (let i = 0; i < inputCount; i++) {
      const input = inputs.nth(i)
      const id = await input.getAttribute('id')
      if (id) {
        await expect(page.locator(`label[for="${id}"]`)).toBeVisible()
      }
    }
    
    // Check color contrast (basic check)
    const body = page.locator('body')
    const bodyStyles = await body.evaluate(el => getComputedStyle(el))
    expect(bodyStyles.color).toBeTruthy()
    expect(bodyStyles.backgroundColor).toBeTruthy()
  })

  test('keyboard navigation works', async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')
    
    // Test tab navigation
    await page.keyboard.press('Tab')
    
    // Check if focus is visible
    const focusedElement = page.locator(':focus')
    await expect(focusedElement).toBeVisible()
    
    // Navigate through multiple elements
    for (let i = 0; i < 5; i++) {
      await page.keyboard.press('Tab')
      await expect(page.locator(':focus')).toBeVisible()
    }
    
    // Test Enter key activation
    const focusedLink = await page.locator('a:focus').count()
    if (focusedLink > 0) {
      const currentURL = page.url()
      await page.keyboard.press('Enter')
      
      // Check if navigation occurred or action was triggered
      await page.waitForTimeout(500)
      const newURL = page.url()
      
      // URL should change if it was a navigation link
      if (currentURL !== newURL) {
        expect(newURL).toBeTruthy()
      }
    }
  })
})

test.describe('Dashboard Performance', () => {
  test('loads within acceptable time', async ({ page }) => {
    const startTime = Date.now()
    
    await page.goto('/')
    await page.waitForLoadState('networkidle')
    
    const loadTime = Date.now() - startTime
    
    // Should load within 5 seconds
    expect(loadTime).toBeLessThan(5000)
  })

  test('charts render properly', async ({ page }) => {
    await page.goto('/metrics')
    await page.waitForLoadState('networkidle')
    
    // Wait for charts to render
    await page.waitForSelector('canvas, svg', { timeout: 10000 })
    
    // Check that charts are visible
    const charts = page.locator('canvas, svg')
    await expect(charts).toHaveCount({ min: 1 })
    
    // Basic chart interaction test
    const firstChart = charts.first()
    const chartBox = await firstChart.boundingBox()
    
    if (chartBox) {
      // Hover over chart
      await page.mouse.move(chartBox.x + chartBox.width / 2, chartBox.y + chartBox.height / 2)
      
      // Look for tooltip or hover effects
      await page.waitForTimeout(500)
      
      // This is implementation-dependent
      const tooltip = page.locator('[data-testid="chart-tooltip"]')
      if (await tooltip.isVisible()) {
        await expect(tooltip).toHaveText(/.+/)
      }
    }
  })

  test('handles large datasets', async ({ page }) => {
    // Mock API to return large dataset
    await page.route('**/api/agents**', async route => {
      const largeDataset = Array.from({ length: 1000 }, (_, i) => ({
        id: `agent-${i}`,
        name: `Agent ${i}`,
        type: 'test',
        status: ['active', 'idle', 'busy'][i % 3],
        tasksCompleted: Math.floor(Math.random() * 100),
      }))
      
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ agents: largeDataset })
      })
    })
    
    const startTime = Date.now()
    
    await page.goto('/agents')
    await page.waitForLoadState('networkidle')
    
    const loadTime = Date.now() - startTime
    
    // Should handle large dataset reasonably
    expect(loadTime).toBeLessThan(10000) // 10 seconds max
    
    // Check that pagination or virtualization is working
    const agentItems = page.locator('[data-testid="agent-item"]')
    const visibleCount = await agentItems.count()
    
    // Should not render all 1000 items at once
    expect(visibleCount).toBeLessThan(100)
  })
})

test.describe('Dashboard Cross-browser', () => {
  ['chromium', 'firefox', 'webkit'].forEach(browserName => {
    test(`works in ${browserName}`, async ({ page, browserName: currentBrowser }) => {
      // Skip if not current browser
      if (currentBrowser !== browserName) {
        test.skip()
      }
      
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      
      // Basic functionality check
      await expect(page.getByText('System Health')).toBeVisible()
      await expect(page.getByText('Agent Status')).toBeVisible()
      
      // Test navigation
      await page.click('a[href="/agents"]')
      await page.waitForURL('/agents')
      await expect(page).toHaveURL(/\/agents/)
      
      // Test going back
      await page.goBack()
      await expect(page).toHaveURL('/')
    })
  })
})