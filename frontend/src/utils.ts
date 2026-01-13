import { AxiosError } from "axios"
import type { ApiError } from "./client"

/**
 * Error codes for common API error scenarios
 */
export const ERROR_CODES = {
  NETWORK_ERROR: "NETWORK_ERROR",
  UNAUTHORIZED: "UNAUTHORIZED",
  FORBIDDEN: "FORBIDDEN",
  NOT_FOUND: "NOT_FOUND",
  CONFLICT: "CONFLICT",
  VALIDATION_ERROR: "VALIDATION_ERROR",
  SERVER_ERROR: "SERVER_ERROR",
  UNKNOWN: "UNKNOWN",
} as const

export type ErrorCode = (typeof ERROR_CODES)[keyof typeof ERROR_CODES]

/**
 * User-friendly error messages for common scenarios
 */
const ERROR_MESSAGES: Record<string, string> = {
  // Network errors
  "Network Error":
    "Unable to connect to the server. Please check your internet connection.",
  "timeout of": "The request timed out. Please try again.",

  // Authentication errors
  "Invalid credentials": "The email or password you entered is incorrect.",
  "Not authenticated": "Your session has expired. Please log in again.",
  "Could not validate credentials":
    "Your session has expired. Please log in again.",

  // Account errors
  "Account not found": "The account you're looking for doesn't exist.",
  "Cannot delete account with transactions":
    "This account has transactions. Please delete or reassign them first.",
  "Account has associated transactions":
    "This account has transactions. Please delete or reassign them first.",

  // User errors
  "user with this email already exists":
    "The user with this email already exists in the system.",

  // Category errors
  "Category not found": "The category you're looking for doesn't exist.",
  "Category already exists": "A category with this name already exists.",
  "category with name": "A category with this name already exists.",
  "Cannot delete category with transactions":
    "This category has transactions. Please reassign them first.",
  "Category has associated transactions":
    "This category has transactions. Please reassign them first.",

  // Transaction errors
  "Transaction not found": "The transaction you're looking for doesn't exist.",
  duplicate: "A transaction with these details already exists.",
  "Duplicate transaction": "A transaction with these details already exists.",
  unique_transaction: "A transaction with these details already exists.",

  // Validation errors
  "Invalid amount": "Please enter a valid amount greater than zero.",
  "Invalid date": "Please enter a valid date.",
  "Field required": "Please fill in all required fields.",

  // Generic errors
  "Internal server error":
    "Something went wrong on our end. Please try again later.",
  "Service unavailable":
    "The service is temporarily unavailable. Please try again later.",
}

/**
 * Extract a user-friendly error message from an API error
 */
export function extractErrorMessage(err: ApiError | Error): string {
  // Handle Axios network errors
  if (err instanceof AxiosError) {
    if (err.code === "ERR_NETWORK") {
      return ERROR_MESSAGES["Network Error"]
    }
    if (err.code === "ECONNABORTED") {
      return "The request timed out. Please try again."
    }
    return err.message
  }

  // Handle API errors with body
  const apiError = err as ApiError
  const errBody = apiError.body as Record<string, unknown> | undefined
  const errDetail = errBody?.detail

  // Handle array of validation errors (FastAPI format)
  if (Array.isArray(errDetail) && errDetail.length > 0) {
    const firstError = errDetail[0]
    if (typeof firstError === "object" && firstError !== null) {
      const msg = (firstError as Record<string, unknown>).msg
      if (typeof msg === "string") {
        return getUserFriendlyMessage(msg)
      }
    }
    return getUserFriendlyMessage(String(errDetail[0]))
  }

  // Handle string error detail
  if (typeof errDetail === "string") {
    return getUserFriendlyMessage(errDetail)
  }

  // Handle status-based errors
  if (apiError.status) {
    switch (apiError.status) {
      case 400:
        return "The request was invalid. Please check your input."
      case 401:
        return "Your session has expired. Please log in again."
      case 403:
        return "You don't have permission to perform this action."
      case 404:
        return "The requested resource was not found."
      case 409:
        return "This operation conflicts with existing data."
      case 422:
        return "Please check your input and try again."
      case 500:
        return "Something went wrong on our end. Please try again later."
      case 502:
      case 503:
      case 504:
        return "The service is temporarily unavailable. Please try again later."
    }
  }

  return "Something went wrong. Please try again."
}

/**
 * Get a user-friendly message for a given error string
 */
function getUserFriendlyMessage(errorString: string): string {
  // Check for known error patterns
  for (const [pattern, message] of Object.entries(ERROR_MESSAGES)) {
    if (errorString.toLowerCase().includes(pattern.toLowerCase())) {
      return message
    }
  }

  // Return the original message if no pattern matches
  return errorString
}

/**
 * Get the error code from an API error
 */
export function getErrorCode(err: ApiError | Error): ErrorCode {
  if (err instanceof AxiosError) {
    if (err.code === "ERR_NETWORK" || err.code === "ECONNABORTED") {
      return ERROR_CODES.NETWORK_ERROR
    }
  }

  const apiError = err as ApiError
  if (apiError.status) {
    switch (apiError.status) {
      case 401:
        return ERROR_CODES.UNAUTHORIZED
      case 403:
        return ERROR_CODES.FORBIDDEN
      case 404:
        return ERROR_CODES.NOT_FOUND
      case 409:
        return ERROR_CODES.CONFLICT
      case 422:
        return ERROR_CODES.VALIDATION_ERROR
      case 500:
      case 502:
      case 503:
      case 504:
        return ERROR_CODES.SERVER_ERROR
    }
  }

  return ERROR_CODES.UNKNOWN
}

/**
 * Check if an error is retryable
 */
export function isRetryableError(err: ApiError | Error): boolean {
  const code = getErrorCode(err)
  return code === ERROR_CODES.NETWORK_ERROR || code === ERROR_CODES.SERVER_ERROR
}

/**
 * Handle API errors with toast notifications
 * This function is designed to be bound to a toast function
 */
export const handleError = function (
  this: (msg: string) => void,
  err: ApiError | Error,
) {
  const errorMessage = extractErrorMessage(err)
  this(errorMessage)
}

/**
 * Create an error handler with retry support
 */
export function createErrorHandler(
  showErrorToast: (msg: string) => void,
  options?: {
    onRetry?: () => void
    maxRetries?: number
  },
) {
  let retryCount = 0
  const maxRetries = options?.maxRetries ?? 3

  return (err: ApiError | Error) => {
    const errorMessage = extractErrorMessage(err)
    const canRetry = isRetryableError(err) && retryCount < maxRetries

    if (canRetry && options?.onRetry) {
      retryCount++
      showErrorToast(
        `${errorMessage} Retrying... (${retryCount}/${maxRetries})`,
      )
      setTimeout(() => {
        options.onRetry?.()
      }, 1000 * retryCount) // Exponential backoff
    } else {
      showErrorToast(errorMessage)
      retryCount = 0 // Reset for next error
    }
  }
}

export const getInitials = (name: string): string => {
  return name
    .split(" ")
    .slice(0, 2)
    .map((word) => word[0])
    .join("")
    .toUpperCase()
}
