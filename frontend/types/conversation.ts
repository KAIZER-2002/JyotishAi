export interface MessageResponse {
  id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

export interface ConversationResponse {
  id: string;
  title: string;
  user_id?: string;
  created_at: string;
  updated_at: string;
  messages: MessageResponse[];
}

export interface ConversationListItem {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}
