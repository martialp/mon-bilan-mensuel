import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Tags } from "lucide-react"
import { useState } from "react"

import { CategoriesService, TransactionsService } from "@/client"
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

interface BulkCategorizationProps {
  selectedTransactionIds: string[]
  onSuccess?: () => void
  onClearSelection?: () => void
}

export function BulkCategorization({
  selectedTransactionIds,
  onSuccess,
  onClearSelection,
}: BulkCategorizationProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [selectedCategoryId, setSelectedCategoryId] = useState<string>("")
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const { data: categories } = useQuery({
    queryKey: ["categories"],
    queryFn: () => CategoriesService.readCategories({ skip: 0, limit: 100 }),
  })

  const bulkCategorizeMutation = useMutation({
    mutationFn: async (categoryId: string | null) => {
      // Update each transaction sequentially
      const results = await Promise.all(
        selectedTransactionIds.map((id) =>
          TransactionsService.updateTransaction({
            id,
            requestBody: {
              category_id: categoryId,
              status: categoryId ? "manual" : null,
            },
          }),
        ),
      )
      return results
    },
    onSuccess: (results) => {
      showSuccessToast(
        `${results.length} transaction(s) categorized successfully`,
      )
      queryClient.invalidateQueries({ queryKey: ["transactions"] })
      setIsOpen(false)
      setSelectedCategoryId("")
      onClearSelection?.()
      onSuccess?.()
    },
    onError: handleError.bind(showErrorToast),
  })

  const handleSubmit = () => {
    const categoryId =
      selectedCategoryId === "uncategorized" ? null : selectedCategoryId
    bulkCategorizeMutation.mutate(categoryId)
  }

  if (selectedTransactionIds.length === 0) {
    return null
  }

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm">
          <Tags className="mr-2 h-4 w-4" />
          Categorize ({selectedTransactionIds.length})
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Bulk Categorization</DialogTitle>
          <DialogDescription>
            Assign a category to {selectedTransactionIds.length} selected
            transaction(s). This will set the status to "manual".
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="bulk-category">Category</Label>
            <Select
              value={selectedCategoryId}
              onValueChange={setSelectedCategoryId}
            >
              <SelectTrigger id="bulk-category">
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
            <Button variant="outline" disabled={bulkCategorizeMutation.isPending}>
              Cancel
            </Button>
          </DialogClose>
          <LoadingButton
            onClick={handleSubmit}
            loading={bulkCategorizeMutation.isPending}
            disabled={!selectedCategoryId}
          >
            Apply to {selectedTransactionIds.length} transaction(s)
          </LoadingButton>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
