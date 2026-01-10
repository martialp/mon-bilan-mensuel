import { useMutation, useQueryClient } from "@tanstack/react-query"
import { CheckCheck } from "lucide-react"
import { useState } from "react"

import { TransactionsService } from "@/client"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { LoadingButton } from "@/components/ui/loading-button"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

interface BulkConfirmationProps {
  selectedTransactionIds: string[]
  onSuccess?: () => void
  onClearSelection?: () => void
}

export function BulkConfirmation({
  selectedTransactionIds,
  onSuccess,
  onClearSelection,
}: BulkConfirmationProps) {
  const [isOpen, setIsOpen] = useState(false)
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const bulkConfirmMutation = useMutation({
    mutationFn: async () => {
      // Update each transaction sequentially
      const results = await Promise.all(
        selectedTransactionIds.map((id) =>
          TransactionsService.updateTransaction({
            id,
            requestBody: {
              status: "confirmed",
            },
          }),
        ),
      )
      return results
    },
    onSuccess: (results) => {
      showSuccessToast(
        `${results.length} transaction(s) confirmed successfully`,
      )
      queryClient.invalidateQueries({ queryKey: ["transactions"] })
      setIsOpen(false)
      onClearSelection?.()
      onSuccess?.()
    },
    onError: handleError.bind(showErrorToast),
  })

  if (selectedTransactionIds.length === 0) {
    return null
  }

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm">
          <CheckCheck className="mr-2 h-4 w-4" />
          Confirm ({selectedTransactionIds.length})
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Confirm Transactions</DialogTitle>
          <DialogDescription>
            Confirm the auto-categorization for {selectedTransactionIds.length}{" "}
            selected transaction(s). This will change their status from "auto"
            to "confirmed".
          </DialogDescription>
        </DialogHeader>
        <DialogFooter className="mt-4">
          <DialogClose asChild>
            <Button variant="outline" disabled={bulkConfirmMutation.isPending}>
              Cancel
            </Button>
          </DialogClose>
          <LoadingButton
            onClick={() => bulkConfirmMutation.mutate()}
            loading={bulkConfirmMutation.isPending}
          >
            Confirm {selectedTransactionIds.length} transaction(s)
          </LoadingButton>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
