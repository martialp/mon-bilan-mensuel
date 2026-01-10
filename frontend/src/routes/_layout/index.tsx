import { useQuery } from "@tanstack/react-query"
import { createFileRoute, Link } from "@tanstack/react-router"
import {
  AlertCircle,
  ArrowRight,
  BarChart3,
  CheckCircle,
  Receipt,
  Tag,
  TrendingDown,
  TrendingUp,
  Wallet,
} from "lucide-react"

import {
  AccountsService,
  AnalysisService,
  CategoriesService,
  TransactionsService,
} from "@/client"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import useAuth from "@/hooks/useAuth"
import { formatCurrency, getDateRangeLastMonths } from "@/lib/finance"

export const Route = createFileRoute("/_layout/")({
  component: Dashboard,
  head: () => ({
    meta: [
      {
        title: "Dashboard - Personal Finance Tracker",
      },
    ],
  }),
})

interface QuickStatCardProps {
  title: string
  value: string | number
  description?: string
  icon: React.ReactNode
  href: string
  isLoading?: boolean
  variant?: "default" | "warning" | "success" | "info"
}

function QuickStatCard({
  title,
  value,
  description,
  icon,
  href,
  isLoading,
  variant = "default",
}: QuickStatCardProps) {
  const variantClasses = {
    default: "",
    warning:
      "border-yellow-200 dark:border-yellow-800 bg-yellow-50/50 dark:bg-yellow-950/20",
    success:
      "border-green-200 dark:border-green-800 bg-green-50/50 dark:bg-green-950/20",
    info: "border-blue-200 dark:border-blue-800 bg-blue-50/50 dark:bg-blue-950/20",
  }

  return (
    <Link to={href}>
      <Card
        className={`hover:shadow-md transition-shadow cursor-pointer ${variantClasses[variant]}`}
      >
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">{title}</CardTitle>
          {icon}
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <Skeleton className="h-8 w-20" />
          ) : (
            <div className="text-2xl font-bold">{value}</div>
          )}
          {description && (
            <p className="text-xs text-muted-foreground mt-1">{description}</p>
          )}
        </CardContent>
      </Card>
    </Link>
  )
}

interface QuickActionCardProps {
  title: string
  description: string
  icon: React.ReactNode
  href: string
  count?: number
  isLoading?: boolean
}

function QuickActionCard({
  title,
  description,
  icon,
  href,
  count,
  isLoading,
}: QuickActionCardProps) {
  return (
    <Link to={href}>
      <Card className="hover:shadow-md transition-shadow cursor-pointer h-full">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <div className="rounded-lg bg-primary/10 p-2">{icon}</div>
            {count !== undefined && (
              <span className="text-2xl font-bold">
                {isLoading ? <Skeleton className="h-8 w-8" /> : count}
              </span>
            )}
          </div>
        </CardHeader>
        <CardContent>
          <CardTitle className="text-base mb-1">{title}</CardTitle>
          <CardDescription>{description}</CardDescription>
        </CardContent>
      </Card>
    </Link>
  )
}

