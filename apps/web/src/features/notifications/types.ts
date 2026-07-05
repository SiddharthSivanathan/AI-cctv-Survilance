export interface AppNotification {
  id: string;
  event_type: string;
  title: string;
  message: string;
  severity: string;
  is_read: boolean;
  read_at: string | null;
  camera_id: string | null;
  created_at: string;
}

export interface NotificationList {
  items: AppNotification[];
  total: number;
  unread_count: number;
}
