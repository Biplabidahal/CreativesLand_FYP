from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    dob = models.DateField(blank=True, null=True)
    bio = models.TextField(blank=True)
    profilePic = models.ImageField(upload_to='profileImages/', blank=True, null=True)
    groups = models.ManyToManyField(
        Group,
        related_name='custom_users',  # Changed related_name to 'custom_users'
        blank=True,
        help_text='The groups this user belongs to.',
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='custom_users',  # Changed related_name to 'custom_users'
        blank=True,
        help_text='Specific permissions for this user.',
    )
    
    # Use email as the primary identifier
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def average_rating(self):
        """Calculate the average rating of all the user's blogs"""
        blogs = self.blogs.all()
        total_rating = 0
        total_rated_blogs = 0
        
        for blog in blogs:
            blog_avg = blog.average_rating()
            if blog_avg > 0:  # Only count blogs that have ratings
                total_rating += blog_avg
                total_rated_blogs += 1
        
        return round(total_rating / total_rated_blogs, 1) if total_rated_blogs > 0 else 0
    
    def __str__(self):
        return self.email


class EmailVerification(models.Model):
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='email_verification'  # One-to-One relation with CustomUser
    )
    code = models.CharField(max_length=6)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Verification for {self.user.email}"


class Blog(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('completed', 'Completed'),
    ]
    VISIBILITY_CHOICES = [
        ('public', 'Public'),
        ('private', 'Private'),
    ]
    
    author = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='blogs'
    )
    title = models.CharField(max_length=255)
    thumbnail = models.ImageField(upload_to='blogThumbnails/', blank=True, null=True)
    description = models.TextField()
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, 
        default='draft',
        help_text="Draft or Completed"
    )
    tags = models.CharField(
        max_length=255, 
        blank=True,
        help_text="Comma-separated tags"
    )
    visibility = models.CharField(
        max_length=10, 
        choices=VISIBILITY_CHOICES, 
        default='public',
        help_text="Public or Private"
    )
    price = models.DecimalField(
        max_digits=7, 
        decimal_places=2, 
        blank=True, 
        null=True,
        help_text="Pricing tier if content is private"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def average_rating(self):
        ratings = self.ratings.all()
        if ratings.exists():
            return sum(r.rating for r in ratings) / ratings.count()
        return 0

    def __str__(self):
        return self.title


class BlogRating(models.Model):
    blog = models.ForeignKey(
        Blog, 
        on_delete=models.CASCADE, 
        related_name='ratings'
    )
    user = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='blog_ratings'
    )
    rating = models.PositiveIntegerField(
        help_text="Rating given to the blog (e.g., 1 to 5)"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('blog', 'user')  # Each user can rate a blog only once

    def __str__(self):
        return f"{self.user.email} rated {self.blog.title} - {self.rating}"


class BlogComment(models.Model):
    blog = models.ForeignKey(
        Blog, 
        on_delete=models.CASCADE, 
        related_name='comments'
    )
    user = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='blog_comments'
    )
    content = models.TextField()
    parent = models.ForeignKey(
        'self', 
        null=True, 
        blank=True, 
        on_delete=models.CASCADE, 
        related_name='replies'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user.email} on {self.blog.title}"
    
class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    blog = models.ForeignKey(
        Blog, 
        on_delete=models.CASCADE, 
        related_name='payments'
    )
    user = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='payments'
    )
    amount = models.DecimalField(max_digits=7, decimal_places=2)
    transaction_id = models.CharField(max_length=100, unique=True, blank=True, null=True)
    payment_status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # New field for eSewa transaction details
    esewa_transaction_uuid = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"Payment by {self.user.email} for {self.blog.title} - {self.payment_status}"