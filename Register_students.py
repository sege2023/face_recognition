import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from PIL import Image, ImageTk
import csv
import os
import cv2
import uuid

# Create a dictionary to store registered student data
students_info = {}

# Specify the directory where you want to save the CSV file
csv_directory = "C:/Users/DELL/Desktop/Holiday school projects/"
# Specify the directory where you want to save student photos
photo_directory = "C:/Users/DELL/Desktop/Holiday school projects/student_photos/"

# Specify the full path to the CSV file
csv_file_path = os.path.join(csv_directory, "RegisteredStudents.csv")

# Create the directory if it doesn't exist
if not os.path.exists(csv_directory):
    os.makedirs(csv_directory)

# Create the directory if it doesn't exist
if not os.path.exists(photo_directory):
    os.makedirs(photo_directory)

# Load existing student data from the CSV file
if os.path.exists(csv_file_path):
    with open(csv_file_path, "r") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            student_id = int(row["ID"])
            students_info[student_id] = {
                "name": row["Name"],
                "course": row["Course"],
                "cohort": row["Cohort"],
                "photo_path": row["PhotoPath"],
            }

# Determine the next available student ID
next_student_id = len(students_info) + 1

# Function to save registered students to the CSV file
def save_registered_students_to_csv():
    with open(csv_file_path, "w", newline="") as csvfile:
        fieldnames = ["ID", "Name", "Course", "Cohort", "PhotoPath"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()

        # Write each student's information
        for student_id, student_info in students_info.items():
            writer.writerow({
                "ID": student_id,
                "Name": student_info["name"],
                "Course": student_info["course"],
                "Cohort": student_info["cohort"],
                "PhotoPath": student_info["photo_path"],
            })

# Function to open the camera feed
def open_camera():
    def capture_image():
        nonlocal capturing
        capturing = True
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        cap.release()

        if ret:
            # Generate a unique student ID
            global next_student_id

            # Create a unique photo name (e.g., using UUID)
            unique_photo_name = str(uuid.uuid4()) + ".jpg"
            photo_save_path = os.path.join(photo_directory, unique_photo_name)

            # Save the captured image
            cv2.imwrite(photo_save_path, frame)

            # Display the captured image in the GUI
            image = Image.open(photo_save_path)
            image.thumbnail((150, 150))
            photo = ImageTk.PhotoImage(image)
            photo_label.config(image=photo)
            photo_label.image = photo
            photo_path_label.config(text=photo_save_path)

            # Show a success message in green
            error_label.config(text="Image captured successfully.", foreground="green")

            # Close the camera window
            camera_window.destroy()

        if not capturing:
            update_camera_feed()  # Restart the camera feed

    def update_camera_feed():
        if not capturing:
            ret, frame = cap.read()
            if ret:
                image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image = Image.fromarray(image)
                photo = ImageTk.PhotoImage(image)

                camera_label.config(image=photo)
                camera_label.photo = photo

                camera_window.after(10, update_camera_feed)  # Update the camera feed every 10 milliseconds

    capturing = False

    camera_window = tk.Toplevel()
    camera_window.title("Camera Feed")

    cap = cv2.VideoCapture(0)

    camera_label = ttk.Label(camera_window)
    camera_label.pack()

    capture_button = ttk.Button(camera_window, text="Capture Image", command=capture_image)
    capture_button.pack()

    update_camera_feed()

# Function to register a student
def register_student():
    name = name_var.get()
    course = course_var.get()
    cohort = cohort_entry.get()
    photo_path = photo_path_label.cget("text")

    if not name or not course or not cohort or not photo_path:
        error_label.config(text="Please fill in all fields.")
        return
    if not cohort.isdigit():
        error_label.config(text="Cohort should be a number.")
        return

    # Check if a student with the same name, course, and cohort already exists
    for student_id, student_info in students_info.items():
        if (
            student_info["name"] == name
            and student_info["course"] == course
            and student_info["cohort"] == cohort
        ):
            error_label.config(text="Student with the same credentials already exists.")
            return

    # Generate a unique student ID
    global next_student_id

    # Save the student photo in the student_photos directory
    os.makedirs(os.path.dirname(photo_path), exist_ok=True)

    # Store student data in the dictionary
    students_info[next_student_id] = {
        "name": name,
        "course": course,
        "cohort": cohort,
        "photo_path": photo_path,
    }

    # Save the registered students to the CSV file
    save_registered_students_to_csv()

    # Clear the form fields
    name_var.set("")  # Clear the "Name" field
    cohort_var.set("")  # Clear the "Cohort" field

    photo_path_label.config(text="")

    # Show a success message in green
    error_label.config(text="Student registered successfully.", foreground="green")

# Function to browse and select a photo
def browse_photo():
    file_path = filedialog.askopenfilename()
    if file_path:
        # Display the selected image in the UI
        image = Image.open(file_path)
        image.thumbnail((150, 150))
        photo = ImageTk.PhotoImage(image)
        photo_label.config(image=photo)
        photo_label.image = photo
        photo_path_label.config(text=file_path)

def display_registered_students():
    registered_students_window = tk.Toplevel()
    registered_students_window.title("Registered Students")

    tree = ttk.Treeview(registered_students_window, columns=("Name", "Course", "Cohort"))
    tree.heading("#1", text="Name")
    tree.heading("#2", text="Course")
    tree.heading("#3", text="Cohort")

    tree.column("#1", width=50)
    tree.column("#2", width=150)
    tree.column("#3", width=150)

    for student_id, student_info in students_info.items():
        course = student_info.get("course", "")
        cohort = student_info.get("cohort", "")
        tree.insert("", "end", text=student_id, values=(student_info["name"], course, cohort))

    tree.pack()

    ttk.Button(registered_students_window, text="Close", command=registered_students_window.destroy).pack()

def capitalize_text(event):
    name_var.set(name_var.get().upper())

def validate_name_input(P):
    return all(char.isalpha() or char.isspace() for char in P)



# Create the main window
root = tk.Tk()
root.title("Student Registration")

# Create and configure form elements
frame = ttk.Frame(root)
frame.grid(column=0, row=0, padx=10, pady=10)

ttk.Label(frame, text="Name:").grid(column=0, row=0)
name_var = tk.StringVar()
name_entry = ttk.Entry(frame, textvariable=name_var)
name_entry.grid(column=1, row=0)
# Bind the Entry widget to the capitalize_text function
name_entry.bind("<KeyRelease>", capitalize_text)
# name_entry.config(validate="key", validatecommand=(name_entry.register(lambda P: P.isalpha() or P == ""), "%P"))
# Use the validate function to allow only alphabets and spaces
name_entry.config(validate="key", validatecommand=(name_entry.register(validate_name_input), "%P"))

ttk.Label(frame, text="Course:").grid(column=0, row=1)
course_var = tk.StringVar()
course_combobox = ttk.Combobox(frame, textvariable=course_var, values=["RDA", "AIML"])
course_combobox.grid(column=1, row=1)

ttk.Label(frame, text="Cohort:").grid(column=0, row=2)
cohort_var = tk.StringVar()
cohort_entry = ttk.Entry(frame, textvariable=cohort_var)
cohort_entry.grid(column=1, row=2)
cohort_entry.config(validate="key", validatecommand=(cohort_entry.register(lambda P: P.isdigit() or P == ""), "%P"))

photo_label = ttk.Label(frame)
photo_label.grid(column=0, row=3, columnspan=2)

browse_button = ttk.Button(frame, text="Browse Photo", command=browse_photo)
browse_button.grid(column=0, row=4, columnspan=2)

photo_path_label = ttk.Label(frame, text="")
photo_path_label.grid(column=0, row=5, columnspan=2)

# Add "Open Camera" button
open_camera_button = ttk.Button(frame, text="Open Camera", command=open_camera)
open_camera_button.grid(column=0, row=6, columnspan=2)

# Add "Register Student" button
register_button = ttk.Button(frame, text="Register Student", command=register_student)
register_button.grid(column=0, row=7, columnspan=2)

# Add "View Registered Students" button
view_registered_students_button = ttk.Button(frame, text="View Registered Students", command=display_registered_students)
view_registered_students_button.grid(column=0, row=8, columnspan=2)

# Create the error_label in the global scope
error_label = ttk.Label(frame, text="", foreground="red")
error_label.grid(column=0, row=9, columnspan=2)

# Start the application
root.mainloop()



