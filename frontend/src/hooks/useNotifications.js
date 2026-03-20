import { useState, useEffect, useCallback } from 'react';

const NOTIFICATION_SETTINGS_KEY = 'rc-notification-settings';

const DEFAULT_SETTINGS = {
  itp_expiry: true,
  backup_reminder: true,
  uptime_alert: true,
};

export function useNotifications() {
  const [permission, setPermission] = useState('default');
  const [settings, setSettings] = useState(() => {
    try {
      const saved = localStorage.getItem(NOTIFICATION_SETTINGS_KEY);
      return saved ? { ...DEFAULT_SETTINGS, ...JSON.parse(saved) } : DEFAULT_SETTINGS;
    } catch {
      return DEFAULT_SETTINGS;
    }
  });
  const [badgeCount, setBadgeCount] = useState(0);

  useEffect(() => {
    if ('Notification' in window) {
      setPermission(Notification.permission);
    }
  }, []);

  useEffect(() => {
    localStorage.setItem(NOTIFICATION_SETTINGS_KEY, JSON.stringify(settings));
  }, [settings]);

  const requestPermission = useCallback(async () => {
    if (!('Notification' in window)) return 'denied';
    const result = await Notification.requestPermission();
    setPermission(result);
    return result;
  }, []);

  const sendNotification = useCallback((title, options = {}) => {
    if (permission !== 'granted') return null;
    try {
      const notification = new Notification(title, {
        icon: '/icons/icon-192.png',
        badge: '/icons/icon-192.png',
        ...options,
      });
      return notification;
    } catch {
      return null;
    }
  }, [permission]);

  const updateSetting = useCallback((key, value) => {
    setSettings(prev => ({ ...prev, [key]: value }));
  }, []);

  const checkITPAlerts = useCallback(async (apiClient) => {
    if (!settings.itp_expiry) return;
    try {
      const { data } = await apiClient.get('/api/itp/alerts');
      const alerts = data.alerts || [];
      const urgent = alerts.filter(a => a.days_remaining <= 7);
      setBadgeCount(urgent.length);
      if (urgent.length > 0 && permission === 'granted') {
        sendNotification('ITP - Expirare apropiata', {
          body: `${urgent.length} inspectii expira in 7 zile!`,
          tag: 'itp-alert',
        });
      }
    } catch { /* ignore */ }
  }, [settings.itp_expiry, permission, sendNotification]);

  return {
    permission,
    settings,
    badgeCount,
    requestPermission,
    sendNotification,
    updateSetting,
    checkITPAlerts,
  };
}
