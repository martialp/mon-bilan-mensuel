import { createFileRoute } from "@tanstack/react-router"
import { Upload } from "lucide-react"

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
      </div>
      <div className="flex flex-col items-center justify-center text-center py-12">
        <div className="rounded-full bg-muted p-4 mb-4">
          <Upload className="h-8 w-8 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-semibold">Import PDF statements</h3>
        <p className="text-muted-foreground">
          Upload your bank statements to import transactions
        </p>
      </div>
    </div>
  )
}
