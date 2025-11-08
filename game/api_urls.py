from django.urls import path
from . import views

urlpatterns = [
    path('start/', views.start_game, name='api_start_game'),
    path('place-shield/', views.place_shield, name='api_place_shield'),
    path('state/<int:game_id>/', views.get_game_state, name='api_game_state'),
    path('end/', views.end_game, name='api_end_game'),
]
