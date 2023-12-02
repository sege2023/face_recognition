import sys
import cv2
import numpy as np
import csv
from datetime import datetime
from PyQt5 import QtWidgets, QtGui, QtCore
import face_recognition
import os

class StudentAttendanceSystem(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Student Attendance System")

        self.recognize_faces = False
        self.student_status = {}
        self.known_faces = []
        self.known_names = []
        self.video_capture = cv2.VideoCapture(0)
        self.recognized_students = set() 
        

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_gui)
        self.timer.start(10)

        self.load_known_students_from_csv("RegisteredStudents.csv")

        self.camera_label = QtWidgets.QLabel(self)
        self.camera_label.setGeometry(0, 0, 640, 480)

        self.toggle_recognition_button = QtWidgets.QPushButton("Start Recognition", self)
        self.toggle_recognition_button.clicked.connect(self.toggle_face_recognition)

        self.check_not_present_button = QtWidgets.QPushButton("Check Not Present Students", self)
        self.check_not_present_button.clicked.connect(self.check_not_present_students)

        self.confirmation_label = QtWidgets.QLabel(self)
        self.confirmation_label.setFont(QtGui.QFont("Helvetica", 16))

        self.face_frame_label = QtWidgets.QLabel(self)
        self.face_frame_label.setGeometry(0, 0, 0, 0)
        self.face_frame_label.setStyleSheet("QLabel { border: 2px solid green; }")  # Green frame

        self.present_students_label = QtWidgets.QLabel(self)
        self.present_students_label.setText("Present Students:")
        
        self.absent_students_button = QtWidgets.QPushButton("Show Absent Students", self)
        self.absent_students_button.clicked.connect(self.show_absent_students)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.camera_label)
        layout.addWidget(self.toggle_recognition_button)
        layout.addWidget(self.check_not_present_button)
        layout.addWidget(self.confirmation_label)
        layout.addWidget(self.present_students_label)
        layout.addWidget(self.absent_students_button)
        self.setLayout(layout)

    
    def mark_student_present(self, student_name):
        if student_name in self.student_status and self.student_status[student_name]["exit_time"] is None:
            # Mark the student as present
            self.student_status[student_name]["entry_time"] = datetime.now()
            self.recognized_students.add(student_name) 

            # Save the attendance data to the CSV file for the current day
            self.save_attendance_for_today()

            # Show a confirmation message
            # QtWidgets.QMessageBox.information(self, "Attendance Confirmation", f"{student_name} is marked present.")

    def save_attendance_for_today(self):
        # Create a folder for attendance if it doesn't exist
        attendance_folder = "attendance"
        if not os.path.exists(attendance_folder):
            os.mkdir(attendance_folder)

        # Get the current date as a string (e.g., "2023-10-16")
        current_date = datetime.now().strftime("%Y-%m-%d")

        # Create a subfolder for the current day if it doesn't exist
        day_folder = os.path.join(attendance_folder, current_date)
        if not os.path.exists(day_folder):
            os.mkdir(day_folder)

        # Define the CSV file for today's attendance
        today_attendance_csv_file = os.path.join(day_folder, "attendance.csv")

        # Write attendance data to the CSV file
        with open(today_attendance_csv_file, "w", newline="") as csvfile:
            fieldnames = ["Student Name", "Entry Time", "Exit Time"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for student_name, status in self.student_status.items():
                entry_time = status["entry_time"] if status["entry_time"] else "N/A"
                exit_time = status["exit_time"] if status["exit_time"] else "N/A"
                writer.writerow({"Student Name": student_name, "Entry Time": entry_time, "Exit Time": exit_time})
    
    def add_known_student(self, image_path, student_name):
        print(image_path)
        image = face_recognition.load_image_file(image_path)
        encoding = face_recognition.face_encodings(image)
        if len(encoding) > 0:
            face_encoding = encoding[0]
            self.known_faces.append(face_encoding)
            self.known_names.append(student_name)

            self.student_status[student_name] = {
            "entry_time": None,
            "exit_time": None,
            "last_marked_time": None
            }
        else:
            print(f"No face found in the image for student '{student_name}'")

    def load_known_students_from_csv(self, csv_file):
        with open(csv_file, "r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                image_path = row["PhotoPath"]
                student_name = row["Name"]

                self.add_known_student(image_path, student_name)

    def toggle_face_recognition(self):
        self.recognize_faces = not self.recognize_faces

    def get_student_info_from_csv(self, student_name):
        with open("RegisteredStudents.csv", mode="r") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row["Name"] == student_name:
                    return {
                        "name": row["Name"],
                        "course": row["Course"],
                        "photo_path": row["PhotoPath"]
                    }
        return "Student not found"

    def update_gui(self):
        ret, frame = self.video_capture.read()
        if ret:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            if self.recognize_faces:
                face_locations = face_recognition.face_locations(rgb_frame)
                face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

                for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                    distances = face_recognition.face_distance(self.known_faces, face_encoding)

                    min_dist = np.min(distances)
                    if min_dist >= 0.3:
                        name = "Unknown"
                    else:
                        index = np.argmin(distances)
                        name = self.known_names[index]

                    if name != "Unknown":
                        student_info = self.get_student_info_from_csv(name)
                        self.display_student_info(student_info, top, right, bottom, left)
                        # Mark the recognized student as present and save attendance data
                        self.mark_student_present(name)

                        # Display the student's information and the green frame
                        student_info = self.get_student_info_from_csv(name)
                        self.display_student_info(student_info, top, right, bottom, left)
                        self.adjust_face_frame(top, right, bottom, left)
                    else:
                        self.display_unrecognized_student()

            height, width, channel = rgb_frame.shape
            bytes_per_line = 3 * width
            q_img = QtGui.QImage(rgb_frame.data, width, height, bytes_per_line, QtGui.QImage.Format_RGB888)
            pixmap = QtGui.QPixmap.fromImage(q_img)
            self.camera_label.setPixmap(pixmap)

    def display_student_info(self, student_info, top, right, bottom, left):
        self.confirmation_label.setText(f"Name: {student_info['name']}, Course: {student_info['course']}")
        self.adjust_face_frame(top, right, bottom, left)

    def display_unrecognized_student(self):
        self.confirmation_label.setText("Unrecognized Student")
        self.face_frame_label.setGeometry(0, 0, 0, 0)

    def adjust_face_frame(self, top, right, bottom, left):
        face_width = right - left
        face_height = bottom - top
        self.face_frame_label.setGeometry(left, top, face_width, face_height)

    def check_not_present_students(self):
        not_present_students = []
        for student_name, status_info in self.student_status.items():
            if status_info["exit_time"] is None:
                not_present_students.append(student_name)
        if not_present_students:
            self.display_not_present_students(not_present_students)

    def display_not_present_students(self, not_present_students):
        not_present_window = QtWidgets.QWidget()
        not_present_window.setWindowTitle("Not Present Today")

        layout = QtWidgets.QVBoxLayout()
        not_present_label = QtWidgets.QLabel("Students Not Present Today:")
        layout.addWidget(not_present_label)

        for student_name in not_present_students:
            not_present_info = self.get_student_info_from_csv(student_name)
            not_present_info_label = QtWidgets.QLabel(f"Name: {student_name}, Course: {not_present_info['course']}")
            layout.addWidget(not_present_info_label)

        not_present_window.setLayout(layout)
        not_present_window.show()

    def show_absent_students(self):
        absent_students = []
        absent_students_info = [] 
        for student_name, status_info in self.student_status.items():
            if status_info["exit_time"] is not None:
                absent_students.append(student_name)
    # Define the list here

        if not absent_students:
            QtWidgets.QMessageBox.information(self, "Absent Students", "All students are present today.")
        else:
            for student_name in absent_students:
                student_info = self.get_student_info_from_csv(student_name)
                student_info_str = f"Name: {student_name}, Course: {student_info['course']}"
                absent_students_info.append(student_info_str)

        absent_students_message = "\n".join(absent_students_info)
        QtWidgets.QMessageBox.information(self, "Absent Students", f"Absent Students:\n{absent_students_message}")


def save_attendance_for_today(student_status):
    # Create a folder for attendance if it doesn't exist
    attendance_folder = "attendance"
    if not os.path.exists(attendance_folder):
        os.mkdir(attendance_folder)

    # Get the current date as a string (e.g., "2023-10-16")
    current_date = datetime.now().strftime("%Y-%m-%d")

    # Create a subfolder for the current day if it doesn't exist
    day_folder = os.path.join(attendance_folder, current_date)
    if not os.path.exists(day_folder):
        os.mkdir(day_folder)

    # Define the CSV file for today's attendance
    today_attendance_csv_file = os.path.join(day_folder, "attendance.csv")

    # Write attendance data to the CSV file
    with open(today_attendance_csv_file, "w", newline="") as csvfile:
        fieldnames = ["Student Name", "Entry Time", "Exit Time"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for student_name, status in student_status.items():
            entry_time = status["entry_time"] if status["entry_time"] else "N/A"
            exit_time = status["exit_time"] if status["exit_time"] else "N/A"
            writer.writerow({"Student Name": student_name, "Entry Time": entry_time, "Exit Time": exit_time})

def main():
    app = QtWidgets.QApplication(sys.argv)
    window = StudentAttendanceSystem()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()


