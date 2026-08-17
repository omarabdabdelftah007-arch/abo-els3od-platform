from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .models import (
    StudentProfile, GRADE_CHOICES, SYSTEM_CHOICES, TopStudent, 
    Exam, StudentResult, Month, Subscription, Lecture
)
import re


# ══════════════════════════════════════════════
# 1. تسجيل حساب جديد (Signup)
# ══════════════════════════════════════════════
def signup_view(request):
    if request.method == 'POST':
        full_name      = request.POST.get('full_name')
        student_phone  = request.POST.get('student_phone')
        parent_phone   = request.POST.get('parent_phone')
        system         = request.POST.get('system')
        grade          = request.POST.get('grade')
        governorate    = request.POST.get('governorate')
        password       = request.POST.get('password')

        if User.objects.filter(username=full_name).exists():
            return render(request, 'signup.html', {
                'error': 'اسم الطالب هذا مسجل بالفعل، يرجى كتابة اسمك ثلاثي أو رباعي!',
                'grades': GRADE_CHOICES,
                'systems': SYSTEM_CHOICES,
            })

        try:
            user = User.objects.create_user(username=full_name, password=password)
            StudentProfile.objects.create(
                user=user,
                phone=student_phone,
                parent_phone=parent_phone,
                system=system,
                grade=grade,
                governorate=governorate,
            )
            login(request, user)
            return redirect('home')
        except Exception:
            return render(request, 'signup.html', {
                'error': 'حدث خطأ أثناء حفظ البيانات، يرجى المحاولة مرة أخرى.',
                'grades': GRADE_CHOICES,
                'systems': SYSTEM_CHOICES,
            })

    return render(request, 'signup.html', {
        'grades': GRADE_CHOICES,
        'systems': SYSTEM_CHOICES,
    })


# ══════════════════════════════════════════════
# 2. تسجيل الدخول (Signin)
# ══════════════════════════════════════════════
def signin_view(request):
    if request.method == 'POST':
        username_input = request.POST.get('username', '').strip()
        password = request.POST.get('password')

        # 🌟 لو الطالب كتب رقم تليفون (كل الحروف أرقام)، هنستخرج اسم المستخدم المربوط برقمه
        if username_input.isdigit():
            try:
                profile = StudentProfile.objects.filter(phone=username_input).first()
                if profile:
                    username_input = profile.user.username
            except Exception:
                pass

        # نمرر اسم المستخدم (سواء كتبه مباشر أو جبناه عن طريق رقم الفون)
        user = authenticate(request, username=username_input, password=password)

        if user is not None:
            if user.is_active:
                login(request, user)
                return redirect('home')
            else:
                return render(request, 'signin.html', {
                    'error': 'هذا الحساب تم تعطيله، تواصل مع الدعم الفني أو السكرتارية'
                })
        else:
            return render(request, 'signin.html', {
                'error': 'اسم المستخدم/رقم الهاتف أو كلمة المرور غير صحيحة!'
            })

    return render(request, 'signin.html')


# ══════════════════════════════════════════════
# 3. تسجيل الخروج (Signout)
# ══════════════════════════════════════════════
def signout_view(request):
    logout(request)
    return redirect('signin')


# ══════════════════════════════════════════════
# 4. الصفحة الرئيسية — مفتوحة للجميع
# ══════════════════════════════════════════════
def home_view(request):
    top_students = TopStudent.objects.all().order_by('arrange')
    courses = Month.objects.filter(is_active=True)

    completed_tasks_count       = 0
    total_completion_percentage = 0
    streak_days                 = 0
    student_profile             = None

    if request.user.is_authenticated:
        try:
            student_profile = request.user.studentprofile
            student_grade   = student_profile.grade
        except StudentProfile.DoesNotExist:
            student_profile = None
            student_grade   = '1'

        is_admin = request.user.is_staff or request.user.is_superuser
        if is_admin:
            top_students = TopStudent.objects.all().order_by('grade', 'arrange')
            courses = Month.objects.filter(is_active=True)
        else:
            top_students = TopStudent.objects.filter(grade=student_grade).order_by('arrange')
            courses = Month.objects.filter(grade=student_grade, is_active=True)

        user_results = StudentResult.objects.filter(student=request.user)
        completed_tasks_count = user_results.filter(status="مكتمل").count()

        total_attended = sum(r.attended_lessons for r in user_results)
        total_lessons  = sum(r.attended_lessons + r.remaining_lessons for r in user_results)
        course_pct     = (total_attended / total_lessons * 100) if total_lessons > 0 else 0

        total_exams = user_results.count()
        exam_pct    = (completed_tasks_count / total_exams * 100) if total_exams > 0 else 0

        total_completion_percentage = int((course_pct + exam_pct) / 2) if (total_exams or total_lessons) else 0
        streak_days = getattr(student_profile, 'streak', 0) if student_profile else 0

    context = {
        'profile': student_profile,
        'courses': courses,
        'top_students': top_students,
        'completed_tasks_count': completed_tasks_count,
        'total_completion_percentage': total_completion_percentage,
        'streak_days': streak_days,
    }
    return render(request, 'home.html', context)


