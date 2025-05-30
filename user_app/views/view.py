from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from ..models import Blog, BlogComment, BlogRating, CustomUser, Payment
import uuid
from esewa import EsewaPayment
from django.db.models import Q
import operator
from functools import reduce

def home(request):
    blogs = Blog.objects.filter(status='completed', visibility='public').order_by('-created_at')
    context = {
        'blogs': blogs,
    }
    return render(request, 'home.html', context)

def posts(request):
    query = request.GET.get("q", "")
    filter_type = request.GET.get("filter", "")

    posts_list = Blog.objects.all().filter(status="completed")

    if query:
        search_terms = query.split()
        title_queries = [Q(title__icontains=term) for term in search_terms]
        tag_queries = [Q(tags__icontains=term) for term in search_terms]
        combined_queries = [title | tag for title, tag in zip(title_queries, tag_queries)]
        combined_query = reduce(operator.and_, combined_queries)
        posts_list = posts_list.filter(combined_query)

    if filter_type == "free":
        posts_list = posts_list.filter(price__isnull=True)
    elif filter_type == "paid":
        posts_list = posts_list.filter(price__isnull=False)

    posts_list = posts_list.order_by("-created_at")
    all_tags = []
    for post in posts_list:
        tags = [tag.strip() for tag in post.tags.split(',') if tag.strip()]
        all_tags.extend(tags)
    unique_tags = sorted(list(set(all_tags)))  

    context = {
        "posts": posts_list,
        "q": query,
        "filter": filter_type,
        "tags": unique_tags, 
    }
    return render(request, "posts.html", context)

def author_profile(request, author_id):
    author = get_object_or_404(CustomUser, id=author_id)
    blogs = author.blogs.all().order_by("-created_at")
    total_blogs = blogs.count()
    avg_rating = author.average_rating()
    
    context = {
        "author": author,
        "blogs": blogs,
        "total_blogs": total_blogs,
        "avg_rating": avg_rating,
    }
    return render(request, "author_profile.html", context)

def post_detail(request, blog_id):
    blog = get_object_or_404(Blog, id=blog_id)
    if blog.status != "completed":
        messages.error(request, "This blog is not yet completed.")
        return redirect("posts")
    comments = blog.comments.filter(parent__isnull=True).order_by("created_at")

    has_paid = True
    if blog.visibility == 'private':
        if request.user.is_authenticated:
            if request.user != blog.author:
                payment = Payment.objects.filter(blog=blog, user=request.user, payment_status='completed').first()
                has_paid = bool(payment)
        else:
            has_paid = False

    user_rating = None
    if request.user.is_authenticated:
        user_rating = blog.ratings.filter(user=request.user).first()

    more_posts = blog.author.blogs.exclude(id=blog.id)[:3]

    context = {
        "blog": blog,
        "comments": comments,
        "has_paid": has_paid,
        "user_rating": user_rating,
        "more_posts": more_posts,
    }
    return render(request, "post_detail.html", context)

esewa_payment = EsewaPayment(
    product_code="EPAYTEST",  
)

@login_required
@csrf_protect
def purchase_blog(request, blog_id):
    blog = get_object_or_404(Blog, id=blog_id, visibility='private')
    
    if request.user == blog.author:
        messages.info(request, "As the author, you have full access to your blog.")
        return redirect('post_detail', blog_id=blog_id)
    
    existing_payment = Payment.objects.filter(blog=blog, user=request.user, payment_status='completed').first()
    if existing_payment:
        messages.info(request, "You already have access to this content.")
        return redirect('post_detail', blog_id=blog_id)
    
    transaction_uuid = str(uuid.uuid4())
    
    payment = Payment.objects.create(
        blog=blog,
        user=request.user,
        amount=blog.price,
        payment_status='pending',
        transaction_id=transaction_uuid,
        esewa_transaction_uuid=transaction_uuid
    )
    
    success_url = request.build_absolute_uri('/payment/success/')
    failure_url = request.build_absolute_uri('/payment/failure/')
    
    esewa_payment.success_url = f"http://localhost:8000/payment/success?transaction_id={transaction_uuid}&amount={blog.price}"
    esewa_payment.failure_url = failure_url
    
    esewa_payment.create_signature(
        float(blog.price),
        transaction_uuid
    )
    
    esewa_form = esewa_payment.generate_form()
    
    context = {
        "blog": blog,
        "esewa_form": esewa_form,
        "transaction_uuid": transaction_uuid, 
    }
    return render(request, "purchase_blog.html", context)

@login_required
@csrf_protect
def add_comment(request, blog_id):
    blog = get_object_or_404(Blog, id=blog_id)
    if request.method == "POST":
        content = request.POST.get("content")
        parent_id = request.POST.get("parent_id")
        parent = None
        if parent_id:
            try:
                parent = BlogComment.objects.get(id=parent_id, blog=blog)
            except BlogComment.DoesNotExist:
                parent = None
        BlogComment.objects.create(
            blog=blog,
            user=request.user,
            content=content,
            parent=parent
        )
        messages.success(request, "Comment added successfully.")
        return redirect("post_detail", blog_id=blog_id)
    return redirect("post_detail", blog_id=blog_id)

@login_required
@csrf_protect
def delete_comment(request, comment_id):
    comment = get_object_or_404(BlogComment, id=comment_id)
    if request.user == comment.user or request.user == comment.blog.author:
        if request.method == "POST":
            comment.delete()
            messages.success(request, "Comment deleted successfully.")
        else:
            messages.error(request, "Invalid request.")
        return redirect("post_detail", blog_id=comment.blog.id)
    else:
        messages.error(request, "You don't have permission to delete this comment.")
        return redirect("post_detail", blog_id=comment.blog.id)

