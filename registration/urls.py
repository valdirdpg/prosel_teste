from django.conf.urls import url

import registration.views
from django.contrib.auth import views as auth_views
from registration import forms
from django.conf import settings

urlpatterns = [
    url(r"^login/$", registration.views.login, name="candidato_login"),
    url(r"^logout/$", registration.views.logout, name="candidato_logout"),
    url(
        r"^password_reset/$",
        auth_views.PasswordResetView.as_view(form_class=forms.BSPasswordResetForm),
        name="admin_password_reset",
        kwargs=dict(from_email=settings.EMAIL_FROM),
    ),
    url(
        r"^password_reset/done/$",
        auth_views.PasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    url(
        r"^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>.+)/$",
        auth_views.PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
        kwargs=dict(set_password_form=forms.BSSetPasswordForm),
    ),
    url(
        r"^reset/done/$",
        auth_views.PasswordChangeDoneView.as_view(),
        name="password_reset_complete",
    ),
]
