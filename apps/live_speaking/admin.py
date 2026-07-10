from django.contrib import admin

from .models import LiveSpeakingSession, LiveSpeakingMessage


class LiveSpeakingMessageInline(admin.TabularInline):
    model = LiveSpeakingMessage
    extra = 0
    readonly_fields = ('role', 'text', 'created_at')
    can_delete = False
    ordering = ('created_at',)


@admin.register(LiveSpeakingSession)
class LiveSpeakingSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'test', 'voice', 'status', 'started_at', 'ended_at')
    list_filter = ('status', 'voice')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('started_at',)
    inlines = [LiveSpeakingMessageInline]
    ordering = ('-started_at',)


@admin.register(LiveSpeakingMessage)
class LiveSpeakingMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'session', 'role', 'short_text', 'created_at')
    list_filter = ('role',)
    search_fields = ('text', 'session__user__username')
    ordering = ('-created_at',)

    def short_text(self, obj):
        return (obj.text[:60] + '...') if len(obj.text) > 60 else obj.text
    short_text.short_description = 'Matn'