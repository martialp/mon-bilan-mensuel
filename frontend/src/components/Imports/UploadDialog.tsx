import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useSuspenseQuery } from "@tanstack/react-query"
import { Upload } from "lucide-react"
import { useRef, useState } from "react"
import { useForm } from "react-hook-form"
import { z } from "zod"

import {
  AccountsService,
  type ImportPreviewPublic,
  ImportsService,
} from "@/client"
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

interface UploadDialogProps {
  onUploadSuccess: (preview: ImportPreviewPublic) => void
}

const MAX_FILE_SIZE = 10 * 1024 * 1024 // 10MB

const formSchema = z.object({
  file: z
    .instanceof(File, { message: "Please select a file" })
    .refine(
      (file) => file.size <= MAX_FILE_SIZE,
      "File size must be under 10MB",
    )
    .refine(
      (file) => file.type === "application/pdf",
      "Please select a PDF file",
    ),
  accountId: z.string().uuid("Please select an account"),
})

type FormData = z.infer<typeof formSchema>

const UploadDialog = ({ onUploadSuccess }: UploadDialogProps) => {
  const [isOpen, setIsOpen] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const {
    showSuccessToast,
    showErrorToast,
    showRetryToast,
    showNetworkErrorToast,
  } = useCustomToast()

  const { data: accountsData } = useSuspenseQuery({
    queryKey: ["accounts"],
    queryFn: () => AccountsService.readAccounts({ limit: 100 }),
  })

  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    mode: "onBlur",
    criteriaMode: "all",
    defaultValues: {
      file: undefined,
      accountId: undefined,
    },
  })

  const mutation = useMutation({
    mutationFn: (data: FormData) =>
      ImportsService.uploadPdf({
        accountId: data.accountId,
        formData: { file: data.file },
      }),
    onSuccess: (preview) => {
      showSuccessToast("PDF uploaded successfully")
      form.reset()
      if (fileInputRef.current) {
        fileInputRef.current.value = ""
      }
      setIsOpen(false)
      onUploadSuccess(preview)
    },
    onError: (err) => {
      const errorCode = getErrorCode(err as Error)
      const errorMessage = extractErrorMessage(err as Error)
      const lowerMessage = errorMessage.toLowerCase()

      // Requirement 6.5: Network error with retry option
      if (errorCode === ERROR_CODES.NETWORK_ERROR) {
        showNetworkErrorToast(() => {
          mutation.mutate(form.getValues())
        })
        return
      }

      // Requirement 6.1: Invalid file type error
      if (
        lowerMessage.includes("invalid file type") ||
        lowerMessage.includes("invalid pdf") ||
        (lowerMessage.includes("invalid") && lowerMessage.includes("file")) ||
        lowerMessage.includes("not a valid pdf")
      ) {
        showErrorToast("Invalid file type. Please upload a PDF file.")
        return
      }

      // Requirement 6.3: No transactions found error
      if (
        lowerMessage.includes("no transactions") ||
        lowerMessage.includes("no transaction found") ||
        lowerMessage.includes("could not extract")
      ) {
        showErrorToast("No transactions found in the PDF")
        return
      }

      // Requirement 6.6: Server errors with retry option
      if (errorCode === ERROR_CODES.SERVER_ERROR) {
        showRetryToast(errorMessage, () => {
          mutation.mutate(form.getValues())
        })
        return
      }

      // Requirement 6.2: Show API error messages for other failures
      showErrorToast(errorMessage)
    },
  })

  const onSubmit = (data: FormData) => {
    mutation.mutate(data)
  }

  const handleFileChange = (
    e: React.ChangeEvent<HTMLInputElement>,
    onChange: (file: File | undefined) => void,
  ) => {
    const file = e.target.files?.[0]
    onChange(file)
  }

  const handleOpenChange = (open: boolean) => {
    setIsOpen(open)
    if (!open) {
      form.reset()
      if (fileInputRef.current) {
        fileInputRef.current.value = ""
      }
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        <Button className="my-4">
          <Upload className="mr-2 h-4 w-4" />
          Import PDF
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Import PDF Statement</DialogTitle>
          <DialogDescription>
            Upload a Mastercard PDF statement to import transactions.
          </DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)}>
            <div className="grid gap-4 py-4">
              <FormField
                control={form.control}
                name="file"
                render={({ field: { onChange, value, ref, ...field } }) => (
                  <FormItem>
                    <FormLabel>
                      PDF File <span className="text-destructive">*</span>
                    </FormLabel>
                    <FormControl>
                      <Input
                        type="file"
                        accept="application/pdf,.pdf"
                        ref={(e) => {
                          ref(e)
                          ;(
                            fileInputRef as React.MutableRefObject<HTMLInputElement | null>
                          ).current = e
                        }}
                        onChange={(e) => handleFileChange(e, onChange)}
                        {...field}
                      />
                    </FormControl>
                    {value && (
                      <p className="text-sm text-muted-foreground">
                        Selected: {value.name}
                      </p>
                    )}
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="accountId"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>
                      Account <span className="text-destructive">*</span>
                    </FormLabel>
                    <Select
                      onValueChange={field.onChange}
                      defaultValue={field.value}
                    >
                      <FormControl>
                        <SelectTrigger className="w-full">
                          <SelectValue placeholder="Select target account" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {accountsData.data.map((account) => (
                          <SelectItem key={account.id} value={account.id}>
                            {account.name}
                            {account.institution && ` (${account.institution})`}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
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
                Upload
              </LoadingButton>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}

export default UploadDialog
