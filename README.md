# SmartOrganizer
Smart Organizer is a Windows desktop application created to instantly clean up misplaced folders (like The Downloads or Desktop). It scans a folder of The choice, categorizes the files (into Images, Documents, Videos, others), and moves them into neatly organized subfolders
This guide will show you exactly how to take the raw code files and turn them into a real, clickable .exe app that you can use forever (or share with friends).

Step 1: The One-Time Setup
The computer needs to learn how to read Python code before it can build the app.

Go to Python.org and click the big yellow "Download Python" button.

Open the file you just downloaded.

STOP AND READ: Before you click "Install Now," look at the very bottom of the window. You MUST check the tiny box that says "Add Python to PATH" (or "Add python.exe to PATH"). If you don't check this box, the next steps will fail!

Click Install Now and wait for it to finish.

Step 2: Prepare The Files
Go to your Desktop and create a brand new, empty folder. Name it something like App Builder.

Move the two files into this folder:

SmartOrganizer.py (The code)

SmartOrganizer.ico

Step 3: The Magic Command Trick
We need to give The computer some typed commands, but we are going to use a shortcut so you don't have to "navigate" anywhere.

Open The new App Builder folder so you are looking at the two files.

Click directly on the Address Bar at the top of the window (the long white bar that says something like C:\Users\TheName\Desktop\App Builder).

Delete all the text in that bar, type the letters cmd, and hit Enter on The keyboard.

A black screen with white text will pop up. A black screen might appear.

Last Step : Building the App
Now, we just copy and paste two commands into that black screen.

Step 1: Install the building blocks
Copy the text below, paste it into the black screen (you might have to right-click to paste), and hit Enter:

Plaintext
pip install customtkinter tkinterdnd2 pyinstaller
Wait a minute for it to download a bunch of stuff. When it stops moving, move to Step 2.

Step 2: Create the .exe file
Copy this long line of text, paste it into the black screen, and hit Enter:

Plaintext
py -m PyInstaller --noconfirm --windowed --icon=SmartOrganizer.ico --add-data "SmartOrganizer.ico;." --collect-all customtkinter --collect-all tkinterdnd2 SmartOrganizer.py
The computer will now compress everything into a single app. This takes about 1 or 2 minutes. When it says "Completed successfully," you can close the black screen!

Phase 5: Find The New App!
Look back inside The App Builder folder. You will see some new folders.

Open the folder named dist.

Open the folder named SmartOrganizer.

You can now right-click that file and select "Create shortcut" to drag onto The desktop.
