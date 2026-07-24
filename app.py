# app.py - file utama buat ngejalanin aplikasi Flask
# ini yang pertama kali dieksekusi waktu server distart

from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
import hashlib
from datetime import date, timedelta, datetime
from config import DB_CONFIG, SECRET_KEY

# inisialisasi app Flask, secret key diambil dari config biar rapi
app = Flask(__name__)
app.secret_key = SECRET_KEY


# --- helper functions ---

def get_db_connection():
    """buka koneksi ke database, dipanggil di setiap route yang butuh akses DB"""
    conn = mysql.connector.connect(**DB_CONFIG)
    return conn

def hash_password(password):
    """hash password pakai sha256 sebelum disimpan ke DB, jangan simpan plain text!"""
    return hashlib.sha256(password.encode()).hexdigest()


# halaman awal - langsung redirect sesuai kondisi user
@app.route('/')
def index():
    # kalau udah login tinggal lempar ke dashboard aja
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


# halaman daftar akun baru
@app.route('/register', methods=['GET', 'POST'])
def register():
    # user yang udah login ga perlu ke sini
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        # ambil data dari form, strip() biar ga ada spasi nyasar
        nama     = request.form['nama'].strip()
        email    = request.form['email'].strip()
        password = request.form['password']

        # cek field wajib dulu sebelum lanjut
        if not nama or not email or not password:
            flash('Semua field wajib diisi!', 'danger')
            return redirect(url_for('register'))

        # password minimal 6 karakter, terlalu pendek ga aman
        if len(password) < 6:
            flash('Password minimal 6 karakter!', 'danger')
            return redirect(url_for('register'))

        try:
            conn   = get_db_connection()
            cursor = conn.cursor()

            # cek dulu apakah email ini udah pernah didaftarkan
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            existing_user = cursor.fetchone()

            if existing_user:
                flash('Email sudah digunakan! Gunakan email lain.', 'danger')
                cursor.close()
                conn.close()
                return redirect(url_for('register'))

            # hash passwordnya dulu, baru simpan
            hashed_pw = hash_password(password)

            # masukin user baru ke database
            cursor.execute(
                "INSERT INTO users (nama, email, password) VALUES (%s, %s, %s)",
                (nama, email, hashed_pw)
            )
            conn.commit()
            cursor.close()
            conn.close()

            flash('Registrasi berhasil! Silakan login.', 'success')
            return redirect(url_for('login'))

        except mysql.connector.Error as e:
            flash(f'Terjadi kesalahan database: {str(e)}', 'danger')
            return redirect(url_for('register'))

    # kalau GET, tampilin halaman register aja
    return render_template('register.html')


# halaman login
@app.route('/login', methods=['GET', 'POST'])
def login():
    # user aktif ga perlu login lagi
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        # ambil email & password dari form
        email    = request.form['email'].strip()
        password = request.form['password']

        # kedua field harus terisi
        if not email or not password:
            flash('Email dan password wajib diisi!', 'danger')
            return redirect(url_for('login'))

        try:
            conn   = get_db_connection()
            cursor = conn.cursor(dictionary=True)  # pakai dict biar bisa akses pakai nama kolom

            # cari user berdasarkan email yang diinput
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()

            cursor.close()
            conn.close()

            # kalau ketemu dan passwordnya cocok, set session
            if user and user['password'] == hash_password(password):
                session['user_id']   = user['id']
                session['user_nama'] = user['nama']
                session['user_email']= user['email']

                flash(f'Selamat datang, {user["nama"]}!', 'success')
                return redirect(url_for('dashboard'))
            else:
                # salah email atau password, jangan kasih tau yang mana biar aman
                flash('Email atau password salah!', 'danger')
                return redirect(url_for('login'))

        except mysql.connector.Error as e:
            flash(f'Terjadi kesalahan database: {str(e)}', 'danger')
            return redirect(url_for('login'))

    # GET request, tampilin form login
    return render_template('login.html')


# logout - bersihkan session lalu balik ke login
@app.route('/logout')
def logout():
    session.clear()
    flash('Anda telah berhasil logout.', 'info')
    return redirect(url_for('login'))


