class KafkaTopics:
    # Events
    EVENT_CREATED = "event.created"
    EVENT_UPDATED = "event.updated"
    EVENT_DELETED = "event.deleted"
    EVENT_STARTED = "event.started"
    EVENT_FINISHED = "event.finished"

    # Participants
    USER_JOINED_EVENT = "event.user.joined"
    USER_LEFT_EVENT = "event.user.left"

    # Comments
    COMMENT_CREATED = "event.comment.created"

    # Users
    USER_REGISTERED = "user.registered"
    USER_UPDATED = "user.updated"

    # Notifications
    NOTIFICATION_EMAIL = "notification.email"
    NOTIFICATION_PUSH = "notification.push"
