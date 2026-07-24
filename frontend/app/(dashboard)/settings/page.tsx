"use client";

import { useState } from "react";
import { Sliders, Cpu, Bell, ShieldAlert, Compass, Globe, LogOut, Trash2 } from "lucide-react";
import { useSettings } from "@/hooks/useSettings";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { toast } from "sonner";
import { cn } from "@/lib/utils";

const THEMES = [
  {
    id: "eclipse",
    name: "Eclipse",
    badge: "Professional",
    desc: "A deep slate cosmic interface with starlight gold accents and indigo depth.",
    bgClass: "bg-[#090b10]",
    meshClass: "bg-[radial-gradient(ellipse_at_top_right,var(--indigo)/30%,transparent_70%)]",
    colorDot: "bg-indigo-500",
  },
  {
    id: "aurora-forest",
    name: "Aurora Forest",
    badge: "Mystical",
    desc: "An organic theme rich in moss green glass layers, emerald glows, and forest air.",
    bgClass: "bg-[#09100d]",
    meshClass: "bg-[radial-gradient(ellipse_at_top_right,oklch(0.70_0.16_160)/30%,transparent_70%)]",
    colorDot: "bg-emerald-500",
  },
  {
    id: "solar-ember",
    name: "Solar Ember",
    badge: "Powerful",
    desc: "Obsidian backgrounds paired with crimson embers, orange smoke, and solar fire.",
    bgClass: "bg-[#0a0706]",
    meshClass: "bg-[radial-gradient(ellipse_at_top_right,oklch(0.68_0.22_28)/35%,transparent_70%)]",
    colorDot: "bg-orange-500",
  },
  {
    id: "celestial-ocean",
    name: "Celestial Ocean",
    badge: "Oceanic",
    desc: "Deep sapphire maritime depths, marine glass filters, and cyan bioluminescence.",
    bgClass: "bg-[#060a12]",
    meshClass: "bg-[radial-gradient(ellipse_at_top_right,oklch(0.65_0.16_220)/30%,transparent_70%)]",
    colorDot: "bg-cyan-500",
  },
  {
    id: "royal-ivory",
    name: "Royal Ivory",
    badge: "Luxury",
    desc: "Frosted champagne white glass, luxury cream/ivory backings, and gold typography.",
    bgClass: "bg-[#fcfbf9] border border-stone-200",
    meshClass: "bg-[radial-gradient(ellipse_at_top_right,oklch(0.74_0.11_75)/20%,transparent_70%)]",
    colorDot: "bg-amber-600",
  },
];

const TIMEZONES = [
  "Asia/Kolkata",
  "America/New_York",
  "Europe/London",
  "Asia/Singapore",
  "Australia/Sydney",
  "America/Los_Angeles",
];

const LANGUAGES = [
  { value: "en", label: "English" },
  { value: "hi", label: "Hindi" },
  { value: "sa", label: "Sanskrit" },
];

const DATE_FORMATS = [
  { value: "YYYY-MM-DD", label: "YYYY-MM-DD (e.g. 2026-07-13)" },
  { value: "DD/MM/YYYY", label: "DD/MM/YYYY (e.g. 13/07/2026)" },
  { value: "MM/DD/YYYY", label: "MM/DD/YYYY (e.g. 07/13/2026)" },
];

const TIME_FORMATS = [
  { value: "HH:mm", label: "24-hour (e.g. 14:30)" },
  { value: "hh:mm A", label: "12-hour (e.g. 02:30 PM)" },
];

