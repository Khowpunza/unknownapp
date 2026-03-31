from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

TUITION_PER_CREDIT = 300.0
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
STUDENTS_FILE = DATA_DIR / "students.json"
COURSES_FILE = DATA_DIR / "courses.json"
SEPARATOR = "=" * 70
THIN_SEP = "-" * 70


@dataclass
class TimeSlot:
    days: str
    start_time: str
    end_time: str

    @classmethod
    def from_dict(cls, data: Optional[dict]) -> Optional["TimeSlot"]:
        if not data:
            return None
        return cls(
            days=data.get("days", ""),
            start_time=data.get("startTime", ""),
            end_time=data.get("endTime", ""),
        )

    def to_dict(self) -> dict:
        return {
            "days": self.days,
            "startTime": self.start_time,
            "endTime": self.end_time,
        }

    def overlaps(self, other: Optional["TimeSlot"]) -> bool:
        if not other:
            return False
        if not set(self._tokenize_days(self.days)) & set(self._tokenize_days(other.days)):
            return False
        return self._to_minutes(self.start_time) < self._to_minutes(other.end_time) and \
            self._to_minutes(other.start_time) < self._to_minutes(self.end_time)

    @staticmethod
    def _tokenize_days(days: str) -> list[str]:
        tokens: list[str] = []
        i = 0
        source = (days or "").upper()
        while i < len(source):
            if source[i:i + 2] == "TH":
                tokens.append("TH")
                i += 2
            else:
                tokens.append(source[i])
                i += 1
        return tokens

    @staticmethod
    def _to_minutes(value: str) -> int:
        hours, minutes = value.split(":")
        return int(hours) * 60 + int(minutes)

    def __str__(self) -> str:
        return f"{self.days} {self.start_time}-{self.end_time}"


@dataclass
class Course:
    code: str
    title: str
    credits: int
    capacity: int
    time_slot: Optional[TimeSlot] = None
    prerequisites: list[str] = field(default_factory=list)
    enrolled_students: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "Course":
        return cls(
            code=data.get("code", "").upper(),
            title=data.get("title", ""),
            credits=int(data.get("credits", 0)),
            capacity=int(data.get("capacity", 0)),
            time_slot=TimeSlot.from_dict(data.get("timeSlot")),
            prerequisites=list(data.get("prerequisites", [])),
            enrolled_students=list(data.get("enrolledStudents", [])),
        )

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "title": self.title,
            "credits": self.credits,
            "capacity": self.capacity,
            "timeSlot": self.time_slot.to_dict() if self.time_slot else None,
            "prerequisites": self.prerequisites,
            "enrolledStudents": self.enrolled_students,
        }

    def is_full(self) -> bool:
        return len(self.enrolled_students) >= self.capacity

    def available_seats(self) -> int:
        return max(0, self.capacity - len(self.enrolled_students))


@dataclass
class Student:
    student_id: str
    name: str
    major: str
    enrolled_courses: list[str] = field(default_factory=list)
    completed_courses: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "Student":
        return cls(
            student_id=data.get("id", ""),
            name=data.get("name", ""),
            major=data.get("major", "Undeclared"),
            enrolled_courses=list(data.get("enrolledCourses", [])),
            completed_courses=list(data.get("completedCourses", [])),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.student_id,
            "name": self.name,
            "major": self.major,
            "enrolledCourses": self.enrolled_courses,
            "completedCourses": self.completed_courses,
        }

    def is_enrolled_in(self, course_code: str) -> bool:
        return course_code in self.enrolled_courses

    def has_completed(self, course_code: str) -> bool:
        return course_code in self.completed_courses


