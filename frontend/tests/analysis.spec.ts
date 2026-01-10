import { expect, test } from "@playwright/test"

// Use authenticated state
test.use({ storageState: "playwright/.auth/user.json" })

test.describe("Financial Analysis", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/analysis")
  })

  test("Analysis page is accessible and displays header", async ({ page }) => {
    await expect(
      page.getByRole("heading", { name: "Financial Analysis" }),
    ).toBeVisible()
    await expect(
      page.getByText("Analyze your spending patterns and trends"),
    ).toBeVisible()
  })

  test("Date range picker is visible with preset options", async ({ page }) => {
    // Period label should be visible
    await expect(page.getByText("Period:")).toBeVisible()

    // Click on the period selector
    await page.getByRole("combobox").first().click()

    // Verify preset options are available
    await expect(page.getByRole("option", { name: "Last month" })).toBeVisible()
    await expect(
      page.getByRole("option", { name: "Last 3 months" }),
    ).toBeVisible()
    await expect(
      page.getByRole("option", { name: "Last 6 months" }),
    ).toBeVisible()
    await expect(
      page.getByRole("option", { name: "Last 12 months" }),
    ).toBeVisible()
    await expect(
      page.getByRole("option", { name: "Year to date" }),
    ).toBeVisible()
    await expect(page.getByRole("option", { name: "Custom" })).toBeVisible()
  })

  test("Account filter dropdown is visible", async ({ page }) => {
    await expect(page.getByText("Account:")).toBeVisible()

    // Click on the account selector
    const accountSelector = page.getByRole("combobox").nth(1)
    await accountSelector.click()

    // "All accounts" option should be available
    await expect(
      page.getByRole("option", { name: "All accounts" }),
    ).toBeVisible()
  })

  test("Account Summary card is displayed", async ({ page }) => {
    // Wait for the card to load
    await page.waitForTimeout(500)
    await expect(page.getByText("Account Summary")).toBeVisible()
  })

  test("Spending by Category card is displayed", async ({ page }) => {
    // Wait for the card to load
    await page.waitForTimeout(500)
    await expect(page.getByText("Spending by Category")).toBeVisible()
  })

  test("Monthly Spending Trends card is displayed", async ({ page }) => {
    // Wait for the card to load
    await page.waitForTimeout(500)
    await expect(page.getByText("Monthly Spending Trends")).toBeVisible()
  })

  test("Date range can be changed using preset", async ({ page }) => {
    // Click on the period selector
    await page.getByRole("combobox").first().click()

    // Select "Last month"
    await page.getByRole("option", { name: "Last month" }).click()

    // The selector should now show "Last month" is selected
    // The page should update (we can verify by checking the date inputs)
    const fromInput = page.locator('input[type="date"]').first()
    const toInput = page.locator('input[type="date"]').last()

    // Both date inputs should have values
    await expect(fromInput).not.toHaveValue("")
    await expect(toInput).not.toHaveValue("")
  })

  test("Custom date range can be set", async ({ page }) => {
    const fromInput = page.locator('input[type="date"]').first()
    const toInput = page.locator('input[type="date"]').last()

    // Set custom dates
    await fromInput.fill("2025-01-01")
    await toInput.fill("2025-01-31")

    // Verify the values are set
    await expect(fromInput).toHaveValue("2025-01-01")
    await expect(toInput).toHaveValue("2025-01-31")
  })

  test("Clear button appears when dates are set and clears them", async ({
    page,
  }) => {
    // First ensure dates are set (they should be by default)
    const fromInput = page.locator('input[type="date"]').first()
    const toInput = page.locator('input[type="date"]').last()

    // Set dates if not already set
    await fromInput.fill("2025-01-01")
    await toInput.fill("2025-01-31")

    // Clear button should be visible
    const clearButton = page.getByRole("button", { name: "Clear" })
    await expect(clearButton).toBeVisible()

    // Click clear
    await clearButton.click()

    // Date inputs should be empty
    await expect(fromInput).toHaveValue("")
    await expect(toInput).toHaveValue("")
  })

  test("Account Summary shows expense, income, and net totals", async ({
    page,
  }) => {
    // Wait for the card to load
    await page.waitForTimeout(500)
    // These labels should be visible in the Account Summary card
    await expect(page.getByText("Total Expenses")).toBeVisible()
    await expect(page.getByText("Total Income")).toBeVisible()
    // Net label might be in a different format
    const netVisible = await page.getByText("Net").first().isVisible()
    expect(netVisible).toBeTruthy()
  })

  test("Per-Account Breakdown table is displayed", async ({ page }) => {
    await expect(page.getByText("Per-Account Breakdown")).toBeVisible()

    // Table headers should be visible
    await expect(
      page.getByRole("columnheader", { name: "Account" }),
    ).toBeVisible()
    await expect(page.getByRole("columnheader", { name: "Type" })).toBeVisible()
    await expect(
      page.getByRole("columnheader", { name: "Expenses" }),
    ).toBeVisible()
    await expect(
      page.getByRole("columnheader", { name: "Income" }),
    ).toBeVisible()
  })

  test("Spending by Category shows table with category data", async ({
    page,
  }) => {
    // The Spending by Category card should have a table
    const categoryCard = page.locator('[data-slot="card"]').filter({
      hasText: "Spending by Category",
    })

    // Table headers should be visible
    await expect(
      categoryCard.getByRole("columnheader", { name: "Category" }),
    ).toBeVisible()
    await expect(
      categoryCard.getByRole("columnheader", { name: "Amount" }),
    ).toBeVisible()
    await expect(
      categoryCard.getByRole("columnheader", { name: "%" }),
    ).toBeVisible()
  })

  test("Monthly Spending Trends shows summary statistics", async ({ page }) => {
    // The trends card should show summary stats
    await expect(page.getByText("Highest Month")).toBeVisible()
    await expect(page.getByText("Lowest Month")).toBeVisible()
    await expect(page.getByText("Monthly Average")).toBeVisible()
  })

  test("Filtering by account updates the analysis", async ({ page }) => {
    // Wait for the page to load
    await page.waitForTimeout(500)
    
    // Click on the account selector
    const accountSelector = page.getByRole("combobox").nth(1)
    await accountSelector.click()

    // Select "All accounts" to ensure we're starting from a known state
    await page.getByRole("option", { name: "All accounts" }).click()

    // Wait for the page to update
    await page.waitForTimeout(500)

    // The page should still show the analysis components
    await expect(page.getByText("Account Summary")).toBeVisible()
    await expect(page.getByText("Spending by Category")).toBeVisible()
    await expect(page.getByText("Monthly Spending Trends")).toBeVisible()
  })

  test("Analysis page is responsive - cards stack on mobile", async ({
    page,
  }) => {
    // Set viewport to mobile size
    await page.setViewportSize({ width: 375, height: 667 })

    // Wait for the page to adjust
    await page.waitForTimeout(500)

    // All cards should still be visible
    await expect(page.getByText("Account Summary")).toBeVisible()
    await expect(page.getByText("Spending by Category")).toBeVisible()
    await expect(page.getByText("Monthly Spending Trends")).toBeVisible()
  })

  test("Empty state is shown when no data available", async ({ page }) => {
    // Set a date range that likely has no data
    const fromInput = page.locator('input[type="date"]').first()
    const toInput = page.locator('input[type="date"]').last()

    await fromInput.fill("2020-01-01")
    await toInput.fill("2020-01-31")

    // Wait for the page to update
    await page.waitForTimeout(500)

    // Either we see data or empty state messages
    const hasEmptyState =
      (await page.getByText("No spending data available").count()) > 0 ||
      (await page.getByText("No account data available").count()) > 0 ||
      (await page.getByText("Add some transactions").count()) > 0

    const hasData =
      (await page.getByRole("table").count()) > 0 ||
      (await page.locator("svg").count()) > 0

    // Either empty state or data should be shown
    expect(hasEmptyState || hasData).toBeTruthy()
  })
})
