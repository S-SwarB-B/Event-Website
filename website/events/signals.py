from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Event, UserProfile
from datetime import datetime


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Автоматически создает профиль при регистрации пользователя"""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Сохраняет профиль при сохранении пользователя"""
    if hasattr(instance, 'profile'):
        instance.profile.save()


@receiver(pre_save, sender=Event)
def auto_update_event_status(sender, instance, **kwargs):
    """Автоматически обновляет статус перед сохранением"""
    if instance.status == 'cancelled':
        return

    event_datetime = datetime.combine(instance.date, instance.time)
    now = datetime.now()

    if event_datetime > now:
        correct_status = 'upcoming'
    elif event_datetime.date() == now.date():
        correct_status = 'ongoing'
    else:
        correct_status = 'completed'
    if instance.status != correct_status:
        instance.status = correct_status