import { expect, test } from "@playwright/test"

// Use authenticated state
test.use({ storageState: "playwright/.auth/user.json" })

test.describe("Transaction Management", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/transactions")
  })

  test("Transactions page is accessible and displays header", async ({
    page,
  }) => {
    await expect(
      page.getByRole("heading", { name: "Transactions" }),
    ).toBeVisible()
    await expect(
      page.getByText("Manage your financial transactions"),
    ).toBeVisible()
  })

  test("Add Transaction button is visible", async ({ page }) => {
    await expect(
      page.getByRole("button", { name: "Add Transaction" }),
    ).toBeVisible()
  })

  test("Filters section is visible with all filter options", async ({
    page,
  }) => {
    // Filters section should be visible
    await expect(page.getByText("Filters")).toBeVisible()

    // All filter dropdowns should be visible
    await expect(page.getByLabel("Account")).toBeVisible()
    await expect(page.getByLabel("Category")).toBeVisible()
    await expect(page.getByLabel("Start Date")).toBeVisible()
    await expect(page.getByLabel("End Date")).toBeVisible()
  })

  test("Add Transaction dialog opens and has required fields", async ({
    page,
  }) => {
    await page.getByRole("button", { name: "Add Transaction" }).click()

    // Dialog should be visible
    await expect(page.getByRole("dialog")).toBeVisible()
    await expect(
      page.getByRole("heading", { name: "Add Transaction" }),
    ).toBeVisible()

    // Required fields should be visible in the dialog
    const dialog = page.getByRole("dialog")
    await expect(dialog.getByRole("textbox", { name: /Date/ })).toBeVisible()
    await expect(dialog.getByRole("combobox", { name: /Type/ })).toBeVisible()
    await expect(
      dialog.getByRole("textbox", { name: /Description/ }),
    ).toBeVisible()
    await expect(
      dialog.getByRole("spinbutton", { name: /Amount/ }),
    ).toBeVisible()
    await expect(
      dialog.getByRole("combobox", { name: /Account/ }),
    ).toBeVisible()

    // Optional fields should be visible
    await expect(
      dialog.getByRole("combobox", { name: "Category" }),
    ).toBeVisible()
    await expect(dialog.getByRole("textbox", { name: "Note" })).toBeVisible()

    // Buttons should be visible
    await expect(page.getByRole("button", { name: "Cancel" })).toBeVisible()
    await expect(page.getByRole("button", { name: "Save" })).toBeVisible()
  })

  test("Add Transaction form validation - empty description shows error", async ({
    page,
  }) => {
    await page.getByRole("button", { name: "Add Transaction" }).click()

    // Clear the description field and blur to trigger validation
    const descriptionField = page.getByRole("textbox", { name: /Description/ })
    await descriptionField.fill("")
    await descriptionField.blur()

    // Try to submit
    await page.getByRole("button", { name: "Save" }).click()

    // Should show validation error for description
    await expect(page.getByText("Description is required")).toBeVisible()
  })

  test("Add Transaction form validation - invalid amount shows error", async ({
    page,
  }) => {
    await page.getByRole("button", { name: "Add Transaction" }).click()

    // Fill amount with invalid value (the spinbutton doesn't allow negative, so test empty)
    const amountField = page.getByRole("spinbutton", { name: /Amount/ })
    await amountField.fill("")
    await amountField.blur()

    // Try to submit
    await page.getByRole("button", { name: "Save" }).click()

    // Should show validation error for amount
    await expect(page.getByText("Amount is required")).toBeVisible()
  })

  test("Add Transaction form - transaction type selection works", async ({
    page,
  }) => {
    await page.getByRole("button", { name: "Add Transaction" }).click()

    // Click on the type combobox (labeled "Type *")
    await page.getByRole("combobox", { name: /Type/ }).click()

    // Verify all transaction types are available
    await expect(page.getByRole("option", { name: "Expense" })).toBeVisible()
    await expect(page.getByRole("option", { name: "Income" })).toBeVisible()
    await expect(page.getByRole("option", { name: "Transfer" })).toBeVisible()
  })

  test("Cancel button closes Add Transaction dialog", async ({ page }) => {
    await page.getByRole("button", { name: "Add Transaction" }).click()
    await expect(page.getByRole("dialog")).toBeVisible()

    await page.getByRole("button", { name: "Cancel" }).click()
    await expect(page.getByRole("dialog")).not.toBeVisible()
  })

  test("Empty state or table is shown", async ({ page }) => {
    // Either empty state or table should be visible
    const emptyStateText = page.getByText("No transactions found")
    const transactionsTable = page.getByRole("table")

    const hasEmptyState = await emptyStateText.isVisible().catch(() => false)
    const hasTable = await transactionsTable.isVisible().catch(() => false)

    expect(hasEmptyState || hasTable).toBeTruthy()
  })

  test("Transaction status badges are displayed correctly", async ({
    page,
  }) => {
    // Check if there are any transactions with status badges
    const table = page.getByRole("table")
    const hasTable = await table.isVisible().catch(() => false)

    if (hasTable) {
      // If there are transactions, check that status badges exist
      // Status badges should show one of: Auto-categorized, Confirmed, Manual
      const statusBadges = page.locator('[class*="badge"]')
      const badgeCount = await statusBadges.count()

      // If there are badges, verify they contain valid status text
      if (badgeCount > 0) {
        const firstBadge = statusBadges.first()
        const badgeText = await firstBadge.textContent()
        expect(
          ["Auto-categorized", "Confirmed", "Manual"].some((status) =>
            badgeText?.includes(status),
          ),
        ).toBeTruthy()
      }
    }
  })

  test("Filter by account works", async ({ page }) => {
    // Click on account filter
    const accountFilter = page.getByLabel("Account")
    await accountFilter.click()

    // Should show "All accounts" option
    await expect(
      page.getByRole("option", { name: "All accounts" }),
    ).toBeVisible()
  })

  test("Filter by category works", async ({ page }) => {
    // Click on category filter
    const categoryFilter = page.getByLabel("Category")
    await categoryFilter.click()

    // Should show "All categories" and "Uncategorized" options
    await expect(
      page.getByRole("option", { name: "All categories" }),
    ).toBeVisible()
    await expect(
      page.getByRole("option", { name: "Uncategorized" }),
    ).toBeVisible()
  })

  test("Clear filters button appears when filters are active", async ({
    page,
  }) => {
    // Initially, clear filters button should not be visible
    const clearButton = page.getByRole("button", { name: /Clear filters/i })
    await expect(clearButton).not.toBeVisible()

    // Set a date filter
    await page.getByLabel("Start Date").fill("2024-01-01")

    // Clear filters button should now be visible
    await expect(clearButton).toBeVisible()

    // Click clear filters
    await clearButton.click()

    // Filter should be cleared
    await expect(page.getByLabel("Start Date")).toHaveValue("")
  })
})

