import { useMemo } from "react"
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"

import type { MonthlySpending } from "@/client"
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
import { centsToDollars, formatCurrency } from "@/lib/finance"

interface SpendingTrendsProps {
  data: MonthlySpending[]
  totalSpendingCents: number
  isLoading?: boolean
}

const MONTH_NAMES = [
  "Jan",
  "Feb",
  "Mar",
  "Apr",
  "May",
  "Jun",
  "Jul",
  "Aug",
  "Sep",
  "Oct",
  "Nov",
  "Dec",
]

const MONTH_NAMES_FULL = [
  "January",
  "February",
  "March",
  "April",
  "May",
  "June",
  "July",
  "August",
  "September",
  "October",
  "November",
  "December",
]

export function SpendingTrends({
  data,
  totalSpendingCents,
  isLoading,
}: SpendingTrendsProps) {
  const chartData = useMemo(() => {
    return data.map((item) => ({
      name: `${MONTH_NAMES[item.month - 1]} ${item.year}`,
      fullName: `${MONTH_NAMES_FULL[item.month - 1]} ${item.year}`,
      amount: centsToDollars(item.total_cents),
      amountCents: item.total_cents,
      transactionCount: item.transaction_count,
      year: item.year,
      month: item.month,
    }))
  }, [data])

  // Calculate average monthly spending
  const averageMonthly = useMemo(() => {
    if (data.length === 0) return 0
    return Math.round(totalSpendingCents / data.length)
  }, [data, totalSpendingCents])

  // Find highest and lowest months
  const { highestMonth, lowestMonth } = useMemo(() => {
    if (data.length === 0) return { highestMonth: null, lowestMonth: null }

    const sorted = [...data].sort((a, b) => b.total_cents - a.total_cents)
    return {
      highestMonth: sorted[0],
      lowestMonth: sorted[sorted.length - 1],
    }
  }, [data])

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Monthly Spending Trends</CardTitle>
          <CardDescription>Loading...</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-[300px] flex items-center justify-center">
            <div className="animate-pulse text-muted-foreground">
              Loading chart data...
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Monthly Spending Trends</CardTitle>
          <CardDescription>
            No spending data available for the selected period
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-[200px] flex items-center justify-center text-muted-foreground">
            Add some transactions to see your spending trends
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Monthly Spending Trends</CardTitle>
        <CardDescription>
          Total: {formatCurrency(totalSpendingCents)} over {data.length}{" "}
          {data.length === 1 ? "month" : "months"} • Average:{" "}
          {formatCurrency(averageMonthly)}/month
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {/* Bar Chart */}
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                <XAxis
                  dataKey="name"
                  tick={{ fontSize: 12 }}
                  tickLine={false}
                  axisLine={false}
                />
                <YAxis
                  tick={{ fontSize: 12 }}
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={(value) => `$${value}`}
                />
                <Tooltip
                  formatter={(value) => [
                    formatCurrency((value as number) * 100),
                    "Spending",
                  ]}
                  labelFormatter={(label) => {
                    const item = chartData.find((d) => d.name === label)
                    return item?.fullName || label
                  }}
                  contentStyle={{
                    backgroundColor: "hsl(var(--card))",
                    border: "1px solid hsl(var(--border))",
                    borderRadius: "var(--radius)",
                  }}
                />
                <Bar
                  dataKey="amount"
                  fill="hsl(var(--primary))"
                  radius={[4, 4, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Summary Stats */}
          <div className="grid gap-4 sm:grid-cols-3">
            <div className="rounded-lg border p-3">
              <div className="text-sm text-muted-foreground">Highest Month</div>
              <div className="text-lg font-semibold">
                {highestMonth
                  ? formatCurrency(highestMonth.total_cents)
                  : "N/A"}
              </div>
              <div className="text-xs text-muted-foreground">
                {highestMonth
                  ? `${MONTH_NAMES_FULL[highestMonth.month - 1]} ${highestMonth.year}`
                  : ""}
              </div>
            </div>
            <div className="rounded-lg border p-3">
              <div className="text-sm text-muted-foreground">Lowest Month</div>
              <div className="text-lg font-semibold">
                {lowestMonth ? formatCurrency(lowestMonth.total_cents) : "N/A"}
              </div>
              <div className="text-xs text-muted-foreground">
                {lowestMonth
                  ? `${MONTH_NAMES_FULL[lowestMonth.month - 1]} ${lowestMonth.year}`
                  : ""}
              </div>
            </div>
            <div className="rounded-lg border p-3">
              <div className="text-sm text-muted-foreground">
                Monthly Average
              </div>
              <div className="text-lg font-semibold">
                {formatCurrency(averageMonthly)}
              </div>
              <div className="text-xs text-muted-foreground">
                {data.length} {data.length === 1 ? "month" : "months"}
              </div>
            </div>
          </div>

          {/* Data Table */}
          <div className="overflow-auto max-h-[250px]">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Month</TableHead>
                  <TableHead className="text-right">Spending</TableHead>
                  <TableHead className="text-right">Transactions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {chartData.map((item) => (
                  <TableRow key={`${item.year}-${item.month}`}>
                    <TableCell className="font-medium">
                      {item.fullName}
                    </TableCell>
                    <TableCell className="text-right">
                      {formatCurrency(item.amountCents)}
                    </TableCell>
                    <TableCell className="text-right">
                      {item.transactionCount}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