# dashboard utama - ngumpulin semua statistik untuk ditampilkan
@app.route('/dashboard')
def dashboard():
    # pastikan user udah login dulu
    if 'user_id' not in session:
        flash('Silakan login terlebih dahulu.', 'warning')
        return redirect(url_for('login'))

    user_id = session['user_id']

    try:
        conn   = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # hitung total semua tugas yang dimiliki user ini
        cursor.execute("SELECT COUNT(*) as total FROM tasks WHERE user_id = %s", (user_id,))
        total_tugas = cursor.fetchone()['total']

        # berapa yang sudah selesai
        cursor.execute(
            "SELECT COUNT(*) as total FROM tasks WHERE user_id = %s AND status = 'Selesai'",
            (user_id,)
        )
        tugas_selesai = cursor.fetchone()['total']

        # sisanya berarti belum selesai
        tugas_belum = total_tugas - tugas_selesai

        # hitung persentase - kalau total 0 jangan dibagi biar ga error
        persen_selesai = round((tugas_selesai / total_tugas) * 100) if total_tugas > 0 else 0

        # ambil daftar tugas yang belum selesai, diurutkan dari deadline terdekat
        cursor.execute(
            """
            SELECT mata_kuliah, judul, deadline, prioritas, status
            FROM tasks
            WHERE user_id = %s AND status = 'Belum Selesai'
            ORDER BY deadline ASC
            LIMIT 10
            """,
            (user_id,)
        )
        daftar_deadline = cursor.fetchall()

        # siapkan tanggal buat reminder hari ini dan besok
        hari_ini = date.today()
        besok    = hari_ini + timedelta(days=1)

        # tugas yang deadlinenya hari ini - perlu diingatkan!
        cursor.execute(
            """
            SELECT mata_kuliah, judul, deadline, prioritas
            FROM tasks
            WHERE user_id = %s AND deadline = %s AND status = 'Belum Selesai'
            """,
            (user_id, hari_ini)
        )
        deadline_hari_ini = cursor.fetchall()

        # tugas yang deadlinenya besok
        cursor.execute(
            """
            SELECT mata_kuliah, judul, deadline, prioritas
            FROM tasks
            WHERE user_id = %s AND deadline = %s AND status = 'Belum Selesai'
            """,
            (user_id, besok)
        )
        deadline_besok = cursor.fetchall()

        cursor.close()
        conn.close()

        # lempar semua data ke template
        return render_template('dashboard.html',
            total_tugas      = total_tugas,
            tugas_selesai    = tugas_selesai,
            tugas_belum      = tugas_belum,
            persen_selesai   = persen_selesai,
            daftar_deadline  = daftar_deadline,
            deadline_hari_ini= deadline_hari_ini,
            deadline_besok   = deadline_besok,
            hari_ini         = hari_ini
        )

    except mysql.connector.Error as e:
        flash(f'Terjadi kesalahan database: {str(e)}', 'danger')
        return redirect(url_for('login'))


# halaman daftar tugas - tambah, edit, hapus semuanya di sini
@app.route('/tasks')
def tasks():
    """tampilkan semua tugas milik user yang lagi login"""
    if 'user_id' not in session:
        flash('Silakan login terlebih dahulu.', 'warning')
        return redirect(url_for('login'))

    user_id = session['user_id']

    # cek apakah ada filter yang dipilih dari URL
    filter_status   = request.args.get('status', '')
    filter_prioritas= request.args.get('prioritas', '')

    try:
        conn   = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # query dasar, nanti ditambah filter kalau ada
        query  = "SELECT * FROM tasks WHERE user_id = %s"
        params = [user_id]

        # tambahkan kondisi filter kalau user milih filter status
        if filter_status:
            query  += " AND status = %s"
            params.append(filter_status)

        # tambahkan filter prioritas juga kalau ada
        if filter_prioritas:
            query  += " AND prioritas = %s"
            params.append(filter_prioritas)

        query += " ORDER BY deadline ASC"

        cursor.execute(query, params)
        semua_tugas = cursor.fetchall()

        cursor.close()
        conn.close()

        return render_template('tasks.html',
            semua_tugas      = semua_tugas,
            filter_status    = filter_status,
            filter_prioritas = filter_prioritas,
            edit_task        = None  # belum ada yang diedit, jadi kosong dulu
        )

    except mysql.connector.Error as e:
        flash(f'Terjadi kesalahan database: {str(e)}', 'danger')
        return redirect(url_for('dashboard'))


