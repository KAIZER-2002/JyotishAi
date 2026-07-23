import * as React from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { PlanetPosition } from "@/types/astrology";
import NakshatraBadge from "./NakshatraBadge";
import { cn } from "@/lib/utils";

interface PlanetTableProps {
  planets: PlanetPosition[];
  className?: string;
}

export default function PlanetTable({
  planets,
  className,
}: PlanetTableProps) {
  return (
    <div className={cn("space-y-4", className)}>
      <div className="rounded-xl border border-white/10 bg-sidebar/30 backdrop-blur-sm overflow-hidden">
        <Table>
          <TableHeader className="bg-white/5">
            <TableRow>
              <TableHead className="font-semibold text-muted-foreground">Planet</TableHead>
              <TableHead className="font-semibold text-muted-foreground">Zodiac Sign</TableHead>
              <TableHead className="font-semibold text-muted-foreground text-center">House</TableHead>
              <TableHead className="font-semibold text-muted-foreground">Degree</TableHead>
              <TableHead className="font-semibold text-muted-foreground">Nakshatra</TableHead>
              <TableHead className="font-semibold text-muted-foreground text-right">Status</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {planets.map((p, idx) => (
              <TableRow key={idx} className="hover:bg-white/5 transition-colors">
                <TableCell className="font-bold text-foreground py-3">
                  {p.planet}
                </TableCell>
                <TableCell className="text-foreground py-3">
                  {p.zodiac_sign}
                </TableCell>
                <TableCell className="text-center font-medium text-foreground py-3">
                  {p.house_number}
                </TableCell>
                <TableCell className="font-mono text-foreground py-3">
                  {p.degree_within_sign.toFixed(2)}°
                </TableCell>
                <TableCell className="py-3">
                  <NakshatraBadge nakshatra={p.nakshatra} pada={p.pada} />
                </TableCell>
                <TableCell className="text-right py-3">
                  {p.retrograde ? (
                    <Badge variant="destructive" className="text-[10px] font-semibold py-0 px-2">
                      R
                    </Badge>
                  ) : (
                    <span className="text-xs text-muted-foreground">—</span>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
