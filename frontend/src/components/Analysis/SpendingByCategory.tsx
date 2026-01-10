import { useMemo } from "react"
import {
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts"

import type { CategorySpending } from "@/client"
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
import { formatCurrency, formatPercentage } from "@/lib/finance"

interface SpendingByCategoryProps {
  data: CategorySpending[]
  totalSpendingCents: number
  isLoading?: boolean
}

// Color palette for chart segments
const COLORS = [
  "#3b82f6", // blue
  "#10b981", // emerald
  "#f59e0b", // amber
  "#ef4444", // red
  "#8b5cf6", // violet
  "#ec4899", // pink
  "#06b6d4", // cyan
  "#84cc16", // lime
  "#f97316", // orange
  "#6366f1", // indigo
]

export function SpendingByCategory({
  data,
  totalSpendingCents,
  isLoading,
}: SpendingByCategoryProps) {
  const chartData = useMemo(() => {
    return data.map((item, index) => ({
      name: item.category_name || "Uncategorized",
      value: item.total_cents,
      percentage: item.percentage,
      transactionCount: item.transaction_count,
      color: COLORS[index % COLORS.length],
    }))
  }, [data])

  // Sort by total_cents descending for the table
  const sortedData = useMemo(() => {
    return [...data].sort((a, b) => b.total_cents - a.total_cents)
  }, [data])

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Spending by Category</CardTitle>
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
          <CardTitle>Spending by Category</CardTitle>
          <CardDescription>
            No spending data available for the selected period
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-[200px] flex items-center justify-center text-muted-foreground">
            Add some transactions to see your spending breakdown
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Spending by Category</CardTitle>
        <CardDescription>
          Total: {formatCurrency(totalSpendingCents)} across {data.length}{" "}
          {data.length === 1 ? "category" : "categories"}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Pie Chart */}
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={chartData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={2}
                  dataKey="value"
                  nameKey="name"
                  label={({ name, percent }) =>
                    (percent || 0) > 0.05
                      ? `${name} (${formatPercentage((percent || 0) * 100)})`
                      : ""
                  }
                  labelLine={false}
                >
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value) => formatCurrency(value as number)}
                  labelFormatter={(name) => name}
                />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Data Table */}
          <div className="overflow-auto max-h-[300px]">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Category</TableHead>
                  <TableHead className="text-right">Amount</TableHead>
                  <TableHead className="text-right">%</TableHead>
                  <TableHead className="text-right">#</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {sortedData.map((item) => (
                  <TableRow key={item.category_id || "uncategorized"}>
                    <TableCell className="font-medium">
                      <div className="flex items-center gap-2">
                        <div
                          className="w-3 h-3 rounded-full"
                          style={{
                            backgroundColor:
                              COLORS[
                                chartData.findIndex(
                                  (d) =>
                                    d.name ===
                                    (item.category_name || "Uncategorized"),
                                ) % COLORS.length
                              ],
                          }}
                        />
                        {item.category_name || "Uncategorized"}
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      {formatCurrency(item.total_cents)}
                    </TableCell>
                    <TableCell className="text-right">
                      {formatPercentage(item.percentage)}
                    </TableCell>
                    <TableCell className="text-right">
                      {item.transaction_count}
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
