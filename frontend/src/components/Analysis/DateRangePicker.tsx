import { Calendar } from "lucide-react"
import { useMemo } from "react"

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
import { getDateRangeLastMonths } from "@/lib/finance"

export interface DateRange {
  startDate: string | null
  endDate: string | null
}

interface DateRangePickerProps {
  dateRange: DateRange
  onDateRangeChange: (range: DateRange) => void
}

type PresetOption = "1m" | "3m" | "6m" | "12m" | "ytd" | "custom"

export function DateRangePicker({
  dateRange,
  onDateRangeChange,
}: DateRangePickerProps) {
  const selectedPreset = useMemo((): PresetOption => {
    if (!dateRange.startDate && !dateRange.endDate) return "3m"

    const now = new Date()
    const today = now.toISOString().split("T")[0]

    // Check for YTD
    const yearStart = `${now.getFullYear()}-01-01`
    if (dateRange.startDate === yearStart && dateRange.endDate === today) {
      return "ytd"
    }

    // Check for month presets
    const presets: { months: number; key: PresetOption }[] = [
      { months: 1, key: "1m" },
      { months: 3, key: "3m" },
      { months: 6, key: "6m" },
      { months: 12, key: "12m" },
    ]

    for (const preset of presets) {
      const range = getDateRangeLastMonths(preset.months)
      if (
        dateRange.startDate === range.startDate &&
        dateRange.endDate === range.endDate
      ) {
        return preset.key
      }
    }

    return "custom"
  }, [dateRange])

  const handlePresetChange = (value: PresetOption) => {
    if (value === "custom") return

    const now = new Date()
    const today = now.toISOString().split("T")[0]

    if (value === "ytd") {
      const yearStart = `${now.getFullYear()}-01-01`
      onDateRangeChange({ startDate: yearStart, endDate: today })
      return
    }

    const monthsMap: Record<string, number> = {
      "1m": 1,
      "3m": 3,
      "6m": 6,
      "12m": 12,
    }

    const months = monthsMap[value]
    if (months) {
      const range = getDateRangeLastMonths(months)
      onDateRangeChange({ startDate: range.startDate, endDate: range.endDate })
    }
  }

  const handleClearDates = () => {
    onDateRangeChange({ startDate: null, endDate: null })
  }

  return (
    <div className="flex flex-wrap items-end gap-4">
      <div className="flex items-center gap-2">
        <Calendar className="h-4 w-4 text-muted-foreground" />
        <span className="text-sm font-medium">Period:</span>
      </div>

      <Select value={selectedPreset} onValueChange={handlePresetChange}>
        <SelectTrigger className="w-[140px]">
          <SelectValue placeholder="Select period" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="1m">Last month</SelectItem>
          <SelectItem value="3m">Last 3 months</SelectItem>
          <SelectItem value="6m">Last 6 months</SelectItem>
          <SelectItem value="12m">Last 12 months</SelectItem>
          <SelectItem value="ytd">Year to date</SelectItem>
          <SelectItem value="custom">Custom</SelectItem>
        </SelectContent>
      </Select>

      <div className="flex items-end gap-2">
        <div className="space-y-1">
          <Label htmlFor="start-date" className="text-xs">
            From
          </Label>
          <Input
            id="start-date"
            type="date"
            value={dateRange.startDate || ""}
            onChange={(e) =>
              onDateRangeChange({
                ...dateRange,
                startDate: e.target.value || null,
              })
            }
            className="w-[140px]"
          />
        </div>
        <div className="space-y-1">
          <Label htmlFor="end-date" className="text-xs">
            To
          </Label>
          <Input
            id="end-date"
            type="date"
            value={dateRange.endDate || ""}
            onChange={(e) =>
              onDateRangeChange({
                ...dateRange,
                endDate: e.target.value || null,
              })
            }
            className="w-[140px]"
          />
        </div>
      </div>

      {(dateRange.startDate || dateRange.endDate) && (
        <Button variant="ghost" size="sm" onClick={handleClearDates}>
          Clear
        </Button>
      )}
    </div>
  )
}
