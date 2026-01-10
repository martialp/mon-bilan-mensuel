import { toast } from "sonner"

export interface ToastAction {
  label: string
  onClick: () => void
}

const useCustomToast = () => {
  const showSuccessToast = (description: string) => {
    toast.success("Success!", {
      description,
    })
  }

  const showErrorToast = (description: string, action?: ToastAction) => {
    toast.error("Something went wrong!", {
      description,
      action: action
        ? {
            label: action.label,
            onClick: action.onClick,
          }
        : undefined,
    })
  }

  const showWarningToast = (description: string) => {
    toast.warning("Warning", {
      description,
    })
  }

  const showInfoToast = (description: string) => {
    toast.info("Info", {
      description,
    })
  }

  const showRetryToast = (description: string, onRetry: () => void) => {
    toast.error("Request failed", {
      description,
      action: {
        label: "Retry",
        onClick: onRetry,
      },
      duration: 10000, // Keep visible longer for retry actions
    })
  }

  const showNetworkErrorToast = (onRetry?: () => void) => {
    toast.error("Connection Error", {
      description:
        "Unable to connect to the server. Please check your internet connection.",
      action: onRetry
        ? {
            label: "Retry",
            onClick: onRetry,
          }
        : undefined,
      duration: 10000,
    })
  }

  return {
    showSuccessToast,
    showErrorToast,
    showWarningToast,
    showInfoToast,
    showRetryToast,
    showNetworkErrorToast,
  }
}

export default useCustomToast
