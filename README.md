## Python-script for send mails about results of 1c scheduled jobs

### 1. Install
`$ git clone https://github.com/anavozhko/connecting-to-1c`

Install package pypiwin32, if you don`t have it:
```
$ git cd connecting-to-1c
$ pip install pypiwin32
```

### 2. Edit create_db.py and create database.db with your settings
`$ python create_db.py`

### 3. Edit settings of SMTP-server in run.py

### 4. Run
`$ python run.py`