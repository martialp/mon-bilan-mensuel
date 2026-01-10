import { EllipsisVertical } from "lucide-react"
import { useState } from "react"

import type { AccountPublic } from "@/client"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import DeleteAccount from "./DeleteAccount"
import EditAccount from "./EditAccount"

interface AccountActionsMenuProps {
  account: AccountPublic
}

export const AccountActionsMenu = ({ account }: AccountActionsMenuProps) => {
  const [open, setOpen] = useState(false)

  return (
    <DropdownMenu open={open} onOpenChange={setOpen}>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon">
          <EllipsisVertical />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <EditAccount account={account} onSuccess={() => setOpen(false)} />
        <DeleteAccount
          id={account.id}
          name={account.name}
          onSuccess={() => setOpen(false)}
        />
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
