from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from .models import (
    Course,
    Module,
    Lesson,
    Test,
    Question,
    Answer,
    Task,
    UserProgress,
)  # 👈 ДОБАВИТЬ Task
import subprocess
import sys
import tempfile
import os


def course_list(request):
    """Список всех курсов"""
    courses = Course.objects.all()
    return render(request, "courses/course_list.html", {"courses": courses})


def course_detail(request, course_id):
    """Детальная страница курса"""
    course = get_object_or_404(Course, id=course_id)
    modules = course.modules.all()
    return render(
        request,
        "courses/course_detail.html",
        {
            "course": course,
            "modules": modules,
        },
    )


def lesson_detail(request, lesson_id):
    """Страница урока с навигацией и заданиями"""
    lesson = get_object_or_404(Lesson, id=lesson_id)

    # Все уроки в этом модуле
    lessons_in_module = list(lesson.module.lessons.all().order_by("order"))
    current_index = lessons_in_module.index(lesson)

    previous_lesson = (
        lessons_in_module[current_index - 1] if current_index > 0 else None
    )
    next_lesson = (
        lessons_in_module[current_index + 1]
        if current_index < len(lessons_in_module) - 1
        else None
    )

    # Проверяем, есть ли тест у этого урока
    has_test = hasattr(lesson, "test")

    # 👇 ДОБАВИТЬ: Получаем все задания для этого урока
    tasks = lesson.tasks.all().order_by("order")

    return render(
        request,
        "courses/lesson_detail.html",
        {
            "lesson": lesson,
            "previous_lesson": previous_lesson,
            "next_lesson": next_lesson,
            "has_test": has_test,
            "tasks": tasks,  # 👈 ДОБАВИТЬ задания в контекст
        },
    )


def test_detail(request, lesson_id):
    """Страница с тестом"""
    lesson = get_object_or_404(Lesson, id=lesson_id)
    test = get_object_or_404(Test, lesson=lesson)
    questions = test.questions.all().order_by("order")

    return render(
        request,
        "courses/test_detail.html",
        {
            "lesson": lesson,
            "test": test,
            "questions": questions,
        },
    )


def test_submit(request, lesson_id):
    """Обработка отправленного теста"""
    lesson = get_object_or_404(Lesson, id=lesson_id)
    test = get_object_or_404(Test, lesson=lesson)

    if request.method == "POST":
        score = 0
        total_questions = test.questions.count()

        # Проверяем каждый вопрос
        for question in test.questions.all():
            selected_answer_id = request.POST.get(f"question_{question.id}")
            if selected_answer_id:
                try:
                    selected_answer = Answer.objects.get(id=selected_answer_id)
                    if selected_answer.is_correct:
                        score += 1
                except Answer.DoesNotExist:
                    pass

        # Вычисляем процент
        if total_questions > 0:
            percentage = int((score / total_questions) * 100)
        else:
            percentage = 0

        passed = percentage >= test.passing_score

        return render(
            request,
            "courses/test_result.html",
            {
                "lesson": lesson,
                "test": test,
                "score": score,
                "total_questions": total_questions,
                "percentage": percentage,
                "passed": passed,
            },
        )

    return redirect("lesson_detail", lesson_id=lesson_id)


def task_detail(request, task_id):
    """Страница отдельного задания (опционально)"""
    task = get_object_or_404(Task, id=task_id)
    lesson = task.lesson

    # Навигация по заданиям
    tasks_in_lesson = list(lesson.tasks.all().order_by("order"))
    current_index = tasks_in_lesson.index(task)

    previous_task = tasks_in_lesson[current_index - 1] if current_index > 0 else None
    next_task = (
        tasks_in_lesson[current_index + 1]
        if current_index < len(tasks_in_lesson) - 1
        else None
    )

    return render(
        request,
        "courses/task_detail.html",
        {
            "task": task,
            "lesson": lesson,
            "previous_task": previous_task,
            "next_task": next_task,
        },
    )


