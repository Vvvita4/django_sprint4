from django.contrib import admin
from .models import Post, Category, Location, Comment


class PostAdmin(admin.ModelAdmin):
    search_fields = ('text',)
    list_display = (
        'title',
        'text',
        'pub_date',
        'author',
        'location',
        'category',
        'is_published',
        'created_at'
    )
    list_display_links = ('title',)
    list_editable = (
        'category',
        'is_published',
        'location')
    list_filter = ('created_at',)
    empty_vatue_display = 'не задано'


admin.site.register(Post, PostAdmin)
admin.site.register(Category)
admin.site.register(Location)
admin.site.register(Comment)
