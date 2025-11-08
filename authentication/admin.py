from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'total_score', 'games_played', 'games_won', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('-total_score',)
    
    fieldsets = UserAdmin.fieldsets + (
        ('Game Stats', {
            'fields': ('google_id', 'avatar_url', 'total_score', 'games_played', 'games_won', 'best_score')
        }),
    )
