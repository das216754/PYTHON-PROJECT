# FacultySync

**Student-Driven Faculty Availability Matching Using Augmented Interval Trees**

## Problem Statement

Students often struggle to coordinate their free time with professors for doubt-clearing sessions, project discussions, research guidance, and academic consultations.

FacultySync matches student availability with faculty schedules and finds suitable appointment slots without conflicts.

## Main Data Structure

Augmented Interval Tree

Each node stores the maximum endpoint (`max_end`) of its subtree to help identify overlapping intervals efficiently.

## Algorithms

- Interval Overlap Search
- Free-Slot Computation
- Conflict Detection
- Earliest Appointment Sorting

## Technology Stack

- Python
- PySide6
- JSON
- Git and GitHub

## Project Structure

- `src/facultysync/models.py` — Time interval model
- `src/facultysync/interval_tree.py` — Augmented interval tree
- `src/facultysync/scheduler.py` — Scheduling logic
- `src/facultysync/repository.py` — Schedule data loading
- `src/facultysync/gui/main_window.py` — Desktop GUI
- `src/data/schedule.json` — Sample faculty schedules
- `tests/test_interval_tree.py` — Unit tests

## How to Run

Install dependencies:

```bash
pip install -r requirements.txt
```

Launch FacultySync from the project root:

```bash
PYTHONPATH=src python -m facultysync.main
```

Run tests:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

## Current Limitations

This prototype uses sample JSON data. Database integration, authentication, and appointment booking persistence can be added later.