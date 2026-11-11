from django.urls import path

from .views import Create, CurrentUser, Login, Logout

urlpatterns = [
    path("create/", Create.as_view(), name="create"),
    path("login/", Login.as_view(), name="login"),
    path("logout/", Logout.as_view(), name="logout"),
    path("me/", CurrentUser.as_view(), name="current-user"),
]