const AI_MODELS = [
  { value: "gemini-flash-latest", label: "Google Gemini Flash (Default & Fast)" },
  { value: "gemini-2.5-flash", label: "Google Gemini 2.5 Flash" },
  { value: "gemini-2.0-flash", label: "Google Gemini 2.0 Flash" },
  { value: "openai/gpt-4o-mini", label: "OpenRouter — GPT-4o Mini" },
  { value: "anthropic/claude-3.5-sonnet", label: "OpenRouter — Claude 3.5 Sonnet" },
  { value: "meta-llama/llama-3.3-70b-instruct", label: "OpenRouter — Llama 3.3 70B" },
  { value: "gpt-4o-mini", label: "OpenAI Direct — GPT-4o Mini" },
  { value: "gpt-4o", label: "OpenAI Direct — GPT-4o" },
  { value: "claude-3-5-sonnet-20241022", label: "Anthropic Direct — Claude 3.5 Sonnet" },
  { value: "claude-3-haiku-20240307", label: "Anthropic Direct — Claude 3 Haiku" },
];

const RESPONSE_LENGTHS = [
  { value: "short", label: "Concise" },
  { value: "medium", label: "Standard Balanced" },
  { value: "long", label: "Extensive Analysis" },
];

const AYANAMSAS = ["Lahiri", "Raman", "Krishnamurti", "True Chitra"];

const HOUSE_SYSTEMS = [
  { value: "1", label: "Placidus" },
  { value: "2", label: "Whole Sign" },
  { value: "3", label: "Equal House" },
];

const CHART_STYLES = ["North Indian", "South Indian", "East Indian"];

const DIVISIONAL_CHARTS = [
  { value: "D1", label: "D1 - Rashi (Natal Chart)" },
  { value: "D9", label: "D9 - Navamsha (Spouse & Dharma)" },
  { value: "D60", label: "D60 - Shastiamsa (Past Karma)" },
];

