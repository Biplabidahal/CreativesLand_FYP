- Project Title: Creative Writing Management System (Creatives' Land)
- Tagline: "A platform for writers to create, share, and monetize content"
  **Academic Context:**
  - University: University of Wolverhampton
  - Student: Biplabi Dahal
  - **User Management**: 
  - Role-based access (Admin/Reader/Writer) 
  - OTP authentication
  **Content Tools**:
  - Rich text editor
  - Draft saving
  - Genre/theme tagging
  **Monetization**:
  - Pay-per-content model
  - eSewa integration
  **Community Features**:
  - Commenting/rating system
  - Peer-review workflow
  **Discovery**:
  - Advanced search/filters
  - Trending topics tracking
**Component & Technologies/Tools**
 Frontend - React, Tailwind CSS
 Backend - Python Django
 Database - MySQL
 Design - Figma (Wireframes/UI)
 Version Control - Github
 IDE - VS Code

**Installation Guide (Minimal)**
1. Backend: 
   ```bash
   virtualenv env
   ./env/Scripts/activate    
   pip install -r requirements.txt
   python .\manage.py makemigrations
   python manage.py migrate
   pip install pymysql
   pip show mysqlclient
   python .\manage.py runserver
     
**Critical Limitations**
- No real-time collaboration
- Region-limited payments
- Mobile-responsive (no native app)
- Manual content dispute resolution