# route untuk simpan tugas baru dari form
@app.route('/tasks/add', methods=['POST'])
def add_task():
    """terima data form lalu insert ke database"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # ambil semua input dari form
    mata_kuliah = request.form['mata_kuliah'].strip()
    judul       = request.form['judul'].strip()
    deskripsi   = request.form['deskripsi'].strip()
    deadline    = request.form['deadline']
    prioritas   = request.form['prioritas']
    status      = request.form['status']
    user_id     = session['user_id']

    # minimal tiga field ini harus ada
    if not mata_kuliah or not judul or not deadline:
        flash('Mata Kuliah, Judul, dan Deadline wajib diisi!', 'danger')
        return redirect(url_for('tasks'))

    try:
        conn   = get_db_connection()
        cursor = conn.cursor()

        # simpan tugas baru ke database
        cursor.execute(
            """
            INSERT INTO tasks (user_id, mata_kuliah, judul, deskripsi, deadline, prioritas, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (user_id, mata_kuliah, judul, deskripsi, deadline, prioritas, status)
        )
        conn.commit()
        cursor.close()
        conn.close()

        flash('Tugas berhasil ditambahkan!', 'success')

    except mysql.connector.Error as e:
        flash(f'Gagal menambahkan tugas: {str(e)}', 'danger')

    return redirect(url_for('tasks'))


# route untuk masuk mode edit - load data tugas ke form
@app.route('/tasks/edit/<int:task_id>')
def edit_task(task_id):
    """ambil data tugas berdasarkan ID dan kirim ke form edit"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    try:
        conn   = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # ambil tugas yang mau diedit - pastikan juga milik user ini, bukan punya orang lain
        cursor.execute(
            "SELECT * FROM tasks WHERE id = %s AND user_id = %s",
            (task_id, user_id)
        )
        task_to_edit = cursor.fetchone()

        if not task_to_edit:
            flash('Tugas tidak ditemukan!', 'danger')
            cursor.close()
            conn.close()
            return redirect(url_for('tasks'))

        # ambil juga semua tugas buat ditampilkan di tabel di bawah form
        cursor.execute(
            "SELECT * FROM tasks WHERE user_id = %s ORDER BY deadline ASC",
            (user_id,)
        )
        semua_tugas = cursor.fetchall()

        cursor.close()
        conn.close()

        # kirim ke template, edit_task berisi data yang mau diisi ke form
        return render_template('tasks.html',
            semua_tugas      = semua_tugas,
            edit_task        = task_to_edit,
            filter_status    = '',
            filter_prioritas = ''
        )

    except mysql.connector.Error as e:
        flash(f'Terjadi kesalahan: {str(e)}', 'danger')
        return redirect(url_for('tasks'))


# route untuk simpan perubahan setelah edit
@app.route('/tasks/update/<int:task_id>', methods=['POST'])
def update_task(task_id):
    """update data tugas yang sudah diedit ke database"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # ambil data terbaru dari form edit
    mata_kuliah = request.form['mata_kuliah'].strip()
    judul       = request.form['judul'].strip()
    deskripsi   = request.form['deskripsi'].strip()
    deadline    = request.form['deadline']
    prioritas   = request.form['prioritas']
    status      = request.form['status']
    user_id     = session['user_id']

    # validasi dasar sebelum update
    if not mata_kuliah or not judul or not deadline:
        flash('Mata Kuliah, Judul, dan Deadline wajib diisi!', 'danger')
        return redirect(url_for('edit_task', task_id=task_id))

    try:
        conn   = get_db_connection()
        cursor = conn.cursor()

        # update semua kolom yang bisa diubah user
        cursor.execute(
            """
            UPDATE tasks
            SET mata_kuliah=%s, judul=%s, deskripsi=%s, deadline=%s, prioritas=%s, status=%s
            WHERE id=%s AND user_id=%s
            """,
            (mata_kuliah, judul, deskripsi, deadline, prioritas, status, task_id, user_id)
        )
        conn.commit()
        cursor.close()
        conn.close()

        flash('Tugas berhasil diperbarui!', 'success')

    except mysql.connector.Error as e:
        flash(f'Gagal memperbarui tugas: {str(e)}', 'danger')

    return redirect(url_for('tasks'))


# route untuk hapus tugas
@app.route('/tasks/delete/<int:task_id>')
def delete_task(task_id):
    """hapus tugas dari database, pastikan yang hapus adalah pemiliknya"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    try:
        conn   = get_db_connection()
        cursor = conn.cursor()

        # tambahkan kondisi user_id biar user ga bisa hapus tugas orang lain
        cursor.execute(
            "DELETE FROM tasks WHERE id = %s AND user_id = %s",
            (task_id, user_id)
        )
        conn.commit()
        cursor.close()
        conn.close()

        flash('Tugas berhasil dihapus!', 'success')

    except mysql.connector.Error as e:
        flash(f'Gagal menghapus tugas: {str(e)}', 'danger')

    return redirect(url_for('tasks'))


if __name__ == '__main__':
    # debug=True nyalahin auto-reload dan error detail di browser
    # ingat matiin ini kalau mau deploy ke production!
    app.run(debug=True, port=5000)
