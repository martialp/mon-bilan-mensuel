import { X } from "lucide-react"
import type { AccountPublic, CategoryPublic } from "@/client"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

export interface TransactionFiltersState {
  accountId: string | null
  categoryId: string | null
  startDate: string | null
  endDate: string | null
}

interface TransactionFiltersProps {
  filters: TransactionFiltersState
  onFiltersChange: (filters: TransactionFiltersState) => void
  accounts: AccountPublic[]
  categories: CategoryPublic[]
}

const UNCATEGORIZED_VALUE = "__uncategorized__"

export function TransactionFilters({
  filters,
  onFiltersChange,
  accounts,
  categories,
}: TransactionFiltersProps) {
  const handleAccountChange = (value: string) => {
    onFiltersChange({
      ...filters,
      accountId: value === "all" ? null : value,
    })
  }

  const handleCategoryChange = (value: string) => {
    onFiltersChange({
      ...filters,
      categoryId:
        value === "all" ? null : value === UNCATEGORIZED_VALUE ? "" : value,
    })
  }

  const handleStartDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onFiltersChange({
      ...filters,
      startDate: e.target.value || null,
    })
  }

  const handleEndDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onFiltersChange({
      ...filters,
      endDate: e.target.value || null,
    })
  }

  const clearFilters = () => {
    onFiltersChange({
      accountId: null,
      categoryId: null,
      startDate: null,
      endDate: null,
    })
  }

  const hasActiveFilters =
    filters.accountId ||
    filters.categoryId !== null ||
    filters.startDate ||
    filters.endDate

  return (
    <div className="flex flex-col gap-4 p-4 border rounded-lg bg-muted/20">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium">Filters</h3>
        {hasActiveFilters && (
          <Button
            variant="ghost"
            size="sm"
            onClick={clearFilters}
            className="h-8 px-2 text-xs"
          >
            <X className="mr-1 h-3 w-3" />
            Clear filters
          </Button>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="space-y-2">
          <Label htmlFor="account-filter" className="text-xs">
            Account
          </Label>
          <Select
            value={filters.accountId || "all"}
            onValueChange={handleAccountChange}
          >
            <SelectTrigger id="account-filter" className="h-9">
              <SelectValue placeholder="All accounts" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All accounts</SelectItem>
              {accounts.map((account) => (
                <SelectItem key={account.id} value={account.id}>
                  {account.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label htmlFor="category-filter" className="text-xs">
            Category
          </Label>
          <Select
            value={
              filters.categoryId === null
                ? "all"
                : filters.categoryId === ""
                  ? UNCATEGORIZED_VALUE
                  : filters.categoryId
            }
            onValueChange={handleCategoryChange}
          >
            <SelectTrigger id="category-filter" className="h-9">
              <SelectValue placeholder="All categories" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All categories</SelectItem>
              <SelectItem value={UNCATEGORIZED_VALUE}>Uncategorized</SelectItem>
              {categories.map((category) => (
                <SelectItem key={category.id} value={category.id}>
                  {category.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label htmlFor="start-date" className="text-xs">
            Start Date
          </Label>
          <Input
            id="start-date"
            type="date"
            value={filters.startDate || ""}
            onChange={handleStartDateChange}
            className="h-9"
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="end-date" className="text-xs">
            End Date
          </Label>
          <Input
            id="end-date"
            type="date"
            value={filters.endDate || ""}
            onChange={handleEndDateChange}
            className="h-9"
          />
        </div>
      </div>
    </div>
  )
}
