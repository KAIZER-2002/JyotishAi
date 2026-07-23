"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useConversations } from "@/hooks/useConversations";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { 
  MessageSquare, 
  Compass, 
  Activity, 
  Search, 
  Trash2, 
  Edit2, 
  Calendar, 
  Clock, 
  ArrowRight, 
  Check, 
  X, 
  ChevronLeft, 
  ChevronRight, 
  Sparkles,
  Inbox,
  AlertCircle
} from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";

interface LocalHistoryEntry {
  id: string;
  date: string;
  latitude: number;
  longitude: number;
  timezone: string;
  ayanamsa: string;
  house_system: number;
  created_at: string;
}

export default function HistoryPage() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<"consultations" | "charts" | "analyses">("consultations");

  // ── Consultations (Chat History) State ─────────────────────────────────────
  const [chatSearch, setChatSearch] = useState("");
  const [chatPage, setChatPage] = useState(0);
  const itemsPerPage = 8;

  const {
    conversations = [],
    isLoading: isChatsLoading,
    isError: isChatsError,
    renameConversation,
    deleteConversation,
    refetch: refetchConversations,
  } = useConversations(itemsPerPage, chatPage * itemsPerPage, chatSearch || undefined);

  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState("");

  // Re-fetch conversations when page changes
  useEffect(() => {
    refetchConversations();
  }, [chatPage, refetchConversations]);

  // Handle Search Input (simple debouncing or manual trigger)
  const handleChatSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setChatPage(0);
    refetchConversations();
  };

  const handleStartRename = (id: string, currentTitle: string) => {
    setEditingId(id);
    setEditTitle(currentTitle);
  };

  const handleSaveRename = (id: string) => {
    if (!editTitle.trim()) {
      toast.error("Title cannot be empty.");
      return;
    }
    renameConversation({ id, title: editTitle.trim() });
    setEditingId(null);
  };

  const handleDeleteChat = (id: string) => {
    const confirm = window.confirm("Are you sure you want to delete this conversation?");
    if (confirm) {
      deleteConversation(id);
    }
  };

  // ── Birth Charts & Analyses Local Storage State ────────────────────────────
  const [localCharts, setLocalCharts] = useState<LocalHistoryEntry[]>(() => {
    if (typeof window === "undefined") return [];
    try {
      return JSON.parse(localStorage.getItem("jyotishai_chart_history") || "[]");
    } catch {
      return [];
    }
  });
  const [chartSearch, setChartSearch] = useState("");
  const [chartPage, setChartPage] = useState(0);

  const [localAnalyses, setLocalAnalyses] = useState<LocalHistoryEntry[]>(() => {
    if (typeof window === "undefined") return [];
    try {
      return JSON.parse(localStorage.getItem("jyotishai_analysis_history") || "[]");
    } catch {
      return [];
    }
  });
  const [analysisSearch, setAnalysisSearch] = useState("");
  const [analysisPage, setAnalysisPage] = useState(0);

  // Filter & Paginate Local Charts
  const filteredCharts = localCharts.filter((c) => {
    const term = chartSearch.toLowerCase();
    if (!term) return true;
    const formattedDate = new Date(c.date).toLocaleDateString(undefined, {
      dateStyle: "medium",
    });
    return (
      c.timezone.toLowerCase().includes(term) ||
      c.ayanamsa.toLowerCase().includes(term) ||
      formattedDate.toLowerCase().includes(term) ||
      String(c.latitude).includes(term) ||
      String(c.longitude).includes(term)
    );
  });

  const paginatedCharts = filteredCharts.slice(
    chartPage * itemsPerPage,
    (chartPage + 1) * itemsPerPage
  );

  const handleDeleteChart = (id: string) => {
    const confirm = window.confirm("Are you sure you want to delete this chart entry?");
    if (!confirm) return;

    const updated = localCharts.filter((c) => c.id !== id);
    setLocalCharts(updated);
    localStorage.setItem("jyotishai_chart_history", JSON.stringify(updated));
    toast.success("Birth chart entry removed.");
  };

  const handleViewChart = (c: LocalHistoryEntry) => {
    const params = new URLSearchParams({
      date: c.date,
      latitude: String(c.latitude),
      longitude: String(c.longitude),
      timezone: c.timezone,
      ayanamsa: c.ayanamsa,
      house_system: String(c.house_system),
    });
    // For D1/divisional view, we set state in chart page or query parameters
    router.push(`/chart?${params.toString()}`);
  };

  // Filter & Paginate Local Analyses
  const filteredAnalyses = localAnalyses.filter((a) => {
    const term = analysisSearch.toLowerCase();
    if (!term) return true;
    const formattedDate = new Date(a.date).toLocaleDateString(undefined, {
      dateStyle: "medium",
    });
    return (
      a.timezone.toLowerCase().includes(term) ||
      a.ayanamsa.toLowerCase().includes(term) ||
      formattedDate.toLowerCase().includes(term) ||
      String(a.latitude).includes(term) ||
      String(a.longitude).includes(term)
    );
  });

  const paginatedAnalyses = filteredAnalyses.slice(
    analysisPage * itemsPerPage,
    (analysisPage + 1) * itemsPerPage
  );

  const handleDeleteAnalysis = (id: string) => {
    const confirm = window.confirm("Are you sure you want to delete this analysis entry?");
    if (!confirm) return;

    const updated = localAnalyses.filter((a) => a.id !== id);
    setLocalAnalyses(updated);
    localStorage.setItem("jyotishai_analysis_history", JSON.stringify(updated));
    toast.success("Astrometric analysis entry removed.");
  };

  const handleViewAnalysis = (a: LocalHistoryEntry) => {
    const params = new URLSearchParams({
      date: a.date,
      latitude: String(a.latitude),
      longitude: String(a.longitude),
      timezone: a.timezone,
      ayanamsa: a.ayanamsa,
      house_system: String(a.house_system),
    });
    router.push(`/analysis?${params.toString()}`);
  };

  function formatDate(isoStr: string) {
    return new Date(isoStr).toLocaleDateString(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
    });
  }

  return (
    <div className="space-y-8 py-6 max-w-6xl mx-auto px-4">
      <div className="space-y-1.5">
        <h1 className="text-3xl font-extrabold tracking-tight text-foreground bg-clip-text">
          Calculation History
        </h1>
        <p className="text-sm text-muted-foreground max-w-2xl leading-relaxed">
          Review your persistent AI chat consultations, previously computed birth charts, and comprehensive life-path analyses.
        </p>
      </div>

      <Tabs
        defaultValue="consultations"
        value={activeTab}
        onValueChange={(v) => setActiveTab(v as "consultations" | "charts" | "analyses")}
        className="w-full"
      >
        <TabsList className="grid grid-cols-3 max-w-md w-full bg-sidebar/35 border border-white/5 p-1 rounded-xl">
          <TabsTrigger value="consultations" className="rounded-lg gap-2 text-xs font-semibold py-2">
            <MessageSquare className="size-3.5" />
            <span>Consultations</span>
          </TabsTrigger>
          <TabsTrigger value="charts" className="rounded-lg gap-2 text-xs font-semibold py-2">
            <Compass className="size-3.5" />
            <span>Birth Charts</span>
          </TabsTrigger>
          <TabsTrigger value="analyses" className="rounded-lg gap-2 text-xs font-semibold py-2">
            <Activity className="size-3.5" />
            <span>Analyses</span>
          </TabsTrigger>
        </TabsList>

        {/* ── CONSULTATIONS TAB ───────────────────────────────────────────────── */}
        <TabsContent value="consultations" className="mt-6">
          <Card className="glass-card border-white/10 bg-sidebar/5 backdrop-blur-sm">
            <CardHeader className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4">
              <div>
                <CardTitle className="text-xl font-bold flex items-center gap-2">
                  <MessageSquare className="size-5 text-primary" /> Recent Consultations
                </CardTitle>
                <CardDescription>Click a thread to continue your diagnostic Vedic dialogue.</CardDescription>
              </div>
              <form onSubmit={handleChatSearchSubmit} className="flex items-center gap-2 max-w-xs w-full">
                <div className="relative flex-1">
                  <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                  <Input
                    type="search"
                    placeholder="Search titles..."
                    value={chatSearch}
                    onChange={(e) => setChatSearch(e.target.value)}
                    className="pl-9 bg-background/40"
                  />
                </div>
                <Button type="submit" variant="secondary" className="px-3 shrink-0">
                  Find
                </Button>
              </form>
            </CardHeader>

            <CardContent className="space-y-4">
              {isChatsLoading ? (
                <div className="space-y-3">
                  {[...Array(4)].map((_, i) => (
                    <div key={i} className="flex items-center justify-between p-4 rounded-xl border border-white/5 bg-white/5">
                      <div className="space-y-2 flex-1 max-w-md">
                        <Skeleton className="h-4 w-2/3" />
                        <Skeleton className="h-3 w-1/3" />
                      </div>
                      <Skeleton className="h-9 w-24 rounded-lg" />
                    </div>
                  ))}
                </div>
              ) : isChatsError ? (
                <div className="flex flex-col items-center justify-center py-12 border border-dashed border-destructive/25 rounded-2xl bg-destructive/5 text-center">
                  <AlertCircle className="size-8 text-destructive mb-2" />
                  <p className="text-sm font-semibold text-destructive">Failed to load consultations</p>
                  <p className="text-xs text-muted-foreground mt-1">Please check your internet connection and try again.</p>
                  <Button variant="outline" onClick={() => refetchConversations()} className="mt-4 gap-2">
                    Reload list
                  </Button>
                </div>
              ) : conversations.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-16 text-center border border-dashed border-white/10 rounded-2xl bg-white/[0.02]">
                  <Inbox className="size-10 text-muted-foreground/50 mb-3" />
                  <h3 className="text-sm font-bold text-foreground">No conversations found</h3>
                  <p className="text-xs text-muted-foreground mt-1 max-w-xs leading-relaxed">
                    {chatSearch ? "Try adjusting your search query filters." : "Launch a new chat session to generate readings."}
                  </p>
                  {!chatSearch && (
                    <Button onClick={() => router.push("/chat")} className="mt-4 gap-2">
                      <Sparkles className="size-4" /> Start New Chat
                    </Button>
                  )}
                </div>
              ) : (
                <div className="space-y-3">
                  {conversations.map((c) => (
                    <div
                      key={c.id}
                      className="group flex flex-col sm:flex-row sm:items-center justify-between p-4 rounded-xl border border-white/5 bg-white/[0.02] hover:bg-white/[0.05] hover:border-white/10 transition-all gap-4"
                    >
                      <div className="flex-1 space-y-1.5 overflow-hidden">
                        {editingId === c.id ? (
                          <div className="flex items-center gap-2 max-w-md">
                            <Input
                              value={editTitle}
                              onChange={(e) => setEditTitle(e.target.value)}
                              className="h-8 bg-background/50 text-sm py-1"
                              autoFocus
                            />
                            <Button size="icon" variant="ghost" onClick={() => handleSaveRename(c.id)} className="size-8 text-success hover:bg-success/10 shrink-0">
                              <Check className="size-4" />
                            </Button>
                            <Button size="icon" variant="ghost" onClick={() => setEditingId(null)} className="size-8 text-destructive hover:bg-destructive/10 shrink-0">
                              <X className="size-4" />
                            </Button>
                          </div>
                        ) : (
                          <h3 className="text-sm font-semibold text-foreground truncate pr-4">
                            {c.title}
                          </h3>
                        )}
                        <div className="flex items-center gap-4 text-xs text-muted-foreground">
                          <span className="flex items-center gap-1">
                            <Calendar className="size-3" />
                            {formatDate(c.updated_at)}
                          </span>
                        </div>
                      </div>

                      <div className="flex items-center justify-end gap-2">
                        {editingId !== c.id && (
                          <>
                            <Button
                              size="icon"
                              variant="ghost"
                              onClick={() => handleStartRename(c.id, c.title)}
                              className="size-9 rounded-lg hover:bg-white/10"
                              title="Rename conversation"
                            >
                              <Edit2 className="size-4 text-muted-foreground hover:text-foreground" />
                            </Button>
                            <Button
                              size="icon"
                              variant="ghost"
                              onClick={() => handleDeleteChat(c.id)}
                              className="size-9 rounded-lg hover:bg-destructive/10 hover:text-destructive"
                              title="Delete conversation"
                            >
                              <Trash2 className="size-4" />
                            </Button>
                          </>
                        )}
                        <Button
                          onClick={() => router.push(`/chat?conversationId=${c.id}`)}
                          variant="secondary"
                          className="gap-1.5 h-9 py-0 px-3 rounded-lg hover:bg-primary hover:text-primary-foreground transition-all"
                        >
                          <span>Continue</span>
                          <ArrowRight className="size-3.5" />
                        </Button>
                      </div>
                    </div>
                  ))}

                  {/* Pagination Footer */}
                  <div className="flex items-center justify-between pt-4 border-t border-white/5">
                    <span className="text-xs text-muted-foreground">
                      Showing page {chatPage + 1}
                    </span>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        disabled={chatPage === 0}
                        onClick={() => setChatPage((p) => p - 1)}
                        className="h-8 gap-1 rounded-lg"
                      >
                        <ChevronLeft className="size-4" /> Prev
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        disabled={conversations.length < itemsPerPage}
                        onClick={() => setChatPage((p) => p + 1)}
                        className="h-8 gap-1 rounded-lg"
                      >
                        Next <ChevronRight className="size-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* ── BIRTH CHARTS TAB ────────────────────────────────────────────────── */}
        <TabsContent value="charts" className="mt-6">
          <Card className="glass-card border-white/10 bg-sidebar/5 backdrop-blur-sm">
            <CardHeader className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4">
              <div>
                <CardTitle className="text-xl font-bold flex items-center gap-2">
                  <Compass className="size-5 text-primary" /> Generated Birth Charts
                </CardTitle>
                <CardDescription>Re-render previously computed divisional and planetary coordinates.</CardDescription>
              </div>
              <div className="relative max-w-xs w-full">
                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  type="search"
                  placeholder="Filter by timezone, date..."
                  value={chartSearch}
                  onChange={(e) => {
                    setChartSearch(e.target.value);
                    setChartPage(0);
                  }}
                  className="pl-9 bg-background/40"
                />
              </div>
            </CardHeader>

            <CardContent className="space-y-4">
              {filteredCharts.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-16 text-center border border-dashed border-white/10 rounded-2xl bg-white/[0.02]">
                  <Inbox className="size-10 text-muted-foreground/50 mb-3" />
                  <h3 className="text-sm font-bold text-foreground">No birth charts recorded</h3>
                  <p className="text-xs text-muted-foreground mt-1 max-w-xs leading-relaxed">
                    Compute a birth chart in the Chart tab to persist calculations.
                  </p>
                  <Button onClick={() => router.push("/chart")} className="mt-4 gap-2">
                    <Compass className="size-4" /> Compute Chart
                  </Button>
                </div>
              ) : (
                <div className="space-y-3">
                  {paginatedCharts.map((c) => (
                    <div
                      key={c.id}
                      className="group flex flex-col sm:flex-row sm:items-center justify-between p-4 rounded-xl border border-white/5 bg-white/[0.02] hover:bg-white/[0.05] hover:border-white/10 transition-all gap-4"
                    >
                      <div className="space-y-1 flex-1 overflow-hidden">
                        <h3 className="text-sm font-semibold text-foreground truncate">
                          Chart Config — {formatDate(c.date)}
                        </h3>
                        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground">
                          <span className="flex items-center gap-1">
                            <Clock className="size-3" />
                            {c.timezone}
                          </span>
                          <span>•</span>
                          <span>Ayanamsa: {c.ayanamsa}</span>
                          <span>•</span>
                          <span>Lat/Lng: {c.latitude.toFixed(4)}, {c.longitude.toFixed(4)}</span>
                        </div>
                      </div>

                      <div className="flex items-center justify-end gap-2">
                        <Button
                          size="icon"
                          variant="ghost"
                          onClick={() => handleDeleteChart(c.id)}
                          className="size-9 rounded-lg hover:bg-destructive/10 hover:text-destructive"
                          title="Delete entry"
                        >
                          <Trash2 className="size-4" />
                        </Button>
                        <Button
                          onClick={() => handleViewChart(c)}
                          variant="secondary"
                          className="gap-1.5 h-9 py-0 px-3 rounded-lg hover:bg-primary hover:text-primary-foreground transition-all"
                        >
                          <span>Render Chart</span>
                          <ArrowRight className="size-3.5" />
                        </Button>
                      </div>
                    </div>
                  ))}

                  {/* Pagination Footer */}
                  {filteredCharts.length > itemsPerPage && (
                    <div className="flex items-center justify-between pt-4 border-t border-white/5">
                      <span className="text-xs text-muted-foreground">
                        Showing page {chartPage + 1} of {Math.ceil(filteredCharts.length / itemsPerPage)}
                      </span>
                      <div className="flex items-center gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          disabled={chartPage === 0}
                          onClick={() => setChartPage((p) => p - 1)}
                          className="h-8 gap-1 rounded-lg"
                        >
                          <ChevronLeft className="size-4" /> Prev
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          disabled={(chartPage + 1) * itemsPerPage >= filteredCharts.length}
                          onClick={() => setChartPage((p) => p + 1)}
                          className="h-8 gap-1 rounded-lg"
                        >
                          Next <ChevronRight className="size-4" />
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* ── ANALYSES TAB ────────────────────────────────────────────────────── */}
        <TabsContent value="analyses" className="mt-6">
          <Card className="glass-card border-white/10 bg-sidebar/5 backdrop-blur-sm">
            <CardHeader className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4">
              <div>
                <CardTitle className="text-xl font-bold flex items-center gap-2">
                  <Activity className="size-5 text-primary" /> Astro-interpretive Analyses
                </CardTitle>
                <CardDescription>Reload previously calculated dasha periods, yogas, and interpretation sheets.</CardDescription>
              </div>
              <div className="relative max-w-xs w-full">
                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  type="search"
                  placeholder="Filter by timezone, date..."
                  value={analysisSearch}
                  onChange={(e) => {
                    setAnalysisSearch(e.target.value);
                    setAnalysisPage(0);
                  }}
                  className="pl-9 bg-background/40"
                />
              </div>
            </CardHeader>

            <CardContent className="space-y-4">
              {filteredAnalyses.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-16 text-center border border-dashed border-white/10 rounded-2xl bg-white/[0.02]">
                  <Inbox className="size-10 text-muted-foreground/50 mb-3" />
                  <h3 className="text-sm font-bold text-foreground">No analyses recorded</h3>
                  <p className="text-xs text-muted-foreground mt-1 max-w-xs leading-relaxed">
                    Compute a detailed analysis inside the Analysis tab to save progress.
                  </p>
                  <Button onClick={() => router.push("/analysis")} className="mt-4 gap-2">
                    <Activity className="size-4" /> Compute Analysis
                  </Button>
                </div>
              ) : (
                <div className="space-y-3">
                  {paginatedAnalyses.map((a) => (
                    <div
                      key={a.id}
                      className="group flex flex-col sm:flex-row sm:items-center justify-between p-4 rounded-xl border border-white/5 bg-white/[0.02] hover:bg-white/[0.05] hover:border-white/10 transition-all gap-4"
                    >
                      <div className="space-y-1 flex-1 overflow-hidden">
                        <h3 className="text-sm font-semibold text-foreground truncate">
                          Astro Analysis — {formatDate(a.date)}
                        </h3>
                        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground">
                          <span className="flex items-center gap-1">
                            <Clock className="size-3" />
                            {a.timezone}
                          </span>
                          <span>•</span>
                          <span>Ayanamsa: {a.ayanamsa}</span>
                          <span>•</span>
                          <span>Lat/Lng: {a.latitude.toFixed(4)}, {a.longitude.toFixed(4)}</span>
                        </div>
                      </div>

                      <div className="flex items-center justify-end gap-2">
                        <Button
                          size="icon"
                          variant="ghost"
                          onClick={() => handleDeleteAnalysis(a.id)}
                          className="size-9 rounded-lg hover:bg-destructive/10 hover:text-destructive"
                          title="Delete entry"
                        >
                          <Trash2 className="size-4" />
                        </Button>
                        <Button
                          onClick={() => handleViewAnalysis(a)}
                          variant="secondary"
                          className="gap-1.5 h-9 py-0 px-3 rounded-lg hover:bg-primary hover:text-primary-foreground transition-all"
                        >
                          <span>Reload Analysis</span>
                          <ArrowRight className="size-3.5" />
                        </Button>
                      </div>
                    </div>
                  ))}

                  {/* Pagination Footer */}
                  {filteredAnalyses.length > itemsPerPage && (
                    <div className="flex items-center justify-between pt-4 border-t border-white/5">
                      <span className="text-xs text-muted-foreground">
                        Showing page {analysisPage + 1} of {Math.ceil(filteredAnalyses.length / itemsPerPage)}
                      </span>
                      <div className="flex items-center gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          disabled={analysisPage === 0}
                          onClick={() => setAnalysisPage((p) => p - 1)}
                          className="h-8 gap-1 rounded-lg"
                        >
                          <ChevronLeft className="size-4" /> Prev
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          disabled={(analysisPage + 1) * itemsPerPage >= filteredAnalyses.length}
                          onClick={() => setAnalysisPage((p) => p + 1)}
                          className="h-8 gap-1 rounded-lg"
                        >
                          Next <ChevronRight className="size-4" />
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