test.describe("Transaction CRUD Operations", () => {
  test.beforeEach(async ({ page }) => {
    // Ensure we have an account to use for transactions
    await page.goto("/accounts")

    // Check if we need to create an account
    const addAccountButton = page.getByRole("button", { name: "Add Account" })
    const hasAccounts = await page
      .getByRole("table")
      .isVisible()
      .catch(() => false)

    if (!hasAccounts) {
      // Create a test account
      await addAccountButton.click()
      await page.getByLabel(/Name/).fill("Test Transaction Account")
      await page.getByRole("combobox").click()
      await page.getByRole("option", { name: "Chequing" }).click()
      await page.getByRole("button", { name: "Save" }).click()
      await expect(page.getByText("Account created successfully")).toBeVisible()
    }

    await page.goto("/transactions")
  })

  test("Create transaction successfully", async ({ page }) => {
    const description = `Test Transaction ${Date.now()}`

    await page.getByRole("button", { name: "Add Transaction" }).click()

    const dialog = page.getByRole("dialog")

    // Select type first
    await dialog.getByRole("combobox", { name: /Type/ }).click()
    await page.getByRole("option", { name: "Expense" }).click()

    // Fill description
    await dialog.getByRole("textbox", { name: /Description/ }).fill(description)

    // Fill amount
    await dialog.getByRole("spinbutton", { name: /Amount/ }).fill("25.50")

    // Select account
    await dialog.getByRole("combobox", { name: /Account/ }).click()
    await page.getByRole("option").first().click()

    // Submit the form
    await page.getByRole("button", { name: "Save" }).click()

    // Should show success message
    await expect(
      page.getByText("Transaction created successfully"),
    ).toBeVisible()

    // Dialog should close
    await expect(page.getByRole("dialog")).not.toBeVisible()

    // Transaction should appear in the list
    await expect(page.getByRole("cell", { name: description })).toBeVisible()
  })

  test("Edit transaction dialog opens with existing data", async ({ page }) => {
    // First create a transaction
    const description = `Edit Test Transaction ${Date.now()}`

    await page.getByRole("button", { name: "Add Transaction" }).click()

    const dialog = page.getByRole("dialog")
    await dialog.getByRole("combobox", { name: /Type/ }).click()
    await page.getByRole("option", { name: "Income" }).click()
    await dialog.getByRole("textbox", { name: /Description/ }).fill(description)
    await dialog.getByRole("spinbutton", { name: /Amount/ }).fill("100.00")
    await dialog.getByRole("combobox", { name: /Account/ }).click()
    await page.getByRole("option").first().click()
    await page.getByRole("button", { name: "Save" }).click()

    // Wait for success and dialog to close
    await expect(
      page.getByText("Transaction created successfully"),
    ).toBeVisible()
    await expect(page.getByRole("dialog")).not.toBeVisible()

    // Wait for the transaction to appear in the table
    await expect(page.getByRole("cell", { name: description })).toBeVisible()

    // Find the transaction row and click the actions menu (last button in the row)
    const transactionRow = page
      .getByRole("row")
      .filter({ hasText: description })
    await transactionRow.getByRole("button").last().click()

    // Click Edit Transaction
    await page.getByRole("menuitem", { name: "Edit Transaction" }).click()

    // Verify dialog opens with existing data
    await expect(page.getByRole("dialog")).toBeVisible()
    await expect(
      page.getByRole("dialog").getByRole("textbox", { name: /Description/ }),
    ).toHaveValue(description)
    await expect(
      page.getByRole("dialog").getByRole("spinbutton", { name: /Amount/ }),
    ).toHaveValue("100.00")
  })

  test("Delete transaction with confirmation dialog", async ({ page }) => {
    // First create a transaction to delete
    const description = `Delete Test Transaction ${Date.now()}`

    await page.getByRole("button", { name: "Add Transaction" }).click()

    const dialog = page.getByRole("dialog")
    await dialog.getByRole("combobox", { name: /Type/ }).click()
    await page.getByRole("option", { name: "Transfer" }).click()
    await dialog.getByRole("textbox", { name: /Description/ }).fill(description)
    await dialog.getByRole("spinbutton", { name: /Amount/ }).fill("50.00")
    await dialog.getByRole("combobox", { name: /Account/ }).click()
    await page.getByRole("option").first().click()
    await page.getByRole("button", { name: "Save" }).click()

    // Wait for success
    await expect(
      page.getByText("Transaction created successfully"),
    ).toBeVisible()
    await expect(page.getByRole("dialog")).not.toBeVisible()

    // Wait for the transaction to appear in the table
    await expect(page.getByRole("cell", { name: description })).toBeVisible()

    // Find the transaction row and click the actions menu (last button in the row)
    const transactionRow = page
      .getByRole("row")
      .filter({ hasText: description })
    await transactionRow.getByRole("button").last().click()

    // Click Delete Transaction
    await page.getByRole("menuitem", { name: "Delete Transaction" }).click()

    // Verify confirmation dialog appears
    await expect(page.getByRole("dialog")).toBeVisible()
    await expect(
      page.getByText("Are you sure you want to delete the transaction"),
    ).toBeVisible()

    // Confirm deletion
    await page.getByRole("button", { name: "Delete" }).click()

    // Should show success message
    await expect(
      page.getByText("The transaction was deleted successfully"),
    ).toBeVisible()

    // Transaction should no longer be in the list
    await expect(
      page.getByRole("cell", { name: description }),
    ).not.toBeVisible()
  })
})
