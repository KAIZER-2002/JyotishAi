import * as React from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { HousePosition } from "@/types/astrology";
import { cn } from "@/lib/utils";

interface HouseTableProps {
  houses: HousePosition[];
  className?: string;
}

export default function HouseTable({
  houses,
  className,
}: HouseTableProps) {
  return (
    <div className={cn("space-y-4", className)}>
      <div className="rounded-xl border border-white/10 bg-sidebar/30 backdrop-blur-sm overflow-hidden">
        <Table>
          <TableHeader className="bg-white/5">
            <TableRow>
              <TableHead className="font-semibold text-muted-foreground">House</TableHead>
              <TableHead className="font-semibold text-muted-foreground">Start Longitude</TableHead>
              <TableHead className="font-semibold text-muted-foreground text-right">End Longitude</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {houses.map((h, idx) => (
              <TableRow key={idx} className="hover:bg-white/5 transition-colors">
                <TableCell className="font-bold text-foreground py-3">
                  House {h.house_number}
                </TableCell>
                <TableCell className="font-mono text-foreground py-3">
                  {h.start_longitude.toFixed(2)}°
                </TableCell>
                <TableCell className="font-mono text-right text-foreground py-3">
                  {h.end_longitude.toFixed(2)}°
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
