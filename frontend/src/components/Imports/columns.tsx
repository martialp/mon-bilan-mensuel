import type { ColumnDef } from "@tanstack/react-table"
import { ArrowDownLeft, ArrowRightLeft, ArrowUpRight } from "lucide-react"

import type {
  ImportSessionPublic,
  ImportStatus,
  TransactionPreview,
  TransactionType,
} from "@/client"
import { Badge } from "@/components/ui/badge"
import { formatCurrency, formatDate, formatDateTime, getTransactionTypeColor } from "@/lib/finance"
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


// Status badge configuration for import sessions
const importStatusConfig: Record<
  ImportStatus,
  { label: string; variant: "default" | "secondary" | "destructive" | "outline" }
> = {
  pending: { label: "Pending", variant: "default" },
  completed: { label: "Completed", variant: "outline" },
  rejected: { label: "Rejected", variant: "secondary" },
  failed: { label: "Failed", variant: "destructive" },
}

function ImportStatusBadge({ status }: { status: ImportStatus }) {
  const config = importStatusConfig[status]

  return (
    <Badge
      variant={config.variant}
      className={cn(
        status === "completed" && "border-green-500 text-green-600 dark:text-green-400"
      )}
    >
      {config.label}
    </Badge>
  )
}

export interface HistoryColumnContext {
  accounts: Map<string, string>
}

export const createHistoryColumns = (
  context: HistoryColumnContext
): ColumnDef<ImportSessionPublic>[] => [
  {
    accessorKey: "file_name",
    header: "File Name",
    cell: ({ row }) => (
      <span
        className="max-w-[200px] truncate block font-medium"
        title={row.original.file_name}
      >
        {row.original.file_name}
      </span>
    ),
    size: 200,
    minSize: 150,
  },
  {
    accessorKey: "account_id",
    header: "Account",
    cell: ({ row }) => {
      const accountName = context.accounts.get(row.original.account_id)
      return (
        <span className="text-sm text-muted-foreground truncate block max-w-[150px]">
          {accountName || "Unknown"}
        </span>
      )
    },
    size: 150,
    minSize: 120,
    maxSize: 150,
  },
  {
    accessorKey: "status",
    header: "Status",
    cell: ({ row }) => (
      <ImportStatusBadge status={row.original.status ?? "pending"} />
    ),
    size: 100,
    minSize: 100,
    maxSize: 100,
  },
  {
    accessorKey: "transaction_count",
    header: "Transactions",
    cell: ({ row }) => (
      <span className="text-sm tabular-nums">
        {row.original.transaction_count ?? 0}
      </span>
    ),
    size: 100,
    minSize: 80,
    maxSize: 100,
  },
  {
    accessorKey: "created_at",
    header: "Date",
    cell: ({ row }) => (
      <span className="text-sm text-muted-foreground whitespace-nowrap">
        {formatDateTime(row.original.created_at)}
      </span>
    ),
    size: 160,
    minSize: 140,
    maxSize: 180,
  },
]
