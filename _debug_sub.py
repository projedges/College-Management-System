import django, os
os.environ['DJANGO_SETTINGS_MODULE'] = 'studentmanagementsystem.settings'
django.setup()
from students.models import Faculty, CollegeFeatureConfig, LeaveApplication, Substitution
from django.utils import timezone
from datetime import date

fac = Faculty.objects.get(user__username='fac_ml')
college = fac.department.college
feature_cfg = CollegeFeatureConfig.objects.filter(college=college).first()

print("Feature config:", feature_cfg)
if feature_cfg:
    print("  max_casual_leaves:", feature_cfg.max_casual_leaves)
    print("  max_substitutions:", feature_cfg.max_substitutions)

today = timezone.localdate()
current_year = today.year
leaves_this_year = LeaveApplication.objects.filter(
    faculty=fac, from_date__year=current_year, status__in=['APPROVED', 'PENDING']
)
print(f"\nLeaves this year: {leaves_this_year.count()}")

def _leave_days(qs, leave_type):
    total = 0
    for l in qs.filter(leave_type=leave_type):
        total += max((l.to_date - l.from_date).days + 1, 1)
    return total

leave_quota = {
    'CL': {'used': _leave_days(leaves_this_year, 'CL'), 'max': feature_cfg.max_casual_leaves if feature_cfg else 12},
    'ML': {'used': _leave_days(leaves_this_year, 'ML'), 'max': feature_cfg.max_medical_leaves if feature_cfg else 10},
    'EL': {'used': _leave_days(leaves_this_year, 'EL'), 'max': feature_cfg.max_earned_leaves if feature_cfg else 15},
    'OD': {'used': _leave_days(leaves_this_year, 'OD'), 'max': feature_cfg.max_od_leaves if feature_cfg else 20},
}
for k, v in leave_quota.items():
    v['remaining'] = max(v['max'] - v['used'], 0)
    print(f"  {k}: used={v['used']} max={v['max']} remaining={v['remaining']}")

sem_start_month = 7 if today.month >= 7 else 1
sem_start = date(today.year, sem_start_month, 1)
subs_used = Substitution.objects.filter(
    original_faculty=fac, date__gte=sem_start, status__in=['PENDING', 'ACCEPTED']
).count()
sub_max = feature_cfg.max_substitutions if feature_cfg else 10
print(f"\nSubs used: {subs_used}/{sub_max}, remaining: {max(sub_max-subs_used,0)}")
print("\nAll OK - no errors")
