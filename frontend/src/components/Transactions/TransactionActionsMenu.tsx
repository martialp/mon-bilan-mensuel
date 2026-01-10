import { EllipsisVertical } from "lucide-react"
import { useState } from "react"

import type { TransactionPublic } from "@/client"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import DeleteTransaction from "./DeleteTransaction"
import EditTransaction from "./EditTransaction"

interface TransactionActionsMenuProps {
  transaction: TransactionPublic
  accounts: Map<string, string>
  categories: Map<string, string>
}

export const TransactionActionsMenu = ({
  transaction,
}: TransactionActionsMenuProps) => {
  const [open, setOpen] = useState(false)

  return (
    <DropdownMenu open={open} onOpenChange={setOpen}>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon">
          <EllipsisVertical />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <EditTransaction
          transaction={transaction}
          onSuccess={() => setOpen(false)}
        />
        <DeleteTransaction
          id={transaction.id}
          description={transaction.description}
          onSuccess={() => setOpen(false)}
        />
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
