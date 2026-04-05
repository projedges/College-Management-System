# Bugfix Requirements Document

## Introduction

EduTrack has a functional core (auth, attendance, exams, assignments, quizzes, fees, reports) but
several workflows, features, and enforcement rules are either entirely absent or only partially
implemented. This document captures the defects as observable gaps — what the system currently
does (or fails to do), what it should do, and what existing behaviour must not regress.

The issues are grouped into six areas:
1. Missing administrative workflows (transfer, re-admission, fee waiver, grade appeal, parent portal, alumni)
2. Reporting gaps (export formats, scheduled delivery, per-student attendance, faculty performance, placement)
3. Fee system gaps (due dates, late fees, installment plans, fee-type breakdown, FeeStructure linkage)
4. Quiz enforcement gaps (server-side time limit, negative marking, shuffle, attempts limit)
5. Assignment gaps (file-type restrictions, late-submission penalty, plagiarism check)

---

## Bug Analysis

### Current Behavior (Defect)

**Section 1 — Missing Administrative Workflows**

1.1 WHEN an admin attempts to transfer a student from one department to another THEN the system
    has no transfer workflow, no URL, no view, and no audit model — the operation cannot be
    performed without direct database access.

1.2 WHEN a student with status `DROPPED` needs to be re-admitted THEN the system has no
    re-admission workflow; the `Student.status` field has no `READMITTED` state and no view
    exists to reinstate a dropped student.

1.3 WHEN a student qualifies for a fee waiver or scholarship THEN the system has no waiver or
    scholarship model, no approval workflow, and no mechanism to reduce the fee amount owed.

1.4 WHEN a student wants to appeal a grade THEN the system has `RevaluationRequest` for
    re-checking answer scripts but no grade appeal workflow for disputing a final published
    grade through an academic committee.

1.5 WHEN a parent logs in (or is given access) THEN the system has a `Parent` model with
    contact data but zero views, zero URLs, and no portal — parents cannot view their child's
    attendance, results, or fee status.

1.6 WHEN a student graduates (status `GRADUATED`) THEN the system has no alumni model, no
    alumni directory, no placement tracking, and no way to record post-graduation data.

**Section 2 — Reporting Gaps**

2.1 WHEN an admin requests a data export THEN the system generates PDF only via
    `admin_report_pdf`; there is no Excel/CSV export for reports (only a raw student CSV
    export exists at `admin_students_export_csv`).

2.2 WHEN an admin wants reports delivered on a schedule or via email THEN the system has no
    scheduled report task, no email delivery mechanism, and no Celery/cron integration.

2.3 WHEN an admin or faculty wants an attendance report broken down per individual student
    THEN `admin_report_pdf` for `attendance` aggregates only by department — no per-student
    attendance percentage report exists.

2.4 WHEN an admin wants a faculty performance report THEN the `FacultyPerformance` model
    exists (rating + feedback) but no view, URL, or report renders this data.

2.5 WHEN an admin wants placement statistics for graduated students THEN no placement model,
    no placement data entry, and no placement report exist.

**Section 3 — Fee System Gaps**

3.1 WHEN a fee record is created THEN the `Fee` model has no `due_date` field — there is no
    way to record or enforce a payment deadline.

3.2 WHEN a student pays after the due date THEN the system has no late fee or fine model and
    no logic to calculate or apply a penalty amount.

3.3 WHEN a student cannot pay the full semester fee at once THEN the system has no installment
    plan model — partial payments are tracked via `paid_amount` but there is no structured
    installment schedule.

3.4 WHEN a fee record is created THEN the `Fee` model stores only a single `total_amount` with
    no breakdown by fee type (tuition, exam fee, lab fee, library fee, etc.).

3.5 WHEN a fee record is auto-created for a student THEN the view at line 318 of `_legacy.py`
    falls back to a hardcoded `₹50,000` default (`structure.total_fees if structure else 50000.0`)
    instead of raising an error or requiring a `FeeStructure` record to exist — fees can be
    silently wrong when no `FeeStructure` is configured.

**Section 4 — Quiz Enforcement Gaps**

4.1 WHEN a student submits a quiz via a direct HTTP POST after the timer has expired THEN the
    server-side check at line 2914 of `_legacy.py` evaluates `if request.method == 'POST' or
    time_expired` — a POST always satisfies the condition regardless of `time_expired`, so a
    student who manipulates the client to delay the POST can submit answers after the time
    limit and have them graded normally.

4.2 WHEN a student answers a question incorrectly THEN the system awards 0 marks for that
    question; there is no negative marking field on `QuizQuestion` and no deduction logic.

4.3 WHEN a quiz is taken THEN questions and options are always presented in the same fixed
    order; there is no shuffle flag on `Quiz` and no randomisation logic.

4.4 WHEN a student has already submitted a quiz THEN `QuizAttempt` has a `unique_together`
    constraint on `(quiz, student)` preventing a second attempt, but there is no configurable
    `max_attempts` field on `Quiz` — it is permanently hardcoded to 1 with no way to allow
    retakes.

**Section 5 — Assignment Gaps**

5.1 WHEN a student submits an assignment THEN the `student_submit_assignment` view accepts any
    file type with no validation — there is no allowed-extensions list on `Assignment` and no
    server-side file-type check.

5.2 WHEN a student submits an assignment after the deadline THEN the submission is accepted
    without any penalty; there is no late-submission flag, no penalty percentage field on
    `Assignment`, and no deduction applied to `AssignmentSubmission.marks`.

5.3 WHEN two students submit identical or near-identical assignment files THEN the system
    performs no similarity check — there is no plagiarism detection field, flag, or integration.

---

