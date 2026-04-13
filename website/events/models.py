from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from datetime import datetime


class Event(models.Model):
    """
    Модель мероприятия / события
    """
    STATUS_CHOICES = [
        ('upcoming', 'Предстоящее'),
        ('ongoing', 'Идет сейчас'),
        ('completed', 'Завершено'),
        ('cancelled', 'Отменено'),
    ]

    # Основные поля
    title = models.CharField(
        max_length=200,
        verbose_name="Название",
        help_text="Введите название мероприятия"
    )

    description = models.TextField(
        verbose_name="Описание",
        help_text="Подробное описание мероприятия"
    )

    # Даты и время
    date = models.DateField(
        verbose_name="Дата проведения",
        help_text="Выберите дату мероприятия"
    )

    time = models.TimeField(
        verbose_name="Время начала",
        default='10:00',
        help_text="Укажите время начала"
    )

    end_time = models.TimeField(
        verbose_name="Время окончания",
        null=True,
        blank=True,
        help_text="Необязательно"
    )

    # Местоположение
    location = models.CharField(
        max_length=300,
        verbose_name="Место проведения",
        help_text="Адрес или место проведения"
    )

    # Изображение
    image = models.ImageField(
        upload_to='events/',
        null=True,
        blank=True,
        verbose_name="Изображение"
    )

    # Статус
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='upcoming',
        verbose_name="Статус"
    )

    # Вместимость
    max_participants = models.PositiveIntegerField(
        default=0,
        verbose_name="Максимум участников",
        help_text="0 — без ограничений"
    )

    # Создатель и участники
    creator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_events',
        verbose_name="Организатор"
    )

    participants = models.ManyToManyField(
        User,
        related_name='joined_events',
        blank=True,
        verbose_name="Участники"
    )

    # Временные метки
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления"
    )

    # Дополнительно
    is_public = models.BooleanField(
        default=True,
        verbose_name="Публичное",
        help_text="Доступно всем пользователям"
    )

    category = models.ForeignKey(
        'Category',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='events',
        verbose_name="Категория"
    )

    class Meta:
        verbose_name = "Мероприятие"
        verbose_name_plural = "Мероприятия"
        ordering = ['-date', '-time']
        indexes = [
            models.Index(fields=['date', 'status']),
            models.Index(fields=['creator']),
        ]

    def __str__(self):
        return f"{self.title} ({self.date})"

    def get_absolute_url(self):
        return reverse('event_detail', kwargs={'id': self.pk})

    @property
    def participants_count(self):
        """Количество участников"""
        return self.participants.count()

    @property
    def is_full(self):
        """Проверка на заполненность"""
        if self.max_participants == 0:
            return False
        return self.participants_count >= self.max_participants

    @property
    def available_seats(self):
        """Количество свободных мест"""
        if self.max_participants == 0:
            return None
        return self.max_participants - self.participants_count

    @property
    def is_past(self):
        """Проверка, прошло ли мероприятие"""
        event_datetime = datetime.combine(self.date, self.time)
        if timezone.is_naive(event_datetime):
            event_datetime = timezone.make_aware(event_datetime)
        return event_datetime < timezone.now()

    def get_status_color(self):
        """Возвращает CSS класс для статуса"""
        colors = {
            'upcoming': 'status-upcoming',
            'ongoing': 'status-ongoing',
            'completed': 'status-completed',
            'cancelled': 'status-cancelled',
        }
        return colors.get(self.status, '')

    def get_status_icon(self):
        """Возвращает иконку для статуса"""
        icons = {
            'upcoming': 'fa-calendar-alt',
            'ongoing': 'fa-play-circle',
            'completed': 'fa-check-circle',
            'cancelled': 'fa-times-circle',
        }
        return icons.get(self.status, 'fa-calendar-alt')

    def update_status(self):
        """Автоматическое обновление статуса - РАБОЧАЯ ВЕРСИЯ"""
        if self.status == 'cancelled':
            return False

        event_datetime = datetime.combine(self.date, self.time)

        now = datetime.now()

        if event_datetime > now:
            # Будущее событие
            new_status = 'upcoming'
        elif event_datetime.date() == now.date():
            # Сегодня и время уже наступило
            new_status = 'ongoing'
        else:
            # Прошлое событие
            new_status = 'completed'

        if self.status != new_status:
            self.status = new_status
            self.save(update_fields=['status'])
            return True
        return False


    def can_user_join(self, user):
        """Проверка, может ли пользователь присоединиться"""
        if not self.is_public and user != self.creator:
            return False
        if user in self.participants.all():
            return False
        if self.is_full:
            return False
        if self.status in ['completed', 'cancelled']:
            return False
        return True

    def can_user_edit(self, user):
        """Проверка прав на редактирование"""
        return user == self.creator or user.is_staff


