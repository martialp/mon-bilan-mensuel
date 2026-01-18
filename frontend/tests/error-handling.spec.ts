import { expect, test } from "@playwright/test"

// Use authenticated state
test.use({ storageState: "playwright/.auth/user.json" })

test.describe("Form Validation Error Display", () => {
  test.describe("Account Form Validation", () => {
    test.beforeEach(async ({ page }) => {
      await page.goto("/accounts")
    })

    test("shows error when name is empty", async ({ page }) => {
      await page.getByRole("button", { name: "Add Account" }).click()

      // Clear name field and blur to trigger validation
      const nameField = page.getByLabel(/Name/)
      await nameField.fill("")
      await nameField.blur()

      // Try to submit
      await page.getByRole("button", { name: "Save" }).click()

      // Should show validation error
      await expect(page.getByText("Name is required")).toBeVisible()
    })

    test("shows error when name is only whitespace", async ({ page }) => {
      await page.getByRole("button", { name: "Add Account" }).click()

      // Fill with whitespace only
      const nameField = page.getByLabel(/Name/)
      await nameField.fill("   ")
      await nameField.blur()

      // Try to submit
      await page.getByRole("button", { name: "Save" }).click()

      // Should show validation error
      await expect(page.getByText(/cannot be only whitespace/i)).toBeVisible()
    })

    test("shows error when account type is not selected", async ({ page }) => {
      await page.getByRole("button", { name: "Add Account" }).click()

      // Fill name but don't select type
      await page.getByLabel(/Name/).fill("Test Account")

      // Try to submit
      await page.getByRole("button", { name: "Save" }).click()

      // Should show validation error for type
      await expect(page.getByText("Account type is required")).toBeVisible()
    })
  })

  test.describe("Category Form Validation", () => {
    test.beforeEach(async ({ page }) => {
      await page.goto("/categories")
    })

    test("shows error when category name is empty", async ({ page }) => {
      await page.getByRole("button", { name: "Add Category" }).click()

      // Try to submit without filling name
      await page.getByRole("button", { name: "Save" }).click()

      // Should show validation error
      await expect(page.getByText("Name is required")).toBeVisible()
    })

    test("shows error when category name is only whitespace", async ({
      page,
    }) => {
      await page.getByRole("button", { name: "Add Category" }).click()

      // Fill with whitespace only
      const nameField = page.getByLabel(/Name/)
      await nameField.fill("   ")
      await nameField.blur()

      // Try to submit
      await page.getByRole("button", { name: "Save" }).click()

      // Should show validation error
      await expect(page.getByText(/cannot be only whitespace/i)).toBeVisible()
    })

    test("shows error when creating duplicate category", async ({ page }) => {
      // First create a category
      const categoryName = `Duplicate Test ${Date.now()}`

      await page.getByRole("button", { name: "Add Category" }).click()
      await page.getByLabel(/Name/).fill(categoryName)
      await page.getByRole("button", { name: "Save" }).click()

      // Wait for success
      await expect(
        page.getByText("Category created successfully"),
      ).toBeVisible()
      await expect(page.getByRole("dialog")).not.toBeVisible()

      // Try to create another category with the same name
      await page.getByRole("button", { name: "Add Category" }).click()
      await page.getByLabel(/Name/).fill(categoryName)
      await page.getByRole("button", { name: "Save" }).click()

      // Should show error about duplicate
      await expect(page.getByText(/already exists/i)).toBeVisible()
    })
  })

  test.describe("Transaction Form Validation", () => {
    test.beforeEach(async ({ page }) => {
      // Ensure we have an account
      await page.goto("/accounts")
      const hasAccounts = await page
        .getByRole("table")
        .isVisible()
        .catch(() => false)

      if (!hasAccounts) {
        await page.getByRole("button", { name: "Add Account" }).click()
        await page.getByLabel(/Name/).fill("Error Test Account")
        await page.getByRole("combobox").click()
        await page.getByRole("option", { name: "Chequing" }).click()
        await page.getByRole("button", { name: "Save" }).click()
        await expect(
          page.getByText("Account created successfully"),
        ).toBeVisible()
      }

      await page.goto("/transactions")
    })

    test("shows error when description is empty", async ({ page }) => {
      await page.getByRole("button", { name: "Add Transaction" }).click()

      const dialog = page.getByRole("dialog")

      // Clear description and blur
      const descField = dialog.getByRole("textbox", { name: /Description/ })
      await descField.fill("")
      await descField.blur()

      // Try to submit
      await page.getByRole("button", { name: "Save" }).click()

      // Should show validation error
      await expect(page.getByText("Description is required")).toBeVisible()
    })

    test("shows error when amount is empty", async ({ page }) => {
      await page.getByRole("button", { name: "Add Transaction" }).click()

      const dialog = page.getByRole("dialog")

      // Clear amount and blur
      const amountField = dialog.getByRole("spinbutton", { name: /Amount/ })
      await amountField.fill("")
      await amountField.blur()

      // Try to submit
      await page.getByRole("button", { name: "Save" }).click()

      // Should show validation error
      await expect(page.getByText("Amount is required")).toBeVisible()
    })

    test("shows error when amount is zero or negative", async ({ page }) => {
      await page.getByRole("button", { name: "Add Transaction" }).click()

      const dialog = page.getByRole("dialog")

      // Fill with zero
      const amountField = dialog.getByRole("spinbutton", { name: /Amount/ })
      await amountField.fill("0")
      await amountField.blur()

      // Try to submit
      await page.getByRole("button", { name: "Save" }).click()

      // Should show validation error
      await expect(page.getByText(/positive number/i)).toBeVisible()
    })

    test("shows error when transaction type is not selected", async ({
      page,
    }) => {
      await page.getByRole("button", { name: "Add Transaction" }).click()

      const dialog = page.getByRole("dialog")

      // Fill other fields but not type
      await dialog.getByRole("textbox", { name: /Description/ }).fill("Test")
      await dialog.getByRole("spinbutton", { name: /Amount/ }).fill("10.00")
      await dialog.getByRole("combobox", { name: /Account/ }).click()
      await page.getByRole("option").first().click()

      // Try to submit
      await page.getByRole("button", { name: "Save" }).click()

      // Should show validation error for type
      await expect(page.getByText("Transaction type is required")).toBeVisible()
    })

    test("shows error when account is not selected", async ({ page }) => {
      await page.getByRole("button", { name: "Add Transaction" }).click()

      const dialog = page.getByRole("dialog")

      // Fill other fields but not account
      await dialog.getByRole("combobox", { name: /Type/ }).click()
      await page.getByRole("option", { name: "Expense" }).click()
      await dialog.getByRole("textbox", { name: /Description/ }).fill("Test")
      await dialog.getByRole("spinbutton", { name: /Amount/ }).fill("10.00")

      // Try to submit
      await page.getByRole("button", { name: "Save" }).click()

      // Should show validation error for account
      await expect(page.getByText("Account is required")).toBeVisible()
    })
  })
})

