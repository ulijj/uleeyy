from django.contrib import admin
from .models import UserProfile
from courses.models import UserProgress, TestResult


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "is_2fa_enabled"]
    list_filter = ["is_2fa_enabled"]
    search_fields = ["user__username", "user__email"]


@admin.register(UserProgress)
class UserProgressAdmin(admin.ModelAdmin):
    list_display = ["user", "lesson", "is_completed", "completed_at"]
    list_filter = ["is_completed", "lesson__module__course"]
    search_fields = ["user__username", "lesson__title"]


@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    list_display = ["user", "test", "percentage", "passed", "completed_at"]
    list_filter = ["passed", "test__lesson__module__course"]
    search_fields = ["user__username"]
