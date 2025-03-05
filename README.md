# Application-devlopment-1-project

*Description*
I have undertaken this project with the goal of develop web-based inventory management system for grocery store. Primary objective of this project is to create a user-friendly platform that enable people to buy product from grocery store online
My project focus on developing web application using flask by which user can buy products of grocery store online and admin can manage products and category on web application

*Technologies used*
Flask framework: used for building application’s backend.
Flask-Security: For proper login system.
SQLite database: For data storage and retrieving
Bootstrap: For styling
Jinja 2: For Template
Flask-SQLAlchemy: For Database Integration
Flask RESTful: To design and implement Restful API endpoints.

*Architecture and Features*
My project follows model-view-controller architecture. For this project I have created one file “app.py”. All the controllers are reside in app.py. All the templates are present inside “Template” folder. And YAML file and database file is present inside project folder.

*Features Implemented:*
I have implemented following features in my application:
 User registration and Authentication: I have use flask security to make proper login system
 Role-based Access Control: I have implemented role-based access control, allowing admin to manage categories and products while restricting regular users from these actions
 Category Management: Use can view list of category and Admin can add and delete Category.
 Shopping cart: Users can add and remove products from their shopping cart
 Search Functionality: Users and admin can search for products or category using keywords, and the application displays relevant results
 Api For CRUD operation on category:
 Styling:
