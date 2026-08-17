import re
from django.db import models
from django.contrib.auth.models import User


# 1. خيارات الصفوف الدراسية والنظم التعليمية
GRADE_CHOICES = (
    ('1', 'الصف الثاني الثانوي'),
    ('2', 'الصف الثالث الثانوي'),
)

SYSTEM_CHOICES = (
    ('general', 'عام'),
    ('azhari', 'أزهري'),
    ('baccalaureate', 'بكالوريا'),
)
# 2. بروفايل الطالب
class StudentProfile(models.Model):
    user         = models.OneToOneField(User, on_delete=models.CASCADE, related_name='studentprofile')
    phone        = models.CharField(max_length=15, verbose_name="رقم تليفون الطالب")
    parent_phone = models.CharField(max_length=15, blank=True, null=True, verbose_name="رقم تليفون ولي الأمر")
    system       = models.CharField(max_length=20, choices=SYSTEM_CHOICES, default='general', verbose_name="النظام التعليمي")
    governorate  = models.CharField(max_length=50, blank=True, null=True, verbose_name="المحافظة")
    grade        = models.CharField(max_length=1, choices=GRADE_CHOICES, default='1', verbose_name="الصف الدراسي")
    streak       = models.IntegerField(default=0, verbose_name="أيام متتالية")

    class Meta:
        verbose_name        = "بروفايل الطالب"
        verbose_name_plural = "👤 بروفايل الطلاب"

    def __str__(self):
        return self.user.username


# 3. الكورسات/الشهور التعليمية
class Month(models.Model):
    title       = models.CharField(max_length=200, verbose_name="اسم الكورس/الشهر")
    description = models.TextField(blank=True, verbose_name="وصف الكورس")
    grade       = models.CharField(max_length=1, choices=GRADE_CHOICES, default='1', verbose_name="الصف الدراسي")
    thumbnail   = models.ImageField(upload_to='months/thumbnails/', blank=True, null=True, verbose_name="صورة الكورس")
    price       = models.DecimalField(max_digits=6, decimal_places=2, default=0, verbose_name="سعر الكورس")
    is_active   = models.BooleanField(default=True, verbose_name="ظاهر للطلاب؟")
    created_at  = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")

    class Meta:
        verbose_name        = "كورس/شهر"
        verbose_name_plural = "📚 الكورسات والشهور"
        ordering            = ['grade', 'title']

    def __str__(self):
        return f"{self.title} — {self.get_grade_display()}"

    def lectures_count(self):
        return self.lectures.count()

    def exams_count(self):
        return self.exams.count()


# 4. المحاضرات
class Lecture(models.Model):
    title         = models.CharField(max_length=200, verbose_name="عنوان المحاضرة")
    month         = models.ForeignKey(Month, on_delete=models.CASCADE, related_name='lectures', verbose_name="التابع لكورس")
    video_url     = models.URLField(blank=True, null=True, verbose_name="رابط فيديو المحاضرة")
    pdf_file      = models.FileField(upload_to='lectures_pdf/', blank=True, null=True, verbose_name="ملف PDF للمحاضرة")
    order         = models.IntegerField(default=1, verbose_name="ترتيب المحاضرة")
    is_individual = models.BooleanField(default=False, verbose_name="محاضرة منفصلة؟")
    created_at    = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    class Meta:
        verbose_name        = "محاضرة"
        verbose_name_plural = "🎥 المحاضرات"
        ordering            = ['order', 'id']

    def __str__(self):
        return self.title

    def get_embed_url(self):
        if not self.video_url:
            return ""
        
        regex = r'(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/|youtube\.com\/shorts\/)([^"&?\/\s]{11})'
        match = re.search(regex, self.video_url)
        
        if match:
            video_id = match.group(1)
            return f"https://www.youtube-nocookie.com/embed/{video_id}?rel=0&modestbranding=1&origin=http://127.0.0.1:8000"
        
        return self.video_url


