from datetime import datetime

from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils import timezone

from events.forms import EventForm
from events.models import Event, Category


def welcome(request):
    if request.user.is_authenticated:
        return redirect('main')
    return render(request, 'html/welcome.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('main')

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request, email=email, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.username}!')
            return redirect('main')
        else:
            messages.error(request, 'Неверная почта или пароль')

    return render(request, 'html/login.html')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('main')

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')

        if password != password_confirm:
            messages.error(request, 'Пароли не совпадают')
            return redirect('register')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Пользователь с таким именем уже существует')
            return redirect('register')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Пользователь с такой почтой уже существует')
            return redirect('register')

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        # Указываем бэкенд
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')

        messages.success(request, f'Регистрация успешна! Добро пожаловать, {username}!')
        return redirect('main')

    return render(request, 'html/register.html')


@login_required
def main_view(request):
    """Главная страница"""
    # Обновляем статусы
    for event in Event.objects.all():
        event.update_status()

    my_events = request.user.joined_events.all()
    all_events_count = Event.objects.count()
    latest_events = Event.objects.filter(
        status__in=['upcoming', 'ongoing']
    ).order_by('-created_at')[:6]

    context = {
        'events': my_events,
        'all_events_count': all_events_count,
        'latest_events': latest_events,
        'now': timezone.now(),
    }
    return render(request, 'html/main.html', context)


@login_required
def profile(request):
    """Профиль пользователя"""
    my_events = request.user.joined_events.all()
    created_events = request.user.created_events.all()

    context = {
        'my_events': my_events,
        'created_events': created_events,
    }
    return render(request, 'html/profile.html', context)


@login_required
def profile_edit(request):
    """Редактирование профиля"""
    user = request.user
    profile = user.profile

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')

        if User.objects.filter(username=username).exclude(id=user.id).exists():
            messages.error(request, 'Пользователь с таким именем уже существует')
            return redirect('profile_edit')

        if User.objects.filter(email=email).exclude(id=user.id).exists():
            messages.error(request, 'Пользователь с таким email уже существует')
            return redirect('profile_edit')

        user.username = username
        user.email = email
        user.save()

        profile.bio = request.POST.get('bio', '')
        profile.phone = request.POST.get('phone', '')
        profile.city = request.POST.get('city', '')
        profile.telegram = request.POST.get('telegram', '')

        birth_date = request.POST.get('birth_date')
        if birth_date:
            profile.birth_date = birth_date

        profile.receive_notifications = request.POST.get('receive_notifications') == 'on'
        profile.email_notifications = request.POST.get('email_notifications') == 'on'

        if 'avatar' in request.FILES:
            profile.avatar = request.FILES['avatar']

        profile.save()
        messages.success(request, 'Профиль успешно обновлен!')
        return redirect('profile')

    context = {
        'user': user,
        'profile': profile,
    }
    return render(request, 'html/profile_edit.html', context)


@login_required
def events_list(request):
    """Список всех событий"""
    # Обновляем статусы
    for event in Event.objects.all():
        event.update_status()

    events = Event.objects.all().order_by('-date', '-time')

    # Фильтры...
    status = request.GET.get('status')
    if status:
        events = events.filter(status=status)

    category = request.GET.get('category')
    if category:
        events = events.filter(category_id=category)

    search = request.GET.get('search')
    if search:
        events = events.filter(
            Q(title__icontains=search) | Q(description__icontains=search)
        )

    paginator = Paginator(events, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    categories = Category.objects.all()

    context = {
        'events': page_obj,
        'categories': categories,
        'current_status': status,
        'current_category': category,
        'search': search,
    }
    return render(request, 'html/events_list.html', context)


@login_required
def event_detail(request, id):
    """Детальная страница события"""
    event = get_object_or_404(Event, id=id)

    # Обновляем статус
    event.update_status()

    is_participant = request.user in event.participants.all()
    is_creator = event.creator == request.user
    can_join = event.can_user_join(request.user)

    context = {
        'event': event,
        'is_participant': is_participant,
        'is_creator': is_creator,
        'can_join': can_join,
    }
    return render(request, 'html/event_detail.html', context)


@login_required
def event_create(request):
    """Создание нового события"""
    if not request.user.is_staff:
        messages.error(request, 'Только администраторы могут создавать события!')
        return redirect('main')

    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.creator = request.user
            event.save()
            messages.success(request, f'Событие "{event.title}" успешно создано!')
            return redirect('event_detail', id=event.id)
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме')
    else:
        form = EventForm()

    context = {'form': form}
    return render(request, 'html/event_form.html', context)


@login_required
def event_edit(request, id):
    """Редактирование события"""
    event = get_object_or_404(Event, id=id)

    if not event.can_user_edit(request.user):
        messages.error(request, 'У вас нет прав на редактирование этого события!')
        return redirect('event_detail', id=id)

    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            event = form.save()
            messages.success(request, f'Событие "{event.title}" успешно обновлено!')
            return redirect('event_detail', id=event.id)
    else:
        form = EventForm(instance=event)

    context = {'form': form, 'event': event}
    return render(request, 'html/event_form.html', context)


@login_required
def event_delete(request, id):
    """Удаление события"""
    event = get_object_or_404(Event, id=id)

    if not event.can_user_edit(request.user):
        messages.error(request, 'У вас нет прав на удаление этого события!')
        return redirect('event_detail', id=id)

    if request.method == 'POST':
        title = event.title
        event.delete()
        messages.success(request, f'Событие "{title}" удалено!')
        return redirect('events_list')

    return render(request, 'html/event_confirm_delete.html', {'event': event})


@login_required
def join_event(request, id):
    """Присоединиться к событию"""
    event = get_object_or_404(Event, id=id)

    if event.can_user_join(request.user):
        event.participants.add(request.user)
        messages.success(request, f'Вы присоединились к событию "{event.title}"!')
    else:
        messages.error(request, 'Невозможно присоединиться к этому событию')

    return redirect('event_detail', id=id)


@login_required
def leave_event(request, id):
    """Покинуть событие"""
    event = get_object_or_404(Event, id=id)

    if request.user in event.participants.all():
        event.participants.remove(request.user)
        messages.success(request, f'Вы покинули событие "{event.title}"')

    return redirect('event_detail', id=id)


def logout_view(request):
    logout(request)
    messages.info(request, 'Вы вышли из системы')
    return redirect('login')