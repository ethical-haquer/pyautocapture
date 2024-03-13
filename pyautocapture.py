"""
pyautocapture - Automate taking multiple screenshots and videos
Copyright (C) 2024 ethical_haquer

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import shlex
import subprocess
import threading
import time
import tkinter as tk
from tkinter import scrolledtext

import cv2
import numpy as np
import PIL
import pyautogui
from skimage.metrics import structural_similarity

# TODO - Add support for pyscreenshot
# import pyscreenshot

file_name = "file.txt"
save_delay = 1
save_pending = False

open_apps = []


# Function to read the text file and display its content in the text widget
def display_text_file():
    text_area.delete("1.0", tk.END)
    with open(file_name, "r") as file:
        for line in file:
            text_area.insert(tk.END, line)


# Function to save the text widget content to the text file after a delay
def save_text_file_delayed(event):
    global save_pending
    if not save_pending:
        save_pending = True
        print("Saving text file soon")
        root.after(save_delay * 2000, save_text_file)


# Function to save the text widget content to the text file
def save_text_file():
    global save_pending
    save_pending = False
    print("Saving text file...")
    with open(file_name, "w") as file:
        file.write(text_area.get("1.0", tk.END))


# Function to read the text file and execute commands
def read_text_file_and_execute():
    display_text_file()
    execute_commands()


# Function to execute commands based on the text file content
def execute_commands():
    with open(file_name, "r") as file:
        for line_num, line in enumerate(file, start=1):
            line = line.strip()

            if not line:
                print(f"Skipping empty line {line_num}")
                continue

            parts = shlex.split(line)

            command = parts[0]
            args = []
            kwargs = {}
            i = 1
            while i < len(parts):
                if parts[i].startswith("-"):
                    arg_name = parts[i][1:]
                    i += 1
                    if i < len(parts):
                        value = parts[i]
                        if value.isdigit():
                            value = int(value)
                        kwargs[arg_name] = value
                else:
                    value = parts[i]
                    if value.isdigit():
                        value = int(value)
                    args.append(value)
                i += 1

            if command in function_mapping:
                try:
                    function = function_mapping[command]
                    function(*args, **kwargs)
                except TypeError as e:
                    print(
                        f"Error executing '{command}' command on line {line_num}: {e}"
                    )
            elif command.startswith("#"):
                pass
            else:
                print(f"Invalid command on line {line_num}: {command}")


def sleep(secs):
    print(f"Sleeping for {secs} seconds")
    time.sleep(float(secs))


# WIP
class Recorder:
    def __init__(self):
        self.is_recording = False
        self.video = None

    def start(self, file_extension="avi"):
        size = pyautogui.size()
        frame_rate = 30
        file_name = "Screen_Recording." + file_extension

        if file_extension == "mp4":
            codec = cv2.VideoWriter_fourcc(*"mp4v")
        else:
            codec = cv2.VideoWriter_fourcc(*"XVID")

        self.video = cv2.VideoWriter(file_name, codec, frame_rate, size)

        self.is_recording = True

        while self.is_recording:
            try:
                screen_shot = pyautogui.screenshot()
                recframe = np.array(screen_shot)
                recframe = cv2.cvtColor(recframe, cv2.COLOR_BGR2RGB)
                recframe = cv2.resize(recframe, size)

                if self.video is not None:
                    self.video.write(recframe)

                if cv2.waitKey(1) == ord("e"):
                    self.stop()
                    break
            except Exception as e:
                print("An error occurred:", e)
                self.stop()
                break

    def stop(self):
        self.is_recording = False
        cv2.destroyAllWindows()
        if self.video is not None:
            self.video.release()


def record(file_extension="mp4"):
    if file_extension not in ["avi", "mp4"]:
        raise ValueError(
            "Invalid file_extension for record(). Valid values are 'avi' or 'mp4'."
        )

    global recorder
    recorder = Recorder()

    def record_thread():
        recorder.start(file_extension)

    threading.Thread(target=record_thread).start()


def stop_record():
    global recorder
    recorder.stop()


def click(image=None, x=None, y=None, times=1):
    sleep(0.1)
    print("Clicking...")
    if image != None:
        location = pyautogui.locateOnScreen(image)
        x, y = pyautogui.center(location)
    else:
        x = int(x)
        y = int(y)

    pyautogui.moveTo(x, y)
    for _ in range(times):
        pyautogui.click()


def create_backdrop():
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    backdrop = tk.Toplevel(root)
    backdrop.title("backdrop")
    # backdrop.wm_transient(root)
    # backdrop.grab_set()
    backdrop.geometry(f"{screen_width}x{screen_height}+0+0")
    backdrop.configure(bg="red")

    backdrop.update()
    backdrop.update_idletasks()


# WIP
def old_get_loc():
    pyautogui.screenshot("pre-extract.png")

    # Define the solid color used in the full-screen window (in BGR format)
    solid_color = np.array([0, 0, 255])  # Assuming red color (BGR format)

    # Create a solid color image based on the defined color
    height, width = 1080, 1920  # Define the dimensions of the full-screen window
    solid_color_img = np.full((height, width, 3), solid_color, dtype=np.uint8)

    # Load the screenshot image
    screenshot_img = cv2.imread("pre-extract.png")

    # Resize the solid color image to match the dimensions of the screenshot image
    solid_color_img_resized = cv2.resize(
        solid_color_img, (screenshot_img.shape[1], screenshot_img.shape[0])
    )

    # Convert the images to grayscale
    solid_gray = cv2.cvtColor(solid_color_img_resized, cv2.COLOR_BGR2GRAY)
    screenshot_gray = cv2.cvtColor(screenshot_img, cv2.COLOR_BGR2GRAY)

    # Calculate absolute difference between the images
    diff = cv2.absdiff(solid_gray, screenshot_gray)

    # Threshold the difference image to get a binary mask
    _, threshold = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)

    # Find contours in the binary mask
    contours, _ = cv2.findContours(
        threshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    # Get the bounding box of the largest contour (assuming the app is the largest difference)
    x, y, w, h = cv2.boundingRect(contours[0])

    # Extract the section from the screenshot image based on the calculated position and size
    extracted_section = screenshot_img[y : y + h, x : x + w]

    # Draw a bounding box around the extracted area on the full screenshot image
    annotated_img = screenshot_img.copy()
    cv2.rectangle(annotated_img, (x, y), (x + w, y + h), (0, 255, 0), 2)

    # Save the extracted section as a PNG file
    cv2.imwrite("extracted_section.png", extracted_section)

    # Display the full screenshot image with the extracted area highlighted
    cv2.imshow("Annotated Screenshot", annotated_img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    # Print the size and position of the extracted area
    print("Extracted Area:")
    print("Position (x, y):", x, y)
    print("Size (width, height):", w, h)
    return (x, y, w, h)


def get_loc(old, new):
    try:
        # Load images
        old = str(old)
        new = str(new)
        image1 = cv2.imread(old)
        image2 = cv2.imread(new)

        # Convert to grayscale
        image1_gray = cv2.cvtColor(image1, cv2.COLOR_BGR2GRAY)
        image2_gray = cv2.cvtColor(image2, cv2.COLOR_BGR2GRAY)

        # Compute SSIM between the two images
        (score, diff) = structural_similarity(image1_gray, image2_gray, full=True)

        # The diff image contains the actual image differences between the two images
        # and is represented as a floating point data type in the range [0,1]
        # so we must convert the array to 8-bit unsigned integers in the range
        # [0,255] image1 we can use it with OpenCV
        diff = (diff * 255).astype("uint8")
        print("Image Similarity: {:.4f}%".format(score * 100))

        # Threshold the difference image, followed by finding contours to
        # obtain the regions of the two input images that differ
        thresh = cv2.threshold(diff, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
        contours = cv2.findContours(
            thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        contours = contours[0] if len(contours) == 2 else contours[1]

        contour_sizes = [(cv2.contourArea(contour), contour) for contour in contours]
        result = image2.copy()
        # The largest contour should be the new detected difference
        if len(contour_sizes) > 0:
            largest_contour = max(contour_sizes, key=lambda x: x[0])[1]
            x, y, w, h = cv2.boundingRect(largest_contour)
            cv2.rectangle(result, (x, y), (x + w, y + h), (36, 255, 12), 2)

        print(f"{x}, {y}, {x+w}, {y+h}")
        sleep(0.1)
        cv2.imshow("result", result)
        cv2.waitKey(0)
        cv2.imshow("diff", diff)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        sleep(0.3)
        return (x, y, (x + w), (y + h))
        # diff = PIL.ImageGrab.grab(bbox=(x, y, (x + w), (y + h)), xdisplay=None).save("diff.png")
    except Exception as e:
        print(f"e: {e}")


def start(command, name, backdrop=True, delay=0.5):
    try:
        if backdrop == True:
            # create_backdrop()
            pass
        sleep(0.1)
        pyautogui.screenshot("old.png")
        subprocess.Popen(shlex.split(command))
        sleep(0.5)
        pyautogui.screenshot("new.png")
        print(f"Running '{command}'")
        # sleep(delay)
        loc = get_loc("old.png", "new.png")
        sleep(0.5)
        open_apps.append({"app": name, "location": loc})
        print(open_apps)
    except Exception as e:
        print(f"Error executing 'start' command: {e}")


def move(app):
    # Move and resize an opened app
    pass


def shoot(file_name, app=None):
    try:
        if app == None:
            print("Shooting...")
            pyautogui.screenshot(file_name)
        else:
            # Take screenshot of the specified app

            # screenshot = PIL.ImageGrab.grab(bbox=(x, y, (x + w), (y + h)), xdisplay=None).save("diff.png")
            pass
    except Exception as e:
        print(f"Error executing 'shoot' command: {e}")


function_mapping = {
    "start": start,
    "sleep": sleep,
    "shoot": shoot,
    "click": click,
    "record": record,
    "stop_record": stop_record,
    "create_backdrop": create_backdrop,
}


# Create the root window
root = tk.Tk(className="pyautocapture")

# Scrolled text widget
text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=50, height=20)
text_area.pack()

display_text_file()

# Start button to read the text file and execute commands
start_button = tk.Button(root, text="Start", command=read_text_file_and_execute)
start_button.pack()

# Bind the text widget to save the file after a delay when modified
text_area.bind("<KeyRelease>", save_text_file_delayed)

root.mainloop()