@login_required
@csrf_protect
def add_rating(request, blog_id):
    blog = get_object_or_404(Blog, id=blog_id)
    if request.method == "POST":
        rating_value = request.POST.get("rating")
        try:
            rating_value = int(rating_value)
        except ValueError:
            messages.error(request, "Invalid rating value.")
            return redirect("post_detail", blog_id=blog_id)
        if rating_value < 1 or rating_value > 5:
            messages.error(request, "Rating must be between 1 and 5.")
            return redirect("post_detail", blog_id=blog_id)
        BlogRating.objects.update_or_create(
            blog=blog, 
            user=request.user, 
            defaults={"rating": rating_value}
        )
        messages.success(request, "Rating submitted.")
        return redirect("post_detail", blog_id=blog_id)
    return redirect("post_detail", blog_id=blog_id)

@login_required
def profile(request):
    blogs = Blog.objects.filter(author=request.user).order_by("-created_at")
    context = {"blogs": blogs}
    return render(request, "profile.html", context)

@login_required
@csrf_protect
def create_blog(request):
    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        status = request.POST.get("status")
        tags = request.POST.get("tags")
        visibility = request.POST.get("visibility")
        price = request.POST.get("price")
        thumbnail = request.FILES.get("thumbnail")
        
        if visibility == "private" and price:
            try:
                price = Decimal(price)
            except Exception:
                price = None
        else:
            price = None

        Blog.objects.create(
            author=request.user,
            title=title,
            description=description,
            status=status,
            tags=tags,
            visibility=visibility,
            price=price,
            thumbnail=thumbnail
        )
        messages.success(request, "Blog created successfully!")
        return redirect("profile")
    return render(request, "create_blog.html")

@login_required
@csrf_protect
def edit_blog(request, blog_id):
    blog = get_object_or_404(Blog, id=blog_id, author=request.user)
    if request.method == "POST":
        blog.title = request.POST.get("title")
        blog.description = request.POST.get("description")
        blog.status = request.POST.get("status")
        blog.tags = request.POST.get("tags")
        blog.visibility = request.POST.get("visibility")
        price = request.POST.get("price")
        thumbnail = request.FILES.get("thumbnail")
        blog.thumbnail = thumbnail if thumbnail else blog.thumbnail
        if blog.visibility == "private" and price:
            try:
                blog.price = Decimal(price)
            except Exception:
                blog.price = None
        else:
            blog.price = None
        blog.save()
        messages.success(request, "Blog updated successfully!")
        return redirect("profile")
    return render(request, "edit_blog.html", {"blog": blog})

@login_required
@csrf_protect
def delete_blog(request, blog_id):
    blog = get_object_or_404(Blog, id=blog_id, author=request.user)
    if request.method == "POST":
        blog.delete()
        messages.success(request, "Blog deleted successfully!")
        return redirect("profile")
    return render(request, "delete_blog.html", {"blog": blog})

@login_required
@csrf_protect
def edit_profile(request):
    if request.method == "POST":
        user = request.user
        user.first_name = request.POST.get("first_name", user.first_name)
        user.last_name = request.POST.get("last_name", user.last_name)
        user.username = request.POST.get("username", user.username)
        user.phone = request.POST.get("phone", user.phone)
        user.dob = request.POST.get("dob", user.dob)
        user.bio = request.POST.get("bio", user.bio)
        if "profilePic" in request.FILES:
            user.profilePic = request.FILES["profilePic"]
        try:
            user.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("profile")
        except Exception as e:
            messages.error(request, f"Error updating profile: {e}")
    return render(request, "edit_profile.html", {"user": request.user})

@csrf_protect
def payment_success(request):
    transaction_uuid = request.GET.get('transaction_id')
    amount_with_data = request.GET.get('amount')

    if amount_with_data:
        amount = amount_with_data.split('?')[0]
    else:
        amount = None

    esewa_payment.amount = amount
    esewa_payment.uuid = transaction_uuid
    esewa_payment.product_code = "EPAYTEST"

    status = esewa_payment.is_completed(dev=True)

    if status:
        payment = Payment.objects.get(esewa_transaction_uuid=transaction_uuid)
        payment.payment_status = 'completed'
        payment.save()
        messages.success(request, "Payment successful! You now have access to the full content.")
        return redirect('post_detail', blog_id=payment.blog.id)
    else:
        messages.error(request, "Payment failed. Please try again.")
        return redirect('post_detail', blog_id=payment.blog.id)

@csrf_protect
def payment_failure(request):
    messages.error(request, "Payment failed. Please try again.")
    return redirect('posts')

@login_required
def my_purchases(request):
    payments = Payment.objects.filter(
        user=request.user,
        payment_status='completed'
    ).order_by('-created_at')
    
    context = {
        "payments": payments,
        "title": "My Purchases"
    }
    return render(request, "my_purchases.html", context)

@login_required
def author_sales(request):
    user_blogs = Blog.objects.filter(author=request.user)
    payments = Payment.objects.filter(
        blog__in=user_blogs,
        payment_status='completed'
    ).order_by('-created_at')
    total_earnings = sum(payment.amount for payment in payments)
    
    context = {
        "payments": payments,
        "total_earnings": total_earnings,
        "title": "My Sales"
    }
    return render(request, "author_sales.html", context)

def wishlist_view(request):
    return render(request, "wishlist.html")