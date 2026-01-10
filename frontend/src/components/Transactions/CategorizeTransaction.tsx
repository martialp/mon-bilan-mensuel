import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Tag } from "lucide-react"
import { useState } from "react"

import { CategoriesService, type TransactionPublic, TransactionsService } from "@/client"
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
import { Label } from "@/components/ui/label"
import { LoadingButton } from "@/components/ui/loading-button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

interface CategorizeTransactionProps {
  transaction: TransactionPublic
  onSuccess?: () => void
}

export function CategorizeTransaction({
  transaction,
  onSuccess,
}: CategorizeTransactionProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [selectedCategoryId, setSelectedCategoryId] = useState<string>(
    transaction.category_id || "uncategorized"
  )
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const { data: categories } = useQuery({
    queryKey: ["categories"],
    queryFn: () => CategoriesService.readCategories({ skip: 0, limit: 100 }),
  })

  const categorizeMutation = useMutation({
    mutationFn: (categoryId: string | null) =>
      TransactionsService.updateTransaction({
        id: transaction.id,
        requestBody: {
          category_id: categoryId,
          status: categoryId ? "manual" : null,
        },
      }),
    onSuccess: () => {
      showSuccessToast("Transaction categorized successfully")
      queryClient.invalidateQueries({ queryKey: ["transactions"] })
      setIsOpen(false)
      onSuccess?.()
    },
    onError: handleError.bind(showErrorToast),
  })

  const handleSubmit = () => {
    const categoryId =
      selectedCategoryId === "uncategorized" ? null : selectedCategoryId
    categorizeMutation.mutate(categoryId)
  }

  const currentCategoryName = transaction.category_id
    ? categories?.data.find((c) => c.id === transaction.category_id)?.name
    : "Uncategorized"

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DropdownMenuItem
        onSelect={(e) => e.preventDefault()}
        onClick={() => setIsOpen(true)}
      >
        <Tag className="mr-2 h-4 w-4" />
        Categorize
      </DropdownMenuItem>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Categorize Transaction</DialogTitle>
          <DialogDescription>
            Assign a category to this transaction. Current category:{" "}
            <span className="font-medium">{currentCategoryName}</span>
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="category">Category</Label>
            <Select
              value={selectedCategoryId}
              onValueChange={setSelectedCategoryId}
            >
              <SelectTrigger id="category">
                <SelectValue placeholder="Select a category" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="uncategorized">Uncategorized</SelectItem>
                {categories?.data.map((category) => (
                  <SelectItem key={category.id} value={category.id}>
                    {category.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
        <DialogFooter>
          <DialogClose asChild>
            <Button variant="outline" disabled={categorizeMutation.isPending}>
              Cancel
            </Button>
          </DialogClose>
          <LoadingButton
            onClick={handleSubmit}
            loading={categorizeMutation.isPending}
          >
            Save
          </LoadingButton>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
