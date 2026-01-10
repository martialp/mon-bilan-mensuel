import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Check } from "lucide-react"

import type { TransactionPublic } from "@/client"
import { TransactionsService } from "@/client"
import { Button } from "@/components/ui/button"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

interface ConfirmTransactionProps {
  transaction: TransactionPublic
  onSuccess?: () => void
}

export function ConfirmTransaction({
  transaction,
  onSuccess,
}: ConfirmTransactionProps) {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const confirmMutation = useMutation({
    mutationFn: () =>
      TransactionsService.confirmTransaction({
        id: transaction.id,
      }),
    onSuccess: () => {
      showSuccessToast("Transaction confirmed successfully")
      queryClient.invalidateQueries({ queryKey: ["transactions"] })
      onSuccess?.()
    },
    onError: handleError.bind(showErrorToast),
  })

  // Only show for auto-categorized transactions
  if (transaction.status !== "auto") {
    return null
  }

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 text-green-600 hover:text-green-700 hover:bg-green-50 dark:hover:bg-green-950"
            onClick={() => confirmMutation.mutate()}
            disabled={confirmMutation.isPending}
          >
            <Check className="h-4 w-4" />
            <span className="sr-only">Confirm categorization</span>
          </Button>
        </TooltipTrigger>
        <TooltipContent>
          <p>Confirm auto-categorization</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}