function Dashboard() {
  const { user: currentUser } = useAuth()

  // Get date range for current month analysis
  const dateRange = getDateRangeLastMonths(1)

  // Fetch accounts
  const { data: accounts, isLoading: isLoadingAccounts } = useQuery({
    queryKey: ["accounts"],
    queryFn: () => AccountsService.readAccounts({ skip: 0, limit: 100 }),
  })

  // Fetch categories
  const { data: categories, isLoading: isLoadingCategories } = useQuery({
    queryKey: ["categories"],
    queryFn: () => CategoriesService.readCategories({ skip: 0, limit: 100 }),
  })

  // Fetch all transactions for counts
  const { data: transactions, isLoading: isLoadingTransactions } = useQuery({
    queryKey: ["transactions", "all"],
    queryFn: () =>
      TransactionsService.readTransactions({ skip: 0, limit: 1000 }),
  })

  // Fetch account summary for this month
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

  // Calculate counts
  const uncategorizedCount =
    transactions?.data.filter((t) => t.category_id === null).length || 0
  const pendingConfirmationCount =
    transactions?.data.filter((t) => t.status === "auto").length || 0
  const totalTransactions = transactions?.data.length || 0

  return (
    <div className="flex flex-col gap-6">
      {/* Welcome Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight truncate max-w-md">
          Hi, {currentUser?.full_name || currentUser?.email} 👋
        </h1>
        <p className="text-muted-foreground">
          Here's an overview of your finances
        </p>
      </div>

      {/* Quick Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <QuickStatCard
          title="Total Accounts"
          value={accounts?.data.length || 0}
          description="Financial accounts tracked"
          icon={<Wallet className="h-4 w-4 text-muted-foreground" />}
          href="/accounts"
          isLoading={isLoadingAccounts}
        />
        <QuickStatCard
          title="Total Transactions"
          value={totalTransactions}
          description="All time transactions"
          icon={<Receipt className="h-4 w-4 text-muted-foreground" />}
          href="/transactions"
          isLoading={isLoadingTransactions}
        />
        <QuickStatCard
          title="Uncategorized"
          value={uncategorizedCount}
          description="Transactions need categories"
          icon={<AlertCircle className="h-4 w-4 text-yellow-600" />}
          href="/transactions"
          isLoading={isLoadingTransactions}
          variant={uncategorizedCount > 0 ? "warning" : "default"}
        />
        <QuickStatCard
          title="Pending Confirmation"
          value={pendingConfirmationCount}
          description="Auto-categorized to review"
          icon={<CheckCircle className="h-4 w-4 text-blue-600" />}
          href="/transactions"
          isLoading={isLoadingTransactions}
          variant={pendingConfirmationCount > 0 ? "info" : "default"}
        />
      </div>

      {/* This Month Summary */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>This Month</CardTitle>
              <CardDescription>
                Financial summary for the current month
              </CardDescription>
            </div>
            <Link to="/analysis">
              <Button variant="outline" size="sm">
                View Analysis
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            <div className="flex items-center gap-3">
              <div className="rounded-full bg-red-100 dark:bg-red-900/30 p-2">
                <TrendingDown className="h-5 w-5 text-red-600 dark:text-red-400" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Expenses</p>
                {isLoadingSummary ? (
                  <Skeleton className="h-6 w-24" />
                ) : (
                  <p className="text-xl font-semibold text-red-600 dark:text-red-400">
                    {formatCurrency(
                      accountSummary?.consolidated_expense_cents || 0,
                    )}
                  </p>
                )}
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="rounded-full bg-green-100 dark:bg-green-900/30 p-2">
                <TrendingUp className="h-5 w-5 text-green-600 dark:text-green-400" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Income</p>
                {isLoadingSummary ? (
                  <Skeleton className="h-6 w-24" />
                ) : (
                  <p className="text-xl font-semibold text-green-600 dark:text-green-400">
                    {formatCurrency(
                      accountSummary?.consolidated_income_cents || 0,
                    )}
                  </p>
                )}
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="rounded-full bg-blue-100 dark:bg-blue-900/30 p-2">
                <BarChart3 className="h-5 w-5 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Net</p>
                {isLoadingSummary ? (
                  <Skeleton className="h-6 w-24" />
                ) : (
                  <p
                    className={`text-xl font-semibold ${
                      (accountSummary?.consolidated_net_cents || 0) >= 0
                        ? "text-green-600 dark:text-green-400"
                        : "text-red-600 dark:text-red-400"
                    }`}
                  >
                    {formatCurrency(
                      Math.abs(accountSummary?.consolidated_net_cents || 0),
                    )}
                    {(accountSummary?.consolidated_net_cents || 0) < 0 && " -"}
                  </p>
                )}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <div>
        <h2 className="text-lg font-semibold mb-4">Quick Actions</h2>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <QuickActionCard
            title="Accounts"
            description="Manage your financial accounts"
            icon={<Wallet className="h-5 w-5 text-primary" />}
            href="/accounts"
            count={accounts?.data.length}
            isLoading={isLoadingAccounts}
          />
          <QuickActionCard
            title="Transactions"
            description="View and manage transactions"
            icon={<Receipt className="h-5 w-5 text-primary" />}
            href="/transactions"
            count={totalTransactions}
            isLoading={isLoadingTransactions}
          />
          <QuickActionCard
            title="Categories"
            description="Organize your spending"
            icon={<Tag className="h-5 w-5 text-primary" />}
            href="/categories"
            count={categories?.data.length}
            isLoading={isLoadingCategories}
          />
          <QuickActionCard
            title="Analysis"
            description="View spending insights"
            icon={<BarChart3 className="h-5 w-5 text-primary" />}
            href="/analysis"
          />
        </div>
      </div>
    </div>
  )
}
