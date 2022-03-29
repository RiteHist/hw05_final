from django.core.paginator import Paginator
from yatube.settings import NUM_OBJECTS_TO_DISPLAY


def objects_to_paginator(request, objects):
    """
    Перевод списка объектов в паджинатор
    с выводом 10 объектов на страницу.
    """
    paginator = Paginator(objects, NUM_OBJECTS_TO_DISPLAY)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
