import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Trash2 } from "lucide-react"
import { useState } from "react"
import { useForm } from "react-hook-form"

import { CategoriesService } from "@/client"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { DropdownMenuItem } from "@/components/ui/dropdown-menu"
import { LoadingButton } from "@/components/ui/loading-button"
import useCustomToast from "@/hooks/useCustomToast"
import { ERROR_CODES, extractErrorMessage, getErrorCode } from "@/utils"

interface DeleteCategoryProps {
  id: string
  name: string
  onSuccess: () => void
}

const DeleteCategory = ({ id, name, onSuccess }: DeleteCategoryProps) => {
  const [isOpen, setIsOpen] = useState(false)
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast, showRetryToast } = useCustomToast()
  const { handleSubmit } = useForm()

  const deleteCategory = async (id: string) => {
    await CategoriesService.deleteCategory({ id: id })
  }

  const mutation = useMutation({
    mutationFn: deleteCategory,
    onSuccess: () => {
      showSuccessToast("The category was deleted successfully")
      setIsOpen(false)
      onSuccess()
    },
    onError: (err) => {
      const errorCode = getErrorCode(err as Error)
      const errorMessage = extractErrorMessage(err as Error)

      // Handle specific error cases
      if (
        errorCode === ERROR_CODES.CONFLICT ||
        errorMessage.includes("transactions")
      ) {
        showErrorToast(
          "This category has transactions. Please reassign them first.",
        )
      } else if (errorCode === ERROR_CODES.NOT_FOUND) {
        showErrorToast(
          "This category no longer exists. It may have been deleted already.",
        )
        setIsOpen(false)
      } else if (errorCode === ERROR_CODES.NETWORK_ERROR) {
        showRetryToast(errorMessage, () => {
          mutation.mutate(id)
        })
      } else {
        showErrorToast(errorMessage)
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["categories"] })
    },
  })

  const onSubmit = async () => {
    mutation.mutate(id)
  }

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DropdownMenuItem
        variant="destructive"
        onSelect={(e) => e.preventDefault()}
        onClick={() => setIsOpen(true)}
      >
        <Trash2 />
        Delete Category
      </DropdownMenuItem>
      <DialogContent className="sm:max-w-md">
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>Delete Category</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete the category "{name}"? This action
              cannot be undone.
              <br />
              <br />
              <strong>Note:</strong> Categories with existing transactions
              cannot be deleted. You must first reassign all transactions
              associated with this category.
            </DialogDescription>
          </DialogHeader>

          <DialogFooter className="mt-4">
            <DialogClose asChild>
              <Button variant="outline" disabled={mutation.isPending}>
                Cancel
              </Button>
            </DialogClose>
            <LoadingButton
              variant="destructive"
              type="submit"
              loading={mutation.isPending}
            >
              Delete
            </LoadingButton>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

export default DeleteCategory
