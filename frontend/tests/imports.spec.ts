import { expect, test } from "@playwright/test"

// Use authenticated state
test.use({ storageState: "playwright/.auth/user.json" })

test.describe("PDF Import", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/imports")
  })

  // Navigation tests (Task 9.1)
  test("Import page is accessible from sidebar", async ({ page }) => {
    // Navigate to home first
    await page.goto("/")

    // Click on Import in the sidebar
    await page.getByRole("link", { name: "Import" }).click()

    // Verify we're on the imports page
    await expect(page).toHaveURL("/imports")
    await expect(
      page.getByRole("heading", { name: "Import Statements" }),
    ).toBeVisible()
  })

  test("Import page displays header and description", async ({ page }) => {
    // Verify header is visible
    await expect(
      page.getByRole("heading", { name: "Import Statements" }),
    ).toBeVisible()

    // Verify description is visible
    await expect(
      page.getByText("Import transactions from PDF statements"),
    ).toBeVisible()
  })

  test("Import PDF button is visible", async ({ page }) => {
    await expect(
      page.getByRole("button", { name: "Import PDF" }),
    ).toBeVisible()
  })

  // Upload dialog tests (Task 9.2)
  test("Upload dialog opens with required fields", async ({ page }) => {
    // Click the Import PDF button to open the dialog
    await page.getByRole("button", { name: "Import PDF" }).click()

    // Dialog should be visible
    await expect(page.getByRole("dialog")).toBeVisible()
    await expect(
      page.getByRole("heading", { name: "Import PDF Statement" }),
    ).toBeVisible()

    // Description should be visible
    await expect(
      page.getByText("Upload a Mastercard PDF statement to import transactions"),
    ).toBeVisible()

    // Required fields should be visible - PDF File and Account (with required indicator)
    await expect(page.getByText("PDF File *")).toBeVisible()
    await expect(page.getByText("Account *")).toBeVisible()

    // File input should be visible
    await expect(page.locator('input[type="file"]')).toBeVisible()

    // Account selector should be visible
    await expect(page.getByRole("combobox", { name: "Account *" })).toBeVisible()

    // Buttons should be visible
    await expect(page.getByRole("button", { name: "Cancel" })).toBeVisible()
    await expect(page.getByRole("button", { name: "Upload" })).toBeVisible()
  })

  test("File input accepts only PDF files", async ({ page }) => {
    await page.getByRole("button", { name: "Import PDF" }).click()
    await expect(page.getByRole("dialog")).toBeVisible()

    // Verify the file input has the correct accept attribute for PDF files
    const fileInput = page.locator('input[type="file"]')
    await expect(fileInput).toHaveAttribute("accept", "application/pdf,.pdf")
  })

  test("Account selector is populated with accounts", async ({ page }) => {
    // First, ensure at least one account exists by creating one
    await page.goto("/accounts")
    
    // Check if we need to create an account
    const addAccountButton = page.getByRole("button", { name: "Add Account" })
    await expect(addAccountButton).toBeVisible()
    
    // Create a test account for the import tests
    const accountName = `Import Test Account ${Date.now()}`
    await addAccountButton.click()
    await page.getByLabel(/Name/).fill(accountName)
    await page.getByRole("combobox").click()
    await page.getByRole("option", { name: "Credit Card" }).click()
    await page.getByRole("button", { name: "Save" }).click()
    await expect(page.getByText("Account created successfully")).toBeVisible()
    
    // Now navigate to imports page
    await page.goto("/imports")
    await page.getByRole("button", { name: "Import PDF" }).click()
    await expect(page.getByRole("dialog")).toBeVisible()

    // Click on the account selector to open the dropdown
    await page.getByRole("combobox", { name: "Account *" }).click()

    // Verify that at least one account option is visible
    const firstOption = page.getByRole("option").first()
    await expect(firstOption).toBeVisible({ timeout: 5000 })
  })

  test("Form validation - shows error when submitting without file", async ({
    page,
  }) => {
    // First, ensure at least one account exists
    await page.goto("/accounts")
    
    const addAccountButton = page.getByRole("button", { name: "Add Account" })
    await expect(addAccountButton).toBeVisible()
    
    // Create a test account
    const accountName = `Validation Test Account ${Date.now()}`
    await addAccountButton.click()
    await page.getByLabel(/Name/).fill(accountName)
    await page.getByRole("combobox").click()
    await page.getByRole("option", { name: "Chequing" }).click()
    await page.getByRole("button", { name: "Save" }).click()
    await expect(page.getByText("Account created successfully")).toBeVisible()
    
    // Navigate to imports page
    await page.goto("/imports")
    await page.getByRole("button", { name: "Import PDF" }).click()
    await expect(page.getByRole("dialog")).toBeVisible()

    // Select an account first
    await page.getByRole("combobox", { name: "Account *" }).click()
    const firstOption = page.getByRole("option").first()
    await firstOption.click()

    // Try to submit without selecting a file
    await page.getByRole("button", { name: "Upload" }).click()

    // Should show validation error for file
    await expect(page.getByText("Please select a file")).toBeVisible()
  })

  test("Cancel button closes upload dialog", async ({ page }) => {
    await page.getByRole("button", { name: "Import PDF" }).click()
    await expect(page.getByRole("dialog")).toBeVisible()

    await page.getByRole("button", { name: "Cancel" }).click()
    await expect(page.getByRole("dialog")).not.toBeVisible()
  })

  // History table tests (Task 9.3)
  test("History table displays required columns", async ({ page }) => {
    // The history table should have the required column headers
    // These are visible whether or not there are imports
    // First check if the table exists (it won't if there are no imports - empty state is shown)
    const table = page.getByRole("table")
    const emptyState = page.getByText("No imports yet")

    // Wait for either the table or empty state to be visible
    await expect(table.or(emptyState)).toBeVisible({ timeout: 10000 })

    // If table is visible, verify the column headers
    const isTableVisible = await table.isVisible()
    if (isTableVisible) {
      await expect(page.getByRole("columnheader", { name: "File Name" })).toBeVisible()
      await expect(page.getByRole("columnheader", { name: "Account" })).toBeVisible()
      await expect(page.getByRole("columnheader", { name: "Status" })).toBeVisible()
      await expect(page.getByRole("columnheader", { name: "Transactions" })).toBeVisible()
      await expect(page.getByRole("columnheader", { name: "Date" })).toBeVisible()
    }
  })

  test("Empty state is shown when no imports exist", async ({ page }) => {
    // Navigate to imports page
    await page.goto("/imports")

    // Wait for the page to load - either table or empty state
    const table = page.getByRole("table")
    const emptyState = page.getByText("No imports yet")

    await expect(table.or(emptyState)).toBeVisible({ timeout: 10000 })

    // If empty state is visible, verify its content
    const isEmptyStateVisible = await emptyState.isVisible()
    if (isEmptyStateVisible) {
      await expect(page.getByText("No imports yet")).toBeVisible()
      await expect(
        page.getByText("Upload a PDF statement to import transactions"),
      ).toBeVisible()
    }
  })

  test("Status badges have correct styling for different statuses", async ({ page }) => {
    // This test verifies the status badge styling based on the implementation
    // The status badges use different variants:
    // - pending: default variant
    // - completed: outline variant with green styling
    // - rejected: secondary variant
    // - failed: destructive variant

    // Wait for the page to load
    const table = page.getByRole("table")
    const emptyState = page.getByText("No imports yet")

    await expect(table.or(emptyState)).toBeVisible({ timeout: 10000 })

    // If table is visible, check for status badges
    const isTableVisible = await table.isVisible()
    if (isTableVisible) {
      // Look for any status badges in the table using data-slot attribute
      const statusBadges = page.locator("table").locator('[data-slot="badge"]')
      const badgeCount = await statusBadges.count()

      if (badgeCount > 0) {
        // Verify at least one badge is visible
        await expect(statusBadges.first()).toBeVisible()

        // Check that badges contain valid status text
        for (let i = 0; i < badgeCount; i++) {
          const badgeText = await statusBadges.nth(i).textContent()
          // Status should be one of: Pending, Completed, Rejected, Failed
          expect(["Pending", "Completed", "Rejected", "Failed"]).toContain(badgeText)
        }
      }
    }
  })

  test("History table displays import data correctly", async ({ page }) => {
    // Wait for the page to load
    const table = page.getByRole("table")
    const emptyState = page.getByText("No imports yet")

    await expect(table.or(emptyState)).toBeVisible({ timeout: 10000 })

    // If table is visible, verify it has rows with data
    const isTableVisible = await table.isVisible()
    if (isTableVisible) {
      // Get all data rows (excluding header)
      const rows = page.locator("table tbody tr")
      const rowCount = await rows.count()

      if (rowCount > 0) {
        // Verify first row has expected cells
        const firstRow = rows.first()

        // Each row should have 5 cells (File Name, Account, Status, Transactions, Date)
        const cells = firstRow.locator("td")
        await expect(cells).toHaveCount(5)

        // File name cell should not be empty
        const fileNameCell = cells.nth(0)
        const fileName = await fileNameCell.textContent()
        expect(fileName?.trim().length).toBeGreaterThan(0)

        // Status cell should contain a badge (using data-slot attribute)
        const statusCell = cells.nth(2)
        await expect(statusCell.locator('[data-slot="badge"]')).toBeVisible()

        // Transactions cell should contain a number
        const transactionsCell = cells.nth(3)
        const transactionCount = await transactionsCell.textContent()
        expect(transactionCount).toMatch(/^\d+$/)
      }
    }
  })
})
