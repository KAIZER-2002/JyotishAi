"use client";

import { useState, useEffect, useMemo, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import ConversationSidebar from "@/components/chat/ConversationSidebar";
import ChatMessage from "@/components/chat/ChatMessage";
import ChatInput from "@/components/chat/ChatInput";
import TypingIndicator from "@/components/chat/TypingIndicator";
import AutoScrollContainer from "@/components/chat/AutoScrollContainer";
import { useChat } from "@/hooks/useChat";
import { useConversations } from "@/hooks/useConversations";
import { useProfile } from "@/hooks/useProfile";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { AlertCircle, Sparkles, Loader2 } from "lucide-react";
import BirthDataForm from "@/components/astrology/BirthDataForm";
import { BirthChartRequest, Ayanamsa } from "@/types/astrology";
import { BirthDataFormData } from "@/validations/astrology";

/** Inner component rendered once birth data is known. */
function ChatWithBirthData({
  birthData,
  initialConversationId,
}: {
  birthData: BirthChartRequest;
  initialConversationId: string | null;
}) {
  const router = useRouter();
  const [inputVal, setInputVal] = useState("");
  const {
    messages,
    conversationId,
    isGenerating,
    error,
    sendMessage,
    stopGeneration,
    retryGeneration,
  } = useChat(birthData, initialConversationId);

  // Fetch conversations from backend
  const { conversations = [], deleteConversation, refetch } = useConversations(30, 0);

  // Sync route URL when a new conversation is initialized by the stream
  useEffect(() => {
    if (conversationId && conversationId !== initialConversationId) {
      router.replace(`/chat?conversationId=${conversationId}`);
      refetch();
    }
  }, [conversationId, initialConversationId, router, refetch]);

  function handleSubmit() {
    if (!inputVal.trim()) return;
    sendMessage(inputVal);
    setInputVal("");
  }

  function handleSelectConversation(id: string) {
    router.push(`/chat?conversationId=${id}`);
  }

  function handleNewChat() {
    router.push("/chat");
  }

  async function handleDeleteConversation(id: string) {
    const confirmDelete = window.confirm("Are you sure you want to delete this conversation?");
    if (!confirmDelete) return;
    deleteConversation(id);
    if (id === conversationId || id === initialConversationId) {
      router.push("/chat");
    }
  }

  // Convert list to shape expected by Sidebar
  const sidebarConvs = conversations.map((c) => ({
    id: c.id,
    title: c.title,
  }));

  const activeId = conversationId || initialConversationId || undefined;

  return (
    <div className="flex h-[calc(100vh-8rem)] rounded-xl border border-white/10 overflow-hidden bg-sidebar/5 backdrop-blur-sm">
      {/* Sidebar - Hidden on mobile, shown on md and larger screens */}
      <ConversationSidebar
        conversations={sidebarConvs}
        activeId={activeId}
        onSelect={handleSelectConversation}
        onDelete={handleDeleteConversation}
        onNewChat={handleNewChat}
        className="hidden md:flex w-80 shrink-0"
      />

      {/* Chat Area */}
      <div className="flex-1 flex flex-col h-full bg-transparent">
        {/* Messages viewport */}
        <AutoScrollContainer className="flex-1 p-4 space-y-4">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center space-y-4 max-w-lg mx-auto py-12">
              <div className="flex size-12 items-center justify-center rounded-xl bg-primary/10 text-primary ring-1 ring-primary/20">
                <Sparkles className="size-6" />
              </div>
              <div className="space-y-2">
                <h3 className="text-xl font-bold text-foreground">Jyotish AI Assistant</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  Start a conversation to get deep Vedic insights about your birth chart, planetary transits, dasha sequences, and yoga activations.
                </p>
              </div>
              <div className="grid gap-2 w-full sm:grid-cols-2 text-left pt-4">
                <button
                  onClick={() => setInputVal("Explain the impact of my active Vimshottari Mahadasha.")}
                  className="p-3 text-xs rounded-xl border border-white/5 hover:border-white/15 bg-white/5 text-foreground hover:bg-white/10 transition-all font-medium text-left cursor-pointer"
                >
                  &ldquo;Explain my active Dasha period&rdquo; →
                </button>
                <button
                  onClick={() => setInputVal("What yogas are activated in my horoscope?")}
                  className="p-3 text-xs rounded-xl border border-white/5 hover:border-white/15 bg-white/5 text-foreground hover:bg-white/10 transition-all font-medium text-left cursor-pointer"
                >
                  &ldquo;What yogas are active in my chart?&rdquo; →
                </button>
              </div>
            </div>
          ) : (
            <div className="space-y-2">
              {messages.map((m, idx) => (
                <ChatMessage
                  key={idx}
                  role={m.role}
                  content={m.content}
                  isStreaming={m.isStreaming}
                  onRetry={idx === messages.length - 1 ? retryGeneration : undefined}
                />
              ))}

              {isGenerating && messages[messages.length - 1]?.role !== "assistant" && (
                <div className="flex gap-4 p-4 md:p-6 bg-sidebar/20 border-y border-white/5">
                  <div className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-amber-500/10 text-amber-500 ring-1 ring-amber-500/20">
                    <Sparkles className="size-4 animate-spin" />
                  </div>
                  <div className="flex-1 space-y-2">
                    <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                      Jyotish AI
                    </span>
                    <TypingIndicator />
                  </div>
                </div>
              )}
            </div>
          )}

          {error && (
            <div className="p-4 md:px-6">
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertTitle>Stream Failure</AlertTitle>
                <AlertDescription className="flex items-center justify-between">
                  <span>{error}</span>
                  <button
                    onClick={retryGeneration}
                    className="text-xs underline font-semibold hover:opacity-85"
                  >
                    Retry Query
                  </button>
                </AlertDescription>
              </Alert>
            </div>
          )}
        </AutoScrollContainer>

        {/* Input box */}
        <div className="p-4 border-t border-white/10 bg-sidebar/10">
          <ChatInput
            value={inputVal}
            onChange={setInputVal}
            onSubmit={handleSubmit}
            isGenerating={isGenerating}
            onStop={stopGeneration}
            className="max-w-3xl mx-auto"
          />
        </div>
      </div>
    </div>
  );
}

