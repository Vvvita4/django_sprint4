from django.db.models import Manager


class PostManager(Manager):
    def get_queryset(self):
        return super().get_queryset().select_related(
            'author', 'category', 'location',)
