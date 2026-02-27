import { Loader2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { STATUS_LABELS, STATUS_VARIANT } from "@/lib/constants";
import { ProtocoloStatus } from "@/types/api";

interface StatusChipProps {
  status: ProtocoloStatus;
}

export function StatusChip({ status }: StatusChipProps) {
  return (
    <Badge variant={STATUS_VARIANT[status]} className="gap-1">
      {status === "PENDING" && <Loader2 className="h-3 w-3 animate-spin" />}
      {STATUS_LABELS[status]}
    </Badge>
  );
}
