import { ArrowDownIcon, ArrowUpIcon, MinusIcon, Wallet } from "lucide-react"
import { useMemo } from "react"

import type { AccountSpending } from "@/client"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { formatCurrency, getAccountTypeLabel } from "@/lib/finance"

interface AccountSummaryProps {
  accounts: AccountSpending[]
  consolidatedExpenseCents: number
  consolidatedIncomeCents: number
  consolidatedNetCents: number
  totalTransactionCount: number
  isLoading?: boolean
}

export function AccountSummary({
  accounts,
  consolidatedExpenseCents,
  consolidatedIncomeCents,
  consolidatedNetCents,
  totalTransactionCount,
  isLoading,
}: AccountSummaryProps) {
  // Sort accounts by total expense descending
  const sortedAccounts = useMemo(() => {
    return [...accounts].sort(
      (a, b) => b.total_expense_cents - a.total_expense_cents,
    )
  }, [accounts])

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Account Summary</CardTitle>
          <CardDescription>Loading...</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-[200px] flex items-center justify-center">
            <div className="animate-pulse text-muted-foreground">
              Loading account data...
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (accounts.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Account Summary</CardTitle>
          <CardDescription>
            No account data available for the selected period
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-[200px] flex items-center justify-center text-muted-foreground">
            <div className="text-center">
              <Wallet className="h-8 w-8 mx-auto mb-2 opacity-50" />
              <p>Add accounts and transactions to see your summary</p>
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Account Summary</CardTitle>
        <CardDescription>
          {accounts.length} {accounts.length === 1 ? "account" : "accounts"} •{" "}
          {totalTransactionCount}{" "}
          {totalTransactionCount === 1 ? "transaction" : "transactions"}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {/* Consolidated Summary Cards */}
          <div className="grid gap-4 sm:grid-cols-3">
            <div className="rounded-lg border p-4 bg-red-50 dark:bg-red-950/20">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <ArrowDownIcon className="h-4 w-4 text-red-500" />
                Total Expenses
              </div>
              <div className="text-2xl font-bold text-red-600 dark:text-red-400">
                {formatCurrency(consolidatedExpenseCents)}
              </div>
            </div>
            <div className="rounded-lg border p-4 bg-green-50 dark:bg-green-950/20">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <ArrowUpIcon className="h-4 w-4 text-green-500" />
                Total Income
              </div>
              <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                {formatCurrency(consolidatedIncomeCents)}
              </div>
            </div>
            <div
              className={`rounded-lg border p-4 ${
                consolidatedNetCents >= 0
                  ? "bg-green-50 dark:bg-green-950/20"
                  : "bg-red-50 dark:bg-red-950/20"
              }`}
            >
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <MinusIcon className="h-4 w-4" />
                Net
              </div>
              <div
                className={`text-2xl font-bold ${
                  consolidatedNetCents >= 0
                    ? "text-green-600 dark:text-green-400"
                    : "text-red-600 dark:text-red-400"
                }`}
              >
                {consolidatedNetCents >= 0 ? "+" : ""}
                {formatCurrency(Math.abs(consolidatedNetCents))}
              </div>
            </div>
          </div>

          {/* Per-Account Breakdown Table */}
          <div>
            <h4 className="text-sm font-medium mb-3">Per-Account Breakdown</h4>
            <div className="overflow-auto max-h-[300px]">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Account</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead className="text-right">Expenses</TableHead>
                    <TableHead className="text-right">Income</TableHead>
                    <TableHead className="text-right">Net</TableHead>
                    <TableHead className="text-right">#</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {sortedAccounts.map((account) => (
                    <TableRow key={account.account_id}>
                      <TableCell className="font-medium">
                        {account.account_name}
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        {getAccountTypeLabel(
                          account.account_type as
                            | "credit_card"
                            | "chequing"
                            | "savings"
                            | "investment"
                            | "other",
                        )}
                      </TableCell>
                      <TableCell className="text-right text-red-600 dark:text-red-400">
                        {formatCurrency(account.total_expense_cents)}
                      </TableCell>
                      <TableCell className="text-right text-green-600 dark:text-green-400">
                        {formatCurrency(account.total_income_cents)}
                      </TableCell>
                      <TableCell
                        className={`text-right font-medium ${
                          account.net_cents >= 0
                            ? "text-green-600 dark:text-green-400"
                            : "text-red-600 dark:text-red-400"
                        }`}
                      >
                        {account.net_cents >= 0 ? "+" : ""}
                        {formatCurrency(Math.abs(account.net_cents))}
                      </TableCell>
                      <TableCell className="text-right">
                        {account.transaction_count}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