# 5. اشتراكات الطلاب
class Subscription(models.Model):
    student       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions', verbose_name="الطالب")
    month         = models.ForeignKey(Month, on_delete=models.CASCADE, blank=True, null=True, related_name='subscriptions', verbose_name="الكورس المشترك فيه")
    lecture       = models.ForeignKey(Lecture, on_delete=models.CASCADE, blank=True, null=True, related_name='subscriptions', verbose_name="المحاضرة الفردية (اختياري)")
    is_active     = models.BooleanField(default=False, verbose_name="مفعّل؟")
    subscribed_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الاشتراك")

    class Meta:
        verbose_name        = "اشتراك"
        verbose_name_plural = "💳 اشتراكات الطلاب"

    def __str__(self):
        status = "✅" if self.is_active else "⏳"
        if self.lecture:
            return f"{status} {self.student.username} ← محاضرة فردية: {self.lecture.title}"
        return f"{status} {self.student.username} ← كورس: {self.month.title if self.month else 'غير محدد'}"


# 6. الامتحانات
class Exam(models.Model):
    title            = models.CharField(max_length=200, verbose_name="عنوان الامتحان")
    month            = models.ForeignKey(Month, on_delete=models.CASCADE, blank=True, null=True, related_name='exams', verbose_name="التابع لكورس")
    lecture          = models.ForeignKey(Lecture, on_delete=models.SET_NULL, blank=True, null=True, related_name='exams', verbose_name="تابع لمحاضرة (اختياري)")
    is_comprehensive = models.BooleanField(default=False, verbose_name="امتحان شامل؟")
    duration_mins    = models.IntegerField(default=30, verbose_name="مدة الامتحان بالدقائق")

    class Meta:
        verbose_name        = "امتحان"
        verbose_name_plural = "📝 الامتحانات"

    def __str__(self):
        return self.title


# 7. الأسئلة
class Question(models.Model):
    exam    = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='questions', verbose_name="الامتحان")
    text    = models.TextField(verbose_name="نص السؤال")
    image   = models.ImageField(upload_to='questions_images/', blank=True, null=True, verbose_name="صورة مع السؤال (اختياري)")
    choice1 = models.CharField(max_length=255, verbose_name="الاختيار الأول")
    choice2 = models.CharField(max_length=255, verbose_name="الاختيار الثاني")
    choice3 = models.CharField(max_length=255, verbose_name="الاختيار الثالث")
    choice4 = models.CharField(max_length=255, verbose_name="الاختيار الرابع")

    CORRECT_ANSWER_CHOICES = [
        ('1', 'الاختيار الأول'),
        ('2', 'الاختيار الثاني'),
        ('3', 'الاختيار الثالث'),
        ('4', 'الاختيار الرابع'),
    ]
    correct_answer = models.CharField(max_length=1, choices=CORRECT_ANSWER_CHOICES, verbose_name="الإجابة الصحيحة")

    class Meta:
        verbose_name        = "سؤال"
        verbose_name_plural = "❓ الأسئلة"

    def __str__(self):
        return f"سؤال في: {self.exam.title}"


# 8. لوحة أوائل الطلاب
class TopStudent(models.Model):
    student_name        = models.CharField(max_length=150, verbose_name="اسم الطالب المتفوق")
    score_or_percentage = models.CharField(max_length=50, verbose_name="الدرجة أو النسبة")
    grade               = models.CharField(max_length=1, choices=GRADE_CHOICES, verbose_name="الصف الدراسي")
    image               = models.ImageField(upload_to="top_students/", blank=True, null=True, verbose_name="صورة الطالب (اختياري)")
    arrange             = models.IntegerField(default=1, verbose_name="الترتيب")

    class Meta:
        verbose_name        = "طالب متفوق"
        verbose_name_plural = "🏆 لوحة الأوائل"

    def __str__(self):
        return f"{self.student_name} - الترتيب: {self.arrange}"


# 9. لوحة نتائج ومتابعة الطلاب
class StudentResult(models.Model):
    student           = models.ForeignKey(User, on_delete=models.CASCADE, related_name='results', verbose_name="الطالب")
    course_name       = models.CharField(max_length=200, verbose_name="اسم الكورس / الامتحان")
    score             = models.CharField(max_length=50, verbose_name="الدرجة")
    attended_lessons  = models.IntegerField(default=0, verbose_name="المحاضرات المحضورة")
    remaining_lessons = models.IntegerField(default=0, verbose_name="المحاضرات المتبقية")
    status            = models.CharField(max_length=50, default="جاري", verbose_name="الحالة")

    class Meta:
        verbose_name        = "نتيجة ومتابعة الطالب"
        verbose_name_plural = "📊 لوحة متابعة النتائج"

    def __str__(self):
        return f"{self.student.username} - {self.course_name}"