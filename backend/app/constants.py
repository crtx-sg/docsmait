# Shared constants for the application

# Review status options used across Document Reviews and Code Reviews
REVIEW_STATUS_OPTIONS = ["draft", "review_request", "needs_update", "approved"]

# Legacy status mapping for backward compatibility
LEGACY_STATUS_MAPPING = {
    "pending": "draft",
    "changes_requested": "needs_update", 
    "commented": "review_request",
    "approved": "approved"
}