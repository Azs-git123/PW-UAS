# config.py - pengaturan koneksi database dan secret key

DB_CONFIG = {
    'host': 'uowoto.h.filess.io',      
    'user': 'students_task_manager_caveuseful',         
    'password': '353cb13776b5e11871a13095c73b76a0e5fad8b2',        
    'database': 'students_task_manager_caveuseful',
    'port': 3307,
    'charset': 'utf8mb4'
}

# secret key buat enkripsi session Flask
SECRET_KEY = 'student_task_manager_secret_2024'
