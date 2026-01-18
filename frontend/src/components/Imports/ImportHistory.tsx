import { useSuspenseQuery } from "@tanstack/react-query"
import { FileText } from "lucide-react"
import { useMemo } from "react"

import { AccountsService, ImportsService } from "@/client"
import { DataTable } from "@/components/Common/DataTable"
import { createHistoryColumns } from "./columns"

function getImportsQueryOptions() {
  return {
    queryFn: () => ImportsService.listImports({ skip: 0, limit: 100 }),
    queryKey: ["imports"],
  }
}

function getAccountsQueryOptions() {
  return {
    queryFn: () => AccountsService.readAccounts({ skip: 0, limit: 100 }),
    queryKey: ["accounts"],
  }
}

export function ImportHistory() {
  const { data: imports } = useSuspenseQuery(getImportsQueryOptions())
  const { data: accounts } = useSuspenseQuery(getAccountsQueryOptions())

  // Create account lookup map
  const accountsMap = useMemo(() => {
    const map = new Map<string, string>()
    for (const account of accounts.data) {
      map.set(account.id, account.name)
    }
    return map
  }, [accounts.data])

  const columns = useMemo(
    () => createHistoryColumns({ accounts: accountsMap }),
    [accountsMap]
  )

  if (imports.data.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center text-center py-12">
        <div className="rounded-full bg-muted p-4 mb-4">
          <FileText className="h-8 w-8 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-semibold">No imports yet</h3>
        <p className="text-muted-foreground">
          Upload a PDF statement to import transactions
        </p>
      </div>
    )
  }

  return <DataTable columns={columns} data={imports.data} />
}
