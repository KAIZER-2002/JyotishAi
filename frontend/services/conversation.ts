import { api } from "@/lib/api";
import { ConversationListItem, ConversationResponse } from "@/types/conversation";

/**
 * ConversationService handles REST requests for conversation history management.
 */
export const ConversationService = {
  /** List authenticated user's conversations with pagination and search. */
  async getConversations(
    limit: number = 20,
    offset: number = 0,
    search?: string
  ): Promise<ConversationListItem[]> {
    const response = await api.get<ConversationListItem[]>("/conversations", {
      params: { limit, offset, search },
    });
    return response.data;
  },

  /** Retrieve full messages for a specific conversation. */
  async getConversation(id: string): Promise<ConversationResponse> {
    const response = await api.get<ConversationResponse>(`/conversations/${id}`);
    return response.data;
  },

  /** Update conversation title. */
  async renameConversation(id: string, title: string): Promise<ConversationListItem> {
    const response = await api.patch<ConversationListItem>(`/conversations/${id}`, { title });
    return response.data;
  },

  /** Delete a conversation thread. */
  async deleteConversation(id: string): Promise<void> {
    await api.delete(`/conversations/${id}`);
  },
};
