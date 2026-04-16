from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, time, timedelta
from events.models import Event, Category, UserProfile


class UserAuthenticationTests(TestCase):
    """Тесты аутентификации пользователей"""

    def setUp(self):
        """Создание тестовых данных перед каждым тестом"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_login_success(self):
        """Тест успешного входа в систему"""
        response = self.client.post('/login/', {
            'email': 'test@example.com',
            'password': 'testpass123'
        })
        self.assertRedirects(response, '/main/')
        self.assertTrue('_auth_user_id' in self.client.session)

    def test_login_failure_wrong_password(self):
        """Тест неудачного входа с неверным паролем"""
        response = self.client.post('/login/', {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse('_auth_user_id' in self.client.session)
        messages_list = list(response.context['messages'])
        self.assertTrue(any('Неверная почта или пароль' in str(msg) for msg in messages_list))

    def test_login_failure_nonexistent_user(self):
        """Тест неудачного входа с несуществующим пользователем"""
        response = self.client.post('/login/', {
            'email': 'nonexistent@example.com',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse('_auth_user_id' in self.client.session)
        messages_list = list(response.context['messages'])
        self.assertTrue(any('Неверная почта или пароль' in str(msg) for msg in messages_list))

    def test_logout(self):
        """Тест выхода из системы"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/logout/')
        self.assertRedirects(response, '/login/')
        self.assertFalse('_auth_user_id' in self.client.session)


