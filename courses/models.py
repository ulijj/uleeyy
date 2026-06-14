from django.db import models
from django.contrib.auth.models import User


class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to="courses/", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Module(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="modules")
    title = models.CharField(max_length=200)
    order = models.IntegerField()

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.title


class Lesson(models.Model):
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=200)
    content = models.TextField()
    video_url = models.URLField(blank=True)
    order = models.IntegerField()

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.title


class Test(models.Model):
    lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE)
    passing_score = models.IntegerField(default=70)

    def __str__(self):
        return f"Test for {self.lesson.title}"


class Question(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField()
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.text[:50]


class Answer(models.Model):
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="answers"
    )
    text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.text} ({'✓' if self.is_correct else '✗'})"


class Task(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="tasks")
    title = models.CharField(max_length=200, verbose_name="Название")
    description = models.TextField(verbose_name="Описание")
    starter_code = models.TextField(
        blank=True,
        help_text="Код, который будет показан студенту для начала работы",
        verbose_name="Начальный код",
    )
    test_code = models.TextField(
        help_text="Код для проверки решения студента (выполняется на сервере)",
        verbose_name="Проверочный код",
    )
    points = models.IntegerField(default=10, verbose_name="Баллы")
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.title


class UserProgress(models.Model):
    """Прогресс пользователя по курсам"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="progress")
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["user", "lesson"]
        ordering = ["completed_at"]

    def __str__(self):
        return f"{self.user.username} - {self.lesson.title} - {'✅' if self.is_completed else '❌'}"


class TestResult(models.Model):
    """Результаты прохождения тестов"""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="test_results"
    )
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    score = models.IntegerField()
    total_questions = models.IntegerField()
    percentage = models.IntegerField()
    passed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-completed_at"]

    def __str__(self):
        return f"{self.user.username} - {self.test.lesson.title} - {self.percentage}%"
