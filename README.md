# Course Scheduler App

## Overview
The Course Scheduler App is a Python-based GUI application that helps students manage their course schedules efficiently. The app supports multiple users, allowing them to add, edit, and delete courses with specific sections, while automatically detecting and preventing schedule conflicts.

The application is built using `tkinter` and utilizes JSON for persistent storage, enabling automatic data saving and retrieval for different students.

## Features
- **Multi-user support**: Load and save schedules for different students.
- **Graphical User Interface (GUI)**: Built with `tkinter` using a dark mode theme.
- **Course Management**:
  - Add, edit, and delete courses with specific sections (day, start time, end time).
  - Prevent overlapping schedules.
- **Auto-Saving**: Automatically saves user data every 5 seconds.
- **Schedule Generation**:
  - Generate all valid schedules based on courses.
  - Prevent conflicting course sections.
- **JSON-based Storage**: Saves and loads data from a `schedules_data.json` file.

## Installation
### Requirements
Ensure you have Python installed (3.6 or later). Then, install the required dependencies:
```sh
pip install tk
```

## Usage
Run the application by executing:
```sh
python course_scheduler.py
```

### Steps to Use:
1. **Enter Student ID** and click **New/Load Student Data**.
2. **Add Courses**:
   - Enter a course name.
   - Select a day, start time, and end time.
   - Click **Add Section** (Repeat for multiple sections per course).
   - Click **Save/Update Course** to store the course.
3. **Manage Courses**:
   - Select a course from the saved list to edit or delete.
4. **Generate Schedules**:
   - Click **Generate Schedules** to view all valid schedules.
   
## File Structure
```
course_scheduler.py  # Main application file
schedules_data.json  # JSON storage for user schedules (auto-created)
```

## Contributions
Feel free to modify and improve this project. Pull requests are welcome!

## License
This project is open-source and available under the MIT License.

