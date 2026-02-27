import { Download } from "lucide-react";
import { Button } from "@/components/ui/button";
import { downloadBlob } from "@/lib/utils";

interface DownloadButtonProps {
  base64Content: string;
  filename: string;
}

export function DownloadButton({ base64Content, filename }: DownloadButtonProps) {
  return (
    <Button
      size="sm"
      onClick={() => downloadBlob(base64Content, filename)}
      className="gap-2"
    >
      <Download className="h-4 w-4" />
      Baixar TXT
    </Button>
  );
}