@csrf_exempt
@require_http_methods(["POST"])
def run_code(request):
    """
    API для выполнения Python кода.
    Получает код от клиента, выполняет его и возвращает вывод.
    """
    code = request.POST.get("code", "")

    if not code or not code.strip():
        return JsonResponse({"output": "⚠️ Пожалуйста, введите код для выполнения"})

    try:
        # Создаем временный файл с кодом
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as f:
            f.write(code)
            temp_file = f.name

        # Выполняем код в отдельном процессе
        result = subprocess.run(
            [sys.executable, temp_file],
            capture_output=True,
            text=True,
            timeout=5,  # 5 секунд на выполнение
            cwd=os.path.dirname(temp_file) if os.path.dirname(temp_file) else None,
        )

        # Получаем вывод
        output = result.stdout if result.stdout else result.stderr

        if not output:
            output = "✅ Код выполнен успешно (нет вывода)"

        # Удаляем временный файл
        try:
            os.unlink(temp_file)
        except:
            pass

        return JsonResponse({"output": output})

    except subprocess.TimeoutExpired:
        return JsonResponse(
            {
                "output": "⏰ Превышено время выполнения (5 секунд). Проверьте, нет ли бесконечного цикла."
            }
        )

    except Exception as e:
        return JsonResponse({"output": f"❌ Ошибка выполнения: {str(e)}"})


def check_task(request, task_id):
    """Проверка задания и сохранение прогресса"""
    if request.method != "POST":
        return JsonResponse({"error": "Метод не поддерживается"}, status=405)

    task = get_object_or_404(Task, id=task_id)
    user_code = request.POST.get("code", "")

    # Проверяем, авторизован ли пользователь
    user = request.user if request.user.is_authenticated else None

    if not user_code.strip():
        return JsonResponse({"output": "⚠️ Введите код для проверки"})

    # Если у задания есть проверочный код
    if task.test_code:
        full_code = user_code + "\n\n" + task.test_code
    else:
        full_code = user_code

    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as f:
            f.write(full_code)
            temp_file = f.name

        result = subprocess.run(
            [sys.executable, temp_file], capture_output=True, text=True, timeout=5
        )

        output = result.stdout if result.stdout else result.stderr

        # ПРОВЕРЯЕМ, ПРАВИЛЬНО ЛИ ВЫПОЛНЕНО ЗАДАНИЕ
        is_correct = "✅" in output and (
            "Все тесты пройдены" in output or "Правильно" in output
        )

        if is_correct:
            # СОХРАНЯЕМ ПРОГРЕСС (отмечаем задание и урок выполненными)
            if user:
                # Отмечаем задание как выполненное (если добавим модель TaskProgress)
                # Отмечаем урок как пройденный
                progress, created = UserProgress.objects.get_or_create(
                    user=user, lesson=task.lesson, defaults={"is_completed": True}
                )
                if not progress.is_completed:
                    progress.is_completed = True
                    progress.save()
                    output += "\n\n✅ Прогресс сохранён! Урок отмечен как пройденный."
            else:
                output += "\n\n⚠️ Войдите в аккаунт, чтобы сохранить прогресс."

        if not output:
            output = "✅ Все тесты пройдены!"

        os.unlink(temp_file)

        return JsonResponse(
            {"output": output, "passed": "✅ Все тесты пройдены" in output}
        )

    except subprocess.TimeoutExpired:
        return JsonResponse({"output": "⏰ Превышено время выполнения"})
    except Exception as e:
        return JsonResponse({"output": f"❌ Ошибка: {str(e)}"})


@login_required
def complete_lesson(request, lesson_id):
    """Отметить урок как пройденный"""
    lesson = get_object_or_404(Lesson, id=lesson_id)

    progress, created = UserProgress.objects.get_or_create(
        user=request.user, lesson=lesson, defaults={"is_completed": True}
    )

    if not progress.is_completed:
        progress.is_completed = True
        progress.save()
        messages.success(request, f"✅ Урок '{lesson.title}' отмечен как пройденный!")
    else:
        messages.info(request, f"ℹ️ Урок '{lesson.title}' уже был пройден ранее.")

    return redirect("lesson_detail", lesson_id=lesson_id)
