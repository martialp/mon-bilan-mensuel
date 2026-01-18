import { useMutation } from "@tanstack/react-query"
import { AlertTriangle, FileText } from "lucide-react"

import { type ImportPreviewPublic, ImportsService } from "@/client"
import { DataTable } from "@/components/Common/DataTable"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { LoadingButton } from "@/components/ui/loading-button"
import useCustomToast from "@/hooks/useCustomToast"
import { formatCurrency, formatDate } from "@/lib/finance"
import { ERROR_CODES, extractErrorMessage, getErrorCode } from "@/utils"
import { previewColumns } from "./columns"

interface ImportPreviewProps {
  preview: ImportPreviewPublic
  onConfirm: () => void
  onReject: () => void
}

const ImportPreview = ({
  preview,
  onConfirm,
  onReject,
}: ImportPreviewProps) => {
  const {
    showSuccessToast,
    showErrorToast,
    showInfoToast,
    showRetryToast,
    showNetworkErrorToast,
  } = useCustomToast()

  const confirmMutation = useMutation({
    mutationFn: () =>
      ImportsService.confirmImport({ importId: preview.import_id }),
    onSuccess: (result) => {
      showSuccessToast(
        `Successfully imported ${result.transactions_imported} transactions`,
      )
      onConfirm()
    },
    onError: (err) => {
      const errorCode = getErrorCode(err as Error)
      const errorMessage = extractErrorMessage(err as Error)

      // Handle network errors with retry option - keep preview open
      if (errorCode === ERROR_CODES.NETWORK_ERROR) {
        showNetworkErrorToast(() => {
          confirmMutation.mutate()
        })
        return
      }

      // Handle server errors with retry option - keep preview open
      if (errorCode === ERROR_CODES.SERVER_ERROR) {
        showRetryToast(errorMessage, () => {
          confirmMutation.mutate()
        })
        return
      }

      // Requirement 6.4: Show error message and keep preview open
      showErrorToast(errorMessage)
    },
  })

  const rejectMutation = useMutation({
    mutationFn: () =>
      ImportsService.rejectImport({ importId: preview.import_id }),
    onSuccess: () => {
      showInfoToast("Import cancelled")
      onReject()
    },
    onError: (err) => {
      const errorCode = getErrorCode(err as Error)
      const errorMessage = extractErrorMessage(err as Error)

      // Handle network errors with retry option - keep preview open
      if (errorCode === ERROR_CODES.NETWORK_ERROR) {
        showNetworkErrorToast(() => {
          rejectMutation.mutate()
        })
        return
      }

      // Handle server errors with retry option - keep preview open
      if (errorCode === ERROR_CODES.SERVER_ERROR) {
        showRetryToast(errorMessage, () => {
          rejectMutation.mutate()
        })
        return
      }

      // Show error message and keep preview open
      showErrorToast(errorMessage)
    },
  })

  const isLoading = confirmMutation.isPending || rejectMutation.isPending

  const handleConfirm = () => {
    confirmMutation.mutate()
  }

  const handleReject = () => {
    rejectMutation.mutate()
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileText className="h-5 w-5" />
          Import Preview
        </CardTitle>
        <CardDescription>
          Review the extracted transactions before confirming the import.
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* File info */}
        <div className="flex flex-wrap gap-x-6 gap-y-2 text-sm">
          <div>
            <span className="text-muted-foreground">File: </span>
            <span className="font-medium">{preview.file_name}</span>
          </div>
          {preview.statement_date && (
            <div>
              <span className="text-muted-foreground">Statement Date: </span>
              <span className="font-medium">
                {formatDate(preview.statement_date)}
              </span>
            </div>
          )}
          <div>
            <span className="text-muted-foreground">Transactions: </span>
            <span className="font-medium">{preview.transactions.length}</span>
          </div>
        </div>

        {/* Totals */}
        <div className="flex flex-wrap gap-x-6 gap-y-2 text-sm">
          {preview.statement_total_cents !== null && (
            <div>
              <span className="text-muted-foreground">Statement Total: </span>
              <span className="font-medium">
                {formatCurrency(preview.statement_total_cents)}
              </span>
            </div>
          )}
          <div>
            <span className="text-muted-foreground">Calculated Total: </span>
            <span className="font-medium">
              {formatCurrency(preview.calculated_total_cents)}
            </span>
          </div>
        </div>

        {/* Totals mismatch warning */}
        {!preview.totals_match && preview.statement_total_cents !== null && (
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertTitle>Totals Mismatch</AlertTitle>
            <AlertDescription>
              The statement total (
              {formatCurrency(preview.statement_total_cents)}) does not match
              the calculated total (
              {formatCurrency(preview.calculated_total_cents)}). Please review
              the transactions carefully.
            </AlertDescription>
          </Alert>
        )}

        {/* Warnings */}
        {preview.warnings.length > 0 &&
          preview.warnings.map((warning, index) => (
            <Alert key={index}>
              <AlertTriangle className="h-4 w-4" />
              <AlertTitle>Warning</AlertTitle>
              <AlertDescription>{warning}</AlertDescription>
            </Alert>
          ))}

        {/* Transaction table */}
        <DataTable columns={previewColumns} data={preview.transactions} />
      </CardContent>

      <CardFooter className="flex justify-end gap-2">
        <Button variant="outline" onClick={handleReject} disabled={isLoading}>
          {rejectMutation.isPending ? "Cancelling..." : "Cancel"}
        </Button>
        <LoadingButton
          onClick={handleConfirm}
          loading={confirmMutation.isPending}
          disabled={isLoading}
        >
          Confirm Import
        </LoadingButton>
      </CardFooter>
    </Card>
  )
}

export default ImportPreview
