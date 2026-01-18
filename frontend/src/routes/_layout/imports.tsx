import { useQueryClient } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { Suspense, useState } from "react"

import type { ImportPreviewPublic } from "@/client"
import { ImportHistory } from "@/components/Imports/ImportHistory"
import ImportPreview from "@/components/Imports/ImportPreview"
import UploadDialog from "@/components/Imports/UploadDialog"
import PendingImports from "@/components/Pending/PendingImports"

export const Route = createFileRoute("/_layout/imports")({
  component: Imports,
  head: () => ({
    meta: [
      {
        title: "Import Statements - Personal Finance Tracker",
      },
    ],
  }),
})

function Imports() {
  const [previewData, setPreviewData] = useState<ImportPreviewPublic | null>(
    null,
  )
  const queryClient = useQueryClient()

  const handleUploadSuccess = (preview: ImportPreviewPublic) => {
    setPreviewData(preview)
  }

  const handleConfirm = () => {
    setPreviewData(null)
    queryClient.invalidateQueries({ queryKey: ["imports"] })
    queryClient.invalidateQueries({ queryKey: ["transactions"] })
  }

  const handleReject = () => {
    setPreviewData(null)
    queryClient.invalidateQueries({ queryKey: ["imports"] })
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            Import Statements
          </h1>
          <p className="text-muted-foreground">
            Import transactions from PDF statements
          </p>
        </div>
        <UploadDialog onUploadSuccess={handleUploadSuccess} />
      </div>

      {previewData && (
        <ImportPreview
          preview={previewData}
          onConfirm={handleConfirm}
          onReject={handleReject}
        />
      )}

      <Suspense fallback={<PendingImports />}>
        <ImportHistory />
      </Suspense>
    </div>
  )
}
