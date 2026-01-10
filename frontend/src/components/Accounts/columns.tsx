import type { ColumnDef } from "@tanstack/react-table"
import { Check, Copy, CreditCard, Landmark, PiggyBank, TrendingUp, HelpCircle } from "lucide-react"

import type { AccountPublic, AccountType } from "@/client"
import { Button } from "@/components/ui/button"
import { useCopyToClipboard } from "@/hooks/useCopyToClipboard"
import { cn } from "@/lib/utils"
import { AccountActionsMenu } from "./AccountActionsMenu"

function CopyId({ id }: { id: string }) {
  const [copiedText, copy] = useCopyToClipboard()
  const isCopied = copiedText === id

  return (
    <div className="flex items-center gap-1.5 group">
      <span className="font-mono text-xs text-muted-foreground">{id}</span>
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

const accountTypeConfig: Record<AccountType, { label: string; icon: React.ComponentType<{ className?: string }> }> = {
  credit_card: { label: "Credit Card", icon: CreditCard },
  chequing: { label: "Chequing", icon: Landmark },
  savings: { label: "Savings", icon: PiggyBank },
  investment: { label: "Investment", icon: TrendingUp },
  other: { label: "Other", icon: HelpCircle },
}

function AccountTypeCell({ type }: { type: AccountType }) {
  const config = accountTypeConfig[type]
  const Icon = config.icon

  return (
    <div className="flex items-center gap-2">
      <Icon className="size-4 text-muted-foreground" />
      <span>{config.label}</span>
    </div>
  )
}

export const columns: ColumnDef<AccountPublic>[] = [
  {
    accessorKey: "id",
    header: "ID",
    cell: ({ row }) => <CopyId id={row.original.id} />,
  },
  {
    accessorKey: "name",
    header: "Name",
    cell: ({ row }) => (
      <span className="font-medium">{row.original.name}</span>
    ),
  },
  {
    accessorKey: "type",
    header: "Type",
    cell: ({ row }) => <AccountTypeCell type={row.original.type} />,
  },
  {
    accessorKey: "institution",
    header: "Institution",
    cell: ({ row }) => {
      const institution = row.original.institution
      return (
        <span
          className={cn(
            "text-muted-foreground",
            !institution && "italic",
          )}
        >
          {institution || "Not specified"}
        </span>
      )
    },
  },
  {
    accessorKey: "description",
    header: "Description",
    cell: ({ row }) => {
      const description = row.original.description
      return (
        <span
          className={cn(
            "max-w-xs truncate block text-muted-foreground",
            !description && "italic",
          )}
        >
          {description || "No description"}
        </span>
      )
    },
  },
  {
    id: "actions",
    header: () => <span className="sr-only">Actions</span>,
    cell: ({ row }) => (
      <div className="flex justify-end">
        <AccountActionsMenu account={row.original} />
      </div>
    ),
  },
]
