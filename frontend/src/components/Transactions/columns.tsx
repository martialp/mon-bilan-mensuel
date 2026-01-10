import type { ColumnDef } from "@tanstack/react-table"
import {
  ArrowDownLeft,
  ArrowRightLeft,
  ArrowUpRight,
  Check,
  Copy,
} from "lucide-react"

import type {
  TransactionPublic,
  TransactionStatus,
  TransactionType,
} from "@/client"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { useCopyToClipboard } from "@/hooks/useCopyToClipboard"
import {
  formatCurrency,
  formatDate,
  getTransactionStatusBadgeClass,
  getTransactionStatusLabel,
  getTransactionTypeColor,
} from "@/lib/finance"
import { cn } from "@/lib/utils"
import { TransactionActionsMenu } from "./TransactionActionsMenu"

function CopyId({ id }: { id: string }) {
  const [copiedText, copy] = useCopyToClipboard()
  const isCopied = copiedText === id

  return (
    <div className="flex items-center gap-1.5 group">
      <span className="font-mono text-xs text-muted-foreground">
        {id.slice(0, 8)}...
      </span>
      <Button
        variant="ghost"
        size="icon"
        className="size-6 opacity-0 group-hover:opacity-100 transition-opacity"
        onClick={() => copy(id)}
      >
        {isCopied ? (
          <Check className="size-3 text-green-500" />
        ) : (
          <Copy className="size-3" />
        )}
        <span className="sr-only">Copy ID</span>
      </Button>
    </div>
  )
}

const transactionTypeConfig: Record<
  TransactionType,
  { label: string; icon: React.ComponentType<{ className?: string }> }
> = {
  expense: { label: "Expense", icon: ArrowDownLeft },
  income: { label: "Income", icon: ArrowUpRight },
  transfer: { label: "Transfer", icon: ArrowRightLeft },
}

function TransactionTypeCell({ type }: { type: TransactionType }) {
  const config = transactionTypeConfig[type]
  const Icon = config.icon
  const colorClass = getTransactionTypeColor(type)

  return (
    <div className={cn("flex items-center gap-2", colorClass)}>
      <Icon className="size-4" />
      <span>{config.label}</span>
    </div>
  )
}

function TransactionStatusBadge({ status }: { status: TransactionStatus }) {
  const badgeClass = getTransactionStatusBadgeClass(status)
  const label = getTransactionStatusLabel(status)

  return (
    <Badge variant="outline" className={cn("text-xs", badgeClass)}>
      {label}
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

export interface TransactionColumnContext {
  accounts: Map<string, string>
  categories: Map<string, string>
}

export const createColumns = (
  context: TransactionColumnContext,
): ColumnDef<TransactionPublic>[] => [
  {
    accessorKey: "id",
    header: "ID",
    cell: ({ row }) => <CopyId id={row.original.id} />,
  },
  {
    accessorKey: "date_transaction",
    header: "Date",
    cell: ({ row }) => (
      <span className="text-sm">
        {formatDate(row.original.date_transaction)}
      </span>
    ),
  },
  {
    accessorKey: "description",
    header: "Description",
    cell: ({ row }) => (
      <span
        className="max-w-[200px] truncate block font-medium"
        title={row.original.description}
      >
        {row.original.description}
      </span>
    ),
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
  },
  {
    accessorKey: "type",
    header: "Type",
    cell: ({ row }) => <TransactionTypeCell type={row.original.type} />,
  },
  {
    accessorKey: "account_id",
    header: "Account",
    cell: ({ row }) => {
      const accountName = context.accounts.get(row.original.account_id)
      return (
        <span className="text-sm text-muted-foreground">
          {accountName || "Unknown"}
        </span>
      )
    },
  },
  {
    accessorKey: "category_id",
    header: "Category",
    cell: ({ row }) => {
      const categoryId = row.original.category_id
      if (!categoryId) {
        return (
          <span className="text-sm text-muted-foreground italic">
            Uncategorized
          </span>
        )
      }
      const categoryName = context.categories.get(categoryId)
      return <span className="text-sm">{categoryName || "Unknown"}</span>
    },
  },
  {
    accessorKey: "status",
    header: "Status",
    cell: ({ row }) => <TransactionStatusBadge status={row.original.status} />,
  },
  {
    id: "actions",
    header: () => <span className="sr-only">Actions</span>,
    cell: ({ row }) => (
      <div className="flex justify-end">
        <TransactionActionsMenu
          transaction={row.original}
          accounts={context.accounts}
          categories={context.categories}
        />
      </div>
    ),
  },
]
