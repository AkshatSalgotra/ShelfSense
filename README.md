# 📦 ShelfSense

An ML-powered inventory management system built for kirana (small retail) stores — a FastAPI backend with Prophet-based demand forecasting, paired with a cross-platform Expo mobile app for managers and cashiers.

---

## 🏗️ Project Structure

```
ShelfSense/
├── BackEnd/          # Python REST API + ML forecasting
│   ├── core/          # Auth/security, reorder-alert logic
│   ├── database/       # Schema, ER diagram
│   ├── ml/             # Prophet demand forecasting
│   ├── models/          # SQLAlchemy models
│   ├── routers/          # API endpoints (auth, inventory, sales, orders, payments, predictions, alerts, staff)
│   └── schemas/           # Pydantic request/response schemas
└── MobileApp/         # Expo React Native app (manager + cashier roles)
    ├── app/(auth)/      # Manager / cashier login
    ├── app/(manager)/    # Dashboard, inventory, alerts, staff management
    ├── app/(cashier)/     # Point-of-sale
    └── stores/             # Zustand state (auth, cart)
```

> Note: the previous React web dashboard (`FrontEnd/`) has been removed from this branch — the project now consists of the backend API and the mobile app only.

---

## ✨ Features

- 🔐 **Multi-role auth** — Shop owner/manager registration & JWT login, plus manager-created cashier accounts with their own login
- 🗃️ **Inventory management** — Add, edit, delete, and track products with per-shop categories and suppliers
- 🔎 **Product search** — Lookup by name or SKU/barcode for fast POS scanning
- 🛒 **Point of Sale (POS)** — Order creation, Razorpay checkout, and server-side payment signature verification
- 📈 **Sales logging & summaries** — Per-shop sales history and aggregated summaries
- 🤖 **ML demand forecasting** — Prophet-based per-SKU and category-level forecasts, holiday-aware, with a rule-based fallback for low-history products
- 🔔 **Reorder alerts** — Automatic low-stock/out-of-stock detection on startup with a resolution workflow and recommended reorder quantities
- 👥 **Staff management** — Managers can create, deactivate, and reactivate cashier accounts
- 📱 **Mobile app** — Role-based navigation (manager tabs vs. cashier POS) built with Expo Router, secure token storage, and offline-friendly state via Zustand

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, FastAPI, SQLAlchemy, Alembic, PostgreSQL |
| Auth | JWT (python-jose), bcrypt (passlib) |
| ML | Prophet, pandas, holidays |
| Payments | Razorpay |
| Mobile | React Native (Expo 54), Expo Router, TypeScript, Zustand, Axios, expo-secure-store |
| Charts | react-native-gifted-charts |

---

## 🚀 Getting Started

### Prerequisites
- Node.js v18+
- Python 3.10+
- PostgreSQL
- Expo Go app (for mobile) or an Android/iOS dev build (Razorpay checkout requires a dev build — it's disabled in Expo Go)

---

### 1. Clone the repo

```bash
git clone <repo-url>
cd ShelfSense
```

---

### 2. Backend Setup

```bash
cd BackEnd
pip install -r ../requirements.txt
```

Create a `.env` file in `BackEnd/`:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/shelfsense_db
SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080
RAZORPAY_KEY_ID=your_razorpay_key_id
RAZORPAY_KEY_SECRET=your_razorpay_key_secret
```

Run the server:
```bash
uvicorn main:app --reload
```
Backend runs on `http://localhost:8000` (interactive docs at `/docs`)

---

### 3. Mobile App Setup

```bash
cd MobileApp
npm install
```

Create a `.env` file in `MobileApp/`:
```env
EXPO_PUBLIC_API_URL=http://<your-local-ip>:8000
```

Start Expo:
```bash
# Set your machine's hotspot/LAN IP
$env:REACT_NATIVE_PACKAGER_HOSTNAME="192.168.x.x"  # PowerShell
npx expo start --clear
```

Scan the QR code with **Expo Go**, or run `npx expo run:android` / `npx expo run:ios` for a dev build (required to test Razorpay checkout).

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

The project uses PostgreSQL. To set up the database:

```bash
psql -U postgres -c "CREATE DATABASE shelfsense_db;"
psql -U postgres -d shelfsense_db -f BackEnd/database/schema.sql
```

An ER diagram is available at `BackEnd/database/er.png`.

---

## 👥 Contributors
- [AkshatSalgotra](https://github.com/AkshatSalgotra)
- [Aditya Dadhich](https://github.com/degenerate007)
- [Keerthana](https://github.com/FriedIce-623)


---

## 📄 License

This project is for educational purposes.
