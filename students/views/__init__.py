"""
students/views package

All views are currently in _legacy.py (the original monolithic views.py).
New views should be added to the appropriate module:
  auth.py        — login, logout, register, home
  super_admin.py — super_admin_* views
  admin.py       — admin_* views
  principal.py   — principal_dashboard
  hod.py         — hod_* views
  faculty.py     — faculty_* views
  student.py     — student_* views
  lab.py         — lab_staff_dashboard
  helpdesk.py    — helpdesk_view, ticket_detail_view

_helpers.py contains all shared utilities and decorators.
"""

# Re-export everything from the legacy module so urls.py keeps working unchanged.
from ._legacy import *  # noqa: F401, F403