class Category(models.Model):
    """
    Категории мероприятий
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Название категории"
    )

    slug = models.SlugField(
        max_length=100,
        unique=True,
        verbose_name="URL-идентификатор"
    )

    description = models.TextField(
        blank=True,
        verbose_name="Описание"
    )

    color = models.CharField(
        max_length=7,
        default='#b6ff00',
        verbose_name="Цвет",
        help_text="HEX-код цвета"
    )

    icon = models.CharField(
        max_length=50,
        default='fa-calendar',
        verbose_name="Иконка",
        help_text="Название иконки Font Awesome"
    )

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('category_detail', kwargs={'slug': self.slug})


class Comment(models.Model):
    """
    Комментарии к мероприятиям
    """
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name="Мероприятие"
    )

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name="Автор"
    )

    text = models.TextField(
        verbose_name="Текст комментария"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Обновлено"
    )

    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
        verbose_name="Ответ на комментарий"
    )

    class Meta:
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"
        ordering = ['-created_at']

    def __str__(self):
        return f"Комментарий от {self.author} к {self.event}"

    @property
    def is_reply(self):
        return self.parent is not None


class Notification(models.Model):
    """
    Уведомления пользователей
    """
    NOTIFICATION_TYPES = [
        ('event_invite', 'Приглашение на мероприятие'),
        ('event_update', 'Обновление мероприятия'),
        ('event_reminder', 'Напоминание о мероприятии'),
        ('new_comment', 'Новый комментарий'),
        ('participation', 'Подтверждение участия'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name="Пользователь"
    )

    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES,
        verbose_name="Тип уведомления"
    )

    title = models.CharField(
        max_length=200,
        verbose_name="Заголовок"
    )

    message = models.TextField(
        verbose_name="Сообщение"
    )

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications',
        verbose_name="Связанное мероприятие"
    )

    is_read = models.BooleanField(
        default=False,
        verbose_name="Прочитано"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Создано"
    )

    class Meta:
        verbose_name = "Уведомление"
        verbose_name_plural = "Уведомления"
        ordering = ['-created_at']

    def __str__(self):
        return f"Уведомление для {self.user}: {self.title}"


class UserProfile(models.Model):
    """
    Расширенный профиль пользователя
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name="Пользователь"
    )

    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True,
        verbose_name="Аватар"
    )

    bio = models.TextField(
        max_length=500,
        blank=True,
        verbose_name="О себе"
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Телефон"
    )

    telegram = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Telegram"
    )

    birth_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Дата рождения"
    )

    city = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Город"
    )

    interests = models.ManyToManyField(
        Category,
        blank=True,
        verbose_name="Интересы"
    )

    receive_notifications = models.BooleanField(
        default=True,
        verbose_name="Получать уведомления"
    )

    email_notifications = models.BooleanField(
        default=True,
        verbose_name="Уведомления на email"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата регистрации"
    )

    class Meta:
        verbose_name = "Профиль"
        verbose_name_plural = "Профили"

    def __str__(self):
        return f"Профиль {self.user.username}"

    def get_absolute_url(self):
        return reverse('profile')

    @property
    def events_created_count(self):
        return self.user.created_events.count()

    @property
    def events_joined_count(self):
        return self.user.joined_events.count()


class Favorite(models.Model):
    """
    Избранные мероприятия пользователя
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name="Пользователь"
    )

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='favorited_by',
        verbose_name="Мероприятие"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Добавлено"
    )

    class Meta:
        verbose_name = "Избранное"
        verbose_name_plural = "Избранное"
        unique_together = ['user', 'event']

    def __str__(self):
        return f"{self.user} добавил в избранное {self.event}"