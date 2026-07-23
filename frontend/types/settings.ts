export interface GeneralSettings {
  theme: string;
  language: string;
  timezone: string;
  date_format: string;
  time_format: string;
}

export interface AISettings {
  default_ai_model: string;
  response_length: string;
  streaming_toggle: boolean;
  temperature: number;
}

export interface AstrologySettings {
  default_ayanamsa: string;
  house_system: number;
  preferred_chart_style: string;
  default_divisional_chart: string;
}

export interface NotificationSettings {
  email_notifications: boolean;
  product_updates: boolean;
  marketing_emails: boolean;
}

export interface UserSettings {
  general: GeneralSettings;
  ai: AISettings;
  astrology: AstrologySettings;
  notifications: NotificationSettings;
}

export interface UserSettingsUpdate {
  general?: Partial<GeneralSettings>;
  ai?: Partial<AISettings>;
  astrology?: Partial<AstrologySettings>;
  notifications?: Partial<NotificationSettings>;
}
