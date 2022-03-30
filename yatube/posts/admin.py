from django.contrib import admin
from .models import Post, Group, Comment


class GroupAdmin(admin.ModelAdmin):
    list_display = ('title',
                    'slug',
                    'description')
    search_fields = ('title', 'slug')
    empty_value_display = '-пусто-'


class PostAdmin(admin.ModelAdmin):
    list_display = ('pk',
                    'text',
                    'pub_date',
                    'author',
                    'group')
    list_editable = ('group',)
    search_fields = ('text',)
    list_filter = ('pub_date',)
    empty_value_display = '-пусто-'


class CommentAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'text',
        'author',
        'created',
        'post'
    )
    list_editable = ('text',)
    search_fields = ('author',)
    list_filter = ('created', 'author')
    empty_value_display = '-пусто-'


admin.site.register(Post, PostAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Comment, CommentAdmin)
