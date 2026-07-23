import * as React from "react";
import { FileText } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface InterpretationCardProps {
  title: string;
  text: string;
  className?: string;
}

export default function InterpretationCard({
  title,
  text,
  className,
}: InterpretationCardProps) {
  return (
    <Card className={cn("border-white/10 bg-sidebar/30 backdrop-blur-sm shadow-md", className)}>
      <CardHeader className="flex flex-row items-center gap-3 space-y-0 pb-3">
        <div className="flex size-9 items-center justify-center rounded-lg bg-primary/10 text-primary ring-1 ring-primary/20">
          <FileText className="size-4" />
        </div>
        <CardTitle className="text-base font-bold text-foreground">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground whitespace-pre-line leading-relaxed">{text}</p>
      </CardContent>
    </Card>
  );
}
