import { AlertTriangle, FileText } from "lucide-react"

import type { ImportPreviewPublic } from "@/client"
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
import { formatCurrency, formatDate } from "@/lib/finance"
import { previewColumns } from "./columns"

interface ImportPreviewProps {
  preview: ImportPreviewPublic
  onConfirm: () => void
  onReject: () => void
  isConfirming: boolean
  isRejecting: boolean
}

const ImportPreview = ({
  preview,
  onConfirm,
  onReject,
  isConfirming,
  isRejecting,
}: ImportPreviewProps) => {
  const isLoading = isConfirming || isRejecting

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
              The statement total ({formatCurrency(preview.statement_total_cents)}
              ) does not match the calculated total (
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
        <Button variant="outline" onClick={onReject} disabled={isLoading}>
          {isRejecting ? "Cancelling..." : "Cancel"}
        </Button>
        <LoadingButton onClick={onConfirm} loading={isConfirming} disabled={isLoading}>
          Confirm Import
        </LoadingButton>
      </CardFooter>
    </Card>
  )
}

export default ImportPreview