### Expected Behavior (Correct)

**Section 1 — Missing Administrative Workflows**

2.1 WHEN an admin initiates a student department transfer THEN the system SHALL record the
    transfer with source department, target department, effective date, and reason; update
    `Student.department`; and maintain an audit trail.

2.2 WHEN an admin re-admits a dropped student THEN the system SHALL support a `READMITTED`
    status on `Student`, record the re-admission date and conditions, and restore the student
    to active standing.

2.3 WHEN an admin grants a fee waiver or scholarship THEN the system SHALL record the waiver
    amount or percentage, link it to the student's `Fee` record, and reduce the effective
    amount due accordingly.

2.4 WHEN a student submits a grade appeal THEN the system SHALL record the appeal against a
    specific published result, route it through a configurable review workflow, and allow an
    authorised reviewer to accept or reject it with remarks.

2.5 WHEN a parent authenticates or is given a view link THEN the system SHALL display that
    parent's linked student's attendance summary, current results, and fee payment status in a
    read-only portal.

2.6 WHEN a student's status is set to `GRADUATED` THEN the system SHALL allow recording of
    alumni data (graduation year, employment status, employer, further education) and expose
    an alumni directory to authorised users.

**Section 2 — Reporting Gaps**

2.1 WHEN an admin requests a data export THEN the system SHALL provide an Excel (`.xlsx`)
    export option in addition to PDF for attendance, payment, and result reports.

2.2 WHEN an admin configures a scheduled report THEN the system SHALL support periodic
    generation and email delivery of reports to configured recipients.

2.3 WHEN an admin or faculty requests a per-student attendance report THEN the system SHALL
    generate a report listing each student's attendance percentage per subject and overall for
    the selected semester.

2.4 WHEN an admin views faculty performance THEN the system SHALL render a report from
    `FacultyPerformance` records showing ratings, feedback, and attendance data per faculty.

2.5 WHEN an admin views placement statistics THEN the system SHALL display placement data for
    graduated students including employment rate, top recruiters, and average package.

**Section 3 — Fee System Gaps**

3.1 WHEN a fee record is created THEN the system SHALL store a `due_date` and display it to
    the student.

3.2 WHEN a student pays after the `due_date` THEN the system SHALL calculate and apply a
    configurable late fee or fine to the outstanding balance.

3.3 WHEN an admin creates an installment plan for a student THEN the system SHALL record
    individual installment due dates and amounts, and track payment against each installment.

3.4 WHEN a fee record is created THEN the system SHALL support a breakdown of the total into
    named fee-type components (e.g. tuition, exam fee, lab fee) that sum to the total.

3.5 WHEN no `FeeStructure` record exists for a student's college/department/semester THEN the
    system SHALL raise a visible configuration error rather than silently defaulting to
    ₹50,000.

**Section 4 — Quiz Enforcement Gaps**

4.1 WHEN a student submits a quiz via POST THEN the system SHALL check whether the elapsed
    time since `attempt.started_at` exceeds `quiz.duration_minutes * 60` (plus grace) and
    SHALL reject the submission with an error if the time limit has been exceeded, regardless
    of how the POST was triggered.

4.2 WHEN a student answers a question incorrectly and negative marking is enabled on the quiz
    THEN the system SHALL deduct the configured negative marks from the student's score for
    that question.

4.3 WHEN a quiz has shuffle enabled THEN the system SHALL present questions and/or options in
    a randomised order that is consistent within a single attempt but differs across students.

4.4 WHEN a quiz has a `max_attempts` value greater than 1 THEN the system SHALL allow a
    student to start a new attempt after submitting, up to the configured limit.

**Section 5 — Assignment Gaps**

5.1 WHEN a student submits an assignment THEN the system SHALL validate the uploaded file
    against the allowed extensions configured on the `Assignment` and reject disallowed types
    with a clear error message.

5.2 WHEN a student submits an assignment after the deadline THEN the system SHALL flag the
    submission as late and apply a configurable penalty percentage to the marks awarded.

5.3 WHEN an assignment submission is received THEN the system SHALL compute a similarity hash
    or score against other submissions for the same assignment and flag submissions that exceed
    a configurable similarity threshold for faculty review.

---

### Unchanged Behavior (Regression Prevention)

3.1 WHEN a student with status `ACTIVE` is viewed or edited through existing admin views THEN
    the system SHALL CONTINUE TO display and save the student record correctly without
    requiring a transfer or re-admission workflow.

3.2 WHEN an admin generates an attendance, payment, or result PDF report THEN the system SHALL
    CONTINUE TO produce a valid PDF via the existing `admin_report_pdf` view.

3.3 WHEN a `FeeStructure` record exists for a student's college/department/semester THEN the
    system SHALL CONTINUE TO use that structure's `total_fees` value when creating a fee
    record.

3.4 WHEN a student submits a quiz within the time limit via a normal browser POST THEN the
    system SHALL CONTINUE TO grade and record the submission correctly.

3.5 WHEN a student submits an assignment before the deadline with an allowed file type THEN
    the system SHALL CONTINUE TO accept the submission and store it without penalty.

3.6 WHEN a student makes a partial fee payment THEN the system SHALL CONTINUE TO update
    `Fee.paid_amount` and set `Fee.status` to `PARTIAL` as it does today.

3.7 WHEN a `RevaluationRequest` is submitted by a student THEN the system SHALL CONTINUE TO
    route it through the existing exam department revaluation workflow unchanged.

3.8 WHEN a parent record is read from the database THEN the system SHALL CONTINUE TO store
    and retrieve `Parent` data correctly — the existing model and admin registration of parent
    data must not be broken by adding portal views.
