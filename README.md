# 📦 Inventory Management System

A full-stack inventory management solution built for small and medium businesses, featuring a web dashboard, REST API backend with ML-powered demand forecasting, and a cross-platform mobile app.

---

## 🏗️ Project Structure

```
Inventory-Management-System/
├── BackEnd/          # Python REST API + ML forecasting
├── FrontEnd/         # React + TypeScript web dashboard
└── MobileApp/        # Expo React Native mobile app
```

---

## ✨ Features

- 📊 **Dashboard** — Real-time sales, revenue, and stock overview
- 🗃️ **Inventory Management** — Add, edit, delete, and track products
- 🛒 **Point of Sale (POS)** — Billing and transaction management
- 📈 **Analytics** — Sales trends and performance insights
- 🤖 **ML Demand Forecasting** — Prophet-based stock prediction
- 📱 **Mobile App** — On-the-go inventory access via Expo Go
- 🔐 **Secure API** — JWT-based authentication

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React, TypeScript, Tailwind CSS, Framer Motion |
| Backend | Python, FastAPI, PostgreSQL |
| ML | Prophet (demand forecasting) |
| Mobile | React Native, Expo Router |
| Database | PostgreSQL (PLpgSQL procedures) |

---

## 🚀 Getting Started

### Prerequisites
- Node.js v18+
- Python 3.10+
- PostgreSQL
- Expo Go app (for mobile)

---

### 1. Clone the repo

```bash
git clone https://github.com/FriedIce-623/Inventory-Management-System.git
cd Inventory-Management-System
```

---

### 2. Backend Setup

```bash
cd BackEnd
pip install -r requirements.txt
```

Create a `.env` file in `BackEnd/`:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/inventory_db
SECRET_KEY=your_secret_key
```

Run the server:
```bash
python app.py
```
Backend runs on `http://localhost:8000`

---

### 3. Frontend Setup

```bash
cd FrontEnd
npm install
npm run dev
```
Frontend runs on `http://localhost:5173`

---

### 4. Mobile App Setup

```bash
cd MobileApp
npm install
```

Set your backend IP in the config/`.env`:
```env
API_URL=http://<your-local-ip>:8000
```

Start Expo:
```bash
# Set your machine's hotspot/LAN IP
$env:REACT_NATIVE_PACKAGER_HOSTNAME="192.168.x.x"  # PowerShell
npx expo start --clear
```

Scan the QR code with **Expo Go** on your phone.

---

## 📱 Running on Device (Hotspot Setup)

Best setup for development:
1. Connect laptop to Ethernet
2. Share connection via **Mobile Hotspot** to your phone
3. Find your hotspot IP: `ipconfig` → look for `192.168.137.1`
4. Set `REACT_NATIVE_PACKAGER_HOSTNAME` to that IP
5. Run `npx expo start --clear` and scan the QR

---

## 🗄️ Database

The project uses PostgreSQL with PLpgSQL stored procedures. To set up the database:

```bash
psql -U postgres -c "CREATE DATABASE inventory_db;"
psql -U postgres -d inventory_db -f BackEnd/schema.sql
```

---

## 👥 Contributors

- [FriedIce-623](https://github.com/FriedIce-623)
- [AkshatSalgotra](https://github.com/AkshatSalgotra)
- [degenerate007](https://github.com/degenerate007)

---

## 📄 License

This project is for educational purposes.
