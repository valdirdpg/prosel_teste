from django.conf.urls import url
from monitoring import views

urlpatterns = [
    url("^jobs/$", views.ListJobView.as_view(), name="list_job_monitoring"),
    url(r"^wait/(?P<pk>[\d]+)/$", views.WaitView.as_view(), name="wait_view"),
    url(
        r"^job_check/(?P<pk>[\d]+)/$",
        views.AjaxCheckView.as_view(),
        name="ajax_check_job",
    ),
]
