from django import template

register = template.Library()

@register.filter(name='abs')
def abs_filter(value):
    """Returns the absolute value of a number."""
    try:
        return abs(value)
    except (ValueError, TypeError):
        return value

@register.filter(name='get_item')
def get_item(dictionary, key):
    """Returns the value from a dictionary for the given key."""
    return dictionary.get(key)


@register.filter
def mul(value, arg):
    """Умножает значение на аргумент"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return ''


@register.filter
def floatformat_or_empty(value, arg=1):
    """Форматирует значение как число с плавающей точкой или возвращает пустую строку"""
    try:
        return f"{float(value):.{arg}f}"
    except (ValueError, TypeError):
        return ''

@register.filter(name='div')
def divide(value, arg):
    """Деление значения на аргумент"""
    try:
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0


@register.filter(name='mul')
def multiply(value, arg):
    """Умножение значения на аргумент"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter(name='div')
def divide(value, arg):
    """Деление значения на аргумент"""
    try:
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0


@register.filter(name='perc')
def percentage(value, arg):
    """Вычисление процента одного значения от другого"""
    try:
        return (float(value) / float(arg)) * 100
    except (ValueError, TypeError, ZeroDivisionError):
        return 0


@register.filter(name='replace_char')
def replace_char(value, arg):
    """
    Заменяет все вхождения первого символа аргумента на второй символ.

    Пример использования: {{ 'muscle_gain'|replace_char:"_" " " }}
    Результат: 'muscle gain'
    """
    if len(arg) >= 2:
        old_char, new_char = arg[0], arg[1]
        return value.replace(old_char, new_char)
    return value


def get_day_name(day_num):
    """
    Возвращает название дня недели по его номеру.

    Args:
        day_num: Номер дня недели (0-6, где 0 - понедельник)

    Returns:
        Строка с названием дня недели
    """
    days = {
        '0': 'Monday',
        '1': 'Tuesday',
        '2': 'Wednesday',
        '3': 'Thursday',
        '4': 'Friday',
        '5': 'Saturday',
        '6': 'Sunday'
    }
    return days.get(str(day_num), f"Day {day_num}")


@register.filter(name='get_exercise_name')
def get_exercise_name(exercise_id):
    """
    Возвращает название упражнения по его ID.
    Для использования в шаблонах вместо обращения к базе данных.

    Args:
        exercise_id: ID упражнения

    Returns:
        Строка с названием упражнения или "Unknown Exercise"
    """
    try:
        from workouts.models import Exercise
        exercise = Exercise.objects.get(id=exercise_id)
        return exercise.name
    except:
        return "Unknown Exercise"


@register.filter(name='average_weight')
def average_weight(logs):
    """
    Вычисляет средний вес из списка логов упражнений.

    Args:
        logs: Список объектов UserPlanExercise

    Returns:
        Среднее значение веса или None, если нет данных
    """
    if not logs:
        return None

    weights = [log.weight for log in logs if log.weight is not None]

    if not weights:
        return None

    return sum(weights) / len(weights)


@register.filter(name='youtube_embed_url')
def youtube_embed_url(url):
    """
    Преобразует обычную ссылку на YouTube в ссылку для вставки (embed).

    Args:
        url: URL видео на YouTube

    Returns:
        URL для встраивания видео
    """
    if 'youtube.com/watch' in url:
        # Обрабатываем полные URL
        parts = url.split('v=')
        if len(parts) > 1:
            video_id = parts[1].split('&')[0]
            return f"https://www.youtube.com/embed/{video_id}"
    elif 'youtu.be/' in url:
        # Обрабатываем сокращенные URL
        parts = url.split('youtu.be/')
        if len(parts) > 1:
            video_id = parts[1].split('?')[0]
            return f"https://www.youtube.com/embed/{video_id}"

    # Если это не YouTube-видео или формат не определен, вернем исходный URL
    return url


@register.filter(name='sub')
def subtract(value, arg):
    """
    Вычитает аргумент из значения.

    Args:
        value: Исходное значение
        arg: Значение для вычитания

    Returns:
        Результат вычитания
    """
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0
@register.filter(name='add_class')
def add_class(field, css_class):
    """Add a CSS class to the field's widget."""
    if hasattr(field, 'as_widget'):
        return field.as_widget(attrs={"class": css_class})
    else:
        return field