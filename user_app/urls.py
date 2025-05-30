from django.urls import path
from .views import login,logout,register,verify,home,profile,edit_profile,create_blog,edit_blog,delete_blog,posts,post_detail,add_rating,add_comment,delete_comment,author_profile,purchase_blog,payment_success,payment_failure,author_sales,my_purchases,wishlist_view
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("",home,name="home"),
    path("login/", login, name="login"),
    path("register/", register, name="register"),
    path("logout/", logout, name="logout"),
    path("verify/", verify, name="verify"),
    path("profile/", profile, name="profile"),
    path("edit_profile/", edit_profile, name="edit_profile"),
    path('blog/create/', create_blog, name='create_blog'),
    path('blog/edit/<int:blog_id>/', edit_blog, name='edit_blog'),
    path('blog/delete/<int:blog_id>/', delete_blog, name='delete_blog'),
    path('posts/', posts, name='posts'),
    path('posts/<int:blog_id>/', post_detail, name='post_detail'),
    path('posts/<int:blog_id>/add_comment/', add_comment, name='add_comment'),
    path('comments/<int:comment_id>/delete/', delete_comment, name='delete_comment'),
    path('posts/<int:blog_id>/add_rating/', add_rating, name='add_rating'),
    path('author/<int:author_id>/', author_profile, name='author_profile'),
    path('purchase/<int:blog_id>/', purchase_blog, name='purchase_blog'),
    path('wishlist/', wishlist_view, name='wishlist_view'),

    # Esewa payment success and failure URLs
    path('payment/success/', payment_success, name='payment_success'),
    path('payment/failure/', payment_failure, name='payment_failure'),

    path('my-purchases/', my_purchases, name='my_purchases'),
    path('my-sales/', author_sales, name='author_sales'),

     # Password Reset Request – the user submits their email here.
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(template_name="auth/password_reset.html"),
        name="password_reset",
    ),
    # Inform the user that an email has been sent.
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(template_name="auth/password_reset_done.html"),
        name="password_reset_done",
    ),
    # The link from the email goes here, with uid and token for verification.
    path(
        "password-reset-confirm/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="auth/password_reset_confirm.html"
        ),
        name="password_reset_confirm",
    ),
    # Final confirmation that the password has been reset.
    path(
        "password-reset-complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="auth/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
]