function ChatPageContent() {
  const searchParams = useSearchParams();
  const conversationId = searchParams.get("conversationId");

  const [customBirthData, setCustomBirthData] = useState<BirthChartRequest | null>(null);
  const [isLoadingChart, setIsLoadingChart] = useState(false);

  // Load user profile to check if birth details are already saved
  const { profile, isLoading: isProfileLoading, updateProfile } = useProfile();

  const birthData = useMemo<BirthChartRequest | null>(() => {
    if (customBirthData) return customBirthData;
    if (profile && profile.date_of_birth && profile.latitude !== null && profile.longitude !== null) {
      // Ensure time_of_birth is exactly HH:mm or HH:mm:ss. 
      // We can take the first 5 characters (HH:mm) and safely append :00
      const timeStr = profile.time_of_birth ? profile.time_of_birth.substring(0, 5) : "00:00";
      const birthDateTime = `${profile.date_of_birth}T${timeStr}:00`;
      
      return {
        date: new Date(birthDateTime).toISOString(),
        latitude: profile.latitude,
        longitude: profile.longitude,
        timezone: profile.timezone || "Asia/Kolkata",
        ayanamsa: (profile.ayanamsa as Ayanamsa) || "Lahiri",
        house_system: 1,
      };
    }
    return null;
  }, [customBirthData, profile]);

  function handleBirthDataSubmit(_result: unknown, formData: BirthDataFormData) {
    const request: BirthChartRequest = {
      date: new Date(formData.date).toISOString(),
      latitude: formData.latitude,
      longitude: formData.longitude,
      timezone: formData.timezone,
      ayanamsa: formData.ayanamsa as Ayanamsa,
      house_system: formData.house_system,
    };
    
    // Save to profile automatically so the user doesn't have to enter it again
    updateProfile({
      date_of_birth: formData.date.split("T")[0],
      time_of_birth: formData.date.includes("T") ? formData.date.split("T")[1].substring(0, 5) + ":00" : null,
      latitude: formData.latitude,
      longitude: formData.longitude,
      timezone: formData.timezone,
      ayanamsa: formData.ayanamsa,
    });
    
    setIsLoadingChart(false);
    setCustomBirthData(request);
  }

  if (isProfileLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[calc(100vh-8rem)]">
        <Loader2 className="size-8 text-primary animate-spin" />
        <span className="mt-2 text-sm text-muted-foreground">Loading practitioner details...</span>
      </div>
    );
  }

  if (!birthData) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[calc(100vh-8rem)] p-6 gap-6">
        <div className="text-center space-y-2 max-w-md">
          <h2 className="text-2xl font-bold tracking-tight">Enter Your Birth Details</h2>
          <p className="text-sm text-muted-foreground">
            Jyotish AI needs your birth information to generate personalised Vedic insights.
          </p>
        </div>
        <BirthDataForm onSubmit={handleBirthDataSubmit} isLoading={isLoadingChart} />
      </div>
    );
  }

  return <ChatWithBirthData birthData={birthData} initialConversationId={conversationId} />;
}

export default function ChatPage() {
  return (
    <Suspense
      fallback={
        <div className="flex flex-col items-center justify-center min-h-[calc(100vh-8rem)]">
          <Loader2 className="size-8 text-primary animate-spin" />
        </div>
      }
    >
      <ChatPageContent />
    </Suspense>
  );
}
