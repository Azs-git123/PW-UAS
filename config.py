# config.py - pengaturan koneksi database dan secret key
# edit bagian ini kalau ganti server atau environment

# setting koneksi ke MariaDB via XAMPP
# kalau pakai hosting lain, sesuaikan host, user, dan passwordnya
DB_CONFIG = {
    'host': 'localhost',      # biasanya localhost kalau masih lokal
    'user': 'root',           # default user XAMPP
    'password': '',           # default XAMPP ga pakai password
    'database': 'student_task_manager',  # nama database yang udah dibuat
    'charset': 'utf8mb4'
}

# secret key buat enkripsi session Flask
# ganti ini dengan string random yang panjang kalau mau deploy!
SECRET_KEY = 'student_task_manager_secret_2024'
