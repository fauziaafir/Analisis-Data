import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from sqlalchemy import create_engine, text

st.title("📈 Prediksi Harga Emas Tahunan (Moving Average + Database)")

# Koneksi ke database SQLite
engine = create_engine('sqlite:///prediksi.db')
conn = engine.connect()

# Buat tabel prediksi jika belum ada
conn.execute(text("""
CREATE TABLE IF NOT EXISTS prediksi (
    tanggal_prediksi TEXT,
    harga_prediksi INTEGER,
    window INTEGER,
    sumber_file TEXT
)
"""))

# Upload file CSV
uploaded_file = st.file_uploader("📤 Upload file CSV (format: Tanggal,Harga)", type="csv")

if uploaded_file:
    # Baca data
    df = pd.read_csv(uploaded_file)
    df['Tanggal'] = pd.to_datetime(df['Tanggal'])
    df = df.sort_values('Tanggal')

    # Moving Average
    window = st.slider("🔁 Jendela Moving Average (tahun)", 2, 5, 3)
    df['MA'] = df['Harga'].rolling(window=window).mean()

    # Prediksi tahun berikutnya
    last_date = df['Tanggal'].iloc[-1]
    next_date = last_date + pd.DateOffset(years=1)
    prediksi_harga = df['MA'].iloc[-1]

    st.subheader("📊 Data Harga dan Moving Average")
    st.write(df.tail())

    # Plot grafik
    st.subheader("📉 Grafik Harga dan Prediksi")
    fig, ax = plt.subplots()
    ax.plot(df['Tanggal'], df['Harga'], label='Harga Aktual', marker='o')
    ax.plot(df['Tanggal'], df['MA'], label=f'MA ({window})', linestyle='--', color='orange')

    if not pd.isna(prediksi_harga):
        ax.axvline(next_date, color='red', linestyle='--', label='Tanggal Prediksi')
        ax.scatter(next_date, prediksi_harga, color='red', label=f'Prediksi {next_date.year}', zorder=5)
        st.success(f"🎯 Prediksi harga {next_date.year}: Rp {int(prediksi_harga):,}")

    ax.set_xlabel("Tahun")
    ax.set_ylabel("Harga (Rp)")
    ax.legend()
    ax.grid(True)
    st.pyplot(fig)

    # Simpan ke database (opsional)
    if st.button("💾 Simpan ke Database"):
        insert_stmt = text("""
            INSERT INTO prediksi (tanggal_prediksi, harga_prediksi, window, sumber_file)
            VALUES (:tanggal, :harga, :window, :file)
        """)
        conn.execute(insert_stmt, {
            "tanggal": next_date.date().isoformat(),
            "harga": int(prediksi_harga),
            "window": window,
            "file": uploaded_file.name
        })
        conn.commit()
        st.success("✅ Data prediksi berhasil disimpan ke database!")

    # Lihat histori prediksi
    with st.expander("📚 Lihat histori prediksi"):
        df_prediksi = pd.read_sql("SELECT * FROM prediksi ORDER BY tanggal_prediksi DESC", conn)
        st.dataframe(df_prediksi)

else:
    st.info("Silakan upload file CSV terlebih dahulu.")