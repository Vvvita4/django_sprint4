from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count
from django.http.response import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse_lazy, reverse
from django.utils.timezone import now
from django.views.generic import CreateView, DeleteView, UpdateView
from .forms import PostForm, CommentForm, UserEditForm
from django.contrib.auth.models import User
from blog.models import Post, Category, Comment


User = get_user_model()

posts_by_page = 10


# используем декоратор login_required,
# т.к.надо ограничить доступ на основе аутентификации пользователя
@login_required
def edit(request):
    """Редактирование профиля"""
    if request.method == 'POST':
        user_form = UserEditForm(instance=request.user, data=request.POST)
        if user_form.is_valid():
            user_form.save()
            return HttpResponseRedirect('/')
    else:
        user_form = UserEditForm(instance=request.user)
        return render(request, 'blog/user.html', {'form': user_form})


@login_required
def add_comment(request, post_id):
    """Добавление комментария"""
    posts = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = posts
        comment.save()
    return redirect('blog:post_detail', post_id=post_id)


@login_required
def edit_comment(request, post_id, comment_id):
    # Находим запрошенный объект для редактирования по первичному ключу
    # или возвращаем 404 ошибку, если такого объекта нет.
    comment = get_object_or_404(Comment, id=comment_id)
    if comment.author != request.user:
        return redirect('blog:post_detail', post_id=post_id)
    # Если был получен POST-запрос...
    if request.method == 'POST':
        form = CommentForm(request.POST or None, instance=comment)
        # Сохраняем данные, полученные из формы, и отправляем ответ:
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', post_id=post_id)
    else:
        form = CommentForm(instance=comment)
    context = {'form': form, 'comment': comment}
    return render(request, 'blog/comment.html', context)


@login_required
def delete_comment(request, post_id, comment_id):
    """Удаление комментария"""
    # Получаем объект модели или выбрасываем 404 ошибку.
    comment = get_object_or_404(Comment, id=comment_id)
    if comment.author != request.user:
        return redirect('blog:post_detail', post_id=post_id)
    if request.method == 'POST':
        # ...удаляем объект:
        comment.delete()
        # ...и переадресовываем пользователя на страницу со списком записей.
        return redirect('blog:post_detail', post_id=post_id)
    context = {'comment': comment}
    return render(request, 'blog/comment.html', context)


def filter_posts(posts):
    """Фильтрация для постов"""
    return posts.select_related(
        'author', 'category', 'location'
    ).filter(
        is_published=True,
        pub_date__lte=now(),
        category__is_published=True,
    ).annotate(comment_count=Count('comments')).order_by('-pub_date')


def paginate_obj(request, post_list, posts_by_page):
    paginator = Paginator(post_list, posts_by_page)
    page = request.GET.get('page')

    try:
        page_number = paginator.page(page)
    except PageNotAnInteger:
        # Если страница не является целым числом, возвращаем первую страницу.
        page_number = paginator.page(1)
    except EmptyPage:
        # Если номер страницы больше, возвращаем последнюю.
        page_number = paginator.page(paginator.num_pages)

    return page_number


def index(request):
    post_list = filter_posts(Post.objects)
    page_obj = paginate_obj(request, post_list, posts_by_page)
    context = {"page_obj": page_obj}
    return render(request, "blog/index.html", context)


def post_detail(request, post_id):
    posts_id = get_object_or_404(Post.objects.select_related(
        'author', 'category', 'location'), id=post_id)
    if posts_id.author != request.user:
        posts_id = get_object_or_404(filter_posts(Post.objects), id=post_id)
    comment = Comment.objects.select_related(
        'author', 'post').filter(post__id=post_id).order_by('created_at')
    form = CommentForm()
    context = {'post': posts_id, 'form': form, 'comments': comment}
    return render(request, "blog/detail.html", context)


def category_posts(request, category_slug):
    category = get_object_or_404(Category, is_published=True,
                                 slug=category_slug)
    post_list = filter_posts(category.posts)
    page_obj = paginate_obj(request, post_list, posts_by_page)
    context = {"category": category,
               "page_obj": page_obj}
    return render(request, "blog/category.html", context)


def profile(request, username):
    profile = get_object_or_404(User, username=username)
    if request.user == profile:
        post_list = Post.objects.filter(
            author=profile).annotate(
                comment_count=Count('comments')
        ).order_by('-pub_date')
    else:
        post_list = Post.objects.filter(
            author=profile,
            pub_date__lte=now(),
            is_published=True
        ).annotate(comment_count=Count('comments')).order_by('-pub_date')
    page_obj = paginate_obj(request, post_list, posts_by_page)
    context = {'profile': profile, 'page_obj': page_obj}
    return render(request, 'blog/profile.html', context)


class OnlyAuthorMixin(UserPassesTestMixin):
    """Проверка авторства"""

    def test_func(self):
        return self.get_object().author == self.request.user


class PostCreate(LoginRequiredMixin, CreateView):
    """Создание поста"""

    model = Post
    form_class = PostForm
    paginate_by = posts_by_page
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:profile', kwargs={'username': self.object.author})


class EditPostView(OnlyAuthorMixin, UpdateView):
    """Редактирование поста"""

    model = Post
    pk_url_kwarg = 'post_id'
    form_class = PostForm
    template_name = 'blog/create.html'

    def dispatch(self, request, *args, **kwargs):
        post = self.get_object()
        if post.author != self.request.user:
            return redirect('blog:post_detail', post.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        post = self.get_object()
        return reverse_lazy('blog:post_detail', kwargs={'post_id': post.id})


class DeletePostView(OnlyAuthorMixin, DeleteView):
    """Удаление поста"""

    model = Post
    pk_url_kwarg = 'post_id'
    template_name = 'blog/create.html'
    success_url = reverse_lazy('blog:index')
