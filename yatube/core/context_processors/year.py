from django.utils import timezone, dateformat


def year(request):
    year = dateformat.format(timezone.now(), 'Y')
    year = int(year)
    """Добавляет переменную с текущим годом."""
    return {
        'year': year
    }