# ══════════════════════════════════════════════
# 5. صفحة كل الكورسات — محمية بـ login
# ══════════════════════════════════════════════
@login_required(login_url='signin')
def courses_list_view(request):
    try:
        student_grade = request.user.studentprofile.grade
    except StudentProfile.DoesNotExist:
        student_grade = '1'

    months = Month.objects.filter(grade=student_grade)

    subscribed_ids = set(
        Subscription.objects.filter(
            student=request.user,
            is_active=True,
            month__isnull=False  # تضمن سحب اشتراكات الكورسات فقط
        ).values_list('month_id', flat=True)
    )

    months_list = []
    for month in months:
        month.is_subscribed = month.id in subscribed_ids
        months_list.append(month)

    return render(request, 'courses.html', {
        'months': months_list,
        'student_grade': student_grade,
    })


# ══════════════════════════════════════════════
# 6. صفحة كورساتي
# ══════════════════════════════════════════════
@login_required(login_url='signin')
def my_courses_view(request):
    all_subscriptions = Subscription.objects.filter(student=request.user, is_active=True).select_related('month', 'lecture')
    
    month_subscriptions = all_subscriptions.filter(month__isnull=False).order_by('month__grade', 'month__title')
    individual_subscriptions = all_subscriptions.filter(lecture__isnull=False).order_by('lecture__created_at')

    return render(request, 'my-courses.html', {
        'subscriptions': month_subscriptions,
        'individual_subscriptions': individual_subscriptions,
        'total_subscribed': month_subscriptions.count() + individual_subscriptions.count(),
    })


# ══════════════════════════════════════════════
# 7. صفحة مشاهدة كورس معين
# ══════════════════════════════════════════════
@login_required(login_url='signin')
def course_watch(request, month_id):
    month = get_object_or_404(Month, id=month_id)
    lecture_id = request.GET.get('lecture')
    
    has_month_access = Subscription.objects.filter(
        student=request.user,
        month=month,
        is_active=True
    ).exists()

    current_lecture = None
    
    if not has_month_access:
        if lecture_id:
            has_lecture_access = Subscription.objects.filter(
                student=request.user,
                lecture_id=lecture_id,
                is_active=True
            ).exists()
            
            if has_lecture_access:
                current_lecture = Lecture.objects.filter(id=lecture_id, month=month).first()
        
        if not current_lecture:
            return redirect('my_courses')

    if has_month_access:
        lectures = month.lectures.all().order_by('order', 'id')
        if lecture_id:
            current_lecture = lectures.filter(id=lecture_id).first()
        if not current_lecture and lectures.exists():
            current_lecture = lectures.first()
    else:
        lectures = Lecture.objects.filter(id=current_lecture.id)

    lectures_list = list(lectures)
    prev_lecture  = None
    next_lecture  = None

    if current_lecture and has_month_access:
        for i, lec in enumerate(lectures_list):
            if lec.id == current_lecture.id:
                if i > 0:
                    prev_lecture = lectures_list[i - 1]
                if i < len(lectures_list) - 1:
                    next_lecture = lectures_list[i + 1]
                break

    context = {
        'month'           : month,
        'lectures'        : lectures,
        'current_lecture' : current_lecture,
        'prev_lecture'    : prev_lecture,
        'next_lecture'    : next_lecture,
        'total'           : lectures.count(),
        'has_month_access': has_month_access,
    }
    return render(request, 'course_watch.html', context)


# ══════════════════════════════════════════════
# 8. صفحة الامتحانات
# ══════════════════════════════════════════════
@login_required(login_url='signin')
def exams_view(request):
    try:
        student_grade = request.user.studentprofile.grade
    except StudentProfile.DoesNotExist:
        student_grade = '1'

    subscribed_months = Subscription.objects.filter(
        student=request.user,
        is_active=True,
        month__isnull=False
    ).values_list('month_id', flat=True)

    exams_list = Exam.objects.filter(
        month__grade=student_grade,
        month_id__in=subscribed_months
    )

    return render(request, 'exams.html', {'exams': exams_list})


