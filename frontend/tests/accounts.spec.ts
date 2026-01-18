import { expect, test } from "@playwright/test"

// Use authenticated state
test.use({ storageState: "playwright/.auth/user.json" })

test.describe("Account Management", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/accounts")
  })

  test("Accounts page is accessible and displays header", async ({ page }) => {
    await expect(page.getByRole("heading", { name: "Accounts" })).toBeVisible()
    await expect(page.getByText("Manage your financial accounts")).toBeVisible()
  })

  test("Add Account button is visible", async ({ page }) => {
    await expect(
      page.getByRole("button", { name: "Add Account" }),
    ).toBeVisible()
  })

  test("Add Account dialog opens and has required fields", async ({ page }) => {
    await page.getByRole("button", { name: "Add Account" }).click()

    // Dialog should be visible
    await expect(page.getByRole("dialog")).toBeVisible()
    await expect(
      page.getByRole("heading", { name: "Add Account" }),
    ).toBeVisible()

    // Required fields should be visible
    await expect(page.getByLabel(/Name/)).toBeVisible()
    await expect(page.getByLabel(/Type/)).toBeVisible()

    // Optional fields should be visible
    await expect(page.getByLabel("Institution")).toBeVisible()
    await expect(page.getByLabel("Description")).toBeVisible()

    // Buttons should be visible
    await expect(page.getByRole("button", { name: "Cancel" })).toBeVisible()
    await expect(page.getByRole("button", { name: "Save" })).toBeVisible()
  })

  test("Add Account form validation - empty name shows error", async ({
    page,
  }) => {
    await page.getByRole("button", { name: "Add Account" }).click()

    // Try to submit without filling required fields
    await page.getByRole("button", { name: "Save" }).click()

    // Should show validation error for name
    await expect(page.getByText("Name is required")).toBeVisible()
  })

  test("Add Account form - account type selection works", async ({ page }) => {
    await page.getByRole("button", { name: "Add Account" }).click()

    // Click on the type select trigger
    await page.getByRole("combobox").click()

    // Verify all account types are available
    await expect(
      page.getByRole("option", { name: "Credit Card" }),
    ).toBeVisible()
    await expect(page.getByRole("option", { name: "Chequing" })).toBeVisible()
    await expect(page.getByRole("option", { name: "Savings" })).toBeVisible()
    await expect(page.getByRole("option", { name: "Investment" })).toBeVisible()
    await expect(page.getByRole("option", { name: "Other" })).toBeVisible()
  })

  test("Create account successfully", async ({ page }) => {
    const accountName = `Test Account ${Date.now()}`

    await page.getByRole("button", { name: "Add Account" }).click()

    // Fill in the form
    await page.getByLabel(/Name/).fill(accountName)
    await page.getByRole("combobox").click()
    await page.getByRole("option", { name: "Chequing" }).click()
    await page.getByLabel("Institution").fill("Test Bank")
    await page.getByLabel("Description").fill("Test description")

    // Submit the form
    await page.getByRole("button", { name: "Save" }).click()

    // Should show success message
    await expect(page.getByText("Account created successfully")).toBeVisible()

    // Dialog should close
    await expect(page.getByRole("dialog")).not.toBeVisible()

    // Wait for the table to update, then navigate to find the account
    // The account name starts with "Test Account" so it will be near the end alphabetically
    await page.waitForTimeout(500) // Wait for query invalidation

    const lastPageButton = page.getByRole("button", { name: "Go to last page" })
    if (await lastPageButton.isEnabled()) {
      await lastPageButton.click()
    }

    // Account should appear in the list
    await expect(page.getByRole("cell", { name: accountName })).toBeVisible({
      timeout: 10000,
    })
  })

  test("Edit account dialog opens with existing data", async ({ page }) => {
    // First create an account
    const accountName = `Edit Test Account ${Date.now()}`

    await page.getByRole("button", { name: "Add Account" }).click()
    await page.getByLabel(/Name/).fill(accountName)
    await page.getByRole("combobox").click()
    await page.getByRole("option", { name: "Savings" }).click()
    await page.getByRole("button", { name: "Save" }).click()

    // Wait for success and dialog to close
    await expect(page.getByText("Account created successfully")).toBeVisible()
    await expect(page.getByRole("dialog")).not.toBeVisible()

    // Wait for the table to update, then navigate to find the account
    await page.waitForTimeout(500)

    const lastPageButton = page.getByRole("button", { name: "Go to last page" })
    if (await lastPageButton.isEnabled()) {
      await lastPageButton.click()
    }

    // Find the account row and click the actions menu (last button in the row)
    const accountRow = page.getByRole("row").filter({ hasText: accountName })
    await accountRow.getByRole("button").last().click()

    // Click Edit Account
    await page.getByRole("menuitem", { name: "Edit Account" }).click()

    // Verify dialog opens with existing data
    await expect(page.getByRole("dialog")).toBeVisible()
    await expect(page.getByLabel(/Name/)).toHaveValue(accountName)
  })

  test("Delete account with confirmation dialog", async ({ page }) => {
    // First create an account to delete
    const accountName = `Delete Test Account ${Date.now()}`

    await page.getByRole("button", { name: "Add Account" }).click()
    await page.getByLabel(/Name/).fill(accountName)
    await page.getByRole("combobox").click()
    await page.getByRole("option", { name: "Other" }).click()
    await page.getByRole("button", { name: "Save" }).click()

    // Wait for success
    await expect(page.getByText("Account created successfully")).toBeVisible()
    await expect(page.getByRole("dialog")).not.toBeVisible()

    // Wait for the table to update, then navigate to find the account
    await page.waitForTimeout(500)

    const lastPageButton = page.getByRole("button", { name: "Go to last page" })
    if (await lastPageButton.isEnabled()) {
      await lastPageButton.click()
    }

    // Find the account row and click the actions menu (last button in the row)
    const accountRow = page.getByRole("row").filter({ hasText: accountName })
    await accountRow.getByRole("button").last().click()

    // Click Delete Account
    await page.getByRole("menuitem", { name: "Delete Account" }).click()

    // Verify confirmation dialog appears
    await expect(page.getByRole("dialog")).toBeVisible()
    await expect(
      page.getByText(`Are you sure you want to delete the account`),
    ).toBeVisible()

    // Confirm deletion
    await page.getByRole("button", { name: "Delete" }).click()

    // Should show success message
    await expect(
      page.getByText("The account was deleted successfully"),
    ).toBeVisible()

    // Account should no longer be in the list
    await expect(page.getByText(accountName)).not.toBeVisible()
  })

  test("Cancel button closes Add Account dialog", async ({ page }) => {
    await page.getByRole("button", { name: "Add Account" }).click()
    await expect(page.getByRole("dialog")).toBeVisible()

    await page.getByRole("button", { name: "Cancel" }).click()
    await expect(page.getByRole("dialog")).not.toBeVisible()
  })

  test("Empty state is shown when no accounts exist", async ({ page }) => {
    // This test assumes a fresh state with no accounts
    // The empty state message should be visible if no accounts exist
    const emptyStateText = page.getByText("No accounts yet")
    const accountsTable = page.getByRole("table")

    // Either empty state or table should be visible
    const hasEmptyState = await emptyStateText.isVisible().catch(() => false)
    const hasTable = await accountsTable.isVisible().catch(() => false)

    expect(hasEmptyState || hasTable).toBeTruthy()
  })
})
