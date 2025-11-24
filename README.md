# 4D-G2-IT403-ECommerceMiniStoreProject
##  📌 Project Overview
A simple e-commerce system built using Django.  
Roles supported: **Admin, Seller, Customer**.  
Includes product management, cart system, order summary, and inventory updates.

---

## 👥 Group Members & Roles
- Garcia, Ashley Jamaica– Backend Developer
- Bautista, Reina Janelle – Frontend Developer
- Sanchez, Ynez Yzabel – Project Leader / Database Manager
- Castor, Juliana Mhey – Documentor / Tester

---

## 🛠 Features
### ✔ User Authentication & Profiles
- Signup, Login, Logout
- Role-based permissions (Admin, Seller, Customer)
- Auto-created User Profile using Django signals
- Seller application system (Pending → Approved)

### ✔ Product & Category Management
- Add, Edit, Delete Products
- Manage Categories
- Product images
- Stock tracking
- Category-based product display

### ✔ Seller Features
- Apply to become a seller
- Manage own products
- Admin approval process

### ✔ Shopping Cart (Session-Based)
- Add to cart
- Update quantity
- Remove items
- Clear cart

### ✔ Orders
- Place order
- Order summary page
- Inventory decreases after checkout
- Save customer details and timestamps

### ✔ UI & Template Features
- Responsive templates
- Template inheritance (`base.html`)
- Clean navigation

---

## 🖥 Installation Steps

### **1. Clone the Repository**
git clone https://github.com/ElleQueen31/IT403-ECommerceMiniStoreProject.git

### **2. Go to the project folder**
(for example you put it in the desktop)
cd Desktop
cd ECommerceProject

### **3. Install the required packages**
pip install -r requirements.txt

### **4. Apply migrations**
python manage.py migrate

### **5. Run the server**
python manage.py runserver

### **6. Open in browser**
http://127.0.0.1:8000/

---

## 🔐 Sample User Accounts (Optional)
- **Admin**
  - Email/Username: Administrator
  - Password: W0rdPass123

- **Seller**
  - Email: YnezSanchez@gmail.com
  - Password: Passw0rd123

- **Customer**
  - Email: yanamh@gmail.com
  - Password: Passw0rd123

---

## 🎥 Video Demonstration
OneDrive Link:
👉 👉 https://bulsumain-my.sharepoint.com/:f:/g/personal/2022100681_ms_bulsu_edu_ph/IgAIEhEbWZKsR5j7qQ148aEdAdRdgCTg3mdlHVhXek5h2ow?e=W5wRRl

---

## 📄 Documentation
The Project Proposal and Project Documentation PDFs are stored in the OneDrive folder linked above.

---

## 📝 Notes
This project is submitted as final output for WMAD Elective 5 (WST 3) – Django Web Application Development.
