"""Push Notification Management for Mobile Apps

This module handles push notifications (the alerts that appear on your phone screen).

Key Concept:
Server sends push notification:
"Your data synced! 5 new transactions" → User sees this on their phone screen

Database Table: push_notifications
Stores: Device tokens, notification history, preferences

Note: We're building the framework here.
Later, you'll integrate with Firebase Cloud Messaging (FCM) or OneSignal
to actually send the notifications to phones.
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import Column, String, DateTime, Integer, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID

from backend.models import Base


class PushDeviceToken(Base):
    """
    Device token for push notifications.

    When a user installs your app on their phone, we ask for permission
    to send notifications. The phone gives us a token that looks like:
    "exponentPushToken[abcd1234...hijkl5678...]"

    We store this token so we can send notifications to that specific device.

    Example:
        token = PushDeviceToken(
            user_id=user_id,
            organization_id=org_id,
            device_id="iPhone_12345",
            token="exponentPushToken[abc123...]",
            token_type="expo"  # "expo", "fcm", "apns"
        )
        db.add(token)
        db.commit()
    """

    __tablename__ = "push_device_tokens"

    # Unique ID for this token record
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Which user owns this device
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Which organization
    organization_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Device identifier (so we can track multiple devices per user)
    # Example: "iPhone_UDID_12345" or "Android_DEVICE_ID_67890"
    device_id = Column(String(255), nullable=False)

    # Device name (for display in settings)
    # Example: "John's iPhone 14 Pro"
    device_name = Column(String(255))

    # The actual push notification token from device
    # Example: "exponentPushToken[abcd1234......]"
    # This is what we send to Firebase/OneSignal to deliver notifications
    token = Column(Text, nullable=False, unique=True, index=True)

    # Type of token (which service issued it)
    # Values: "expo" (development), "fcm" (Android), "apns" (iOS)
    # We'll start with "expo" for testing, then migrate to fcm/apns
    token_type = Column(String(50), default="expo")

    # Is this token still valid?
    # FALSE = user uninstalled app or revoked permission
    # We stop trying to send notifications to invalid tokens
    is_active = Column(Boolean, default=True)

    # When token was registered
    registered_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # When token was last used successfully
    last_used_at = Column(DateTime(timezone=True))

    # If token is invalid, when did we discover it?
    invalidated_at = Column(DateTime(timezone=True))

    # Why token is invalid (if is_active = False)
    # Examples:
    # - "user_uninstalled": User uninstalled the app
    # - "fcm_invalid": FCM says token is invalid
    # - "apns_invalid": Apple says token is invalid
    # - "max_failures": We tried to send too many times, failed too often
    invalidation_reason = Column(String(100))

    # Number of failed send attempts
    # After 5 failures, we mark token as invalid
    failed_attempts = Column(Integer, default=0)

    def __repr__(self):
        """Human-readable representation"""
        status = "active" if self.is_active else "inactive"
        return f"<PushToken {self.device_name} ({status})>"

    def mark_used(self):
        """Mark token as successfully used"""
        self.last_used_at = datetime.now(timezone.utc)
        self.failed_attempts = 0  # Reset failure count on success

    def record_failure(self):
        """Record a failed send attempt"""
        self.failed_attempts += 1
        if self.failed_attempts >= 5:
            self.invalidate("max_failures")

    def invalidate(self, reason: str):
        """Mark token as invalid (stop sending to it)"""
        self.is_active = False
        self.invalidated_at = datetime.now(timezone.utc)
        self.invalidation_reason = reason


class PushNotificationLog(Base):
    """
    Log of notifications sent to users.

    Every time we send a notification, we record it here for:
    - Debugging (did we send it?)
    - Analytics (how many notifications sent?)
    - User preferences (user can see history)

    Example:
        log = PushNotificationLog(
            user_id=user_id,
            organization_id=org_id,
            device_token_id=token_id,
            notification_type="sync_complete",
            title="Sync Complete",
            body="Your data synced! 5 new transactions",
            status="sent"
        )
        db.add(log)
        db.commit()
    """

    __tablename__ = "push_notification_logs"

    # Unique ID for this notification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Which user received it
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Which organization
    organization_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Which device token we sent to
    device_token_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # ===== NOTIFICATION CONTENT =====

    # Type of notification (for filtering/preferences)
    # Values: "sync_complete", "sync_error", "alert", "info"
    # User can disable specific types in settings
    notification_type = Column(String(50), nullable=False, index=True)

    # Title that appears on phone (short)
    # Example: "Sync Complete"
    title = Column(String(200), nullable=False)

    # Body text (detailed message)
    # Example: "Your data synced! 5 new transactions"
    body = Column(String(500), nullable=False)

    # Optional extra data to pass with notification
    # Used to navigate to correct screen when user taps notification
    # Example: {"screen": "TransactionList", "sync_id": "abc123"}
    data = Column(String(1000))

    # ===== DELIVERY STATUS =====

    # Status of this notification
    # "pending"  = queued, waiting to send
    # "sent"     = successfully delivered to device
    # "failed"   = failed to deliver (invalid token, etc)
    # "opened"   = user tapped notification (if tracking enabled)
    status = Column(String(50), nullable=False, default="pending", index=True)

    # When we sent it
    sent_at = Column(DateTime(timezone=True))

    # If failed, why?
    # Examples:
    # - "Invalid device token"
    # - "Firebase service unavailable"
    # - "Token was revoked by user"
    failure_reason = Column(Text)

    # When user opened/tapped the notification
    opened_at = Column(DateTime(timezone=True))

    # ===== TIMESTAMPS =====

    # When we created this notification (queued it)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    def __repr__(self):
        """Human-readable representation"""
        return f"<Notification {self.notification_type} ({self.status})>"

    def mark_sent(self):
        """Mark notification as successfully sent"""
        self.status = "sent"
        self.sent_at = datetime.now(timezone.utc)

    def mark_failed(self, reason: str):
        """Mark notification as failed"""
        self.status = "failed"
        self.failure_reason = reason

    def mark_opened(self):
        """Mark notification as opened by user"""
        self.status = "opened"
        self.opened_at = datetime.now(timezone.utc)


class PushNotificationPreference(Base):
    """
    User preferences for push notifications.

    Users can control what notifications they receive.
    This table stores their preferences:
    - Sync notifications: on/off
    - Alert notifications: on/off
    - Info notifications: on/off

    Example:
        pref = PushNotificationPreference(
            user_id=user_id,
            organization_id=org_id,
            sync_notifications=True,
            alert_notifications=True,
            info_notifications=False  # User disabled info notifications
        )
        db.add(pref)
        db.commit()
    """

    __tablename__ = "push_notification_preferences"

    # Unique ID
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Which user
    user_id = Column(UUID(as_uuid=True), nullable=False, unique=True, index=True)

    # Which organization
    organization_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # ===== NOTIFICATION TYPE PREFERENCES =====

    # Should we send sync notifications?
    # "Sync complete! 5 new transactions" - usually yes
    sync_notifications_enabled = Column(Boolean, default=True)

    # Should we send alert notifications?
    # "Large transaction detected: $5,000" - usually yes
    alert_notifications_enabled = Column(Boolean, default=True)

    # Should we send info notifications?
    # "New feature available" - user might disable
    info_notifications_enabled = Column(Boolean, default=False)

    # Should we send report notifications?
    # "Your monthly report is ready" - usually yes
    report_notifications_enabled = Column(Boolean, default=True)

    # ===== QUIET HOURS =====

    # Don't send notifications between these times
    # Example: 22:00 (10 PM) to 07:00 (7 AM)
    quiet_hours_start = Column(String(5))  # Format: "HH:MM" (24-hour)
    quiet_hours_end = Column(String(5))    # Format: "HH:MM" (24-hour)

    # ===== TIMESTAMPS =====

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self):
        """Human-readable representation"""
        return f"<NotificationPreference user={self.user_id}>"

    def should_send_notification(self, notification_type: str) -> bool:
        """
        Check if user wants this type of notification.

        Args:
            notification_type: Type of notification to check

        Returns:
            True if we should send it, False if user disabled it

        Example:
            pref = get_preferences(user_id)
            if pref.should_send_notification("sync_complete"):
                send_notification(user, "Sync complete!")
        """
        if notification_type == "sync_complete":
            return self.sync_notifications_enabled
        elif notification_type == "alert":
            return self.alert_notifications_enabled
        elif notification_type == "info":
            return self.info_notifications_enabled
        elif notification_type == "report":
            return self.report_notifications_enabled
        return True  # Default to send if type not recognized

    def is_in_quiet_hours(self, check_time: datetime) -> bool:
        """
        Check if current time is in quiet hours.

        Don't send notifications during quiet hours (e.g., at night).

        Args:
            check_time: Time to check (default: now)

        Returns:
            True if currently in quiet hours, False otherwise

        Example:
            pref = get_preferences(user_id)
            if pref.is_in_quiet_hours(datetime.now(timezone.utc)):
                queue_notification_for_later()
            else:
                send_notification_now()
        """
        if not self.quiet_hours_start or not self.quiet_hours_end:
            return False

        current_time = check_time.strftime("%H:%M")
        start = self.quiet_hours_start
        end = self.quiet_hours_end

        # If quiet hours don't wrap around midnight (e.g., 22:00 - 07:00)
        if start < end:
            return start <= current_time < end
        else:
            # Quiet hours wrap around midnight
            return current_time >= start or current_time < end
