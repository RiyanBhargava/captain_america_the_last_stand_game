from django.urls import path
from . import views

urlpatterns = [
    path('', views.game_view, name='game'),
    path('leaderboard/', views.leaderboard_view, name='leaderboard'),
]

# API URLs
api_urlpatterns = [
    path('api/game/state/<int:game_id>/', views.get_game_state, name='get_game_state'),
    path('api/game/start/', views.start_game, name='start_game'),
    path('api/game/place-shield/', views.place_shield, name='place_shield'),
]

urlpatterns += api_urlpatterns
