import os

os.system('py -m PyInstaller --noconfirm --onefile --console encrypt.py')
os.system('py -m PyInstaller --noconfirm --onefile --console decrypt.py')
os.system('py -m PyInstaller --noconfirm --onefile --console consoleapp.py')
