from django.urls import path

urlpatterns = [
    path("verify", views.VerificationView.as_view(), name='verify'),
]