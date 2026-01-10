import { useQuery, useSuspenseQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import type { RowSelectionState } from "@tanstack/react-table"
import { AlertCircle, CheckCircle, Receipt } from "lucide-react"
import { Suspense, useCallback, useMemo, useState } from "react"

import {
  AccountsService,
  CategoriesService,
  TransactionsService,
} from "@/client"
import { DataTable } from "@/components/Common/DataTable"
import PendingTransactions from "@/components/Pending/PendingTransactions"
import AddTransaction from "@/components/Transactions/AddTransaction"
import { BulkCategorization } from "@/components/Transactions/BulkCategorization"
import { BulkConfirmation } from "@/components/Transactions/BulkConfirmation"
import { createColumns } from "@/components/Transactions/columns"
import {
  TransactionFilters,
  type TransactionFiltersState,
} from "@/components/Transactions/TransactionFilters"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"

function getTransactionsQueryOptions(filters: TransactionFiltersState) {
  return {
    queryFn: () =>
      TransactionsService.readTransactions({
        skip: 0,
        limit: 100,
        accountId: filters.accountId,
        categoryId: filters.categoryId,
        startDate: filters.startDate,
        endDate: filters.endDate,
      }),
    queryKey: [
      "transactions",
      filters.accountId,
      filters.categoryId,
      filters.startDate,
      filters.endDate,
    ],
  }
}

function getAccountsQueryOptions() {
  return {
    queryFn: () => AccountsService.readAccounts({ skip: 0, limit: 100 }),
    queryKey: ["accounts"],
  }
}

function getCategoriesQueryOptions() {
  return {
    queryFn: () => CategoriesService.readCategories({ skip: 0, limit: 100 }),
    queryKey: ["categories"],
  }
}

export const Route = createFileRoute("/_layout/transactions")({
  component: Transactions,
  head: () => ({
    meta: [
      {
        title: "Transactions - Personal Finance Tracker",
      },
    ],
  }),
})


interface TransactionsTableContentProps {
  filters: TransactionFiltersState
  rowSelection: RowSelectionState
  onRowSelectionChange: (selection: RowSelectionState) => void
  enableSelection: boolean
}

function TransactionsTableContent({
  filters,
  rowSelection,
  onRowSelectionChange,
  enableSelection,
}: TransactionsTableContentProps) {
  const { data: transactions } = useSuspenseQuery(
    getTransactionsQueryOptions(filters),
  )
  const { data: accounts } = useSuspenseQuery(getAccountsQueryOptions())
  const { data: categories } = useSuspenseQuery(getCategoriesQueryOptions())

  // Create lookup maps for accounts and categories
  const accountsMap = useMemo(() => {
    const map = new Map<string, string>()
    accounts.data.forEach((account) => {
      map.set(account.id, account.name)
    })
    return map
  }, [accounts.data])

  const categoriesMap = useMemo(() => {
    const map = new Map<string, string>()
    categories.data.forEach((category) => {
      map.set(category.id, category.name)
    })
    return map
  }, [categories.data])

  const columns = useMemo(
    () =>
      createColumns({
        accounts: accountsMap,
        categories: categoriesMap,
        enableSelection,
      }),
    [accountsMap, categoriesMap, enableSelection],
  )

  if (transactions.data.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center text-center py-12">
        <div className="rounded-full bg-muted p-4 mb-4">
          <Receipt className="h-8 w-8 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-semibold">No transactions found</h3>
        <p className="text-muted-foreground">
          {filters.accountId ||
          filters.categoryId !== null ||
          filters.startDate ||
          filters.endDate ||
          filters.status
            ? "Try adjusting your filters or add a new transaction"
            : "Add your first transaction to get started"}
        </p>
      </div>
    )
  }

  return (
    <DataTable
      columns={columns}
      data={transactions.data}
      columnVisibility={{ id: false, select: enableSelection }}
      rowSelection={rowSelection}
      onRowSelectionChange={onRowSelectionChange}
      getRowId={(row) => row.id}
    />
  )
}

interface TransactionsTableProps {
  filters: TransactionFiltersState
  rowSelection: RowSelectionState
  onRowSelectionChange: (selection: RowSelectionState) => void
  enableSelection: boolean
}

function TransactionsTable({
  filters,
  rowSelection,
  onRowSelectionChange,
  enableSelection,
}: TransactionsTableProps) {
  return (
    <Suspense fallback={<PendingTransactions />}>
      <TransactionsTableContent
        filters={filters}
        rowSelection={rowSelection}
        onRowSelectionChange={onRowSelectionChange}
        enableSelection={enableSelection}
      />
    </Suspense>
  )
}


interface QuickFilterButtonProps {
  label: string
  count: number
  icon: React.ReactNode
  isActive: boolean
  onClick: () => void
  variant?: "warning" | "info"
}