test.describe("API Error Handling and User Feedback", () => {
  test.describe("Success Messages", () => {
    test.beforeEach(async ({ page }) => {
      await page.goto("/accounts")
    })

    test("shows success toast when account is created", async ({ page }) => {
      const accountName = `Success Test ${Date.now()}`

      await page.getByRole("button", { name: "Add Account" }).click()
      await page.getByLabel(/Name/).fill(accountName)
      await page.getByRole("combobox").click()
      await page.getByRole("option", { name: "Savings" }).click()
      await page.getByRole("button", { name: "Save" }).click()

      // Should show success toast
      await expect(page.getByText("Account created successfully")).toBeVisible()
    })

    test("shows success toast when account is updated", async ({ page }) => {
      // First create an account
      const accountName = `Update Test ${Date.now()}`

      await page.getByRole("button", { name: "Add Account" }).click()
      await page.getByLabel(/Name/).fill(accountName)
      await page.getByRole("combobox").click()
      await page.getByRole("option", { name: "Chequing" }).click()
      await page.getByRole("button", { name: "Save" }).click()

      await expect(page.getByText("Account created successfully")).toBeVisible()
      await expect(page.getByRole("dialog")).not.toBeVisible()

      // Wait for the table to update, then navigate to find the account
      await page.waitForTimeout(500)

      const lastPageButton = page.getByRole("button", {
        name: "Go to last page",
      })
      if (await lastPageButton.isEnabled()) {
        await lastPageButton.click()
      }

      // Edit the account (last button in the row is the actions menu)
      const accountRow = page.getByRole("row").filter({ hasText: accountName })
      await accountRow.getByRole("button").last().click()
      await page.getByRole("menuitem", { name: "Edit Account" }).click()

      // Update the name
      await page.getByLabel(/Name/).fill(`${accountName} Updated`)
      await page.getByRole("button", { name: "Save" }).click()

      // Should show success toast
      await expect(page.getByText("Account updated successfully")).toBeVisible()
    })

    test("shows success toast when account is deleted", async ({ page }) => {
      // First create an account
      const accountName = `Delete Test ${Date.now()}`

      await page.getByRole("button", { name: "Add Account" }).click()
      await page.getByLabel(/Name/).fill(accountName)
      await page.getByRole("combobox").click()
      await page.getByRole("option", { name: "Other" }).click()
      await page.getByRole("button", { name: "Save" }).click()

      await expect(page.getByText("Account created successfully")).toBeVisible()
      await expect(page.getByRole("dialog")).not.toBeVisible()

      // Wait for the table to update, then navigate to find the account
      await page.waitForTimeout(500)

      const lastPageButton = page.getByRole("button", {
        name: "Go to last page",
      })
      if (await lastPageButton.isEnabled()) {
        await lastPageButton.click()
      }

      // Delete the account (last button in the row is the actions menu)
      const accountRow = page.getByRole("row").filter({ hasText: accountName })
      await accountRow.getByRole("button").last().click()
      await page.getByRole("menuitem", { name: "Delete Account" }).click()
      await page.getByRole("button", { name: "Delete" }).click()

      // Should show success toast
      await expect(
        page.getByText("The account was deleted successfully"),
      ).toBeVisible()
    })
  })

  test.describe("Category Error Messages", () => {
    test.beforeEach(async ({ page }) => {
      await page.goto("/categories")
    })

    test("shows success toast when category is created", async ({ page }) => {
      const categoryName = `Success Category ${Date.now()}`

      await page.getByRole("button", { name: "Add Category" }).click()
      await page.getByLabel(/Name/).fill(categoryName)
      await page.getByRole("button", { name: "Save" }).click()

      // Should show success toast
      await expect(
        page.getByText("Category created successfully"),
      ).toBeVisible()
    })

    test("shows success toast when category is deleted", async ({ page }) => {
      // First create a category
      const categoryName = `Delete Category ${Date.now()}`

      await page.getByRole("button", { name: "Add Category" }).click()
      await page.getByLabel(/Name/).fill(categoryName)
      await page.getByRole("button", { name: "Save" }).click()

      await expect(
        page.getByText("Category created successfully"),
      ).toBeVisible()
      await expect(page.getByRole("dialog")).not.toBeVisible()

      // Navigate to find the category (sorted by name)
      const lastPageButton = page.getByRole("button", {
        name: "Go to last page",
      })
      if (await lastPageButton.isEnabled()) {
        await lastPageButton.click()
      }

      // Delete the category
      const categoryRow = page
        .getByRole("row")
        .filter({ hasText: categoryName })
      await categoryRow.getByRole("button").last().click()
      await page.getByRole("menuitem", { name: "Delete Category" }).click()
      await page.getByRole("button", { name: "Delete" }).click()

      // Should show success toast
      await expect(
        page.getByText("The category was deleted successfully"),
      ).toBeVisible()
    })
  })

  test.describe("Transaction Error Messages", () => {
    test.beforeEach(async ({ page }) => {
      // Ensure we have an account
      await page.goto("/accounts")
      const hasAccounts = await page
        .getByRole("table")
        .isVisible()
        .catch(() => false)

      if (!hasAccounts) {
        await page.getByRole("button", { name: "Add Account" }).click()
        await page.getByLabel(/Name/).fill("Transaction Error Test Account")
        await page.getByRole("combobox").click()
        await page.getByRole("option", { name: "Chequing" }).click()
        await page.getByRole("button", { name: "Save" }).click()
        await expect(
          page.getByText("Account created successfully"),
        ).toBeVisible()
      }

      await page.goto("/transactions")
    })

    test("shows success toast when transaction is created", async ({
      page,
    }) => {
      const description = `Success Transaction ${Date.now()}`

      await page.getByRole("button", { name: "Add Transaction" }).click()

      const dialog = page.getByRole("dialog")
      await dialog.getByRole("combobox", { name: /Type/ }).click()
      await page.getByRole("option", { name: "Expense" }).click()
      await dialog
        .getByRole("textbox", { name: /Description/ })
        .fill(description)
      await dialog.getByRole("spinbutton", { name: /Amount/ }).fill("25.00")
      await dialog.getByRole("combobox", { name: /Account/ }).click()
      await page.getByRole("option").first().click()
      await page.getByRole("button", { name: "Save" }).click()

      // Should show success toast
      await expect(
        page.getByText("Transaction created successfully"),
      ).toBeVisible()
    })

    test("shows success toast when transaction is deleted", async ({
      page,
    }) => {
      // First create a transaction
      const description = `Delete Transaction ${Date.now()}`

      await page.getByRole("button", { name: "Add Transaction" }).click()

      const dialog = page.getByRole("dialog")
      await dialog.getByRole("combobox", { name: /Type/ }).click()
      await page.getByRole("option", { name: "Expense" }).click()
      await dialog
        .getByRole("textbox", { name: /Description/ })
        .fill(description)
      await dialog.getByRole("spinbutton", { name: /Amount/ }).fill("15.00")
      await dialog.getByRole("combobox", { name: /Account/ }).click()
      await page.getByRole("option").first().click()
      await page.getByRole("button", { name: "Save" }).click()

      await expect(
        page.getByText("Transaction created successfully"),
      ).toBeVisible()
      await expect(page.getByRole("dialog")).not.toBeVisible()

      // Wait for transaction to appear
      await expect(page.getByRole("cell", { name: description })).toBeVisible()

      // Delete the transaction
      const transactionRow = page
        .getByRole("row")
        .filter({ hasText: description })
      await transactionRow.getByRole("button").last().click()
      await page.getByRole("menuitem", { name: "Delete Transaction" }).click()
      await page.getByRole("button", { name: "Delete" }).click()

      // Should show success toast
      await expect(
        page.getByText("The transaction was deleted successfully"),
      ).toBeVisible()
    })
  })
})
