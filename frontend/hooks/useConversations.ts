import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ConversationService } from "@/services/conversation";
import { ConversationListItem, ConversationResponse } from "@/types/conversation";
import { toast } from "sonner";

export const CONVERSATIONS_QUERY_KEY = ["conversations"] as const;

export function useConversations(limit: number = 20, offset: number = 0, search?: string) {
  const queryClient = useQueryClient();

  // Fetch list of conversations
  const {
    data: conversations,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery<ConversationListItem[], Error>({
    queryKey: [...CONVERSATIONS_QUERY_KEY, { limit, offset, search }],
    queryFn: () => ConversationService.getConversations(limit, offset, search),
    staleTime: 30 * 1000, // 30 seconds
  });

  // Rename Mutation
  const renameMutation = useMutation<
    ConversationListItem,
    Error,
    { id: string; title: string }
  >({
    mutationFn: ({ id, title }) => ConversationService.renameConversation(id, title),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CONVERSATIONS_QUERY_KEY });
      toast.success("Conversation renamed successfully.");
    },
    onError: (err) => {
      toast.error(err.message || "Failed to rename conversation.");
    },
  });

  // Delete Mutation
  const deleteMutation = useMutation<void, Error, string>({
    mutationFn: (id) => ConversationService.deleteConversation(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CONVERSATIONS_QUERY_KEY });
      toast.success("Conversation deleted successfully.");
    },
    onError: (err) => {
      toast.error(err.message || "Failed to delete conversation.");
    },
  });

  return {
    conversations,
    isLoading,
    isError,
    error,
    refetch,
    renameConversation: renameMutation.mutate,
    isRenaming: renameMutation.isPending,
    deleteConversation: deleteMutation.mutate,
    isDeleting: deleteMutation.isPending,
  };
}

export function useConversationDetails(id: string | null) {
  return useQuery<ConversationResponse | null, Error>({
    queryKey: [...CONVERSATIONS_QUERY_KEY, "detail", id],
    queryFn: () => (id ? ConversationService.getConversation(id) : Promise.resolve(null)),
    enabled: !!id,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}