class EnrollmentSystem:
    def __init__(self) -> None:
        self.students: dict[str, Student] = {}
        self.courses: dict[str, Course] = {}

    def load_data(self) -> None:
        if STUDENTS_FILE.exists() and COURSES_FILE.exists():
            with COURSES_FILE.open("r", encoding="utf-8") as file:
                for course_data in json.load(file):
                    course = Course.from_dict(course_data)
                    self.courses[course.code] = course

            with STUDENTS_FILE.open("r", encoding="utf-8") as file:
                for student_data in json.load(file):
                    student = Student.from_dict(student_data)
                    self.students[student.student_id] = student
        else:
            self.seed_default_data()
            self.save_data()

    def save_data(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with STUDENTS_FILE.open("w", encoding="utf-8") as file:
            json.dump([student.to_dict() for student in self.students.values()], file, indent=2)
        with COURSES_FILE.open("w", encoding="utf-8") as file:
            json.dump([course.to_dict() for course in self.courses.values()], file, indent=2)

    def seed_default_data(self) -> None:
        defaults = [
            Course("CS101", "Intro to Programming", 3, 30, TimeSlot("MWF", "09:00", "10:00")),
            Course("CS201", "Data Structures", 3, 25, TimeSlot("MWF", "10:00", "11:00"), ["CS101"]),
            Course("CS301", "Algorithms", 3, 25, TimeSlot("TTh", "09:00", "10:30"), ["CS201"]),
            Course("CS401", "Operating Systems", 3, 20, TimeSlot("TTh", "10:30", "12:00"), ["CS301"]),
            Course("MATH101", "Calculus I", 4, 35, TimeSlot("MWF", "08:00", "09:00")),
            Course("MATH201", "Calculus II", 4, 30, TimeSlot("MWF", "11:00", "12:00")),
            Course("ENG101", "Technical Writing", 2, 40, TimeSlot("TTh", "13:00", "14:00")),
            Course("NET101", "Computer Networks", 3, 25, TimeSlot("MWF", "14:00", "15:00")),
            Course("DB101", "Database Systems", 3, 25, TimeSlot("TTh", "14:00", "15:30")),
            Course("SE101", "Software Engineering", 3, 30, TimeSlot("MWF", "15:00", "16:00")),
        ]
        for course in defaults:
            self.courses[course.code] = course

        students = [
            Student("STU001", "Alice Johnson", "Computer Science", completed_courses=["CS101"]),
            Student("STU002", "Bob Smith", "Mathematics"),
            Student("STU003", "Carol Williams", "Information Technology", completed_courses=["CS101", "CS201"]),
        ]
        for student in students:
            self.students[student.student_id] = student

    def get_student(self, student_id: str) -> Optional[Student]:
        return self.students.get(student_id)

    def add_student(self, student: Student) -> bool:
        if not student.student_id or student.student_id in self.students:
            return False
        self.students[student.student_id] = student
        return True

    def get_all_courses(self) -> list[Course]:
        return list(self.courses.values())

    def get_student_schedule(self, student_id: str) -> list[Course]:
        student = self.get_student(student_id)
        if not student:
            return []
        return [self.courses[code] for code in student.enrolled_courses if code in self.courses]

    def calculate_tuition(self, student_id: str) -> float:
        return sum(course.credits for course in self.get_student_schedule(student_id)) * TUITION_PER_CREDIT

    def register_course(self, student_id: str, course_code: str) -> tuple[bool, str]:
        student = self.get_student(student_id)
        if not student:
            return False, f"Student not found: {student_id}"

        course = self.courses.get(course_code)
        if not course:
            return False, f"Course not found: {course_code}"

        if student.is_enrolled_in(course_code):
            return False, f"You are already enrolled in {course_code}."

        if course.is_full():
            return False, f"Course {course_code} is full."

        for prereq in course.prerequisites:
            if not student.has_completed(prereq):
                return False, f"Prerequisite not met: complete {prereq} first."

        for enrolled_code in student.enrolled_courses:
            existing = self.courses.get(enrolled_code)
            if existing and existing.time_slot and course.time_slot and existing.time_slot.overlaps(course.time_slot):
                return False, f"Schedule conflict with {enrolled_code} ({existing.time_slot})."

        student.enrolled_courses.append(course_code)
        course.enrolled_students.append(student_id)
        return True, f"Successfully enrolled in {course_code} - {course.title}."

    def drop_course(self, student_id: str, course_code: str) -> tuple[bool, str]:
        student = self.get_student(student_id)
        if not student:
            return False, f"Student not found: {student_id}"

        course = self.courses.get(course_code)
        if not course:
            return False, f"Course not found: {course_code}"

        if course_code not in student.enrolled_courses:
            return False, f"You are not enrolled in {course_code}."

        student.enrolled_courses.remove(course_code)
        if student_id in course.enrolled_students:
            course.enrolled_students.remove(student_id)
        return True, f"Successfully dropped {course_code} - {course.title}."

    def update_student(self, student_id: str, name: str, major: str) -> bool:
        student = self.get_student(student_id)
        if not student:
            return False
        if name.strip():
            student.name = name.strip()
        if major.strip():
            student.major = major.strip()
        return True


class StudentMenuApp:
    def __init__(self) -> None:
        self.system = EnrollmentSystem()
        self.system.load_data()

    def run(self) -> None:
        print(SEPARATOR)
        print("      PYTHON STUDENT ENROLLMENT MENU")
        print(SEPARATOR)

        while True:
            print("\n[1] Login as Student")
            print("[2] Create New Student Profile")
            print("[3] Exit")
            choice = input("Select option: ").strip()

            if choice == "1":
                self.student_login()
            elif choice == "2":
                self.create_student_profile()
            elif choice == "3":
                self.system.save_data()
                print("\nData saved. Goodbye!")
                break
            else:
                print("Invalid option. Please choose 1, 2, or 3.")

    def student_login(self) -> None:
        student_id = input("Enter your Student ID: ").strip()
        student = self.system.get_student(student_id)
        if not student:
            print("Student ID not found.")
            return
        print(f"Welcome, {student.name}!")
        self.student_menu(student)

    def create_student_profile(self) -> None:
        print("\n--- Create New Student Profile ---")
        student_id = input("Student ID: ").strip()
        if not student_id:
            print("Student ID cannot be empty.")
            return
        if self.system.get_student(student_id):
            print("Student ID already exists.")
            return

        name = input("Full Name: ").strip()
        if not name:
            print("Name cannot be empty.")
            return

        major = input("Major [Undeclared]: ").strip() or "Undeclared"
        student = Student(student_id=student_id, name=name, major=major)
        self.system.add_student(student)
        self.system.save_data()
        print(f"New student profile created for {student.name} ({student.student_id}).")

    def student_menu(self, student: Student) -> None:
        while True:
            print(f"\n{SEPARATOR}")
            print(f"STUDENT MENU - {student.name} [{student.student_id}]")
            print(SEPARATOR)
            print("[1] View Course Catalog")
            print("[2] Register for a Course")
            print("[3] Drop a Course")
            print("[4] View My Schedule")
            print("[5] Billing Summary")
            print("[6] Edit My Profile")
            print("[7] Logout and Save")

            choice = input("Select option: ").strip()

            if choice == "1":
                self.view_course_catalog()
            elif choice == "2":
                self.register_for_course(student)
            elif choice == "3":
                self.drop_course(student)
            elif choice == "4":
                self.view_schedule(student)
            elif choice == "5":
                self.billing_summary(student)
            elif choice == "6":
                self.edit_profile(student)
            elif choice == "7":
                self.system.save_data()
                print("Data saved. Logging out...")
                break
            else:
                print("Invalid option.")

    def view_course_catalog(self) -> None:
        print(f"\n{SEPARATOR}")
        print("COURSE CATALOG")
        print(SEPARATOR)
        print(f"{'Code':<10} {'Title':<28} {'Credits':<8} {'Seats':<10} {'Time':<20} Prerequisites")
        print(THIN_SEP)
        for course in self.system.get_all_courses():
            prereq = ", ".join(course.prerequisites) if course.prerequisites else "None"
            time_value = str(course.time_slot) if course.time_slot else "TBA"
            seats = f"{len(course.enrolled_students)}/{course.capacity}"
            print(f"{course.code:<10} {course.title:<28} {course.credits:<8} {seats:<10} {time_value:<20} {prereq}")

    def register_for_course(self, student: Student) -> None:
        self.view_course_catalog()
        course_code = input("\nEnter course code to register: ").strip().upper()
        if not course_code:
            return
        success, message = self.system.register_course(student.student_id, course_code)
        print(("[SUCCESS] " if success else "[ERROR] ") + message)

    def drop_course(self, student: Student) -> None:
        schedule = self.system.get_student_schedule(student.student_id)
        if not schedule:
            print("You are not enrolled in any courses.")
            return

        print("\nYour current courses:")
        for course in schedule:
            print(f"- {course.code}: {course.title}")

        course_code = input("Enter course code to drop: ").strip().upper()
        if not course_code:
            return
        success, message = self.system.drop_course(student.student_id, course_code)
        print(("[SUCCESS] " if success else "[ERROR] ") + message)

    def view_schedule(self, student: Student) -> None:
        schedule = self.system.get_student_schedule(student.student_id)
        print(f"\nSchedule for {student.name} [{student.student_id}]")
        print(THIN_SEP)
        if not schedule:
            print("You are not enrolled in any courses.")
            return

        total_credits = 0
        for course in schedule:
            total_credits += course.credits
            print(f"- {course.code}: {course.title} | {course.credits} credits | {course.time_slot}")
        print(f"Total Credits: {total_credits}")

    def billing_summary(self, student: Student) -> None:
        schedule = self.system.get_student_schedule(student.student_id)
        print(f"\nBilling Summary for {student.name}")
        print(THIN_SEP)
        if not schedule:
            print("You are not enrolled in any courses. Tuition: $0.00")
            return

        total_credits = sum(course.credits for course in schedule)
        tuition = self.system.calculate_tuition(student.student_id)
        for course in schedule:
            print(f"- {course.code}: {course.title} ({course.credits} credits)")
        print(THIN_SEP)
        print(f"Total Credits : {total_credits}")
        print(f"Rate/Credit   : ${TUITION_PER_CREDIT:.2f}")
        print(f"Total Tuition : ${tuition:.2f}")

    def edit_profile(self, student: Student) -> None:
        print("\n--- Edit My Profile ---")
        name = input(f"New Name [{student.name}]: ").strip()
        major = input(f"New Major [{student.major}]: ").strip()
        self.system.update_student(student.student_id, name, major)
        print("Profile updated.")


if __name__ == "__main__":
    StudentMenuApp().run()
