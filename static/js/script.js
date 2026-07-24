/**
 * script.js
 * berisi beberapa fungsi kecil buat ngebantu tampilan:
 * - alert flash otomatis hilang
 * - tanggal minimum untuk input deadline
 * - scroll otomatis ke form edit
 */

// tunggu DOM selesai dimuat sebelum mulai ngapa-ngapain
document.addEventListener('DOMContentLoaded', function () {

    // --- auto-dismiss flash alert ---
    // alert akan otomatis nutup sendiri setelah 4 detik
    const flashAlerts = document.querySelectorAll('.alert.alert-dismissible');

    flashAlerts.forEach(function (alert) {
        setTimeout(function () {
            // pakai Bootstrap API supaya animasi closenya tetap smooth
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) {
                bsAlert.close();
            }
        }, 4000); // 4 detik cukup untuk dibaca
    });


    // --- set tanggal minimum di input deadline ---
    // user ga boleh pilih tanggal yang udah lewat
    // khusus form tambah saja, form edit dibiarkan bebas
    const deadlineInput = document.getElementById('deadline');

    if (deadlineInput) {
        // kalau value masih kosong berarti ini form tambah
        if (!deadlineInput.value) {
            const today = new Date();
            // format ke YYYY-MM-DD karena itu yang diminta input type="date"
            const yyyy  = today.getFullYear();
            const mm    = String(today.getMonth() + 1).padStart(2, '0');
            const dd    = String(today.getDate()).padStart(2, '0');
            const todayStr = yyyy + '-' + mm + '-' + dd;

            // pasang min attribute biar tanggal lampau ga bisa dipilih
            deadlineInput.setAttribute('min', todayStr);
        }
    }


    // --- scroll otomatis ke form saat mode edit ---
    // kalau user klik tombol edit, halaman langsung lompat ke form
    const formTask = document.getElementById('taskForm');

    if (formTask) {
        // cara nge-cek mode edit: lihat action URL-nya ada kata 'update' ga
        const formAction = formTask.getAttribute('action');

        if (formAction && formAction.includes('update')) {
            // kasih delay sedikit biar render dulu, baru scroll
            setTimeout(function () {
                formTask.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }, 200);
        }
    }


    // --- aktifkan tooltip Bootstrap ---
    // kalau ada elemen dengan data-bs-toggle="tooltip", aktifkan semuanya
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltipTriggerList.forEach(function (el) {
        new bootstrap.Tooltip(el);
    });


    // --- aktifkan popover Bootstrap ---
    // sama seperti tooltip tapi untuk popover
    const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]');
    popoverTriggerList.forEach(function (el) {
        new bootstrap.Popover(el);
    });

});
