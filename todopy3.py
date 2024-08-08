#!/usr/bin/env python3
import tkinter as tk
from tkinter import messagebox, simpledialog
from datetime import datetime, timedelta
import json
import os

# Global variable for maximum hours
max_hours_per_day = 1
tasks_file = 'tasks.json'
translations_file = 'translations.json'

# Load translations
def load_translations(lang):
    try:
        with open(f'translations_{lang}.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        ensure_default_translations()  # Ensure default translations exist
        return load_translations('en')  # Fall back to default language
    except json.JSONDecodeError as e:
        messagebox.showerror("Error", f"JSON Decode Error: {str(e)}")
        return {}

def ensure_default_translations():
    default_translations = {
        "add_task_name_title": "Add Task - Name",
        "add_task_name_prompt": "Task Name:",
        "add_task_importance_title": "Add Task - Importance",
        "add_task_importance_prompt": "Importance (1-5):",
        "add_task_deadline_title": "Add Task - Deadline",
        "add_task_deadline_prompt": "Deadline (dd-mm-yyyy):",
        "add_task_duration_title": "Add Task - Duration",
        "add_task_duration_prompt": "Duration (hours):",
        "add_task": "Add Task",
        "max_hours_per_day": "Max Hours Per Day:",
        "update_task_list": "Update Task List",
        "show_organized_tasks": "Show Organized Tasks",
        "organize_tasks": "Organized Tasks",
        "error": "Error",
        "all_fields_required": "All fields must be filled.",
        "no_tasks_planned": "No tasks planned for the next days."
    }
    with open('translations_en.json', 'w') as f:
        json.dump(default_translations, f, indent=4)

translations = load_translations('en')  # Default language

class Task:
    def __init__(self, name, importance, deadline, duration):
        self.name = name
        self.importance = importance
        self.deadline = self.parse_deadline(deadline)
        self.duration = duration
        self.real_importance = self.calculate_real_importance()

    def parse_deadline(self, deadline):
        try:
            return datetime.strptime(deadline, "%d-%m-%Y").date()
        except ValueError:
            raise ValueError(f"Invalid date format for deadline: {deadline}")

    def calculate_real_importance(self):
        days_until_deadline = (self.deadline - datetime.now().date()).days
        return (self.importance + (self.duration / 2)) / days_until_deadline if days_until_deadline > 0 else self.importance

    def to_dict(self):
        return {
            'name': self.name,
            'importance': self.importance,
            'deadline': self.deadline.strftime("%d-%m-%Y"),
            'duration': self.duration
        }

    @classmethod
    def from_dict(cls, task_dict):
        # Convert deadline to string if it's not already
        deadline = str(task_dict.get('deadline', ''))
        return cls(task_dict['name'], task_dict['importance'], deadline, task_dict['duration'])

def save_tasks():
    with open(tasks_file, 'w') as f:
        json.dump([task.to_dict() for task in tasks], f, indent=4)

def load_tasks():
    if os.path.exists(tasks_file):
        with open(tasks_file, 'r') as f:
            tasks_data = json.load(f)
            loaded_tasks = []
            for task_dict in tasks_data:
                try:
                    loaded_tasks.append(Task.from_dict(task_dict))
                except ValueError as e:
                    messagebox.showerror("Error", f"Failed to load task: {str(e)}")
            return loaded_tasks
    return []

def add_task():
    if not tk._default_root:
        return

    # Ask for task name
    name = simpledialog.askstring(
        translations.get("add_task_name_title", "Add Task - Name"),
        translations.get("add_task_name_prompt", "Task Name:"),
        parent=root
    )
    
    # Ask for importance
    importance = simpledialog.askinteger(
        translations.get("add_task_importance_title", "Add Task - Importance"),
        translations.get("add_task_importance_prompt", "Importance (1-5):"),
        parent=root
    )
    
    # Ask for deadline
    deadline = simpledialog.askstring(
        translations.get("add_task_deadline_title", "Add Task - Deadline"),
        translations.get("add_task_deadline_prompt", "Deadline (dd-mm-yyyy):"),
        parent=root
    )
    
    # Ask for duration
    duration = simpledialog.askinteger(
        translations.get("add_task_duration_title", "Add Task - Duration"),
        translations.get("add_task_duration_prompt", "Duration (hours):"),
        parent=root
    )
    
    if name and importance is not None and deadline and duration is not None:
        try:
            task = Task(name, importance, deadline, duration)
            tasks.append(task)
            update_task_list()
            save_tasks()
        except ValueError as e:
            messagebox.showerror(translations.get("error", "Error"), str(e))
    else:
        messagebox.showerror(translations.get("error", "Error"), translations.get("all_fields_required", "All fields must be filled."))

def update_task_list():
    listbox.delete(0, tk.END)  # Clear the listbox
    for task in tasks:
        listbox.insert(tk.END, f"{task.name} - Deadline: {task.deadline.strftime('%d-%m-%Y')}, Importance: {task.importance}")

def organize_tasks_for_week(tasks):
    tasks_sorted = sorted(tasks, key=lambda x: (-x.real_importance, x.deadline))
    
    organized_tasks = []
    current_day = datetime.now().date()
    current_hours = 0

    for task in tasks_sorted:
        hours_remaining = task.duration
        while hours_remaining > 0:
            if current_hours + 1 > max_hours_per_day:
                current_day += timedelta(days=1)
                current_hours = 0
            if current_hours + 1 <= max_hours_per_day:
                organized_tasks.append((current_day.strftime("%d-%m-%Y"), Task(task.name, task.importance, task.deadline.strftime("%d-%m-%Y"), 1)))
                current_hours += 1
                hours_remaining -= 1
        
        if current_day > datetime.now().date() + timedelta(days=7):
            break

    return organized_tasks

def show_organized_tasks():
    planned_tasks = organize_tasks_for_week(tasks)
    
    if not planned_tasks:
        messagebox.showinfo(translations.get("organize_tasks", "Organized Tasks"), translations.get("no_tasks_planned", "No tasks planned for the next days."))
        return
    
    schedule_output = "\n".join([f"{day}: {'Fazer \'' + task.name + '\' por ' + str(task.duration) + ' horas' if task else 'Dia livre'}" for day, task in planned_tasks])
    messagebox.showinfo(translations.get("organize_tasks", "Organized Tasks"), schedule_output)

def get_max_hours():
    try:
        max_hours = int(max_hours_entry.get())
        if max_hours < 1:
            raise ValueError("Maximum hours must be greater than 0")
        global max_hours_per_day
        max_hours_per_day = max_hours
    except ValueError as e:
        messagebox.showerror(translations.get("error", "Error"), str(e))

def change_language(lang):
    global translations
    translations = load_translations(lang)
    update_ui()

def update_ui():
    add_button.config(text=translations.get("add_task", "Add Task"))
    max_hours_label.config(text=translations.get("max_hours_per_day", "Max Hours Per Day:"))
    update_list_button.config(text=translations.get("update_task_list", "Update Task List"))
    show_organized_tasks_button.config(text=translations.get("show_organized_tasks", "Show Organized Tasks"))

root = tk.Tk()
root.title("Dynamic Task Manager")

add_button = tk.Button(root, text=translations.get("add_task", "Add Task"), command=add_task)
add_button.pack(pady=10)

max_hours_label = tk.Label(root, text=translations.get("max_hours_per_day", "Max Hours Per Day:"))
max_hours_label.pack(pady=10)
max_hours_entry = tk.Entry(root)
max_hours_entry.pack(pady=10)

update_list_button = tk.Button(root, text=translations.get("update_task_list", "Update Task List"), command=update_task_list)
update_list_button.pack(pady=10)

show_organized_tasks_button = tk.Button(root, text=translations.get("show_organized_tasks", "Show Organized Tasks"), command=show_organized_tasks)
show_organized_tasks_button.pack(pady=10)

listbox = tk.Listbox(root, width=50, height=15)
listbox.pack(pady=10)

# Language selection button
language_menu = tk.Menu(root)
language_menu.add_command(label="Português", command=lambda: change_language('pt'))
language_menu.add_command(label="English", command=lambda: change_language('en'))

menu_bar = tk.Menu(root)
menu_bar.add_cascade(label="Language", menu=language_menu)
root.config(menu=menu_bar)

tasks = load_tasks()
update_task_list()

root.mainloop()

