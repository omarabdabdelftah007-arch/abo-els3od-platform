from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from unfold.admin import ModelAdmin, TabularInline, StackedInline
from .models import (
    Month, Lecture, StudentProfile, Subscription,
    Exam, Question, TopStudent, StudentResult
)


# ══════════════════════════════════════════════
# 1. أسئلة الامتحان (Inline جوه الامتحان)
# ══════════════════════════════════════════════
class QuestionInline(TabularInline):
    model  = Question
    extra  = 3
    fields = ('text', 'image', 'choice1', 'choice2', 'choice3', 'choice4', 'correct_answer')


# ══════════════════════════════════════════════
# 2. الامتحانات
# ══════════════════════════════════════════════
@admin.register(Exam)
class ExamAdmin(ModelAdmin):
    inlines      = [QuestionInline]
    list_display = ('title', 'month', 'duration_mins', 'is_comprehensive')
    list_filter  = ('is_comprehensive', 'month')
    search_fields = ('title',)


# ══════════════════════════════════════════════
# 3. بروفايل الطالب (Inline جوه User)
# ══════════════════════════════════════════════
class StudentProfileInline(StackedInline):
    model          = StudentProfile
    can_delete     = False
    verbose_name   = "بروفايل الطالب"


# ══════════════════════════════════════════════
# 4. اشتراكات الطالب (Inline جوه User) - معدل ليدعم المحاضرة الفردية
# ══════════════════════════════════════════════
class SubscriptionInline(TabularInline):
    model         = Subscription
    extra         = 1
    fields        = ('month', 'lecture', 'is_active', 'subscribed_at')  # إضافة حقل المحاضرة الفردية هنا
    readonly_fields = ('subscribed_at',)
    verbose_name  = "اشتراك الطالب"


# ══════════════════════════════════════════════
# 5. لوحة تحكم Users
# ══════════════════════════════════════════════
admin.site.unregister(User)

@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    inlines      = (StudentProfileInline, SubscriptionInline)
    list_display = ('username', 'get_phone', 'get_grade', 'get_active_subs', 'is_active', 'is_staff')
    search_fields = ('username', 'studentprofile__phone')
    list_filter  = ('is_active', 'is_staff', 'studentprofile__grade')

    def get_phone(self, obj):
        try:
            return obj.studentprofile.phone
        except Exception:
            return "—"
    get_phone.short_description = "التليفون"

    def get_grade(self, obj):
        try:
            return obj.studentprofile.get_grade_display()
        except Exception:
            return "—"
    get_grade.short_description = "الصف"

    def get_active_subs(self, obj):
        count = obj.subscriptions.filter(is_active=True).count()
        return f"{count} اشتراك نشط"
    get_active_subs.short_description = "الاشتراكات المفعّلة"


# ══════════════════════════════════════════════
# 6. الكورسات/الشهور
# ══════════════════════════════════════════════
class LectureInline(TabularInline):
    model   = Lecture
    extra   = 1
    fields  = ('title', 'order', 'video_url', 'pdf_file', 'is_individual')  # إضافة الحقل هنا ليسهل تفعيله فوراً
    ordering = ('order',)


class ExamInline(TabularInline):
    model   = Exam
    extra   = 0
    fields  = ('title', 'duration_mins', 'is_comprehensive')


@admin.register(Month)
class MonthAdmin(ModelAdmin):
    inlines      = [LectureInline, ExamInline]
    list_display = ('title', 'grade', 'price', 'is_active', 'get_lectures_count', 'get_subs_count', 'created_at')
    list_filter  = ('grade', 'is_active')
    search_fields = ('title',)
    list_editable = ('is_active', 'price')

    def get_lectures_count(self, obj):
        return f"{obj.lectures.count()} محاضرة"
    get_lectures_count.short_description = "المحاضرات"

    def get_subs_count(self, obj):
        return f"{obj.subscriptions.filter(is_active=True).count()} طالب"
    get_subs_count.short_description = "الطلاب المشتركين"


# ══════════════════════════════════════════════
# 7. المحاضرات
# ══════════════════════════════════════════════
@admin.register(Lecture)
class LectureAdmin(ModelAdmin):
    list_display  = ('title', 'month', 'order', 'is_individual', 'created_at')
    list_filter   = ('month', 'month__grade', 'is_individual')
    search_fields = ('title',)
    list_editable = ('is_individual',)  # تتيح للمدرس قلب المحاضرة لفردية من الجدول مباشرة
    ordering      = ('month', 'order')


# ══════════════════════════════════════════════
# 8. اشتراكات الطلاب - معدل بالكامل للمرونة
# ══════════════════════════════════════════════
@admin.action(description="✅ تفعيل الاشتراكات المحددة")
def activate_subscriptions(modeladmin, request, queryset):
    queryset.update(is_active=True)

@admin.action(description="❌ إلغاء تفعيل الاشتراكات المحددة")
def deactivate_subscriptions(modeladmin, request, queryset):
    queryset.update(is_active=False)

@admin.register(Subscription)
class SubscriptionAdmin(ModelAdmin):
    list_display  = ('student', 'get_subscription_target', 'is_active', 'subscribed_at')
    list_filter   = ('is_active', 'month', 'lecture', 'month__grade')
    search_fields = ('student__username', 'month__title', 'lecture__title')
    list_editable = ('is_active',)
    actions       = [activate_subscriptions, deactivate_subscriptions]

    # دالة ذكية لعرض نوع الاشتراك (شهر كامل أم محاضرة فردية) في الجدول بشكل منسق
    def get_subscription_target(self, obj):
        if obj.lecture:
            return f"🎥 محاضرة فردية: {obj.lecture.title}"
        elif obj.month:
            return f"📚 كورس: {obj.month.title}"
        return "—"
    get_subscription_target.short_description = "نوع الاشتراك / المحتوى المتاح"


# ══════════════════════════════════════════════
# 9. نتائج الطلاب
# ══════════════════════════════════════════════
@admin.register(StudentResult)
class StudentResultAdmin(ModelAdmin):
    list_display  = ('student', 'course_name', 'score', 'status', 'attended_lessons')
    list_filter   = ('status',)
    search_fields = ('student__username', 'course_name')
    list_editable = ('score', 'status')
    ordering      = ('-score',)


# ══════════════════════════════════════════════
# 10. لوحة أوائل الطلاب
# ══════════════════════════════════════════════
@admin.register(TopStudent)
class TopStudentAdmin(ModelAdmin):
    list_display  = ('student_name', 'grade', 'arrange', 'score_or_percentage')
    list_filter   = ('grade',)
    ordering      = ('grade', 'arrange')
    search_fields = ('student_name',)