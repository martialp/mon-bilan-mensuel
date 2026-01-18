import type { ColumnDef } from "@tanstack/react-table"
import { ArrowDownLeft, ArrowRightLeft, ArrowUpRight } from "lucide-react"

import type { TransactionPreview, TransactionType } from "@/client"
import { Badge } from "@/components/ui/badge"
import { formatCurrency, formatDate, getTransactionTypeColor } from "@/lib/finance"
import { cn } from "@/lib/utils"

const transactionTypeConfig: Record<
  TransactionType,
  { label: string; icon: React.ComponentType<{ className?: string }> }
> = {
  expense: { label: "Expense", icon: ArrowDownLeft },
  income: { label: "Income", icon: ArrowUpRight },
  transfer: { label: "Transfer", icon: ArrowRightLeft },
}

function TransactionTypeBadge({ type }: { type: TransactionType }) {
  const config = transactionTypeConfig[type]
  const Icon = config.icon
  const colorClass = getTransactionTypeColor(type)

  return (
    <Badge variant="outline" className={cn("gap-1", colorClass)}>
      <Icon className="size-3" />
      {config.label}
    </Badge>
  )
}

function AmountCell({
  amount_cents,
  type,
}: {
  amount_cents: number
  type: TransactionType
}) {
  const colorClass = getTransactionTypeColor(type)
  const prefix = type === "expense" ? "-" : type === "income" ? "+" : ""

  return (
    <span className={cn("font-medium", colorClass)}>
      {prefix}
      {formatCurrency(amount_cents)}
    </span>
  )
}

export const previewColumns: ColumnDef<TransactionPreview>[] = [
  {
    accessorKey: "date_transaction",
    header: "Date",
    cell: ({ row }) => (
      <span className="text-sm whitespace-nowrap">
        {formatDate(row.original.date_transaction)}
      </span>
    ),
    size: 100,
    minSize: 100,
    maxSize: 100,
  },
  {
    accessorKey: "description",
    header: "Description",
    cell: ({ row }) => (
      <span
        className="max-w-[300px] truncate block font-medium"
        title={row.original.description}
      >
        {row.original.description}
      </span>
    ),
    size: 300,
    minSize: 200,
  },
  {
    accessorKey: "amount_cents",
    header: "Amount",
    cell: ({ row }) => (
      <AmountCell
        amount_cents={row.original.amount_cents}
        type={row.original.type}
      />
    ),
    size: 100,
    minSize: 100,
    maxSize: 100,
  },
  {
    accessorKey: "type",
    header: "Type",
    cell: ({ row }) => <TransactionTypeBadge type={row.original.type} />,
    size: 120,
    minSize: 120,
    maxSize: 120,
  },
]
