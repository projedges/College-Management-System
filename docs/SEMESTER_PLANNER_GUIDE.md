# Semester Planner — Testing Guide & User Manual

**URL:** `/dashboard/admin/academic-planner/`  
**Access:** College Admin only  
**Purpose:** Set up subjects, assign faculty, configure classrooms and breaks, and generate or upload a weekly timetable for any department and semester.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Getting to the Planner](#2-getting-to-the-planner)
3. [Selecting Department and Semester](#3-selecting-department-and-semester)
4. [Stats Bar](#4-stats-bar)
5. [Section Strength](#5-section-strength)
6. [Adding Subjects](#6-adding-subjects)
7. [Assigning Faculty to Subjects](#7-assigning-faculty-to-subjects)
8. [Faculty Availability](#8-faculty-availability)
9. [Faculty Assignment Map](#9-faculty-assignment-map)
10. [CSV Timetable Upload](#10-csv-timetable-upload)
11. [Auto-Generate Timetable](#11-auto-generate-timetable)
12. [Viewing the Generated Timetable](#12-viewing-the-generated-timetable)
13. [Break Management](#13-break-management)
14. [Classroom Management](#14-classroom-management)
15. [Complete Testing Checklist](#15-complete-testing-checklist)
16. [Common Errors and Fixes](#16-common-errors-and-fixes)
17. [Expected Behaviour Reference](#17-expected-behaviour-reference)

---

## 1. Overview

The Semester Planner is the central workspace for building a semester's academic schedule. The workflow is:

```
Add Subjects
    ↓
Assign Faculty to Subjects  (each assignment = one section)
    ↓
Set Faculty Availability  (optional — used by auto-generator)
    ↓
Add Classrooms  (with room type and features)
    ↓
Add Breaks  (lunch, tea, events)
    ↓
Generate Timetable  (auto or CSV upload)
    ↓
Review Weekly Matrix
```

Everything on this page is scoped to one **department + semester** at a time.

---

## 2. Getting to the Planner

1. Log in as College Admin
2. From the sidebar click **Semester Planner**  
   — or go directly to `/dashboard/admin/academic-planner/`
3. The page loads with the first department and Semester 1 selected by default

---

## 3. Selecting Department and Semester

At the top of the page there are two dropdowns:

| Control | What it does |
|---|---|
| Department dropdown | Switches the entire page to that department's data |
| Semester dropdown | Switches to that semester within the selected department |

Both dropdowns **auto-submit** on change — no button needed.

**Test:**
- [ ] Change department — page reloads with correct department name in heading
- [ ] Change semester — stats and subject list update to match
- [ ] Both dropdowns retain selection after a POST action (add subject, assign faculty, etc.)

---

## 4. Stats Bar

Below the filter bar, four stat cards show:

| Card | What it counts |
|---|---|
| Semester Subjects | Subjects added for this dept + semester |
| Faculty Assignments | FacultySubject records for those subjects |
| Availability Slots | FacultyAvailability records for faculty in this dept |
| Timetable Entries | Timetable rows for subjects in this dept + semester |

**Test:**
- [ ] All four cards show 0 on a fresh department/semester
- [ ] Adding a subject increments "Semester Subjects" by 1
- [ ] Assigning faculty increments "Faculty Assignments" by 1
- [ ] Generating timetable increments "Timetable Entries"

---

## 5. Section Strength

Shows how many students are in each section for the selected dept + semester.

- Pulls from `Student.section` field filtered by dept + current_semester
- Displays as coloured pills: `Section A: 42`, `Section B: 38`
- Shows "No student sections formed yet" if no students are assigned

**Test:**
- [ ] Shows correct count per section when students exist
- [ ] Shows empty state message when no students are in this semester
- [ ] Reflects changes immediately after a student's section is updated

---

## 6. Adding Subjects

**Card:** "Add Subject to Semester"

| Field | Required | Notes |
|---|---|---|
| Subject Name | Yes | e.g. "Machine Learning" |
| Subject Code | Yes | e.g. "ISE501" — auto-uppercased |

On submit, the subject is created with `department` and `semester` set from the current filter.

**Test:**
- [ ] Add a subject with a unique name and code → success message, appears in "Current Semester Subjects" table
- [ ] Try adding the same code again → error: "Subject code already exists"
- [ ] Try adding the same name again (different code) → error: "Subject already exists"
- [ ] Leave name blank → browser validation prevents submit
- [ ] Leave code blank → browser validation prevents submit
- [ ] Subject appears in the "Assign Faculty" subject dropdown immediately after adding

**Edge cases:**
- [ ] Code with lowercase letters → saved as uppercase (e.g. "ise501" → "ISE501")
- [ ] Same code in a different department → allowed (codes are unique per dept, not globally)
- [ ] Same code in a different semester of the same dept → allowed

---

## 7. Assigning Faculty to Subjects

**Card:** "Assign Faculty to Subject"

| Field | Required | Notes |
|---|---|---|
| Subject | Yes | Dropdown of subjects in current dept + semester |
| Faculty | Yes | Dropdown of ALL faculty in the college (any dept) |

Each assignment creates one section. Two assignments for the same subject = Section A and Section B.

**Test:**
- [ ] Assign one faculty to a subject → success: "Assigned to ISE501 — Section A"
- [ ] Assign a second faculty to the same subject → success: "Assigned to ISE501 — Section B"
- [ ] Assign the same faculty to the same subject again → warning: "already assigned"
- [ ] Assign faculty from a different department → allowed (cross-dept teaching is valid)
- [ ] Faculty dropdown shows "(dept code)" next to each name for clarity

**Section labelling:**
- First assignment → Section A
- Second assignment → Section B
- Third → Section C (A/B/C based on total count at time of assignment)

---

## 8. Faculty Availability

**Card:** "Faculty Availability"

| Field | Required | Notes |
|---|---|---|
| Faculty | Yes | Only faculty in the selected department |
| Day | Yes | MON / TUE / WED / THU / FRI / SAT |
| Start Time | Yes | HH:MM (24-hour) |
| End Time | Yes | HH:MM (24-hour) |

Availability slots are used by the auto-generator to decide when to schedule a faculty member.  
If no availability is set, the generator falls back to the default time grid (09:00–16:00 Mon–Fri + Sat morning).

**Test:**
- [ ] Add availability for a faculty on Monday 09:00–10:00 → success message, appears in "Availability Slots" table
- [ ] Add the same slot again → Django unique_together prevents duplicate (error or silent skip)
- [ ] Add availability for a faculty not in this department → faculty won't appear in the dropdown (dept-filtered)
- [ ] Availability table shows Faculty / Day / Time columns correctly

**Note:** The new `availability_type` (available/preferred/blocked), `priority_score`, `valid_from`, `valid_to`, and `notes` fields are in the database but not yet surfaced in this form. They default to `available`, priority 5, permanent.

---

## 9. Faculty Assignment Map

**Card:** "Faculty Assignment Map — Sections"

Shows all faculty-subject assignments grouped by subject. Each row = one section.

| Column | What it shows |
|---|---|
| Subject | Code + name (merged cell for multi-section subjects) |
| Section | Sec A, Sec B, Sec C... |
| Faculty | Full name |
| Dept | Faculty's home department code |
| (remove) | Unlink button |

**Test:**
- [ ] Single-faculty subject shows one row with no rowspan
- [ ] Two-faculty subject shows two rows with subject cell spanning both
- [ ] Click the unlink (chain-break) icon → assignment removed, section count decreases
- [ ] After removing Section A, the remaining assignment does NOT auto-rename to Section A (it keeps its DB order)
- [ ] Empty state shows "No faculty assignments yet" message

---

## 10. CSV Timetable Upload

**Card:** "Upload Timetable from CSV"

### Required CSV Columns

| Column | Format | Example |
|---|---|---|
| `day` | MON/TUE/WED/THU/FRI/SAT | MON |
| `start_time` | HH:MM (24-hr) | 09:00 |
| `end_time` | HH:MM (24-hr) | 10:00 |
| `subject_code` | Must match a subject in this dept+semester | ISE501 |
| `faculty_employee_id` | Must match a faculty in this department | FAC001 |
| `room_number` | Room must exist or will be auto-created | ISE-101 |

### Optional Column

| Column | Format | Example |
|---|---|---|
| `section` | A/B/C | A |

Download the template first: click **Download Template** button.

**Test:**
- [ ] Download template → CSV file downloads with correct column headers
- [ ] Upload a valid CSV → success: "X slot(s) created"
- [ ] Upload same CSV again → success: "X updated" (update_or_create behaviour)
- [ ] Upload CSV with wrong column names → error: "CSV must have columns: ..."
- [ ] Upload CSV with invalid day (e.g. "MONDAY") → error on that row, other rows still process
- [ ] Upload CSV with end_time before start_time → error on that row
- [ ] Upload CSV with unknown subject_code → error: "subject code not found in Sem X"
- [ ] Upload CSV with unknown faculty_employee_id → error: "faculty employee ID not found"
- [ ] Upload CSV with faculty from a different department → now allowed (matches UI behaviour)
- [ ] Upload CSV with unknown room_number → room is auto-created with capacity 60
- [ ] Upload non-CSV file (e.g. .xlsx) → error: "Only .csv files are accepted"
- [ ] Upload CSV with `section` column → section saved on timetable entry
- [ ] All uploaded entries have `generation_mode = 'manual'` in the database

**Error reporting:**
- Up to 5 row-level errors shown as a warning message
- Summary shows: "X slot(s) created, Y updated, Z error(s)"

---

## 11. Auto-Generate Timetable

**Button:** "Auto Update Timetable" (top of page, teal button)

### What it does

1. Clears all existing timetable entries for this dept + semester
2. For each subject → for each assigned faculty (= each section):
   - Schedules **L** lecture slots (1-hr blocks from the default grid)
   - Schedules **T** tutorial slot (1-hr block)
   - Schedules **P** practical slots (2 consecutive 50-min blocks)
3. Checks conflicts college-wide (faculty can't be in two places, rooms can't double-book)
4. Returns count of created entries

### Default Time Grid Used

```
MON–FRI: 09:00–10:00, 10:00–11:00, 11:00–12:00, 14:00–15:00, 15:00–16:00
SAT:     09:00–10:00, 10:00–11:00
```

Lab pairs: 14:00–14:50 + 14:50–15:40 on any day

### Test

- [ ] Click "Auto Update Timetable" with no subjects → warning: "No timetable entries could be generated"
- [ ] Click with subjects but no faculty assignments → warning + info: "X subject(s) skipped — no faculty assigned: ISE501, ISE502..."
- [ ] Click with subjects + faculty assigned → success: "Timetable updated with X slot(s)"
- [ ] Faculty with no availability set → info message: "X faculty member(s) have no availability set (using default grid): Dr. Ananya..."
- [ ] Timetable matrix appears below with correct subjects in correct slots
- [ ] Running auto-generate twice → second run clears and rebuilds (no duplicates)
- [ ] Faculty with availability set → generator uses those slots preferentially
- [ ] Subject with `practical_hours > 0` → scheduled in a lab room (if lab rooms exist), two consecutive 50-min slots
- [ ] Subject with `practical_hours = 0` → scheduled in a lecture room
- [ ] Two sections of same subject → scheduled at different times (no student overlap)

### Conflict detection

- [ ] If faculty is already scheduled in another dept at the same slot → that slot is skipped
- [ ] If room is already booked at the same slot → next available room is tried

---

## 12. Viewing the Generated Timetable

Two views are shown after generation:

### Weekly Matrix (Grid View)

- Rows = time periods
- Columns = Mon / Tue / Wed / Thu / Fri / Sat
- Each cell shows subject chips: Subject Name, Code · Section, Room · Faculty
- Break rows shown in grey with break label
- Empty cells show a dash

**Test:**
- [ ] Matrix renders without horizontal scroll on desktop (min-width: 780px with scroll wrapper)
- [ ] Break rows appear in correct time position
- [ ] Multi-section subjects show separate chips in different day/time cells
- [ ] Empty cells show dash, not blank

### Flat List Table

Below the matrix, a detailed table shows every entry:

| Column | Content |
|---|---|
| Day | Monday / Tuesday... |
| Time | 9:00 AM – 10:00 AM |
| Subject | Code + name |
| Sec | Section pill (A/B/C) or dash |
| Faculty | Full name |
| Dept | Faculty's dept code |
| Room | Room number + building |

**Test:**
- [ ] All entries from the matrix appear in the flat list
- [ ] Section pill shows for multi-section subjects, dash for single-section
- [ ] Building shown below room number when set

---

## 13. Break Management

**Card:** "Add Break Slot"

| Field | Options | Notes |
|---|---|---|
| Break Label | Lunch Break / Tea Break / Short Break / Prayer Break | Dropdown |
| Day | MON–SAT | |
| Applies To | All Departments (College-wide) / This Department Only | |
| Start Time | HH:MM | |
| End Time | HH:MM | |

**New fields in DB (not yet in form):** `break_type` (regular/exam/event/holiday), `applies_to` (college/department/section), `valid_from`, `valid_to`

**Test:**
- [ ] Add a Lunch Break on MON 13:00–14:00 → success, appears in "Scheduled Breaks" table
- [ ] Add the exact same break again → warning: "A break already exists at MON 13:00–14:00 with the same scope. No duplicate added."
- [ ] Add same time but different scope (dept vs college-wide) → allowed (different scope = different record)
- [ ] Set scope to "This Department Only" → `applies_to_all = False` in DB
- [ ] Delete a break → removed from table immediately
- [ ] Break appears in the weekly matrix as a grey row at the correct time
- [ ] College-wide break appears in timetable for all departments

---

## 14. Classroom Management

**Card:** "Classrooms / Rooms"

| Field | Required | Notes |
|---|---|---|
| Room Number | Yes | e.g. "ISE-101", "LAB-A" |
| Building | No | e.g. "Block A", "Main Block" |
| Capacity | No | Default 60 |
| Room Type | No | lecture / lab / seminar / tutorial / other |
| Features | No | Comma-separated: projector,computers,ac |

**Test:**
- [ ] Add a room with just room number → success, appears in table with default type "Lecture Hall"
- [ ] Add a room with all fields → all fields saved and shown in table
- [ ] Add a lab room (type = lab) → shown with "Lab" type badge
- [ ] Add features "projector,computers" → shown in Features column
- [ ] Try adding a room with the same number → `get_or_create` — no duplicate, no error shown
- [ ] Rooms table shows: Room / Type / Building / Capacity / Features columns
- [ ] Auto-generator uses rooms from this list when scheduling

---

## 15. Complete Testing Checklist

Use this checklist for a full end-to-end test of the planner.

### Setup Phase
- [ ] Navigate to planner, select ISE department, Semester 5
- [ ] Confirm stats show 0 for all four cards
- [ ] Add 3 subjects: ML (ISE501), Big Data (ISE502), Cloud (ISE503)
- [ ] Confirm "Semester Subjects" stat = 3
- [ ] Confirm all 3 appear in "Current Semester Subjects" table
- [ ] Confirm all 3 appear in the "Assign Faculty" subject dropdown

### Faculty Assignment Phase
- [ ] Assign Dr. Ananya to ISE501 → success: "Assigned to ISE501 — Section A"
- [ ] Assign Dr. Ravi to ISE501 → success: "Assigned to ISE501 — Section B"
- [ ] Assign Dr. Priya to ISE502 → success: "Assigned to ISE502 — Section A"
- [ ] Assign Dr. Suresh to ISE503 → success: "Assigned to ISE503 — Section A"
- [ ] Confirm "Faculty Assignments" stat = 4
- [ ] Confirm assignment map shows ISE501 with 2 rows (Sec A, Sec B)
- [ ] Remove one assignment → stat decreases by 1

### Availability Phase
- [ ] Add availability for Dr. Ananya: MON 09:00–10:00
- [ ] Add availability for Dr. Ananya: TUE 10:00–11:00
- [ ] Confirm "Availability Slots" stat = 2
- [ ] Confirm availability table shows both slots

### Classroom Phase
- [ ] Add room ISE-101, Building: ISE Block, Capacity: 60, Type: lecture
- [ ] Add room ISE-LAB1, Building: ISE Block, Capacity: 30, Type: lab, Features: computers
- [ ] Confirm both rooms appear in table with correct type badges

### Break Phase
- [ ] Add Lunch Break, MON, 13:00–14:00, College-wide
- [ ] Confirm break appears in Scheduled Breaks table
- [ ] Confirm `applies_to_all = True` (College-wide scope)

### Generation Phase
- [ ] Click "Auto Update Timetable"
- [ ] Confirm success message with slot count > 0
- [ ] Confirm "Timetable Entries" stat increases
- [ ] Confirm weekly matrix renders with subject chips
- [ ] Confirm Lunch Break row appears in matrix at 13:00–14:00
- [ ] Confirm ISE501 has two chips (Sec A and Sec B) in different time slots
- [ ] Confirm ISE-LAB1 is used for any subject with practical hours
- [ ] Confirm flat list table shows all entries with correct columns
- [ ] Confirm info message if any faculty had no availability set

### CSV Phase
- [ ] Download template → verify column headers
- [ ] Fill in 2 rows manually, upload → success
- [ ] Check flat list shows new entries with `generation_mode = manual`
- [ ] Upload same file again → "X updated" (no duplicates)
- [ ] Upload file with bad day → row-level error shown, other rows processed

### Edge Cases
- [ ] Switch to a different semester → all data resets to that semester's state
- [ ] Switch back → original data still there
- [ ] Run auto-generate twice → no duplicate entries (second run clears first)
- [ ] Add a subject with no faculty assigned → auto-generate shows warning: "X subject(s) skipped — no faculty assigned: ISE501"
- [ ] Add same break twice → second attempt shows warning, no duplicate in table
- [ ] Upload CSV with cross-dept faculty employee ID → accepted (any college faculty allowed)

---

## 16. Common Errors and Fixes

| Error Message | Cause | Fix |
|---|---|---|
| "Subject name and code are required" | Submitted empty form | Fill both fields |
| "Subject code already exists for Sem X" | Duplicate code in same dept+semester | Use a different code |
| "Select a valid subject and faculty member" | Dropdown left on default "Select..." | Choose both subject and faculty |
| "already assigned to ISE501" | Same faculty assigned to same subject twice | No action needed — already set up |
| "No timetable entries could be generated" | No subjects, or subjects have no faculty assigned | Add subjects and assign faculty first |
| "X subject(s) skipped — no faculty assigned: ISE501" | Auto-generate ran but some subjects had no faculty | Assign faculty to those subjects and re-generate || "X faculty member(s) have no availability set (using default grid)" | Faculty have no availability slots — generator used fallback | Add availability slots for more precise scheduling |
| "A break already exists at MON 13:00–14:00 with the same scope" | Duplicate break attempted | No action needed — break already exists |
| "CSV must have columns: day, end_time, faculty_employee_id, room_number, start_time, subject_code" | Wrong column names in CSV | Download the template and use it |
| "subject code not found in Sem X" | CSV references a subject not added to this semester | Add the subject first, then re-upload |
| "faculty employee ID not found" | Wrong employee ID in CSV | Check the faculty's employee ID in the faculty list |
| "invalid times" | end_time before start_time, or bad format | Use HH:MM 24-hour format, end after start |
| "Room number is required" | Submitted classroom form with empty room number | Fill the room number field |

---

## 17. Expected Behaviour Reference

### Auto-Generator Rules

| Rule | Behaviour |
|---|---|
| No subjects | Returns 0, shows warning |
| Subject with no faculty | Skipped — warning shown: "X subject(s) skipped: ISE501, ISE502" |
| Faculty with availability set | Generator uses those slots first |
| Faculty with no availability | Generator uses default grid + info message shown |
| Faculty already scheduled elsewhere | That slot is skipped, next slot tried |
| Room already booked | Next available room tried |
| Subject with `practical_hours > 0` or `slot_type = lab` | Two consecutive 50-min slots in a **lab room** (falls back to any room if no lab rooms exist) |
| Lecture/tutorial subject | Scheduled in non-lab rooms preferentially |
| Multiple sections (2 faculty for same subject) | Each section gets its own non-overlapping slots |
| Running twice | First run's entries are deleted, fresh generation |
| All generated entries | `generation_mode = 'balanced'` set in DB |

### Section Labelling

| Assignments | Display |
|---|---|
| 1 faculty | No section label (blank) |
| 2 faculty | Section A, Section B |
| 3 faculty | Section A, Section B, Section C |

### Break Deduplication

| Scenario | Result |
|---|---|
| New break (day + time + scope not in DB) | Created |
| Same day + time + scope already exists | Warning shown, no duplicate created |
| Same day + time but different scope | Allowed (college-wide vs dept-only are separate) |

### CSV Upload Rules

| Scenario | Result |
|---|---|
| New slot (subject+day+start not in DB) | Created |
| Existing slot (same subject+day+start) | Updated (faculty, end_time, classroom, section) |
| Unknown room | Auto-created with capacity 60 |
| Unknown subject code | Row skipped, error logged |
| Unknown faculty employee ID | Row skipped, error logged |
| Faculty from different department | Allowed (matches UI behaviour) |
| Invalid day | Row skipped, error logged |
| Invalid time format | Row skipped, error logged |
| All entries | `generation_mode = 'manual'` set |

### Break Scope

| Scope selected | `applies_to_all` in DB | Visible in |
|---|---|---|
| All Departments (College-wide) | True | All dept timetables |
| This Department Only | False | Only this dept's timetable |
