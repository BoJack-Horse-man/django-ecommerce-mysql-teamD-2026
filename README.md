# Django E-Commerce Web Application – AI Native Project



## Project Overview

Full-stack e-commerce web application built using **Django 4.2.16**, **MySQL (MariaDB via XAMPP)**, **Bootstrap 5**, and **PyMySQL**. Developed following **AI Native Software Engineering** principles (high-level spec → AI-generated code → mental execution → [ME] commits) and **2-week Agile sprint** methodology.

Key focus:
- Complete user flow: browse → detail → cart → checkout → order confirmation
- User authentication & profile with photo upload
- Order persistence in DB
- Admin panel for management
- Process documentation (ME.log.md, Architecture Resonance Board)

## Features Implemented

- Product catalog (list view with search/filter, detail view)
- Session-based shopping cart (add, update quantity, remove)
- Cart summary page (table, real-time total, update/delete)
- User registration, login, logout
- Required login for checkout
- Checkout flow (save Order + OrderItems to DB, reduce stock)
- Fake payment simulation ("Pay Now" button changes status)
- User profile page (order history, status view, profile photo upload)
- Responsive UI with Bootstrap 5 + Font Awesome icons
- Admin panel for product/order CRUD & status updates
- Image upload for products (admin) & user profile
- AI Native process logs (ME.log.md) and Architecture Resonance Board

## Tech Stack

- Backend: Django 4.2.16
- Database: MariaDB 10.4 (XAMPP) + PyMySQL
- Frontend: Bootstrap 5, Font Awesome
- Other: Python 3.12, Git/GitHub, Cursor AI (code generation), Pillow (ImageField)

## Local Setup Instructions

1. Start XAMPP (Apache + MySQL)
2. Clone the repository:
3.  Create & activate virtual environment:
4.  Install dependencies:
 (or manually: `pip install django==4.2.16 pymysql Pillow`)
5. Apply migrations:
6.  Create superuser (for admin):  (\ecommerce-django-2026> python manage.py createsuperuser
Username (leave blank to use defult)
Email address:
Password: )

7. Run the development server:
8.  Open in browser:
- http://127.0.0.1:8000/ → Product catalog
- http://127.0.0.1:8000/admin/ → Admin panel
- http://127.0.0.1:8000/cart/ → Cart
- http://127.0.0.1:8000/profile/ → User profile (after login)



- Product list
- Product detail
- Cart summary
- Checkout confirmation
- User profile with photo
- Admin panel

## Process Documentation

- **ME.log.md** → Mental execution logs for key code sections (AI Native requirement)
- **architecture_resonance_board.md** → Risks identified & mitigations
- **Commits** → All major changes tagged with [ME] for mental execution

## License

Feel free to use it

## Contact

For questions or assessment:  
Aarman  
GitHub: BoJack-Horse-man

---
Built with ❤️ using Django & AI-assisted development – January 2026


