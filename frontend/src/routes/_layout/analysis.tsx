import { useQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { BarChart3 } from "lucide-react"
import { useState } from "react"

import { AccountsService, AnalysisService } from "@/client"
import {
  AccountSummary,
  type DateRange,
  DateRangePicker,
  SpendingByCategory,
  SpendingTrends,
} from "@/components/Analysis"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { getDateRangeLastMonths } from "@/lib/finance"

export const Route = createFileRoute("/_layout/analysis")({
  component: Analysis,
  head: () => ({
    meta: [
      {
        title: "Analysis - Personal Finance Tracker",
      },
    ],
  }),
})

function Analysis() {
  // Initialize with last 3 months
  const initialRange = getDateRangeLastMonths(3)
  const [dateRange, setDateRange] = useState<DateRange>({
    startDate: initialRange.startDate,
    endDate: initialRange.endDate,
  })
  const [selectedAccountId, setSelectedAccountId] = useState<string | null>(
    null,
  )

  // Fetch accounts for the filter dropdown
  const { data: accounts } = useQuery({
    queryKey: ["accounts"],
    queryFn: () => AccountsService.readAccounts({ skip: 0, limit: 100 }),
  })

  // Fetch spending by category
  const { data: spendingByCategory, isLoading: isLoadingCategory } = useQuery({
    queryKey: [
      "analysis",
      "spending-by-category",
      dateRange.startDate,
      dateRange.endDate,
      selectedAccountId,
    ],
    queryFn: () =>
      AnalysisService.getSpendingByCategory({
        dateFrom: dateRange.startDate,
        dateTo: dateRange.endDate,
        accountId: selectedAccountId,
      }),
  })

  // Fetch spending trends
  const { data: spendingTrends, isLoading: isLoadingTrends } = useQuery({
    queryKey: [
      "analysis",
      "spending-trends",
      dateRange.startDate,
      dateRange.endDate,
      selectedAccountId,
    ],
    queryFn: () =>
      AnalysisService.getSpendingTrends({
        dateFrom: dateRange.startDate,
        dateTo: dateRange.endDate,
        accountId: selectedAccountId,
      }),
  })

  // Fetch account summary (no account filter for this one)
  const { data: accountSummary, isLoading: isLoadingSummary } = useQuery({
    queryKey: [
      "analysis",
      "account-summary",
      dateRange.startDate,
      dateRange.endDate,
    ],
    queryFn: () =>
      AnalysisService.getAccountSummary({
        dateFrom: dateRange.startDate,
        dateTo: dateRange.endDate,
      }),
  })

  const handleAccountChange = (value: string) => {
    setSelectedAccountId(value === "all" ? null : value)
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            Financial Analysis
          </h1>
          <p className="text-muted-foreground">
            Analyze your spending patterns and trends
          </p>
        </div>
        <BarChart3 className="h-8 w-8 text-muted-foreground" />
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-end gap-4 p-4 rounded-lg border bg-card">
        <DateRangePicker
          dateRange={dateRange}
          onDateRangeChange={setDateRange}
        />

        <div className="flex items-center gap-2">
          <span className="text-sm font-medium">Account:</span>
          <Select
            value={selectedAccountId || "all"}
            onValueChange={handleAccountChange}
          >
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="All accounts" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All accounts</SelectItem>
              {accounts?.data.map((account) => (
                <SelectItem key={account.id} value={account.id}>
                  {account.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Analysis Components */}
      <div className="grid gap-6">
        {/* Account Summary - Full width */}
        <AccountSummary
          accounts={accountSummary?.accounts || []}
          consolidatedExpenseCents={
            accountSummary?.consolidated_expense_cents || 0
          }
          consolidatedIncomeCents={
            accountSummary?.consolidated_income_cents || 0
          }
          consolidatedNetCents={accountSummary?.consolidated_net_cents || 0}
          totalTransactionCount={accountSummary?.total_transaction_count || 0}
          isLoading={isLoadingSummary}
        />

        {/* Spending by Category and Trends - Side by side on large screens */}
        <div className="grid gap-6 xl:grid-cols-2">
          <SpendingByCategory
            data={spendingByCategory?.data || []}
            totalSpendingCents={spendingByCategory?.total_spending_cents || 0}
            isLoading={isLoadingCategory}
          />

          <SpendingTrends
            data={spendingTrends?.data || []}
            totalSpendingCents={spendingTrends?.total_spending_cents || 0}
            isLoading={isLoadingTrends}
          />
        </div>
      </div>
    </div>
  )
}
