import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Pencil } from "lucide-react"
import { useState } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"

import { CategoriesService, type CategoryPublic } from "@/client"
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
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { LoadingButton } from "@/components/ui/loading-button"
import useCustomToast from "@/hooks/useCustomToast"
import { ERROR_CODES, extractErrorMessage, getErrorCode } from "@/utils"

const formSchema = z.object({
  name: z
    .string()
    .min(1, { message: "Name is required" })
    .max(255, { message: "Name must be 255 characters or less" })
    .refine((val) => val.trim().length > 0, {
      message: "Name cannot be only whitespace",
    }),
})

type FormData = z.infer<typeof formSchema>

interface EditCategoryProps {
  category: CategoryPublic
  onSuccess: () => void
}

const EditCategory = ({ category, onSuccess }: EditCategoryProps) => {
  const [isOpen, setIsOpen] = useState(false)
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast, showRetryToast } = useCustomToast()

  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      name: category.name,
    },
  })

  const mutation = useMutation({
    mutationFn: (data: FormData) =>
      CategoriesService.updateCategory({
        id: category.id,
        requestBody: {
          name: data.name.trim(),
        },
      }),
    onSuccess: () => {
      showSuccessToast("Category updated successfully")
      setIsOpen(false)
      onSuccess()
    },
    onError: (err) => {
      const errorCode = getErrorCode(err as Error)
      const errorMessage = extractErrorMessage(err as Error)

      // Handle specific error cases
      if (errorCode === ERROR_CODES.CONFLICT) {
        showErrorToast(
          "A category with this name already exists. Please choose a different name.",
        )
        form.setError("name", {
          type: "manual",
          message: "This category name is already taken",
        })
      } else if (errorCode === ERROR_CODES.NOT_FOUND) {
        showErrorToast(
          "This category no longer exists. It may have been deleted.",
        )
        setIsOpen(false)
      } else if (errorCode === ERROR_CODES.NETWORK_ERROR) {
        showRetryToast(errorMessage, () => {
          form.handleSubmit(onSubmit)()
        })
      } else {
        showErrorToast(errorMessage)
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["categories"] })
    },
  })

  const onSubmit = (data: FormData) => {
    mutation.mutate(data)
  }

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DropdownMenuItem
        onSelect={(e) => e.preventDefault()}
        onClick={() => setIsOpen(true)}
      >
        <Pencil />
        Edit Category
      </DropdownMenuItem>
      <DialogContent className="sm:max-w-md">
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)}>
            <DialogHeader>
              <DialogTitle>Edit Category</DialogTitle>
              <DialogDescription>
                Update the category name below.
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <FormField
                control={form.control}
                name="name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>
                      Name <span className="text-destructive">*</span>
                    </FormLabel>
                    <FormControl>
                      <Input
                        placeholder="Category name"
                        type="text"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <DialogFooter>
              <DialogClose asChild>
                <Button variant="outline" disabled={mutation.isPending}>
                  Cancel
                </Button>
              </DialogClose>
              <LoadingButton type="submit" loading={mutation.isPending}>
                Save
              </LoadingButton>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}

export default EditCategory
