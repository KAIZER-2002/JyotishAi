import * as React from "react";
import { cn } from "@/lib/utils";

interface MarkdownRendererProps {
  content: string;
  isStreaming?: boolean;
  className?: string;
}

export default function MarkdownRenderer({
  content,
  isStreaming = false,
  className,
}: MarkdownRendererProps) {
  // Simple regex-based block parser
  const blocks = React.useMemo(() => {
    const rawLines = content.split("\n");
    const parsedBlocks: Array<
      | { type: "code"; code: string; language: string }
      | { type: "table"; headers: string[]; rows: string[][] }
      | { type: "list"; ordered: boolean; items: string[] }
      | { type: "paragraph"; text: string }
    > = [];

    let i = 0;
    while (i < rawLines.length) {
      const line = rawLines[i];

      // Code Block
      if (line.trim().startsWith("```")) {
        const lang = line.trim().slice(3).trim();
        let codeContent = "";
        i++;
        while (i < rawLines.length && !rawLines[i].trim().startsWith("```")) {
          codeContent += rawLines[i] + "\n";
          i++;
        }
        parsedBlocks.push({
          type: "code",
          code: codeContent.trim(),
          language: lang || "code",
        });
        i++;
        continue;
      }

      // Table Block
      if (line.trim().startsWith("|")) {
        const headers = line
          .split("|")
          .map((s) => s.trim())
          .filter((s, idx, arr) => idx > 0 && idx < arr.length - 1);
        
        i++;
        // Skip separator line (e.g. |---|---|)
        if (i < rawLines.length && rawLines[i].trim().startsWith("|") && rawLines[i].includes("-")) {
          i++;
        }

        const rows: string[][] = [];
        while (i < rawLines.length && rawLines[i].trim().startsWith("|")) {
          const rowCells = rawLines[i]
            .split("|")
            .map((s) => s.trim())
            .filter((s, idx, arr) => idx > 0 && idx < arr.length - 1);
          rows.push(rowCells);
          i++;
        }
        parsedBlocks.push({ type: "table", headers, rows });
        continue;
      }

      // List Block
      if (line.trim().startsWith("- ") || line.trim().startsWith("* ") || /^\d+\.\s/.test(line.trim())) {
        const ordered = /^\d+\.\s/.test(line.trim());
        const items: string[] = [];
        while (
          i < rawLines.length &&
          (rawLines[i].trim().startsWith("- ") ||
            rawLines[i].trim().startsWith("* ") ||
            /^\d+\.\s/.test(rawLines[i].trim()))
        ) {
          const itemText = rawLines[i]
            .trim()
            .replace(/^[-*]\s+/, "")
            .replace(/^\d+\.\s+/, "");
          items.push(itemText);
          i++;
        }
        parsedBlocks.push({ type: "list", ordered, items });
        continue;
      }

      // Paragraph Block (skip empty lines)
      if (line.trim() !== "") {
        parsedBlocks.push({ type: "paragraph", text: line });
      }
      i++;
    }

    return parsedBlocks;
  }, [content]);

  // Inline formatter helper (bold, italic, inline code)
  function formatInlineText(text: string) {
    const parts: React.ReactNode[] = [];
    let remaining = text;
    let keyIdx = 0;

    while (remaining.length > 0) {
      const codeMatch = remaining.match(/`([^`]+)`/);
      const boldMatch = remaining.match(/\*\*([^*]+)\*\*/);
      const italicMatch = remaining.match(/\*([^*]+)\*/);

      const matches: Array<{ index: number; type: "code" | "bold" | "italic"; match: RegExpMatchArray }> = [];
      if (codeMatch && codeMatch.index !== undefined) {
        matches.push({ index: codeMatch.index, type: "code", match: codeMatch });
      }
      if (boldMatch && boldMatch.index !== undefined) {
        matches.push({ index: boldMatch.index, type: "bold", match: boldMatch });
      }
      if (italicMatch && italicMatch.index !== undefined) {
        matches.push({ index: italicMatch.index, type: "italic", match: italicMatch });
      }

      if (matches.length === 0) {
        parts.push(<span key={keyIdx++}>{remaining}</span>);
        break;
      }

      matches.sort((a, b) => a.index - b.index);
      const first = matches[0];

      if (first.index > 0) {
        parts.push(<span key={keyIdx++}>{remaining.substring(0, first.index)}</span>);
      }

      if (first.type === "code") {
        parts.push(
          <code key={keyIdx++} className="px-1.5 py-0.5 rounded bg-white/5 font-mono text-xs text-primary">
            {first.match[1]}
          </code>
        );
      } else if (first.type === "bold") {
        parts.push(<strong key={keyIdx++} className="font-extrabold text-foreground">{first.match[1]}</strong>);
      } else if (first.type === "italic") {
        parts.push(<em key={keyIdx++} className="italic text-foreground/90">{first.match[1]}</em>);
      }

      remaining = remaining.substring(first.index + first.match[0].length);
    }

    return parts;
  }

  return (
    <div className={cn("space-y-4 text-sm text-foreground/90 leading-relaxed", className)}>
      {blocks.map((block, bIdx) => {
        if (block.type === "code") {
          return (
            <div key={bIdx} className="rounded-xl border border-white/10 overflow-hidden my-4 bg-sidebar/50 backdrop-blur-sm">
              <div className="flex items-center justify-between px-4 py-1.5 bg-white/5 border-b border-white/10">
                <span className="text-[10px] uppercase font-bold text-muted-foreground tracking-wider">{block.language}</span>
              </div>
              <pre className="p-4 overflow-x-auto text-xs font-mono text-emerald-400/90 leading-tight">
                <code>{block.code}</code>
              </pre>
            </div>
          );
        }

        if (block.type === "table") {
          return (
            <div key={bIdx} className="rounded-xl border border-white/10 overflow-hidden my-4">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-white/5 border-b border-white/10">
                    {block.headers.map((h, hIdx) => (
                      <th key={hIdx} className="px-4 py-2 text-xs font-semibold text-muted-foreground">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {block.rows.map((row, rIdx) => (
                    <tr key={rIdx} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                      {row.map((cell, cIdx) => (
                        <td key={cIdx} className="px-4 py-2 text-xs text-foreground/95">{formatInlineText(cell)}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          );
        }

        if (block.type === "list") {
          const Tag = block.ordered ? "ol" : "ul";
          return (
            <Tag key={bIdx} className={cn("pl-6 space-y-1.5 my-2 list-outside", block.ordered ? "list-decimal" : "list-disc")}>
              {block.items.map((item, itemIdx) => (
                <li key={itemIdx} className="text-foreground/90">{formatInlineText(item)}</li>
              ))}
            </Tag>
          );
        }

        const isLastParagraph = bIdx === blocks.length - 1;
        return (
          <p key={bIdx} className="text-foreground/90">
            {formatInlineText(block.text)}
            {isLastParagraph && isStreaming && (
              <span className="inline-block w-1.5 h-4 ml-1 bg-primary animate-pulse align-middle" />
            )}
          </p>
        );
      })}
    </div>
  );
}
