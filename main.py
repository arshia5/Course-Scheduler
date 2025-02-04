import tkinter as tk
from tkinter import ttk, scrolledtext
from datetime import datetime, time
import itertools
import json
import os

###############################################################################
# Utility / Helper Functions
###############################################################################

def times_overlap(section1, section2):
    """
    Given two sections: (day_of_week, start_time, end_time).
    Check if they overlap (same day and intersecting time range).
    """
    day1, start1, end1 = section1
    day2, start2, end2 = section2

    # If they're on different days, no overlap
    if day1.lower() != day2.lower():
        return False

    # Same day, check time intervals
    return (start1 < end2) and (end1 > start2)

def is_valid_schedule(schedule):
    """
    A schedule is a tuple of sections (one from each course).
    Return True if no overlapping sections exist in it.
    """
    for i in range(len(schedule)):
        for j in range(i + 1, len(schedule)):
            if times_overlap(schedule[i], schedule[j]):
                return False
    return True

# For chronological sorting by day name
day_order = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6
}

def get_day_index(day_str):
    """
    Return a numeric index for the given day string so we can sort by day.
    Defaults to 999 if day not found.
    """
    return day_order.get(day_str.lower(), 999)

def time_to_string(t):
    """
    Convert a datetime.time object to 'HH:MM' string.
    """
    return t.strftime("%H:%M")

def string_to_time(s):
    """
    Convert a 'HH:MM' string to datetime.time object.
    """
    return datetime.strptime(s, "%H:%M").time()

###############################################################################
# Main Tkinter App
###############################################################################

class CourseSchedulerApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Course Scheduler (Multi-User with Auto Save & Edit Course)")
        self.geometry("900x650")
        self.configure(bg="#2e2e2e")  # Dark background for main window

        # Setup ttk style for dark mode
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure("TFrame", background="#2e2e2e")
        style.configure("TLabel", background="#2e2e2e", foreground="#ffffff", font=("Helvetica", 10))
        style.configure("TButton", background="#3e3e3e", foreground="#ffffff", font=("Helvetica", 10))
        # Change text color on hover (active state) for buttons to black
        style.map("TButton", foreground=[("active", "black")])
        style.configure("TEntry", fieldbackground="#4e4e4e", background="#4e4e4e", foreground="#ffffff", font=("Helvetica", 10))
        style.configure("TCombobox", foreground="#ffffff", font=("Helvetica", 10))
        # Define a custom style for the day picker combobox:
        style.configure("Custom.TCombobox",
                        fieldbackground="#4e4e4e",
                        background="#4e4e4e",
                        foreground="#ffffff",
                        arrowcolor="#ffffff",
                        font=("Helvetica", 10))
        style.map("Custom.TCombobox",
                  fieldbackground=[("readonly", "#4e4e4e")],
                  background=[("readonly", "#4e4e4e")],
                  foreground=[("readonly", "#ffffff")],
                  arrowcolor=[("readonly", "#ffffff")])
        style.configure("TLabelframe", background="#2e2e2e", foreground="#ffffff")
        style.configure("TLabelframe.Label", background="#2e2e2e", foreground="#ffffff")

        # A dictionary to hold data for *all* students loaded from file:
        # { student_id: { "courses": { course_name: [(day, start_time, end_time), ...], ... } }, ... }
        self.users_data = {}

        # We keep track of which student is "active" (the one we are editing)
        self.active_student_id = None

        # For the active student, we keep a dictionary of courses:
        #   self.active_courses = { course_name: [(day, start, end), ...], ... }
        self.active_courses = {}

        # Temporary list of sections for the course currently being edited
        self.current_course_sections = []

        # The JSON file in which we store all data for all students
        self.data_file = "schedules_data.json"

        self.create_widgets()

        # Start the auto-save loop (every 5 seconds)
        self.auto_save()

    def create_widgets(self):
        # -----------------------------
        # Top Frame: Student Controls
        # -----------------------------
        top_frame = ttk.Frame(self, padding="10")
        top_frame.pack(side=tk.TOP, fill=tk.X)
        ttk.Label(top_frame, text="Student ID:", font=('Helvetica', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        self.entry_student_id = ttk.Entry(top_frame, width=15)
        self.entry_student_id.pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="New/Load Student Data", command=self.load_student_data).pack(side=tk.LEFT, padx=10)
        ttk.Button(top_frame, text="Save Student Data", command=self.save_student_data).pack(side=tk.LEFT, padx=10)
        ttk.Button(top_frame, text="Show All Users", command=self.show_all_users).pack(side=tk.LEFT, padx=10)

        # ---------------------------------------------------------
        # Middle Frame: Left (Course Editor) and Right (Saved Courses & Actions)
        # ---------------------------------------------------------
        middle_frame = ttk.Frame(self, padding="10")
        middle_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Left Panel: Course Editor
        course_editor_frame = ttk.LabelFrame(middle_frame, text="Course Editor", padding="10")
        course_editor_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        course_editor_frame.columnconfigure(1, weight=1)

        # Course Name
        ttk.Label(course_editor_frame, text="Course Name:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.entry_course_name = ttk.Entry(course_editor_frame, width=30)
        self.entry_course_name.grid(row=0, column=1, sticky="w", padx=5, pady=5)

        # Day Combobox (using custom style)
        ttk.Label(course_editor_frame, text="Day:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.day_var = tk.StringVar(value="Monday")
        day_options = [d.capitalize() for d in day_order.keys()]
        self.day_dropdown = ttk.Combobox(course_editor_frame, textvariable=self.day_var,
                                         values=day_options, width=10, state="readonly",
                                         style="Custom.TCombobox")
        self.day_dropdown.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        self.day_dropdown.current(0)

        # Start Time Spinboxes
        ttk.Label(course_editor_frame, text="Start Time:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        spin_frame_start = ttk.Frame(course_editor_frame)
        spin_frame_start.grid(row=2, column=1, sticky="w", padx=5, pady=5)
        self.start_hour_var = tk.IntVar(value=8)
        self.start_min_var = tk.IntVar(value=30)
        self.spin_start_hour = tk.Spinbox(spin_frame_start, from_=0, to=23, textvariable=self.start_hour_var, width=3, wrap=True)
        self.spin_start_hour.pack(side=tk.LEFT)
        ttk.Label(spin_frame_start, text=":").pack(side=tk.LEFT)
        self.spin_start_minute = tk.Spinbox(spin_frame_start, from_=0, to=59, textvariable=self.start_min_var, width=3, wrap=True)
        self.spin_start_minute.pack(side=tk.LEFT)

        # End Time Spinboxes
        ttk.Label(course_editor_frame, text="End Time:").grid(row=3, column=0, sticky="e", padx=5, pady=5)
        spin_frame_end = ttk.Frame(course_editor_frame)
        spin_frame_end.grid(row=3, column=1, sticky="w", padx=5, pady=5)
        self.end_hour_var = tk.IntVar(value=10)
        self.end_min_var = tk.IntVar(value=20)
        self.spin_end_hour = tk.Spinbox(spin_frame_end, from_=0, to=23, textvariable=self.end_hour_var, width=3, wrap=True)
        self.spin_end_hour.pack(side=tk.LEFT)
        ttk.Label(spin_frame_end, text=":").pack(side=tk.LEFT)
        self.spin_end_minute = tk.Spinbox(spin_frame_end, from_=0, to=59, textvariable=self.end_min_var, width=3, wrap=True)
        self.spin_end_minute.pack(side=tk.LEFT)

        # Set dark mode colors for the spinboxes
        spinbox_bg = "#4e4e4e"
        spinbox_fg = "#ffffff"
        for spin in [self.spin_start_hour, self.spin_start_minute, self.spin_end_hour, self.spin_end_minute]:
            spin.config(bg=spinbox_bg, fg=spinbox_fg, insertbackground=spinbox_fg, highlightbackground="#2e2e2e")

        # Add Section Button
        ttk.Button(course_editor_frame, text="Add Section", command=self.add_section).grid(row=4, column=1, sticky="w", padx=5, pady=5)

        # Sections Listbox for Current Course
        ttk.Label(course_editor_frame, text="Sections (Current Course):").grid(row=5, column=0, sticky="nw", padx=5, pady=5)
        self.current_sections_listbox = tk.Listbox(course_editor_frame, height=5, width=40, bg="#4e4e4e", fg="#ffffff")
        self.current_sections_listbox.grid(row=6, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)

        # Delete Section Button
        ttk.Button(course_editor_frame, text="Delete Section", command=self.delete_section).grid(row=6, column=2, sticky="n", padx=5, pady=5)

        # Save/Update Course Button
        self.btn_save_course = ttk.Button(course_editor_frame, text="Save/Update Course", command=self.save_course)
        self.btn_save_course.grid(row=7, column=0, columnspan=2, sticky="w", padx=5, pady=10)

        # Right Panel: Container for Saved Courses and Actions
        right_panel = ttk.Frame(middle_frame, padding="10")
        right_panel.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        right_panel.columnconfigure(0, weight=1)

        # Saved Courses Section
        saved_frame = ttk.LabelFrame(right_panel, text="Saved Courses", padding="10")
        saved_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        saved_frame.columnconfigure(0, weight=1)
        # Label and listbox for saved courses
        ttk.Label(saved_frame, text="Saved Courses for Active Student:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.saved_courses_listbox = tk.Listbox(saved_frame, height=10, width=30, bg="#4e4e4e", fg="#ffffff")
        self.saved_courses_listbox.grid(row=1, column=0, rowspan=3, sticky="nsew", padx=5, pady=5)
        # Buttons for editing and deleting courses
        ttk.Button(saved_frame, text="Edit Selected Course", command=self.edit_course).grid(row=1, column=1, sticky="nw", padx=5, pady=5)
        ttk.Button(saved_frame, text="Delete Selected Course", command=self.delete_course).grid(row=2, column=1, sticky="nw", padx=5, pady=5)

        # Actions Section: Below Saved Courses
        action_frame = ttk.LabelFrame(right_panel, text="Actions", padding="10")
        action_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        action_frame.columnconfigure(0, weight=1)
        ttk.Button(action_frame, text="Show All Courses & Sections", command=self.show_all_courses).grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        ttk.Button(action_frame, text="Generate Schedules", command=self.generate_schedules).grid(row=1, column=0, sticky="ew", padx=5, pady=5)

        # Allow the middle frame columns to expand equally
        middle_frame.columnconfigure(0, weight=1)
        middle_frame.columnconfigure(1, weight=1)

        # ---------------------------------
        # Bottom Frame: Output / Messages
        # ---------------------------------
        bottom_frame = ttk.LabelFrame(self, text="Output Messages", padding="10")
        bottom_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.output_box = scrolledtext.ScrolledText(bottom_frame, width=100, height=15, wrap=tk.WORD,
                                                    bg="#4e4e4e", fg="#ffffff", insertbackground="#ffffff")
        self.output_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    ############################################################################
    # Data Loading / Saving (Option 1) with multiple users
    ############################################################################

    def load_student_data(self):
        """
        Loads this student's data (courses, sections) from the JSON file.
        If the file doesn't exist or the student doesn't exist, we start fresh.
        """
        sid = self.entry_student_id.get().strip()
        if not sid:
            self.output_message("Please enter a valid Student ID first.")
            return

        # Ensure the JSON file is loaded into self.users_data
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r") as f:
                    self.users_data = json.load(f)
            except json.JSONDecodeError:
                # If the file is corrupted or empty, just reset
                self.users_data = {}

        # If the student doesn't exist in users_data yet, create a blank entry
        if sid not in self.users_data:
            self.users_data[sid] = {"courses": {}}

        # Set active student
        self.active_student_id = sid

        # Copy that student’s courses into active_courses
        self.active_courses = {}
        for cname, sections in self.users_data[sid]["courses"].items():
            # Convert "HH:MM" strings back to time objects
            time_sections = []
            for (day, start_str, end_str) in sections:
                start_t = string_to_time(start_str)
                end_t = string_to_time(end_str)
                time_sections.append((day, start_t, end_t))
            self.active_courses[cname] = time_sections

        self.refresh_saved_courses_listbox()
        self.output_message(f"Loaded data for student ID: {sid}")

    def save_student_data(self, auto=False):
        """
        Saves the current student’s data (self.active_courses) into the JSON file.
        If called during auto-save (auto=True), no message is shown.
        """
        if not self.active_student_id:
            if not auto:
                self.output_message("No active student selected. Please enter Student ID and Load.")
            return

        # Copy from self.active_courses into self.users_data for this student
        sid = self.active_student_id
        if sid not in self.users_data:
            self.users_data[sid] = {"courses": {}}

        # Convert time objects to "HH:MM" strings
        final_dict = {}
        for cname, sections in self.active_courses.items():
            string_sections = []
            for (day, st, et) in sections:
                string_sections.append((day, time_to_string(st), time_to_string(et)))
            final_dict[cname] = string_sections

        self.users_data[sid]["courses"] = final_dict

        # Write to JSON
        try:
            with open(self.data_file, "w") as f:
                json.dump(self.users_data, f, indent=2)
            if not auto:
                self.output_message(f"Data saved for student ID '{sid}'.")
        except Exception as e:
            if not auto:
                self.output_message(f"Error saving data: {e}")

    ############################################################################
    # Auto Save Functionality
    ############################################################################

    def auto_save(self):
        """
        Automatically saves the current student's data every 5 seconds.
        """
        if self.active_student_id:
            self.save_student_data(auto=True)
        # Schedule the next auto-save in 5000 milliseconds (5 seconds)
        self.after(5000, self.auto_save)

    ############################################################################
    # New Function: Show All Users
    ############################################################################

    def show_all_users(self):
        """
        Loads the JSON file (if it exists) and displays all user IDs in the output box.
        """
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r") as f:
                    self.users_data = json.load(f)
            except json.JSONDecodeError:
                self.output_message("Error reading data file.")
                return
        else:
            self.output_message("No data file found.")
            return

        self.output_box.delete("1.0", tk.END)
        if not self.users_data:
            self.output_box.insert(tk.END, "No users found.\n")
            return

        self.output_box.insert(tk.END, "All Users:\n\n")
        for user_id in self.users_data.keys():
            self.output_box.insert(tk.END, f"- {user_id}\n")

    ############################################################################
    # Adding / Deleting Sections (Spinbox Time) [Option 4 for Time Input]
    ############################################################################

    def add_section(self):
        """
        Add a single section (Day, Start, End from spinboxes) to current_course_sections.
        """
        day = self.day_var.get().capitalize()  # e.g. "Monday"
        start_h = self.start_hour_var.get()
        start_m = self.start_min_var.get()
        end_h = self.end_hour_var.get()
        end_m = self.end_min_var.get()

        try:
            start_time = time(hour=start_h, minute=start_m)
            end_time = time(hour=end_h, minute=end_m)
        except ValueError:
            self.output_message("Invalid time values.")
            return

        if end_time <= start_time:
            self.output_message("End time must be after start time.")
            return

        self.current_course_sections.append((day, start_time, end_time))
        # Show in listbox
        self.current_sections_listbox.insert(
            tk.END,
            f"{day}, {start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}"
        )

    def delete_section(self):
        """
        Delete the selected section from current_course_sections.
        """
        selection = self.current_sections_listbox.curselection()
        if not selection:
            self.output_message("No section selected.")
            return
        index_to_remove = selection[0]
        self.current_sections_listbox.delete(index_to_remove)
        self.current_course_sections.pop(index_to_remove)
        self.output_message("Deleted selected section.")

    ############################################################################
    # Saving / Editing a Course (Option 2: Editing a Saved Course)
    ############################################################################

    def save_course(self):
        """
        Saves/updates the "current course" into self.active_courses,
        then clears the "current course" area for new input.
        """
        if not self.active_student_id:
            self.output_message("No active student. Please load a student first.")
            return

        course_name = self.entry_course_name.get().strip()
        if not course_name:
            self.output_message("Please enter a Course Name.")
            return

        if not self.current_course_sections:
            self.output_message("No sections for this course.")
            return

        # Add or update in active_courses
        self.active_courses[course_name] = self.current_course_sections[:]

        # Clear current course area
        self.entry_course_name.delete(0, tk.END)
        self.current_sections_listbox.delete(0, tk.END)
        self.current_course_sections.clear()

        # Refresh the saved courses list
        self.refresh_saved_courses_listbox()
        self.output_message(f"Course '{course_name}' saved/updated for student {self.active_student_id}.")

    def edit_course(self):
        """
        Loads the selected course from active_courses into the "current course" editor
        so the user can change its name/sections and re-save.
        """
        selection = self.saved_courses_listbox.curselection()
        if not selection:
            self.output_message("No course selected to edit.")
            return
        index = selection[0]
        course_name = self.saved_courses_listbox.get(index)

        # Clear out the current course
        self.entry_course_name.delete(0, tk.END)
        self.current_sections_listbox.delete(0, tk.END)
        self.current_course_sections.clear()

        # Fill with the existing data
        self.entry_course_name.insert(0, course_name)
        sections = self.active_courses.get(course_name, [])
        for (day, st, et) in sections:
            self.current_course_sections.append((day, st, et))
            self.current_sections_listbox.insert(tk.END, f"{day}, {st.strftime('%H:%M')} - {et.strftime('%H:%M')}")

        # Remove that course from active_courses so we don't keep duplicates
        del self.active_courses[course_name]
        self.refresh_saved_courses_listbox()

        self.output_message(f"Course '{course_name}' loaded for editing. Make changes and click 'Save/Update Course'.")

    def delete_course(self):
        """
        Deletes the selected course from the active_courses dictionary.
        """
        selection = self.saved_courses_listbox.curselection()
        if not selection:
            self.output_message("No course selected to delete.")
            return
        index_to_remove = selection[0]
        course_name = self.saved_courses_listbox.get(index_to_remove)

        if course_name in self.active_courses:
            del self.active_courses[course_name]

        self.refresh_saved_courses_listbox()
        self.output_message(f"Course '{course_name}' deleted.")

    ############################################################################
    # Display & Generate Schedules
    ############################################################################

    def refresh_saved_courses_listbox(self):
        """
        Reloads the "Saved Courses" listbox from self.active_courses.
        """
        self.saved_courses_listbox.delete(0, tk.END)
        for cname in self.active_courses.keys():
            self.saved_courses_listbox.insert(tk.END, cname)

    def show_all_courses(self):
        """
        Display all courses & sections for the active student in the output box.
        """
        self.output_box.delete("1.0", tk.END)
        if not self.active_student_id:
            self.output_box.insert(tk.END, "No active student.\n")
            return
        if not self.active_courses:
            self.output_box.insert(tk.END, f"No courses saved for student {self.active_student_id}.\n")
            return

        self.output_box.insert(tk.END, f"Courses for Student {self.active_student_id}:\n\n")
        for cname, sections in self.active_courses.items():
            self.output_box.insert(tk.END, f"Course: {cname}\n")
            for (day, st, et) in sections:
                self.output_box.insert(tk.END, f"   - {day}, {st.strftime('%H:%M')} - {et.strftime('%H:%M')}\n")
            self.output_box.insert(tk.END, "\n")

    def generate_schedules(self):
        """
        Compute all valid schedules (one section per course) for the active student.
        """
        if not self.active_student_id:
            self.output_message("No active student. Please load a student first.")
            return

        if not self.active_courses:
            self.output_message(f"No courses found for student {self.active_student_id}.")
            return

        course_names = list(self.active_courses.keys())
        # Each course has a list of sections.
        # We'll create the cartesian product: one section per course.
        try:
            all_combinations = itertools.product(*(self.active_courses[name] for name in course_names))
        except KeyError:
            self.output_message("Error generating schedules. Check your courses data.")
            return

        valid_schedules = []
        for combo in all_combinations:
            if is_valid_schedule(combo):
                valid_schedules.append(combo)

        self.output_box.delete("1.0", tk.END)
        self.output_box.insert(tk.END, f"Found {len(valid_schedules)} valid schedules for student {self.active_student_id}.\n\n")

        for idx, schedule in enumerate(valid_schedules, start=1):
            schedule_info = []
            for cname, section in zip(course_names, schedule):
                day, st, et = section
                schedule_info.append((day, st, et, cname))

            schedule_info.sort(key=lambda x: (get_day_index(x[0]), x[1]))

            self.output_box.insert(tk.END, f"--- Schedule #{idx} ---\n")
            for (day, st, et, cname) in schedule_info:
                self.output_box.insert(tk.END, f"{day}, {st.strftime('%H:%M')} - {et.strftime('%H:%M')}: {cname}\n")
            self.output_box.insert(tk.END, "\n")

    ############################################################################
    # Helper: Output messages
    ############################################################################

    def output_message(self, msg):
        self.output_box.insert(tk.END, msg + "\n")
        self.output_box.see(tk.END)  # auto-scroll to the bottom

if __name__ == "__main__":
    app = CourseSchedulerApp()
    app.mainloop()