# ══════════════════════════════════════════════
# 9. صفحة النتائج (Dashboard) — مع ترجمة الأنظمة والصفوف للعربي
# ══════════════════════════════════════════════
@login_required(login_url='signin')
def results_view(request):
    user_results = StudentResult.objects.filter(student=request.user)

    try:
        profile = StudentProfile.objects.get(user=request.user)
    except StudentProfile.DoesNotExist:
        profile = None

    # قواميس ترجمة جميع قيم النظام التعليمي والصف الدراسي إلى اللغة العربية
    SYSTEM_MAP = {
        'general': 'عام',
        'General': 'عام',
        'azhari': 'أزهري',
        'Azhari': 'أزهري',
        'baccalaureate': 'بكالوريا',
        'Baccalaureate': 'بكالوريا',
        'bac': 'بكالوريا',
        'عام': 'عام',
        'أزهري': 'أزهري',
        'بكالوريا': 'بكالوريا',
    }

    GRADE_MAP = {
        '1': 'الصف الثاني الثانوي',
        '2': 'الصف الثالث الثانوي',
        '2sec': 'الصف الثاني الثانوي',
        '3sec': 'الصف الثالث الثانوي',
    }

    grade_ar = "غير محدد"
    system_ar = "غير محدد"

    if profile:
        # ترجمة الصف الدراسي
        if profile.grade:
            raw_grade = str(profile.grade).strip()
            grade_ar = GRADE_MAP.get(raw_grade, profile.get_grade_display() or raw_grade)

        # ترجمة النظام التعليمي
        if profile.system:
            raw_system = str(profile.system).strip().lower()
            system_ar = SYSTEM_MAP.get(raw_system, SYSTEM_MAP.get(str(profile.system).strip(), profile.get_system_display() or profile.system))

    # الحسابات الإحصائية
    total_attended = sum(r.attended_lessons for r in user_results)
    total_lessons  = sum(r.attended_lessons + r.remaining_lessons for r in user_results)
    course_view_percentage = int(total_attended / total_lessons * 100) if total_lessons > 0 else 0

    total_exams     = user_results.count()
    completed_exams = user_results.filter(status="مكتمل").count()
    exam_completion_percentage = int(completed_exams / total_exams * 100) if total_exams > 0 else 0

    total_scores = 0
    score_count  = 0
    for r in user_results:
        try:
            parts = str(r.score).split('/')
            if len(parts) == 2:
                student_score  = float(parts[0])
                total_possible = float(parts[1])
                total_scores  += (student_score / total_possible) * 100
                score_count   += 1
            else:
                score_val      = float(r.score)
                total_scores  += score_val
                score_count   += 1
        except (ValueError, TypeError):
            pass

    gpa_percentage = int(total_scores / score_count) if score_count > 0 else 0

    context = {
        'profile'                   : profile,
        'grade_ar'                  : grade_ar,
        'system_ar'                 : system_ar,
        'results'                   : user_results,
        'course_view_percentage'    : course_view_percentage,
        'exam_completion_percentage': exam_completion_percentage,
        'gpa_percentage'            : gpa_percentage,
    }
    return render(request, 'dashboard.html', context)


# ══════════════════════════════════════════════
# Helper — نجيب صف الطالب (داخلي)
# ══════════════════════════════════════════════
def _get_student_grade(user):
    try:
        return user.studentprofile.grade
    except StudentProfile.DoesNotExist:
        return '1'


@login_required
def take_exam_view(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    questions = exam.questions.all()
    
    if request.method == 'POST':
        correct_answers_count = 0
        total_questions = questions.count()
        user_answers_summary = {}

        for question in questions:
            field_name = f'question_{question.id}'
            student_choice = request.POST.get(field_name)
            
            if student_choice:
                student_choice = int(student_choice)
                is_correct = (str(student_choice).strip() == str(question.correct_answer).strip())
                if is_correct:
                    correct_answers_count += 1
                
                user_answers_summary[str(question.id)] = {
                    'student_choice': student_choice,
                    'is_correct': is_correct
                }

        score_percentage = (correct_answers_count / total_questions) * 100 if total_questions > 0 else 0

        StudentResult.objects.create(
            student=request.user,
            course_name=exam.title,
            score=f'{int(score_percentage)}/100',
            status='مكتمل',
            attended_lessons=1,
            remaining_lessons=0,
        )

        request.session[f'exam_score_{exam.id}'] = score_percentage
        request.session[f'exam_answers_{exam.id}'] = user_answers_summary

        return redirect('exam_result', exam_id=exam.id)
        
    context = {
        'exam': exam,
        'questions': questions,
    }
    return render(request, 'take_exam.html', context)


@login_required
def exam_result_view(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    questions = exam.questions.all()
    
    score = request.session.get(f'exam_score_{exam.id}', 0)
    user_answers = request.session.get(f'exam_answers_{exam.id}', {})
    
    questions_with_answers = []
    for question in questions:
        q_id_str = str(question.id)
        student_choice = user_answers.get(q_id_str, {}).get('student_choice', None)
        is_correct = user_answers.get(q_id_str, {}).get('is_correct', False)
        
        questions_with_answers.append({
            'object': question,
            'student_choice': student_choice,
            'is_correct': is_correct
        })

    context = {
        'exam': exam,
        'score': score,
        'questions_with_answers': questions_with_answers,
    }
    return render(request, 'exam_result.html', context)


@login_required(login_url='signin')
def enroll_free_course_view(request, month_id):
    month = get_object_or_404(Month, id=month_id)
    
    already_subscribed = Subscription.objects.filter(
        student=request.user, 
        month=month, 
        is_active=True
    ).exists()
    
    if already_subscribed:
        return redirect('course_watch', month_id=month.id)
    
    if hasattr(month, 'price') and month.price == 0:
        Subscription.objects.create(
            student=request.user,
            month=month,
            is_active=True
        )
        return redirect('course_watch', month_id=month.id)
    else:
        return redirect('courses_list')