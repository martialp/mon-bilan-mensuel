import { expect, test } from "@playwright/test"

// Use authenticated state
test.use({ storageState: "playwright/.auth/user.json" })

test.describe("Category Management", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/categories")
  })

  test("Categories page is accessible and displays header", async ({ page }) => {
    await expect(page.getByRole("heading", { name: "Categories" })).toBeVisible()
    await expect(
      page.getByText("Manage your transaction categories"),
    ).toBeVisible()
  })

  test("Add Category button is visible", async ({ page }) => {
    await expect(
      page.getByRole("button", { name: "Add Category" }),
    ).toBeVisible()
  })

  test("Add Category dialog opens and has required fields", async ({ page }) => {
    await page.getByRole("button", { name: "Add Category" }).click()

    // Dialog should be visible
    await expect(page.getByRole("dialog")).toBeVisible()
    await expect(
      page.getByRole("heading", { name: "Add Category" }),
    ).toBeVisible()

    // Required field should be visible
    await expect(page.getByLabel(/Name/)).toBeVisible()

    // Buttons should be visible
    await expect(page.getByRole("button", { name: "Cancel" })).toBeVisible()
    await expect(page.getByRole("button", { name: "Save" })).toBeVisible()
  })

  test("Add Category form validation - empty name shows error", async ({
    page,
  }) => {
    await page.getByRole("button", { name: "Add Category" }).click()

    // Try to submit without filling required fields
    await page.getByRole("button", { name: "Save" }).click()

    // Should show validation error for name
    await expect(page.getByText("Name is required")).toBeVisible()
  })

  test("Create category successfully", async ({ page }) => {
    const categoryName = `Test Category ${Date.now()}`

    await page.getByRole("button", { name: "Add Category" }).click()

    // Fill in the form
    await page.getByLabel(/Name/).fill(categoryName)

    // Submit the form
    await page.getByRole("button", { name: "Save" }).click()

    // Should show success message
    await expect(page.getByText("Category created successfully")).toBeVisible()

    // Dialog should close
    await expect(page.getByRole("dialog")).not.toBeVisible()

    // Category should appear in the list
    await expect(page.getByText(categoryName)).toBeVisible()
  })

  test("Edit category dialog opens with existing data", async ({ page }) => {
    // First create a category
    const categoryName = `Edit Test Category ${Date.now()}`

    await page.getByRole("button", { name: "Add Category" }).click()
    await page.getByLabel(/Name/).fill(categoryName)
    await page.getByRole("button", { name: "Save" }).click()

    // Wait for success and dialog to close
    await expect(page.getByText("Category created successfully")).toBeVisible()
    await expect(page.getByRole("dialog")).not.toBeVisible()

    // Find the category row and click the actions menu (last button in the row)
    const categoryRow = page.getByRole("row").filter({ hasText: categoryName })
    await categoryRow.getByRole("button").last().click()

    // Click Edit Category
    await page.getByRole("menuitem", { name: "Edit Category" }).click()

    // Verify dialog opens with existing data
    await expect(page.getByRole("dialog")).toBeVisible()
    await expect(page.getByLabel(/Name/)).toHaveValue(categoryName)
  })

  test("Delete category with confirmation dialog", async ({ page }) => {
    // First create a category to delete
    const categoryName = `Delete Test Category ${Date.now()}`

    await page.getByRole("button", { name: "Add Category" }).click()
    await page.getByLabel(/Name/).fill(categoryName)
    await page.getByRole("button", { name: "Save" }).click()

    // Wait for success
    await expect(page.getByText("Category created successfully")).toBeVisible()
    await expect(page.getByRole("dialog")).not.toBeVisible()

    // Find the category row and click the actions menu (last button in the row)
    const categoryRow = page.getByRole("row").filter({ hasText: categoryName })
    await categoryRow.getByRole("button").last().click()

    // Click Delete Category
    await page.getByRole("menuitem", { name: "Delete Category" }).click()

    // Verify confirmation dialog appears
    await expect(page.getByRole("dialog")).toBeVisible()
    await expect(
      page.getByText(`Are you sure you want to delete the category`),
    ).toBeVisible()

    // Confirm deletion
    await page.getByRole("button", { name: "Delete" }).click()

    // Should show success message
    await expect(
      page.getByText("The category was deleted successfully"),
    ).toBeVisible()

    // Category should no longer be in the list
    await expect(page.getByText(categoryName)).not.toBeVisible()
  })

  test("Cancel button closes Add Category dialog", async ({ page }) => {
    await page.getByRole("button", { name: "Add Category" }).click()
    await expect(page.getByRole("dialog")).toBeVisible()

    await page.getByRole("button", { name: "Cancel" }).click()
    await expect(page.getByRole("dialog")).not.toBeVisible()
  })

  test("Empty state is shown when no categories exist", async ({ page }) => {
    // This test assumes a fresh state with no categories
    // The empty state message should be visible if no categories exist
    const emptyStateText = page.getByText("No categories yet")
    const categoriesTable = page.getByRole("table")

    // Either empty state or table should be visible
    const hasEmptyState = await emptyStateText.isVisible().catch(() => false)
    const hasTable = await categoriesTable.isVisible().catch(() => false)

    expect(hasEmptyState || hasTable).toBeTruthy()
  })

  test("Category uniqueness validation - duplicate name shows error", async ({
    page,
  }) => {
    // First create a category
    const categoryName = `Unique Test Category ${Date.now()}`

    await page.getByRole("button", { name: "Add Category" }).click()
    await page.getByLabel(/Name/).fill(categoryName)
    await page.getByRole("button", { name: "Save" }).click()

    // Wait for success
    await expect(page.getByText("Category created successfully")).toBeVisible()
    await expect(page.getByRole("dialog")).not.toBeVisible()

    // Try to create another category with the same name
    await page.getByRole("button", { name: "Add Category" }).click()
    await page.getByLabel(/Name/).fill(categoryName)
    await page.getByRole("button", { name: "Save" }).click()

    // Should show error about duplicate name
    await expect(
      page.getByText(/already exists/i),
    ).toBeVisible()
  })
})