class UserRegistrationTests(TestCase):
    """Тесты регистрации пользователей"""

    def setUp(self):
        self.client = Client()

    def test_register_success(self):
        """Тест успешной регистрации"""
        response = self.client.post('/register/', {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'password_confirm': 'newpass123'
        })
        self.assertRedirects(response, '/main/')
        self.assertTrue(User.objects.filter(username='newuser').exists())
        self.assertTrue(UserProfile.objects.filter(user__username='newuser').exists())

    def test_register_password_mismatch(self):
        """Тест регистрации с несовпадающими паролями"""
        response = self.client.post('/register/', {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'password_confirm': 'differentpass'
        })
        self.assertEqual(response.status_code, 302)
        self.assertFalse(User.objects.filter(username='newuser').exists())

    def test_register_existing_username(self):
        """Тест регистрации с существующим именем пользователя"""
        User.objects.create_user(username='existing', email='exist@example.com', password='testpass123')
        response = self.client.post('/register/', {
            'username': 'existing',
            'email': 'new@example.com',
            'password': 'newpass123',
            'password_confirm': 'newpass123'
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(User.objects.filter(username='existing').count(), 1)

    def test_register_existing_email(self):
        """Тест регистрации с существующим email"""
        User.objects.create_user(username='existing', email='exist@example.com', password='testpass123')
        response = self.client.post('/register/', {
            'username': 'newuser',
            'email': 'exist@example.com',
            'password': 'newpass123',
            'password_confirm': 'newpass123'
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(User.objects.filter(email='exist@example.com').count(), 1)


class EventModelTests(TestCase):
    """Тесты модели Event"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='creator',
            email='creator@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='Тестовая категория',
            slug='test-category'
        )

    def test_event_creation(self):
        """Тест создания мероприятия"""
        event = Event.objects.create(
            title='Тестовое мероприятие',
            description='Описание тестового мероприятия',
            date=date.today() + timedelta(days=7),
            time=time(18, 0),
            location='Москва',
            creator=self.user,
            category=self.category,
            max_participants=50
        )
        self.assertEqual(event.title, 'Тестовое мероприятие')
        self.assertEqual(event.status, 'upcoming')
        self.assertEqual(event.participants_count, 0)
        self.assertFalse(event.is_full)

    def test_event_status_update_upcoming(self):
        """Тест обновления статуса для будущего мероприятия"""
        event = Event.objects.create(
            title='Будущее мероприятие',
            description='Описание',
            date=date.today() + timedelta(days=1),
            time=time(10, 0),
            location='Москва',
            creator=self.user
        )
        event.update_status()
        self.assertEqual(event.status, 'upcoming')

    def test_event_status_update_completed(self):
        """Тест обновления статуса для прошедшего мероприятия"""
        event = Event.objects.create(
            title='Прошедшее мероприятие',
            description='Описание',
            date=date.today() - timedelta(days=1),
            time=time(10, 0),
            location='Москва',
            creator=self.user
        )
        event.update_status()
        self.assertEqual(event.status, 'completed')

    def test_event_status_update_cancelled_unchanged(self):
        """Тест, что отмененное мероприятие не меняет статус"""
        event = Event.objects.create(
            title='Отмененное мероприятие',
            description='Описание',
            date=date.today() - timedelta(days=1),
            time=time(10, 0),
            location='Москва',
            creator=self.user,
            status='cancelled'
        )
        event.update_status()
        self.assertEqual(event.status, 'cancelled')

    def test_can_user_join(self):
        """Тест проверки возможности присоединения"""
        event = Event.objects.create(
            title='Мероприятие',
            description='Описание',
            date=date.today() + timedelta(days=1),
            time=time(10, 0),
            location='Москва',
            creator=self.user,
            max_participants=1
        )
        other_user = User.objects.create_user(username='other', password='testpass123')

        # Пользователь может присоединиться
        self.assertTrue(event.can_user_join(other_user))

        # Присоединяем пользователя
        event.participants.add(other_user)
        self.assertFalse(event.can_user_join(self.user))
        self.assertTrue(event.is_full)

    def test_can_user_edit(self):
        """Тест проверки прав на редактирование"""
        event = Event.objects.create(
            title='Мероприятие',
            description='Описание',
            date=date.today() + timedelta(days=1),
            time=time(10, 0),
            location='Москва',
            creator=self.user
        )
        other_user = User.objects.create_user(username='other', password='testpass123')
        admin_user = User.objects.create_user(username='admin', password='testpass123', is_staff=True)

        self.assertTrue(event.can_user_edit(self.user))
        self.assertFalse(event.can_user_edit(other_user))
        self.assertTrue(event.can_user_edit(admin_user))


class EventViewsTests(TestCase):
    """Тесты представлений мероприятий"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='testpass123',
            is_staff=True
        )
        self.category = Category.objects.create(
            name='Категория',
            slug='category'
        )
        self.event = Event.objects.create(
            title='Тестовое мероприятие',
            description='Описание',
            date=date.today() + timedelta(days=7),
            time=time(18, 0),
            location='Москва',
            creator=self.admin_user,
            category=self.category
        )

    def test_main_view_requires_login(self):
        """Тест, что главная страница требует авторизации"""
        response = self.client.get('/main/')
        self.assertRedirects(response, '/login/?next=/main/')

    def test_main_view_authenticated(self):
        """Тест главной страницы для авторизованного пользователя"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/main/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'html/main/main.html')

    def test_events_list_view(self):
        """Тест страницы списка мероприятий"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/events/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'html/events/events_list.html')
        self.assertContains(response, 'Тестовое мероприятие')

    def test_event_detail_view(self):
        """Тест детальной страницы мероприятия"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(f'/events/{self.event.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'html/events/event_detail.html')
        self.assertContains(response, 'Тестовое мероприятие')

    def test_event_create_view_requires_admin(self):
        """Тест, что создание мероприятия требует прав администратора"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/create/')
        self.assertRedirects(response, '/main/')

    def test_event_create_view_admin(self):
        """Тест создания мероприятия администратором"""
        self.client.login(username='admin', password='testpass123')
        response = self.client.get('/create/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'html/events/event_form.html')

    def test_event_create_post(self):
        """Тест отправки формы создания мероприятия"""
        self.client.login(username='admin', password='testpass123')
        response = self.client.post('/create/', {
            'title': 'Новое мероприятие',
            'description': 'Описание нового мероприятия',
            'date': (date.today() + timedelta(days=14)).isoformat(),
            'time': '14:00',
            'location': 'Санкт-Петербург',
            'max_participants': 100,
            'is_public': True,
            'status': 'upcoming'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Event.objects.filter(title='Новое мероприятие').exists())

    def test_join_event(self):
        """Тест присоединения к мероприятию"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(f'/join/{self.event.id}/')
        self.assertRedirects(response, f'/events/{self.event.id}/')
        self.assertTrue(self.user in self.event.participants.all())

    def test_leave_event(self):
        """Тест выхода из мероприятия"""
        self.event.participants.add(self.user)
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(f'/leave/{self.event.id}/')
        self.assertRedirects(response, f'/events/{self.event.id}/')
        self.assertFalse(self.user in self.event.participants.all())

    def test_event_delete(self):
        """Тест удаления мероприятия"""
        self.client.login(username='admin', password='testpass123')
        response = self.client.post(f'/delete/{self.event.id}/')
        self.assertRedirects(response, '/events/')
        self.assertFalse(Event.objects.filter(id=self.event.id).exists())


class ProfileTests(TestCase):
    """Тесты профиля пользователя"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_profile_view_requires_login(self):
        """Тест, что профиль требует авторизации"""
        response = self.client.get('/profile/')
        self.assertRedirects(response, '/login/?next=/profile/')

    def test_profile_view_authenticated(self):
        """Тест страницы профиля для авторизованного пользователя"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/profile/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'html/profile/profile.html')

    def test_profile_edit_view(self):
        """Тест страницы редактирования профиля"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/profile/edit/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'html/profile/profile_edit.html')

    def test_profile_edit_post(self):
        """Тест обновления профиля"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post('/profile/edit/', {
            'username': 'updateduser',
            'email': 'updated@example.com',
            'bio': 'Новая биография',
            'phone': '+79001234567',
            'city': 'Москва',
            'telegram': '@updated'
        })
        self.assertRedirects(response, '/profile/')
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'updateduser')
        self.assertEqual(self.user.email, 'updated@example.com')
        self.assertEqual(self.user.profile.bio, 'Новая биография')

    def test_profile_edit_duplicate_username(self):
        """Тест обновления профиля с существующим именем пользователя"""
        User.objects.create_user(username='existing', password='testpass123')
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post('/profile/edit/', {
            'username': 'existing',
            'email': 'test@example.com'
        })
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'testuser')


class SearchAndFilterTests(TestCase):
    """Тесты поиска и фильтрации"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category1 = Category.objects.create(name='Конференции', slug='conferences')
        self.category2 = Category.objects.create(name='Вебинары', slug='webinars')

        Event.objects.create(
            title='Django Conference',
            description='Конференция по Django',
            date=date.today() + timedelta(days=30),
            time=time(10, 0),
            location='Москва',
            creator=self.user,
            category=self.category1,
            status='upcoming'
        )
        Event.objects.create(
            title='Python Webinar',
            description='Вебинар по Python',
            date=date.today() + timedelta(days=15),
            time=time(14, 0),
            location='Онлайн',
            creator=self.user,
            category=self.category2,
            status='upcoming'
        )
        Event.objects.create(
            title='Completed Event',
            description='Завершенное мероприятие',
            date=date.today() - timedelta(days=7),
            time=time(10, 0),
            location='Москва',
            creator=self.user,
            status='completed'
        )

    def test_search_by_title(self):
        """Тест поиска по названию"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/events/?search=Django')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Django Conference')
        self.assertNotContains(response, 'Python Webinar')

    def test_filter_by_status(self):
        """Тест фильтрации по статусу"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/events/?status=completed')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Completed Event')
        self.assertNotContains(response, 'Django Conference')

    def test_filter_by_category(self):
        """Тест фильтрации по категории"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(f'/events/?category={self.category1.id}')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Django Conference')
        self.assertNotContains(response, 'Python Webinar')

    def test_combined_filters(self):
        """Тест комбинированной фильтрации"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(f'/events/?status=upcoming&category={self.category1.id}')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Django Conference')
        self.assertNotContains(response, 'Python Webinar')
        self.assertNotContains(response, 'Completed Event')