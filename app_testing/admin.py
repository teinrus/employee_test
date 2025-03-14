from django.contrib import admin
from .models import Theme, Direction, Question, Answer, TestResult

@admin.register(Theme)
class ThemeAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]

@admin.register(Direction)
class DirectionAdmin(admin.ModelAdmin):
    list_display = ["name", "display_themes"]
    search_fields = ["name"]
    filter_horizontal = ("themes",)  # Позволяет выбирать несколько тем в админке

    def display_themes(self, obj):
        return ", ".join([theme.name for theme in obj.themes.all()])
    display_themes.short_description = "Темы"

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ["text", "direction", "display_themes"]
    search_fields = ["text"]
    filter_horizontal = ("themes",)  # Позволяет выбирать несколько тем в админке

    def display_themes(self, obj):
        return ", ".join([theme.name for theme in obj.themes.all()])
    display_themes.short_description = "Темы"

@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    list_display = ["surname", "direction", "correct_answers", "total_questions", "created_at"]
    search_fields = ["surname"]
