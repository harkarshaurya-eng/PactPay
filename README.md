# PactPay

Mobile Escrow Platform on Algorand.

## Project Structure

- `backend/`: Node.js/Express API
- `contracts/`: PyTeal Smart Contracts
- `pactpay/` (mobile): Flutter Mobile App

## Prerequisites

- Node.js v18+
- Python 3.10+
- Flutter 3.x
- Docker & Docker Compose

## Setup Instructions

### 1. Database & Infrastructure

Start the PostgreSQL and Redis containers:

```bash
docker-compose up -d
```

### 2. Backend

```bash
cd backend
npm install
npx prisma generate
npm run dev
```

### 3. Smart Contracts

```bash
cd contracts
python -m venv venv
source venv/bin/activate  # or .\venv\Scripts\activate on Windows
pip install -r requirements.txt
python escrow.py  # Compiles contract to TEAL
```

### 4. Mobile App

```bash
cd pactpay
flutter pub get
flutter run
```

## Documentation

See the `docs/` folder or the generated artifacts for architecture and user flow diagrams.
