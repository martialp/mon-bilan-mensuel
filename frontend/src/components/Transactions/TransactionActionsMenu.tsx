import { Check, EllipsisVertical } from "lucide-react"
import { useState } from "react"

import type { TransactionPublic } from "@/client"
import { TransactionsService } from "@/client"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"
import { CategorizeTransaction } from "./CategorizeTransaction"
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
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const confirmMutation = useMutation({
    mutationFn: () =>
      TransactionsService.updateTransaction({
        id: transaction.id,
        requestBody: {
          status: "confirmed",
        },
      }),
    onSuccess: () => {
      showSuccessToast("Transaction confirmed successfully")
      queryClient.invalidateQueries({ queryKey: ["transactions"] })
      setOpen(false)
    },
    onError: handleError.bind(showErrorToast),
  })

  return (
    <DropdownMenu open={open} onOpenChange={setOpen}>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon">
          <EllipsisVertical />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <CategorizeTransaction
          transaction={transaction}
          onSuccess={() => setOpen(false)}
        />
        {transaction.status === "auto" && (
          <DropdownMenuItem
            onClick={() => confirmMutation.mutate()}
            disabled={confirmMutation.isPending}
          >
            <Check className="mr-2 h-4 w-4" />
            Confirm Categorization
          </DropdownMenuItem>
        )}
        <DropdownMenuSeparator />
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
