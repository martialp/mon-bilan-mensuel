/**
 * Finance utility functions for currency formatting and date handling
 */

/**
 * Convert cents (integer) to dollars (decimal)
 * @param cents - Amount in cents (positive integer)
 * @returns Amount in dollars as a number
 */
export function centsToDollars(cents: number): number {
  return cents / 100
}

/**
 * Convert dollars (decimal) to cents (integer)
 * @param dollars - Amount in dollars
 * @returns Amount in cents as an integer (rounded)
 */
export function dollarsToCents(dollars: number): number {
  return Math.round(dollars * 100)
}

/**
 * Format cents as a currency string
 * @param cents - Amount in cents (positive integer)
 * @param locale - Locale for formatting (default: 'en-CA')
 * @param currency - Currency code (default: 'CAD')
 * @returns Formatted currency string (e.g., "$123.45")
 */
export function formatCurrency(
  cents: number,
  locale: string = "en-CA",
  currency: string = "CAD",
): string {
  const dollars = centsToDollars(cents)
  return new Intl.NumberFormat(locale, {
    style: "currency",
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(dollars)
}

/**
 * Format cents as a signed currency string based on transaction type
 * @param cents - Amount in cents (positive integer)
 * @param type - Transaction type ('expense', 'income', 'transfer')
 * @param locale - Locale for formatting (default: 'en-CA')
 * @param currency - Currency code (default: 'CAD')
 * @returns Formatted currency string with sign (e.g., "-$123.45" for expense)
 */
export function formatSignedCurrency(
  cents: number,
  type: "expense" | "income" | "transfer",
  locale: string = "en-CA",
  currency: string = "CAD",
): string {
  const dollars = centsToDollars(cents)
  const signedDollars = type === "expense" ? -dollars : dollars
  return new Intl.NumberFormat(locale, {
    style: "currency",
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
    signDisplay: "auto",
  }).format(signedDollars)
}

/**
 * Parse a currency input string to cents
 * Handles various formats: "$123.45", "123.45", "123,45", etc.
 * @param input - Currency string to parse
 * @returns Amount in cents, or null if invalid
 */
export function parseCurrencyToCents(input: string): number | null {
  // Remove currency symbols, spaces, and thousands separators
  const cleaned = input.replace(/[$€£\s,]/g, "").replace(",", ".")
  const parsed = Number.parseFloat(cleaned)

  if (Number.isNaN(parsed) || parsed < 0) {
    return null
  }

  return dollarsToCents(parsed)
}

/**
 * Format a date string for display
 * @param dateString - ISO date string (YYYY-MM-DD)
 * @param locale - Locale for formatting (default: 'en-CA')
 * @returns Formatted date string (e.g., "Jan 15, 2024")
 */
export function formatDate(
  dateString: string,
  locale: string = "en-CA",
): string {
  const date = new Date(`${dateString}T00:00:00`)
  return new Intl.DateTimeFormat(locale, {
    year: "numeric",
    month: "short",
    day: "numeric",
  }).format(date)
}

/**
 * Format a date string for display with full month name
 * @param dateString - ISO date string (YYYY-MM-DD)
 * @param locale - Locale for formatting (default: 'en-CA')
 * @returns Formatted date string (e.g., "January 15, 2024")
 */
export function formatDateLong(
  dateString: string,
  locale: string = "en-CA",
): string {
  const date = new Date(`${dateString}T00:00:00`)
  return new Intl.DateTimeFormat(locale, {
    year: "numeric",
    month: "long",
    day: "numeric",
  }).format(date)
}

/**
 * Format a datetime string for display
 * @param dateTimeString - ISO datetime string
 * @param locale - Locale for formatting (default: 'en-CA')
 * @returns Formatted datetime string (e.g., "Jan 15, 2024, 2:30 PM")
 */
export function formatDateTime(
  dateTimeString: string,
  locale: string = "en-CA",
): string {
  const date = new Date(dateTimeString)
  return new Intl.DateTimeFormat(locale, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(date)
}

/**
 * Get the current date as an ISO date string (YYYY-MM-DD)
 * @returns Current date string
 */
export function getCurrentDateString(): string {
  return new Date().toISOString().split("T")[0]
}

/**
 * Get the first day of the current month as an ISO date string
 * @returns First day of month string (YYYY-MM-DD)
 */
export function getFirstDayOfMonth(): string {
  const now = new Date()
  return new Date(now.getFullYear(), now.getMonth(), 1)
    .toISOString()
    .split("T")[0]
}

/**
 * Get the last day of the current month as an ISO date string
 * @returns Last day of month string (YYYY-MM-DD)
 */
export function getLastDayOfMonth(): string {
  const now = new Date()
  return new Date(now.getFullYear(), now.getMonth() + 1, 0)
    .toISOString()
    .split("T")[0]
}

/**
 * Get a date range for the last N months
 * @param months - Number of months to go back
 * @returns Object with startDate and endDate strings
 */
export function getDateRangeLastMonths(months: number): {
  startDate: string
  endDate: string
} {
  const now = new Date()
  const endDate = now.toISOString().split("T")[0]
  const startDate = new Date(now.getFullYear(), now.getMonth() - months + 1, 1)
    .toISOString()
    .split("T")[0]
  return { startDate, endDate }
}

/**
 * Calculate percentage of a value relative to a total
 * @param value - The value to calculate percentage for
 * @param total - The total value
 * @param decimals - Number of decimal places (default: 1)
 * @returns Percentage value, or 0 if total is 0
 */
export function calculatePercentage(
  value: number,
  total: number,
  decimals: number = 1,
): number {
  if (total === 0) return 0
  const percentage = (value / total) * 100
  return Number(percentage.toFixed(decimals))
}

/**
 * Format a percentage for display
 * @param percentage - Percentage value
 * @param decimals - Number of decimal places (default: 1)
 * @returns Formatted percentage string (e.g., "25.5%")
 */
export function formatPercentage(
  percentage: number,
  decimals: number = 1,
): string {
  return `${percentage.toFixed(decimals)}%`
}

/**
 * Get human-readable label for account type
 * @param type - Account type enum value
 * @returns Human-readable label
 */
export function getAccountTypeLabel(
  type: "credit_card" | "chequing" | "savings" | "investment" | "other",
): string {
  const labels: Record<string, string> = {
    credit_card: "Credit Card",
    chequing: "Chequing",
    savings: "Savings",
    investment: "Investment",
    other: "Other",
  }
  return labels[type] || type
}

/**
 * Get human-readable label for transaction type
 * @param type - Transaction type enum value
 * @returns Human-readable label
 */
export function getTransactionTypeLabel(
  type: "expense" | "income" | "transfer",
): string {
  const labels: Record<string, string> = {
    expense: "Expense",
    income: "Income",
    transfer: "Transfer",
  }
  return labels[type] || type
}

/**
 * Get human-readable label for transaction status
 * @param status - Transaction status enum value
 * @returns Human-readable label
 */
export function getTransactionStatusLabel(
  status: "auto" | "confirmed" | "manual",
): string {
  const labels: Record<string, string> = {
    auto: "Auto-categorized",
    confirmed: "Confirmed",
    manual: "Manual",
  }
  return labels[status] || status
}

/**
 * Get CSS color class for transaction type
 * @param type - Transaction type enum value
 * @returns Tailwind CSS color class
 */
export function getTransactionTypeColor(
  type: "expense" | "income" | "transfer",
): string {
  const colors: Record<string, string> = {
    expense: "text-red-600 dark:text-red-400",
    income: "text-green-600 dark:text-green-400",
    transfer: "text-blue-600 dark:text-blue-400",
  }
  return colors[type] || ""
}

/**
 * Get CSS color class for transaction status badge
 * @param status - Transaction status enum value
 * @returns Tailwind CSS classes for badge styling
 */
export function getTransactionStatusBadgeClass(
  status: "auto" | "confirmed" | "manual",
): string {
  const classes: Record<string, string> = {
    auto: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200",
    confirmed:
      "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
    manual: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200",
  }
  return classes[status] || ""
}
