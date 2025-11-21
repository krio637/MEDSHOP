# 💊 MedShop - Online Medicine Store

A modern, responsive e-commerce platform for online medicine sales built with Django. MedShop provides a complete solution for customers to browse, search, and purchase medicines online with an intuitive admin dashboard for store management.

![MedShop Banner](https://img.shields.io/badge/Django-4.2.7-green) ![Python](https://img.shields.io/badge/Python-3.12-blue) ![Bootstrap](https://img.shields.io/badge/Bootstrap-5.1.3-purple) ![License](https://img.shields.io/badge/License-MIT-yellow)

## 🌟 Features

### 🛒 Customer Features
- **Modern UI/UX**: Attractive, responsive design with smooth animations
- **Medicine Catalog**: Browse medicines by categories with advanced search
- **Shopping Cart**: Add/remove items with real-time updates
- **User Authentication**: Secure login, registration, and profile management
- **Order Management**: Complete order lifecycle from cart to delivery
- **Responsive Design**: Optimized for mobile, tablet, and desktop
- **Indian Rupee Support**: Complete INR currency integration

### 👨‍💼 Admin Features
- **Comprehensive Dashboard**: Real-time analytics and statistics
- **Medicine Management**: Add, edit, delete medicines with bulk operations
- **Order Processing**: Track and update order status
- **User Management**: Customer accounts and activity monitoring
- **Category Management**: Organize medicines into categories
- **Reports & Analytics**: Sales reports, inventory tracking, and insights
- **Stock Management**: Low stock alerts and inventory control

### 🔧 Technical Features
- **Django 4.2.7**: Latest Django framework
- **Bootstrap 5**: Modern, responsive UI components
- **Custom CSS**: Advanced styling with gradients and animations
- **SQLite Database**: Lightweight database for development
- **Admin Interface**: Custom admin dashboard + Django admin
- **Security**: CSRF protection, secure authentication
- **SEO Friendly**: Proper meta tags and structure

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/krio637/MEDSHOP.git
   cd MEDSHOP
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install django pillow
   ```

4. **Run migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Create sample data**
   ```bash
   python manage.py create_sample_data
   ```

6. **Start the development server**
   ```bash
   python manage.py runserver
   ```

7. **Access the application**
   - Website: http://127.0.0.1:8000/
   - Admin Dashboard: http://127.0.0.1:8000/admin-dashboard/
   - Django Admin: http://127.0.0.1:8000/admin/

## 👤 Default Accounts

### Superuser Account
- **Username**: `superadmin`
- **Password**: `superadmin123`
- **Access**: Full Django admin + Custom dashboard

### Admin Account
- **Username**: `admin`
- **Password**: `admin123`
- **Access**: Custom admin dashboard

## 📱 Screenshots

### Homepage
- Modern hero section with gradients
- Featured medicines showcase
- Customer testimonials
- Statistics counter

### Medicine Catalog
- Grid-based responsive layout
- Advanced search and filtering
- Stock status indicators
- Price in Indian Rupees

### Admin Dashboard
- Real-time analytics
- Revenue charts
- Order management
- Inventory tracking

## 🛠️ Project Structure

```
medshop/
├── medshop/                 # Django project settings
├── medicines/               # Main application
│   ├── models.py           # Database models
│   ├── views.py            # Customer views
│   ├── views_admin.py      # Admin views
│   ├── forms.py            # Django forms
│   ├── admin.py            # Django admin config
│   └── management/         # Custom commands
├── templates/              # HTML templates
│   ├── base.html          # Base template
│   ├── medicines/         # Customer templates
│   ├── admin/             # Admin templates
│   └── registration/      # Auth templates
├── static/                # Static files
│   └── css/
│       └── responsive.css # Custom styles
├── media/                 # User uploads
├── requirements.txt       # Dependencies
└── README.md             # This file
```

## 🎨 Design Features

- **Modern Gradients**: Beautiful color schemes throughout
- **Smooth Animations**: CSS transitions and JavaScript interactions
- **Responsive Grid**: Mobile-first responsive design
- **Professional Typography**: Google Fonts integration
- **Interactive Elements**: Hover effects and loading states
- **Toast Notifications**: User feedback system

## 📊 Models

### Core Models
- **Medicine**: Product information, pricing, stock
- **Category**: Medicine categorization
- **Cart/CartItem**: Shopping cart functionality
- **Order/OrderItem**: Order management
- **UserProfile**: Extended user information

## 🔐 Security Features

- CSRF protection on all forms
- User authentication and authorization
- Staff-only admin access
- Secure password handling
- Input validation and sanitization

## 🌐 API Endpoints

### Customer URLs
- `/` - Homepage
- `/medicines/` - Medicine catalog
- `/search/` - Advanced search
- `/cart/` - Shopping cart
- `/checkout/` - Order checkout
- `/profile/` - User profile

### Admin URLs
- `/admin-dashboard/` - Main dashboard
- `/admin-medicines/` - Medicine management
- `/admin-orders/` - Order management
- `/admin-users/` - User management
- `/admin-reports/` - Analytics and reports

## 🚀 Deployment

### Production Considerations
1. Change `DEBUG = False` in settings.py
2. Set proper `ALLOWED_HOSTS`
3. Use PostgreSQL or MySQL for production
4. Configure static files serving
5. Set up proper media file handling
6. Use environment variables for secrets

### Environment Variables
```bash
SECRET_KEY=your-secret-key
DEBUG=False
DATABASE_URL=your-database-url
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**Krio637**
- GitHub: [@krio637](https://github.com/krio637)
- Project: [MEDSHOP](https://github.com/krio637/MEDSHOP)

## 🙏 Acknowledgments

- Django framework for the robust backend
- Bootstrap for responsive UI components
- Font Awesome for beautiful icons
- Google Fonts for typography
- Chart.js for analytics visualization

## 📞 Support

If you have any questions or need help with the project, please:
1. Check the existing issues
2. Create a new issue with detailed description
3. Contact the maintainer

---

⭐ **Star this repository if you found it helpful!**

Made with ❤️ by [Krio637](https://github.com/krio637)