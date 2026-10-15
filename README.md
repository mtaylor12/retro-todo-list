# retro-todo-list
Small python todo list, retro styled.

######
To recreate the .exe in the future, download the .py and .spec onto your machine, and then from the folder containing the .py and .spec, install PyInstaller and build from the spec (in powershell):


python -m pip install pyinstaller
pyinstaller 1_todo.spec


PyInstaller normally places the result in a dist folder. The spec file records the build configuration, and PyInstaller can build from it directly. 

If you only want to run the program in the future—not make an .exe—install Python and then in powershell run:

python 1_todo.py
