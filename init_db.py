

import mysql.connector
from config import DB_CONFIG


def init_db():
    print("Menghubungkan ke database...")
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    print(f"Berhasil terhubung ke database '{DB_CONFIG['database']}'")

    # tabel users - menyimpan akun mahasiswa
    print("Membuat tabel 'users'...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nama VARCHAR(100) NOT NULL,
            email VARCHAR(100) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # tabel tasks - menyimpan tugas kuliah, terhubung ke users lewat user_id
    print("Membuat tabel 'tasks'...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            mata_kuliah VARCHAR(100) NOT NULL,
            judul VARCHAR(200) NOT NULL,
            deskripsi TEXT,
            deadline DATE NOT NULL,
            prioritas ENUM('Rendah', 'Sedang', 'Tinggi') DEFAULT 'Sedang',
            status ENUM('Belum Selesai', 'Selesai') DEFAULT 'Belum Selesai',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    conn.commit()

    # verifikasi - tampilkan tabel apa saja yang sekarang ada di database
    cursor.execute("SHOW TABLES")
    tabel_yang_ada = [t[0] for t in cursor.fetchall()]

    cursor.close()
    conn.close()

    print("\nSelesai! Tabel yang ada di database sekarang:")
    for t in tabel_yang_ada:
        print(f"  - {t}")


if __name__ == '__main__':
    try:
        init_db()
    except mysql.connector.Error as e:
        print(f"\nGagal membuat tabel: {e}")
        print("Cek lagi isi config.py (host, user, password, port, nama database).")
