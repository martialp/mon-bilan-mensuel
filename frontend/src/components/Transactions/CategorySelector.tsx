import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Tag } from "lucide-react"

import { CategoriesService, TransactionsService } from "@/client"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import useCustomToast from "@/hooks/useCustomToast"
import { handleError } from "@/utils"

interface CategorySelectorProps {
  transactionId: string
  currentCategoryId: string | null
  onSuccess?: () => void
  compact?: boolean
}

export function CategorySelector({
  transactionId,
  currentCategoryId,
  onSuccess,
  compact = false,
}: CategorySelectorProps) {
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast } = useCustomToast()

  const { data: categories } = useQuery({
    queryKey: ["categories"],
    queryFn: () => CategoriesService.readCategories({ skip: 0, limit: 100 }),
  })

  const categorizeMutation = useMutation({
    mutationFn: (categoryId: string | null) => {
      if (categoryId) {
        // Use the dedicated categorize endpoint which sets status to 'manual'
        return TransactionsService.categorizeTransaction({
          id: transactionId,
          categoryId: categoryId,
        })
      } else {
        // For uncategorizing, use the update endpoint
        return TransactionsService.updateTransaction({
          id: transactionId,
          requestBody: {
            category_id: null,
          },
        })
      }
    },
    onSuccess: () => {
      showSuccessToast("Transaction categorized successfully")
      queryClient.invalidateQueries({ queryKey: ["transactions"] })
      onSuccess?.()
    },
    onError: handleError.bind(showErrorToast),
  })

  const handleCategoryChange = (value: string) => {
    const categoryId = value === "uncategorized" ? null : value
    categorizeMutation.mutate(categoryId)
  }

  if (compact) {
    return (
      <Select
        value={currentCategoryId || "uncategorized"}
        onValueChange={handleCategoryChange}
        disabled={categorizeMutation.isPending}
      >
        <SelectTrigger className="h-8 w-[140px]">
          <SelectValue placeholder="Select category" />
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
    )
  }

  return (
    <div className="flex items-center gap-2">
      <Tag className="h-4 w-4 text-muted-foreground" />
      <Select
        value={currentCategoryId || "uncategorized"}
        onValueChange={handleCategoryChange}
        disabled={categorizeMutation.isPending}
      >
        <SelectTrigger className="w-[180px]">
          <SelectValue placeholder="Select category" />
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
  )
}
