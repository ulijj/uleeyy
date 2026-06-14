from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import SignUpForm, LoginForm
from .models import UserProfile
from courses.models import UserProgress, TestResult, Course, Lesson  # ← ИСПРАВЛЕНО
import pyotp
import qrcode
from io import BytesIO
import base64


def signup_view(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user)
            login(request, user)
            return redirect("/")
    else:
        form = SignUpForm()
    return render(request, "accounts/signup.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            user = authenticate(request, username=username, password=password)

            if user is not None:
                profile, created = UserProfile.objects.get_or_create(user=user)
                if profile.is_2fa_enabled:
                    request.session["pre_2fa_user_id"] = user.id
                    return redirect("accounts:verify_2fa")
                else:
                    login(request, user)
                    messages.success(request, f"Добро пожаловать, {username}!")
                    return redirect("/")
            else:
                messages.error(request, "Неверное имя пользователя или пароль.")
    else:
        form = LoginForm()

    return render(request, "accounts/login.html", {"form": form})


def verify_2fa_view(request):
    user_id = request.session.get("pre_2fa_user_id")
    if not user_id:
        return redirect("accounts:login")

    from django.contrib.auth.models import User

    user = User.objects.get(id=user_id)
    profile = UserProfile.objects.get(user=user)
    totp = pyotp.TOTP(profile.otp_secret)

    if request.method == "POST":
        otp_code = request.POST.get("otp_code")
        if totp.verify(otp_code):
            login(request, user)
            del request.session["pre_2fa_user_id"]
            messages.success(request, f"Добро пожаловать, {user.username}!")
            return redirect("/")
        else:
            messages.error(request, "Неверный код 2FA.")

    return render(request, "accounts/verify_2fa.html")


def logout_view(request):
    logout(request)
    messages.info(request, "Вы вышли из аккаунта.")
    return redirect("accounts:login")


@login_required
def profile_view(request):
    """Личный кабинет пользователя"""
    user = request.user

    # Получаем прогресс по урокам
    completed_lessons = UserProgress.objects.filter(user=user, is_completed=True)
    total_completed = completed_lessons.count()

    # Получаем все уроки, которые есть в курсах
    all_lessons = Lesson.objects.all()
    total_lessons = all_lessons.count()

    # Процент общего прогресса
    progress_percentage = (
        int((total_completed / total_lessons) * 100) if total_lessons > 0 else 0
    )

    # Результаты тестов
    test_results = TestResult.objects.filter(user=user)[:10]

    # Прогресс по курсам
    courses = Course.objects.all()
    course_progress = []

    for course in courses:
        lessons_in_course = Lesson.objects.filter(module__course=course).count()
        completed_in_course = UserProgress.objects.filter(
            user=user, is_completed=True, lesson__module__course=course
        ).count()

        course_percentage = (
            int((completed_in_course / lessons_in_course) * 100)
            if lessons_in_course > 0
            else 0
        )

        course_progress.append(
            {
                "course": course,
                "completed": completed_in_course,
                "total": lessons_in_course,
                "percentage": course_percentage,
            }
        )

    # Последние пройденные уроки
    recent_lessons = UserProgress.objects.filter(user=user, is_completed=True).order_by(
        "-completed_at"
    )[:5]

    context = {
        "user": user,
        "total_completed": total_completed,
        "total_lessons": total_lessons,
        "progress_percentage": progress_percentage,
        "test_results": test_results,
        "course_progress": course_progress,
        "recent_lessons": recent_lessons,
    }

    return render(request, "accounts/profile.html", context)


@login_required
def setup_2fa_view(request):
    """Настройка двухфакторной аутентификации"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    # Генерируем секретный ключ, если его нет
    if not profile.otp_secret:
        profile.otp_secret = pyotp.random_base32()
        profile.save()

    # Создаём TOTP объект
    totp = pyotp.TOTP(profile.otp_secret)

    # Генерируем URI для QR-кода
    provisioning_uri = totp.provisioning_uri(
        name=request.user.email, issuer_name="Uleeyy"
    )

    # Генерируем QR-код
    qr = qrcode.make(provisioning_uri)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()

    if request.method == "POST":
        otp_code = request.POST.get("otp_code")
        if totp.verify(otp_code):
            profile.is_2fa_enabled = True
            profile.save()
            messages.success(
                request, "✅ Двухфакторная аутентификация успешно настроена!"
            )
            return redirect("accounts:profile")
        else:
            messages.error(request, "❌ Неверный код. Попробуйте снова.")

    return render(
        request,
        "accounts/setup_2fa.html",
        {
            "qr_base64": qr_base64,
            "secret": profile.otp_secret,
        },
    )


def verify_2fa_view(request):
    """Проверка кода 2FA при входе"""
    user_id = request.session.get("pre_2fa_user_id")
    if not user_id:
        return redirect("accounts:login")

    from django.contrib.auth.models import User

    try:
        user = User.objects.get(id=user_id)
        profile = UserProfile.objects.get(user=user)
        totp = pyotp.TOTP(profile.otp_secret)
    except User.DoesNotExist:
        return redirect("accounts:login")
    except UserProfile.DoesNotExist:
        return redirect("accounts:login")

    if request.method == "POST":
        otp_code = request.POST.get("otp_code")
        if totp.verify(otp_code):
            login(request, user)
            del request.session["pre_2fa_user_id"]
            messages.success(request, f"Добро пожаловать, {user.username}!")
            return redirect("/")
        else:
            messages.error(request, "❌ Неверный код 2FA.")

    return render(request, "accounts/verify_2fa.html")
