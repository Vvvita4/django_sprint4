from django.contrib import admin
from django.urls import path, include, reverse_lazy
from django.contrib.auth.forms import UserCreationForm
from django.views.generic import CreateView
from django.conf import settings
from django.conf.urls.static import static

handler404 = 'pages.views.page_not_found'
handler500 = 'pages.views.server_error'

urlpatterns = [
    path("admin/", admin.site.urls),
    path('', include("blog.urls", namespace='blog')),
    path("pages/", include("pages.urls", namespace='pages')),
    # Подключаем urls.py приложения для работы с пользователями.
    path('auth/', include('django.contrib.auth.urls')),
    # Регистрация пользователя
    path(
        'auth/registration/',
        CreateView.as_view(
            template_name='registration/registration_form.html',
            # Стандартная форма для создания пользователя
            form_class=UserCreationForm,
            # После регистрации на главную
            success_url=reverse_lazy('blog:index'),
        ),
        name='registration',
    ),
]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
