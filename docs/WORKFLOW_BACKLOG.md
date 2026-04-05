# EduTrack Workflow Backlog

## Goal

Turn EduTrack from a demo-capable platform into a real-time college operations system by fixing workflow gaps in a practical order.

This backlog is derived from:

- [WORKFLOW_AUDIT.md](/d:/MY%20Res/Incomplete%20projects/test_posa_main_prj/College-Management-System/docs/WORKFLOW_AUDIT.md)

## Working Rule

We will fix one workflow area at a time, fully enough that it becomes usable in real college operations before moving to the next.

---

## Phase 1: Admissions And Onboarding

### Priority
`Highest`

### Why first

This is the entry point into the whole system. If onboarding is weak, every downstream workflow inherits bad data and manual follow-up work.

### Fixes

1. Expand registration request states
   - Add: `SUBMITTED`, `UNDER_REVIEW`, `NEEDS_CORRECTION`, `APPROVED`, `REJECTED`, `CONVERTED`

2. Add review metadata
   - reviewer
   - reviewed_at
   - review_notes
   - missing_documents / correction_reason

3. Improve admin request queue
   - filters by status, department, admission year
   - bulk status updates
   - queue-style cards/table instead of passive list only

4. Add student communication flow
   - notify when request is received
   - notify when corrections are needed
   - notify when account is created

5. Make onboarding field requirements configurable by college
   - mandatory profile fields
   - mandatory documents
   - optional guardian information

### Expected outcome

Admissions becomes a proper review workflow instead of a one-step conversion flow.

---

## Phase 2: Faculty Attendance Workflow

### Priority
`Highest`

### Why second

Attendance is a daily high-volume task. It must be fast, clear, and mistake-tolerant.

### Fixes

1. Add `Today’s Classes` faculty work queue
   - one-click entry into attendance for today’s scheduled slots
   - show slot time, room, subject, and state: `pending`, `marked`, `corrected`

2. Improve attendance session lifecycle
   - first mark
   - updated
   - corrected
   - locked

3. Add review summary before submit
   - present / absent / late totals
   - subject/date/slot confirmation

4. Improve correction workflow
   - visible correction history
   - reason required
   - HOD approval when configured

5. Add configurable attendance policy options
   - allow late marks or not
   - correction window
   - status types

### Expected outcome

Faculty can complete attendance from a task queue in a way that matches real timetable-driven work.

---

## Phase 3: Faculty Marks Workflow

### Priority
`Highest`

### Why third

Marks are sensitive academic records and need stronger operational control than raw data entry.

### Fixes

1. Add marks work queue
   - pending exams by subject
   - draft saved
   - submitted for review
   - locked

2. Add marks lifecycle states
   - `DRAFT`
   - `SUBMITTED`
   - `VERIFIED`
   - `LOCKED`

3. Add HOD / Exam Cell review path
   - submit to HOD or exam cell depending on exam type

4. Add bulk marks import
   - CSV upload
   - error report
   - duplicate / missing / invalid row handling

5. Show grading scheme context inside marks entry
   - max marks
   - pass threshold
   - special rules

### Expected outcome

Marks become an auditable academic workflow rather than a direct save form.

---

## Phase 4: Student Finance Ledger

### Priority
`Highest`

### Why fourth

Real colleges need a ledger, not just payment buttons.

### Fixes

1. Build unified student ledger
   - charges
   - payments
   - fines
   - adjustments
   - concessions
   - refunds

2. Unify fee categories
   - tuition
   - semester
   - exam
   - supply
   - revaluation
   - library
   - misc

3. Add offline verification workflow
   - `initiated`
   - `received`
   - `verified`
   - `applied`

4. Add student-facing request history
   - supply requests
   - revaluation requests
   - payment timeline

5. Add finance admin queue
   - pending verifications
   - failed payments
   - exceptions

### Expected outcome

Finance becomes transparent, traceable, and realistic for admin and students.

---

## Phase 5: Exam Cell Workflow

### Priority
`High`

### Fixes

1. Add exam service request timeline
   - supply
   - revaluation
   - override requests

2. Add configurable request windows
   - open date
   - close date
   - late fee rules

3. Add exam operations queues
   - schedules pending
   - hall tickets pending
   - results pending verification
   - revaluation pending review

4. Improve result publication lifecycle
   - computed
   - verified
   - published
   - revised

### Expected outcome

Exam operations become manageable as a workflow, not a collection of forms.

---

## Phase 6: HOD And Principal Operational Tools

### Priority
`High`

### Fixes

1. HOD inbox
   - faculty requests
   - leave requests
   - exemptions
   - attendance issues
   - substitution approvals

2. HOD batch actions
   - approve many
   - reject many
   - assign substitute

3. Principal oversight dashboard
   - trend views
   - exceptions
   - department comparison
   - escalation actions

### Expected outcome

Leadership roles become operationally useful, not just informational.

---

## Phase 7: College Policy Engine

### Priority
`High`

### Fixes

1. College-configurable onboarding policies
2. Attendance capture policies
3. Finance category and approval policies
4. Marks freeze / submission policies
5. Exam request and fee policies
6. Approval routing policies

### Expected outcome

Different colleges can run different processes without code changes.

---

## Phase 8: Accessibility And Usability

### Priority
`High`

### Fixes

1. Keyboard-only pass for all major workflows
2. Screen-reader labels and semantic structure review
3. Better focus states
4. Non-color-only status signaling
5. Accessible table filtering and action controls

### Expected outcome

The system becomes usable for a wider real-world audience and less error-prone for staff.

---

## Phase 9: Performance And Structural Optimization

### Priority
`Medium`

### Fixes

1. Break up [_legacy.py](/d:/MY%20Res/Incomplete%20projects/test_posa_main_prj/College-Management-System/students/views/_legacy.py)
2. Separate dashboards from task pages
3. Paginate all heavy lists
4. Reduce dashboard payload size
5. Strengthen scoped query helpers and middleware enforcement

### Expected outcome

The system stays usable as real data volume grows.

---

## Recommended Implementation Order

1. Admissions and onboarding
2. Faculty attendance
3. Faculty marks
4. Student finance ledger
5. Exam cell workflow
6. HOD and principal operational tools
7. College policy engine
8. Accessibility pass
9. Performance optimization

---

## Immediate Next Step

Start with:

`Phase 1: Admissions And Onboarding`

Reason:

- highest business impact
- affects data quality everywhere else
- currently closest to becoming a robust real workflow with moderate changes

