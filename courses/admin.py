from django.contrib import admin
from .models import Course, Module, Lesson, Test, Question, Answer, Task


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 4
    fields = ["text", "is_correct", "order"]
    ordering = ["order"]


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    fields = ["text", "order"]
    show_change_link = True
    ordering = ["order"]


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ["title", "description", "created_at"]
    list_display_links = ["title"]
    search_fields = ["title", "description"]
    ordering = ["-created_at"]


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ["title", "course", "order"]
    list_display_links = ["title"]
    list_editable = ["order"]
    list_filter = ["course"]
    search_fields = ["title"]
    ordering = ["course", "order"]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ["title", "module", "order"]  # Убрал duration_minutes
    list_display_links = ["title"]
    list_editable = ["order"]  # Убрал duration_minutes
    list_filter = ["module__course", "module"]
    search_fields = ["title", "content"]
    ordering = ["module", "order"]

    # Добавил поля для формы редактирования
    fieldsets = (
        ("Основная информация", {"fields": ("module", "title", "order")}),
        (
            "Контент урока",
            {
                "fields": ("content", "video_url"),
                "description": "Текст урока и ссылка на видео",
            },
        ),
    )


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = [
        "get_lesson_title",
        "passing_score",
    ]  # Используем метод вместо title
    list_display_links = ["get_lesson_title"]
    list_filter = ["lesson__module__course", "lesson__module"]
    search_fields = ["lesson__title"]
    ordering = ["lesson__module__course", "lesson__module", "lesson"]

    # Метод для отображения названия урока
    def get_lesson_title(self, obj):
        return obj.lesson.title

    get_lesson_title.short_description = "Урок"
    get_lesson_title.admin_order_field = "lesson__title"

    # Добавляем вопросы прямо в тесте
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ["text", "test", "order", "answers_count"]
    list_display_links = ["text"]
    list_editable = ["order"]
    list_filter = ["test__lesson__module__course", "test"]
    search_fields = ["text"]
    ordering = ["test", "order"]

    # Добавляем варианты ответов прямо в вопросе
    inlines = [AnswerInline]

    def answers_count(self, obj):
        return obj.answers.count()

    answers_count.short_description = "Количество ответов"


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ["text", "question", "is_correct", "order"]
    list_display_links = ["text"]
    list_editable = ["is_correct", "order"]
    list_filter = ["question__test", "is_correct"]
    search_fields = ["text"]
    ordering = ["question", "order"]


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ["title", "lesson", "points", "order"]
    list_display_links = ["title"]
    list_editable = ["points", "order"]
    list_filter = ["lesson__module__course", "lesson"]
    search_fields = ["title", "description"]
    fieldsets = (
        (
            "Основная информация",
            {"fields": ("lesson", "title", "description", "points", "order")},
        ),
        (
            "Код задания",
            {
                "fields": ("starter_code", "test_code"),
                "description": "starter_code — код, который видит студент. test_code — проверочный код (не показывается)",
            },
        ),
    )
