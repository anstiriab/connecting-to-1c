from cx_Freeze import setup, Executable

executables = [Executable("connect.py", base="Win32GUI")]

options = {
    'build_exe': {
        "include_files": ["database.db", "log.txt"],
    },
}

setup(
    name="Send mails",
    options=options,
    version="0.1",
    description='Python-script for send mails about results of scheduled jobs',
    executables=executables
)
