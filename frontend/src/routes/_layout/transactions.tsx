import { useQuery, useSuspenseQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { Receipt } from "lucide-react"
import { Suspense, useMemo, useState } from "react"

import {
  AccountsService,
  CategoriesService,
  TransactionsService,
} from "@/client"
import { DataTable } from "@/components/Common/DataTable"
import PendingTransactions from "@/components/Pending/PendingTransactions"
import AddTransaction from "@/components/Transactions/AddTransaction"
import { createColumns } from "@/components/Transactions/columns"
import {
  TransactionFilters,
  type TransactionFiltersState,
} from "@/components/Transactions/TransactionFilters"

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

function TransactionsTableContent({
  filters,
}: {
  filters: TransactionFiltersState
}) {
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
      }),
    [accountsMap, categoriesMap],
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
          filters.endDate
            ? "Try adjusting your filters or add a new transaction"
            : "Add your first transaction to get started"}
        </p>
      </div>
    )
  }

  return <DataTable columns={columns} data={transactions.data} />
}

function TransactionsTable({ filters }: { filters: TransactionFiltersState }) {
  return (
    <Suspense fallback={<PendingTransactions />}>
      <TransactionsTableContent filters={filters} />
    </Suspense>
  )
}

function Transactions() {
  const [filters, setFilters] = useState<TransactionFiltersState>({
    accountId: null,
    categoryId: null,
    startDate: null,
    endDate: null,
  })

  const { data: accounts } = useQuery(getAccountsQueryOptions())
  const { data: categories } = useQuery(getCategoriesQueryOptions())

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

      <TransactionFilters
        filters={filters}
        onFiltersChange={setFilters}
        accounts={accounts?.data || []}
        categories={categories?.data || []}
      />

      <TransactionsTable filters={filters} />
    </div>
  )
}
