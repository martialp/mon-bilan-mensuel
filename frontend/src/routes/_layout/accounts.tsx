import { useSuspenseQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { Wallet } from "lucide-react"
import { Suspense } from "react"

import { AccountsService } from "@/client"
import AddAccount from "@/components/Accounts/AddAccount"
import { columns } from "@/components/Accounts/columns"
import { DataTable } from "@/components/Common/DataTable"
import PendingAccounts from "@/components/Pending/PendingAccounts"

function getAccountsQueryOptions() {
  return {
    queryFn: () => AccountsService.readAccounts({ skip: 0, limit: 100 }),
    queryKey: ["accounts"],
  }
}

export const Route = createFileRoute("/_layout/accounts")({
  component: Accounts,
  head: () => ({
    meta: [
      {
        title: "Accounts - Personal Finance Tracker",
      },
    ],
  }),
})

function AccountsTableContent() {
  const { data: accounts } = useSuspenseQuery(getAccountsQueryOptions())

  if (accounts.data.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center text-center py-12">
        <div className="rounded-full bg-muted p-4 mb-4">
          <Wallet className="h-8 w-8 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-semibold">No accounts yet</h3>
        <p className="text-muted-foreground">
          Add your first financial account to get started
        </p>
      </div>
    )
  }

  return <DataTable columns={columns} data={accounts.data} />
}

function AccountsTable() {
  return (
    <Suspense fallback={<PendingAccounts />}>
      <AccountsTableContent />
    </Suspense>
  )
}

function Accounts() {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Accounts</h1>
          <p className="text-muted-foreground">
            Manage your financial accounts
          </p>
        </div>
        <AddAccount />
      </div>
      <AccountsTable />
    </div>
  )
}
