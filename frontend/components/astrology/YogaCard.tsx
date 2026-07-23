import * as React from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface Yoga {
  name: string;
  description: string;
}

interface YogaCardProps {
  yoga: Yoga;
  className?: string;
}

export default function YogaCard({ yoga, className }: YogaCardProps) {
  return (
    <Card className={cn("border-white/10 bg-sidebar/30 backdrop-blur-sm shadow-md", className)}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-semibold text-foreground">{yoga.name}</CardTitle>
        <Badge variant="gold" className="text-[10px] font-semibold uppercase tracking-wider py-0 px-2">
          Active
        </Badge>
      </CardHeader>
      <CardContent>
        <p className="text-xs text-muted-foreground leading-relaxed">{yoga.description}</p>
      </CardContent>
    </Card>
  );
}
