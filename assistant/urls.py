from django.urls import path
from . import views

app_name = "assistant"

urlpatterns = [

    path("feedback/", views.feedback_api, name="feedback"),
    path("questions/", views.user_questions_view, name="user_questions"),
     path("generate_summary/", views.generate_daily_summary, name="generate_daily_summary"),
     path("questions/generate-summary/", views.generate_daily_summary, name="generate_daily_summary"),
    

]