export default function SettingsPage() {
  const {
    settings,
    isLoading,
    isError,
    error,
    updateSettings,
    isSaving,
    deleteAccount,
    isDeleting,
    logoutAll,
    isLoggingOutAll,
  } = useSettings();

  const [deleteConfirmText, setDeleteConfirmText] = useState("");
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [localTemp, setLocalTemp] = useState<number>(() => settings?.ai?.temperature ?? 0.7);

  if (isLoading) {
    return (
      <div className="p-6 max-w-4xl mx-auto space-y-6">
        <Skeleton className="h-10 w-96 rounded-xl" />
        <Skeleton className="h-80 w-full rounded-2xl" />
      </div>
    );
  }

  if (isError || !settings) {
    return (
      <div className="p-6 max-w-4xl mx-auto">
        <Alert variant="destructive">
          <ShieldAlert className="h-4 w-4" />
          <AlertTitle>Settings Failed to Load</AlertTitle>
          <AlertDescription>
            {error instanceof Error ? error.message : "Failed to load preferences."}
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  const handleUpdate = (section: string, field: string, value: unknown) => {
    updateSettings({
      [section]: {
        [field]: value,
      },
    });
  };

  const handleDeleteAccountSubmit = () => {
    if (deleteConfirmText !== "DELETE") {
      toast.error("Please type 'DELETE' exactly to confirm.");
      return;
    }
    deleteAccount();
    setIsDeleteDialogOpen(false);
  };

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      <div className="pb-4 border-b border-white/10">
        <h1 className="text-3xl font-bold tracking-tight text-foreground">Preferences & Settings</h1>
        <p className="text-sm text-muted-foreground mt-1">Configure your Vedic chart rules, notification routes, and AI configurations.</p>
      </div>

      <Tabs defaultValue="general" className="w-full">
        <TabsList className="grid grid-cols-5 w-full bg-sidebar/10 border border-white/10 p-1 rounded-xl h-auto">
          <TabsTrigger value="general" className="gap-2 py-2.5 rounded-lg data-[state=active]:bg-primary/10 data-[state=active]:text-primary">
            <Sliders className="size-4" />
            <span className="hidden sm:inline">General</span>
          </TabsTrigger>
          <TabsTrigger value="ai" className="gap-2 py-2.5 rounded-lg data-[state=active]:bg-primary/10 data-[state=active]:text-primary">
            <Cpu className="size-4" />
            <span className="hidden sm:inline">AI Engine</span>
          </TabsTrigger>
          <TabsTrigger value="astrology" className="gap-2 py-2.5 rounded-lg data-[state=active]:bg-primary/10 data-[state=active]:text-primary">
            <Compass className="size-4" />
            <span className="hidden sm:inline">Astrology</span>
          </TabsTrigger>
          <TabsTrigger value="notifications" className="gap-2 py-2.5 rounded-lg data-[state=active]:bg-primary/10 data-[state=active]:text-primary">
            <Bell className="size-4" />
            <span className="hidden sm:inline">Alerts</span>
          </TabsTrigger>
          <TabsTrigger value="account" className="gap-2 py-2.5 rounded-lg data-[state=active]:bg-primary/10 data-[state=active]:text-primary">
            <ShieldAlert className="size-4" />
            <span className="hidden sm:inline">Account</span>
          </TabsTrigger>
        </TabsList>

        {/* GENERAL PREFERENCES */}
        <TabsContent value="general">
          <Card className="glass-card border-white/10 mt-4 bg-sidebar/5 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="text-xl font-bold flex items-center gap-2">
                <Globe className="size-5 text-primary" /> General Preferences
              </CardTitle>
              <CardDescription>Visual interface, timezone, and calendar date rules.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3">
                <Label>Application Theme</Label>
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                  {THEMES.map((t) => {
                    const isActive = settings.general.theme === t.id;
                    return (
                      <button
                        key={t.id}
                        type="button"
                        onClick={() => handleUpdate("general", "theme", t.id)}
                        disabled={isSaving}
                        className={cn(
                          "group relative flex flex-col overflow-hidden rounded-xl border text-left transition-all duration-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50 cursor-pointer",
                          isActive
                            ? "border-primary bg-primary/10 shadow-lg ring-1 ring-primary"
                            : "border-white/10 bg-sidebar/20 hover:border-white/20 hover:bg-sidebar/40"
                        )}
                      >
                        {/* Miniature Theme Preview background */}
                        <div className={cn(
                          "relative h-20 w-full overflow-hidden border-b border-white/10",
                          t.bgClass
                        )}>
                          {/* Ambient mesh simulator */}
                          <div className={cn("absolute inset-0 opacity-40", t.meshClass)} />
                          
                          {/* Miniature glass card simulator */}
                          <div className={cn(
                            "absolute inset-x-3 bottom-2 top-4 rounded-md border shadow-sm backdrop-blur-sm flex items-center justify-between px-2.5",
                            t.id === "royal-ivory" 
                              ? "border-amber-600/20 bg-stone-50/50" 
                              : "border-white/10 bg-white/5"
                          )}>
                            <span className={cn(
                              "text-[10px] font-semibold",
                              t.id === "royal-ivory" ? "text-stone-850" : "text-white/80"
                            )}>Glass Card</span>
                            <div className={cn("size-2 rounded-full", t.colorDot)} />
                          </div>
                        </div>

                        {/* Title & Description */}
                        <div className="p-3 space-y-1">
                          <div className="flex items-center justify-between">
                            <span className="text-sm font-bold text-foreground">{t.name}</span>
                            <span className="text-[9px] uppercase font-bold tracking-wider text-primary">{t.badge}</span>
                          </div>
                          <p className="text-xs text-muted-foreground leading-snug">{t.desc}</p>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="language">Preferred Interface Language</Label>
                <Select
                  value={settings.general.language}
                  onValueChange={(val) => handleUpdate("general", "language", val)}
                  disabled={isSaving}
                >
                  <SelectTrigger id="language">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {LANGUAGES.map((lang) => (
                      <SelectItem key={lang.value} value={lang.value}>
                        {lang.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="timezone">Default Database Timezone</Label>
                <Select
                  value={settings.general.timezone}
                  onValueChange={(val) => handleUpdate("general", "timezone", val)}
                  disabled={isSaving}
                >
                  <SelectTrigger id="timezone">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {TIMEZONES.map((tz) => (
                      <SelectItem key={tz} value={tz}>
                        {tz}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="date_format">Date Format</Label>
                  <Select
                    value={settings.general.date_format}
                    onValueChange={(val) => handleUpdate("general", "date_format", val)}
                    disabled={isSaving}
                  >
                    <SelectTrigger id="date_format">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {DATE_FORMATS.map((fmt) => (
                        <SelectItem key={fmt.value} value={fmt.value}>
                          {fmt.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="time_format">Time Format</Label>
                  <Select
                    value={settings.general.time_format}
                    onValueChange={(val) => handleUpdate("general", "time_format", val)}
                    disabled={isSaving}
                  >
                    <SelectTrigger id="time_format">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {TIME_FORMATS.map((fmt) => (
                        <SelectItem key={fmt.value} value={fmt.value}>
                          {fmt.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* AI ENGINE PREFERENCES */}
        <TabsContent value="ai">
          <Card className="glass-card border-white/10 mt-4 bg-sidebar/5 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="text-xl font-bold flex items-center gap-2">
                <Cpu className="size-5 text-primary" /> AI Model Parameters
              </CardTitle>
              <CardDescription>Calibrate generative insights, streaming, and response sizes.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="ai_model">Default Reasoning Model</Label>
                <Select
                  value={
                    settings?.ai?.default_ai_model &&
                    AI_MODELS.some((m) => m.value === settings.ai.default_ai_model)
                      ? settings.ai.default_ai_model
                      : "gemini-flash-latest"
                  }
                  onValueChange={(val) => handleUpdate("ai", "default_ai_model", val)}
                  disabled={isSaving}
                >
                  <SelectTrigger id="ai_model">
                    <SelectValue placeholder="Google Gemini Flash (Default & Fast)" />
                  </SelectTrigger>
                  <SelectContent>
                    {AI_MODELS.map((model) => (
                      <SelectItem key={model.value} value={model.value}>
                        {model.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="response_length">Insight Detail Level</Label>
                <Select
                  value={settings.ai.response_length}
                  onValueChange={(val) => handleUpdate("ai", "response_length", val)}
                  disabled={isSaving}
                >
                  <SelectTrigger id="response_length">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {RESPONSE_LENGTHS.map((len) => (
                      <SelectItem key={len.value} value={len.value}>
                        {len.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="flex items-center justify-between p-3 rounded-lg border border-white/5 bg-white/5">
                <div className="space-y-0.5">
                  <Label htmlFor="streaming" className="text-sm font-semibold">Enable Token Streaming</Label>
                  <p className="text-xs text-muted-foreground">Stream AI responses letter-by-letter in real time.</p>
                </div>
                <Checkbox
                  id="streaming"
                  checked={settings.ai.streaming_toggle}
                  onCheckedChange={(checked) => handleUpdate("ai", "streaming_toggle", !!checked)}
                  disabled={isSaving}
                />
              </div>

              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <Label htmlFor="temperature" className="text-sm font-semibold">Creativity Temperature ({localTemp})</Label>
                  <span className="text-xs text-muted-foreground">{localTemp <= 0.4 ? "Deterministic" : localTemp >= 1.0 ? "Creative" : "Balanced"}</span>
                </div>
                <Input
                  id="temperature"
                  type="range"
                  min="0.0"
                  max="1.5"
                  step="0.1"
                  value={localTemp}
                  onChange={(e) => setLocalTemp(parseFloat(e.target.value))}
                  onMouseUp={() => handleUpdate("ai", "temperature", localTemp)}
                  onTouchEnd={() => handleUpdate("ai", "temperature", localTemp)}
                  disabled={isSaving}
                  className="h-2 p-0 bg-secondary accent-primary border-none cursor-pointer"
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* ASTROLOGY RULES */}
        <TabsContent value="astrology">
          <Card className="glass-card border-white/10 mt-4 bg-sidebar/5 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="text-xl font-bold flex items-center gap-2">
                <Compass className="size-5 text-primary" /> Astrology & Chart Rules
              </CardTitle>
              <CardDescription>Fine-tune ephemeris offset adjustments and chart projections.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="ayanamsa">Default Calculation Ayanamsa</Label>
                <Select
                  value={settings.astrology.default_ayanamsa}
                  onValueChange={(val) => handleUpdate("astrology", "default_ayanamsa", val)}
                  disabled={isSaving}
                >
                  <SelectTrigger id="ayanamsa">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {AYANAMSAS.map((ay) => (
                      <SelectItem key={ay} value={ay}>
                        {ay}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="house_system">Zodiac House Division</Label>
                <Select
                  value={String(settings.astrology.house_system)}
                  onValueChange={(val) => handleUpdate("astrology", "house_system", parseInt(val))}
                  disabled={isSaving}
                >
                  <SelectTrigger id="house_system">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {HOUSE_SYSTEMS.map((sys) => (
                      <SelectItem key={sys.value} value={sys.value}>
                        {sys.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="chart_style">Preferred Projection Grid</Label>
                <Select
                  value={settings.astrology.preferred_chart_style}
                  onValueChange={(val) => handleUpdate("astrology", "preferred_chart_style", val)}
                  disabled={isSaving}
                >
                  <SelectTrigger id="chart_style">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {CHART_STYLES.map((style) => (
                      <SelectItem key={style} value={style}>
                        {style}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="divisional">Main Divisional View</Label>
                <Select
                  value={settings.astrology.default_divisional_chart}
                  onValueChange={(val) => handleUpdate("astrology", "default_divisional_chart", val)}
                  disabled={isSaving}
                >
                  <SelectTrigger id="divisional">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {DIVISIONAL_CHARTS.map((chart) => (
                      <SelectItem key={chart.value} value={chart.value}>
                        {chart.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* ALERTS & NOTIFICATIONS */}
        <TabsContent value="notifications">
          <Card className="glass-card border-white/10 mt-4 bg-sidebar/5 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="text-xl font-bold flex items-center gap-2">
                <Bell className="size-5 text-primary" /> Notification Preferences
              </CardTitle>
              <CardDescription>Configure opt-in targets for our upcoming notification engine.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-start gap-3 p-3 rounded-lg border border-white/5 bg-white/5 opacity-85">
                <Checkbox
                  id="email_notif"
                  checked={settings.notifications.email_notifications}
                  onCheckedChange={(checked) => handleUpdate("notifications", "email_notifications", !!checked)}
                  disabled={isSaving}
                  className="mt-1"
                />
                <div className="grid gap-1.5 leading-none">
                  <Label htmlFor="email_notif" className="text-sm font-semibold cursor-pointer flex items-center gap-1">
                    Vedic Transit Summaries <span className="text-[10px] bg-primary/25 text-primary px-1.5 py-0.5 rounded-full font-normal leading-none">Coming Soon</span>
                  </Label>
                  <p className="text-xs text-muted-foreground">Receive weekly emails on planetary transits and yogas affecting your charts.</p>
                </div>
              </div>

              <div className="flex items-start gap-3 p-3 rounded-lg border border-white/5 bg-white/5 opacity-85">
                <Checkbox
                  id="prod_updates"
                  checked={settings.notifications.product_updates}
                  onCheckedChange={(checked) => handleUpdate("notifications", "product_updates", !!checked)}
                  disabled={isSaving}
                  className="mt-1"
                />
                <div className="grid gap-1.5 leading-none">
                  <Label htmlFor="prod_updates" className="text-sm font-semibold cursor-pointer flex items-center gap-1">
                    Product Updates <span className="text-[10px] bg-primary/25 text-primary px-1.5 py-0.5 rounded-full font-normal leading-none">Coming Soon</span>
                  </Label>
                  <p className="text-xs text-muted-foreground">Get notified when new divisional calculators or features are introduced.</p>
                </div>
              </div>

              <div className="flex items-start gap-3 p-3 rounded-lg border border-white/5 bg-white/5 opacity-85">
                <Checkbox
                  id="marketing"
                  checked={settings.notifications.marketing_emails}
                  onCheckedChange={(checked) => handleUpdate("notifications", "marketing_emails", !!checked)}
                  disabled={isSaving}
                  className="mt-1"
                />
                <div className="grid gap-1.5 leading-none">
                  <Label htmlFor="marketing" className="text-sm font-semibold cursor-pointer flex items-center gap-1">
                    Marketing & Offers <span className="text-[10px] bg-primary/25 text-primary px-1.5 py-0.5 rounded-full font-normal leading-none">Coming Soon</span>
                  </Label>
                  <p className="text-xs text-muted-foreground">Receive promotional insights and partner astrometric offerings.</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* ACCOUNT MANAGEMENT */}
        <TabsContent value="account">
          <Card className="glass-card border-destructive/20 mt-4 bg-destructive/5 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="text-xl font-bold flex items-center gap-2 text-destructive">
                <ShieldAlert className="size-5" /> Account & Security
              </CardTitle>
              <CardDescription>Revoke access tokens or permanently remove account credentials.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="p-4 rounded-xl border border-white/10 bg-sidebar/30 space-y-4">
                <div className="space-y-1">
                  <h3 className="text-sm font-semibold text-foreground">Logout from All Devices</h3>
                  <p className="text-xs text-muted-foreground">Terminates other active sessions and refreshes security access checks.</p>
                </div>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => logoutAll()}
                  disabled={isLoggingOutAll}
                  className="gap-2"
                >
                  <LogOut className="size-4" />
                  Logout All Devices
                </Button>
              </div>

              <div className="p-4 rounded-xl border border-destructive/25 bg-destructive/10 space-y-4">
                <div className="space-y-1">
                  <h3 className="text-sm font-semibold text-destructive">Delete Account</h3>
                  <p className="text-xs text-muted-foreground">Permanently drops your credentials, history, and transit details. This action is irreversible.</p>
                </div>

                <Dialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
                  <DialogTrigger asChild>
                    <Button
                      type="button"
                      variant="destructive"
                      className="gap-2 bg-destructive hover:bg-destructive/90 text-destructive-foreground"
                    >
                      <Trash2 className="size-4" />
                      Delete Account
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="glass-card border-white/15 bg-background/95 max-w-md">
                    <DialogHeader>
                      <DialogTitle className="text-xl font-bold text-destructive flex items-center gap-2">
                        <Trash2 className="size-5" /> Permanent Account Deletion
                      </DialogTitle>
                      <DialogDescription className="text-sm mt-2 text-muted-foreground">
                        This action cannot be undone. All transit configs, saved natal coordinates, and payment records will be permanently dropped.
                      </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-2 py-4">
                      <Label htmlFor="confirm_input" className="text-sm font-medium">To confirm, type <span className="font-bold text-foreground select-none">DELETE</span> below:</Label>
                      <Input
                        id="confirm_input"
                        placeholder="Type DELETE"
                        value={deleteConfirmText}
                        onChange={(e) => setDeleteConfirmText(e.target.value)}
                        className="bg-background/50"
                      />
                    </div>
                    <DialogFooter className="gap-2">
                      <Button
                        type="button"
                        variant="outline"
                        onClick={() => setIsDeleteDialogOpen(false)}
                      >
                        Cancel
                      </Button>
                      <Button
                        type="button"
                        variant="destructive"
                        onClick={handleDeleteAccountSubmit}
                        disabled={isDeleting || deleteConfirmText !== "DELETE"}
                        className="bg-destructive hover:bg-destructive/90"
                      >
                        {isDeleting ? "Deleting..." : "Permanently Delete"}
                      </Button>
                    </DialogFooter>
                  </DialogContent>
                </Dialog>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
