"use client";

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

interface AstrologyTableProps<T> {
  title: string;
  columns: { label: string; key: keyof T }[];
  data: T[];
}

export default function AstrologyTable<T>({ title, columns, data }: AstrologyTableProps<T>) {
  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-foreground/90">{title}</h3>
      <div className="rounded-xl border border-white/10 bg-sidebar/30 backdrop-blur-sm overflow-hidden">
        <Table>
          <TableHeader className="bg-white/5">
            <TableRow>
              {columns.map((col) => (
                <TableHead key={col.key as string} className="text-muted-foreground font-medium">
                  {col.label}
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.map((row, i) => (
              <TableRow key={i} className="hover:bg-white/5 transition-colors">
                {columns.map((col) => {
                  const value = row[col.key];
                  return (
                    <TableCell key={col.key as string} className="py-3">
                      {typeof value === "number" ? value.toFixed(2) : String(value ?? "")}
                    </TableCell>
                  );
                })}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