function QuickFilterButton({
  label,
  count,
  icon,
  isActive,
  onClick,
  variant = "info",
}: QuickFilterButtonProps) {
  const variantClasses = {
    warning: isActive
      ? "bg-yellow-100 text-yellow-800 border-yellow-300 dark:bg-yellow-900 dark:text-yellow-200 dark:border-yellow-700"
      : "hover:bg-yellow-50 dark:hover:bg-yellow-950",
    info: isActive
      ? "bg-blue-100 text-blue-800 border-blue-300 dark:bg-blue-900 dark:text-blue-200 dark:border-blue-700"
      : "hover:bg-blue-50 dark:hover:bg-blue-950",
  }

  return (
    <Button
      variant="outline"
      size="sm"
      className={`gap-2 ${variantClasses[variant]}`}
      onClick={onClick}
    >
      {icon}
      {label}
      <Badge variant="secondary" className="ml-1">
        {count}
      </Badge>
    </Button>
  )
}

function Transactions() {
  const [filters, setFilters] = useState<TransactionFiltersState>({
    accountId: null,
    categoryId: null,
    startDate: null,
    endDate: null,
    status: null,
  })
  const [rowSelection, setRowSelection] = useState<RowSelectionState>({})
  const [enableSelection, setEnableSelection] = useState(false)

  const { data: accounts } = useQuery(getAccountsQueryOptions())
  const { data: categories } = useQuery(getCategoriesQueryOptions())
  const { data: allTransactions } = useQuery({
    queryKey: ["transactions", "all"],
    queryFn: () =>
      TransactionsService.readTransactions({ skip: 0, limit: 1000 }),
  })

  // Calculate counts for quick filters
  const uncategorizedCount = useMemo(() => {
    return (
      allTransactions?.data.filter((t) => t.category_id === null).length || 0
    )
  }, [allTransactions])

  const pendingConfirmationCount = useMemo(() => {
    return (
      allTransactions?.data.filter((t) => t.status === "auto").length || 0
    )
  }, [allTransactions])

  const selectedTransactionIds = useMemo(() => {
    return Object.keys(rowSelection).filter((id) => rowSelection[id])
  }, [rowSelection])

  // Get selected transactions that are auto-categorized (for bulk confirm)
  const selectedAutoTransactionIds = useMemo(() => {
    if (!allTransactions) return []
    return selectedTransactionIds.filter((id) => {
      const transaction = allTransactions.data.find((t) => t.id === id)
      return transaction?.status === "auto"
    })
  }, [selectedTransactionIds, allTransactions])

  const handleClearSelection = useCallback(() => {
    setRowSelection({})
  }, [])

  const handleQuickFilterUncategorized = () => {
    setFilters({
      accountId: null,
      categoryId: "uncategorized",
      startDate: null,
      endDate: null,
      status: null,
    })
  }

  const handleQuickFilterPendingConfirmation = () => {
    setFilters({
      accountId: null,
      categoryId: null,
      startDate: null,
      endDate: null,
      status: "auto",
    })
  }

  const isUncategorizedFilterActive = filters.categoryId === "uncategorized"
  const isPendingConfirmationFilterActive = filters.status === "auto"

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Transactions</h1>
          <p className="text-muted-foreground">
            Manage your financial transactions
          </p>
        </div>
        <AddTransaction />
      </div>

      {/* Quick filters for uncategorized and pending confirmation */}
      <div className="flex flex-wrap items-center gap-3">
        <span className="text-sm text-muted-foreground">Quick filters:</span>
        <QuickFilterButton
          label="Uncategorized"
          count={uncategorizedCount}
          icon={<AlertCircle className="h-4 w-4" />}
          isActive={isUncategorizedFilterActive}
          onClick={handleQuickFilterUncategorized}
          variant="warning"
        />
        <QuickFilterButton
          label="Pending Confirmation"
          count={pendingConfirmationCount}
          icon={<CheckCircle className="h-4 w-4" />}
          isActive={isPendingConfirmationFilterActive}
          onClick={handleQuickFilterPendingConfirmation}
          variant="info"
        />
        <div className="ml-auto flex items-center gap-2">
          <Button
            variant={enableSelection ? "secondary" : "outline"}
            size="sm"
            onClick={() => {
              setEnableSelection(!enableSelection)
              if (enableSelection) {
                setRowSelection({})
              }
            }}
          >
            {enableSelection ? "Cancel Selection" : "Select Multiple"}
          </Button>
        </div>
      </div>

      {/* Bulk actions bar */}
      {enableSelection && selectedTransactionIds.length > 0 && (
        <div className="flex items-center gap-3 p-3 bg-muted/50 rounded-lg border">
          <span className="text-sm font-medium">
            {selectedTransactionIds.length} selected
          </span>
          <div className="flex items-center gap-2">
            <BulkCategorization
              selectedTransactionIds={selectedTransactionIds}
              onClearSelection={handleClearSelection}
            />
            {selectedAutoTransactionIds.length > 0 && (
              <BulkConfirmation
                selectedTransactionIds={selectedAutoTransactionIds}
                onClearSelection={handleClearSelection}
              />
            )}
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleClearSelection}
            className="ml-auto"
          >
            Clear selection
          </Button>
        </div>
      )}

      <TransactionFilters
        filters={filters}
        onFiltersChange={setFilters}
        accounts={accounts?.data || []}
        categories={categories?.data || []}
      />

      <TransactionsTable
        filters={filters}
        rowSelection={rowSelection}
        onRowSelectionChange={setRowSelection}
        enableSelection={enableSelection}
      />
    </div>
  )
}
