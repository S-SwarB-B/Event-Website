from django.contrib import admin
from django.utils.html import format_html
from .models import Event, Category, Comment, Notification, UserProfile, Favorite


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'color_preview', 'events_count']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']

    def color_preview(self, obj):
        return format_html(
            '<div style="width:30px;height:20px;background:{};border-radius:4px;"></div>',
            obj.color
        )

    color_preview.short_description = 'Цвет'

    def events_count(self, obj):
        return obj.events.count()

    events_count.short_description = 'Мероприятий'


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    readonly_fields = ['created_at']


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'date', 'time', 'location', 'creator',
        'status_badge', 'participants_count', 'is_public'
    ]
    list_filter = ['status', 'date', 'category', 'is_public']
    search_fields = ['title', 'description', 'location']
    readonly_fields = ['created_at', 'updated_at', 'participants_count']
    inlines = [CommentInline]
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'description', 'image')
        }),
        ('Дата и время', {
            'fields': ('date', 'time', 'end_time')
        }),
        ('Место и категория', {
            'fields': ('location', 'category')
        }),
        ('Участники', {
            'fields': ('creator', 'participants', 'max_participants')
        }),
        ('Статус и доступ', {
            'fields': ('status', 'is_public')
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    filter_horizontal = ['participants']

    def status_badge(self, obj):
        colors = {
            'upcoming': '#3b82f6',
            'ongoing': '#10b981',
            'completed': '#6b7280',
            'cancelled': '#ef4444'
        }
        return format_html(
            '<span style="background:{};color:white;padding:4px 8px;border-radius:12px;font-size:12px;">{}</span>',
            colors.get(obj.status, '#6b7280'),
            obj.get_status_display()
        )

    status_badge.short_description = 'Статус'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['id', 'event', 'author', 'short_text', 'created_at']
    list_filter = ['created_at', 'event']
    search_fields = ['text', 'author__username']

    def short_text(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text

    short_text.short_description = 'Текст'


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification_type', 'title', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['title', 'message', 'user__username']
    list_editable = ['is_read']


class FavoriteInline(admin.TabularInline):
    model = Favorite
    extra = 0


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'city', 'events_created', 'events_joined', 'created_at']
    search_fields = ['user__username', 'user__email', 'phone']
    filter_horizontal = ['interests']

    def events_created(self, obj):
        return obj.user.created_events.count()

    events_created.short_description = 'Создано событий'

    def events_joined(self, obj):
        return obj.user.joined_events.count()

    events_joined.short_description = 'Участвует'


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ['user', 'event', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'event__title']