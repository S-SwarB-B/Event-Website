from django import forms
from .models import Event, Category


class EventForm(forms.ModelForm):
    """Форма для создания и редактирования событий"""

    class Meta:
        model = Event
        fields = [
            'title', 'description', 'category', 'date', 'time',
            'end_time', 'location', 'image', 'max_participants',
            'is_public'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Например: "Весенний фестиваль 2024"',
                'autocomplete': 'off'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Опишите мероприятие, программу, что ждет участников...',
                'rows': 4
            }),
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'min': ''
            }),
            'time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time',
                'value': '10:00'
            }),
            'end_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Адрес или онлайн-платформа'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'max_participants': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': '0'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
        labels = {
            'title': 'Название',
            'description': 'Описание',
            'category': 'Категория',
            'date': 'Дата',
            'time': 'Время',
            'end_time': 'Время окончания',
            'location': 'Место',
            'image': 'Изображение',
            'max_participants': 'Максимум участников',
            'is_public': 'Публичное',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].required = False
        for field in self.fields.values():
            if not field.widget.attrs.get('class'):
                field.widget.attrs['class'] = 'form-control'

    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        time = cleaned_data.get('time')
        end_time = cleaned_data.get('end_time')

        if time and end_time and end_time <= time:
            self.add_error('end_time', 'Время окончания должно быть позже времени начала')

        return cleaned_data