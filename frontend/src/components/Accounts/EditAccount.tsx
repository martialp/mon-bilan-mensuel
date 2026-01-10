import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Pencil } from "lucide-react"
import { useState } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"

import { type AccountPublic, AccountsService, type AccountType } from "@/client"
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import useCustomToast from "@/hooks/useCustomToast"
import { ERROR_CODES, extractErrorMessage, getErrorCode } from "@/utils"

const accountTypes: { value: AccountType; label: string }[] = [
  { value: "credit_card", label: "Credit Card" },
  { value: "chequing", label: "Chequing" },
  { value: "savings", label: "Savings" },
  { value: "investment", label: "Investment" },
  { value: "other", label: "Other" },
]

const formSchema = z.object({
  name: z
    .string()
    .min(1, { message: "Name is required" })
    .max(255, { message: "Name must be 255 characters or less" })
    .refine((val) => val.trim().length > 0, {
      message: "Name cannot be only whitespace",
    }),
  type: z.enum(["credit_card", "chequing", "savings", "investment", "other"], {
    message: "Account type is required",
  }),
  institution: z
    .string()
    .max(255, { message: "Institution must be 255 characters or less" })
    .optional()
    .nullable(),
  description: z
    .string()
    .max(500, { message: "Description must be 500 characters or less" })
    .optional()
    .nullable(),
})

type FormData = z.infer<typeof formSchema>

interface EditAccountProps {
  account: AccountPublic
  onSuccess: () => void
}

const EditAccount = ({ account, onSuccess }: EditAccountProps) => {
  const [isOpen, setIsOpen] = useState(false)
  const queryClient = useQueryClient()
  const { showSuccessToast, showErrorToast, showRetryToast } = useCustomToast()

  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      name: account.name,
      type: account.type,
      institution: account.institution ?? "",
      description: account.description ?? "",
    },
  })

  const mutation = useMutation({
    mutationFn: (data: FormData) =>
      AccountsService.updateAccount({
        id: account.id,
        requestBody: {
          name: data.name.trim(),
          type: data.type,
          institution: data.institution?.trim() || null,
          description: data.description?.trim() || null,
        },
      }),
    onSuccess: () => {
      showSuccessToast("Account updated successfully")
      setIsOpen(false)
      onSuccess()
    },
    onError: (err) => {
      const errorCode = getErrorCode(err as Error)
      const errorMessage = extractErrorMessage(err as Error)

      // Handle specific error cases
      if (errorCode === ERROR_CODES.NOT_FOUND) {
        showErrorToast(
          "This account no longer exists. It may have been deleted.",
        )
        setIsOpen(false)
      } else if (errorCode === ERROR_CODES.NETWORK_ERROR) {
        showRetryToast(errorMessage, () => {
          form.handleSubmit(onSubmit)()
        })
      } else if (errorCode === ERROR_CODES.VALIDATION_ERROR) {
        showErrorToast("Please check your input and try again.")
      } else {
        showErrorToast(errorMessage)
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["accounts"] })
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
        Edit Account
      </DropdownMenuItem>
      <DialogContent className="sm:max-w-md">
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)}>
            <DialogHeader>
              <DialogTitle>Edit Account</DialogTitle>
              <DialogDescription>
                Update the account details below.
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
                        placeholder="Account name"
                        type="text"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="type"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>
                      Type <span className="text-destructive">*</span>
                    </FormLabel>
                    <Select
                      onValueChange={field.onChange}
                      defaultValue={field.value}
                    >
                      <FormControl>
                        <SelectTrigger className="w-full">
                          <SelectValue placeholder="Select account type" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {accountTypes.map((type) => (
                          <SelectItem key={type.value} value={type.value}>
                            {type.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="institution"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Institution</FormLabel>
                    <FormControl>
                      <Input
                        placeholder="Bank or institution name"
                        type="text"
                        {...field}
                        value={field.value ?? ""}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="description"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Description</FormLabel>
                    <FormControl>
                      <Input
                        placeholder="Optional description"
                        type="text"
                        {...field}
                        value={field.value ?? ""}
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

export default EditAccount
