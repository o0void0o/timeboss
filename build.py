# build.py
import PyInstaller.__main__
import os

# Get the path of your current script
script_path = "timeBoss.py"  # Replace with your script name
icon_path = "kk.ico"        # Your icon file

# Run PyInstaller
PyInstaller.__main__.run([
    script_path,
    '--onefile',
    '--noconsole',
    f'--icon={icon_path}',
    '--name=TimeBoss',
    '--add-data=kk.ico;.',  # Include the icon file
    # Add any other required files/folders
    '--hidden-import=customtkinter',
    '--hidden-import=tkinter',
    '--hidden-import=PIL',
])