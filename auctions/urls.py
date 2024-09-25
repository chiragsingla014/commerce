from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("create_listing/", views.create_listing, name="create_listing"),
    path("view_listing/<int:listing_id>", views.view_listing, name="view_listing"),
    path("category", views.category, name="category"),
    path("category/<str:cat>", views.cat, name="cat"),
    path("watchlist", views.watchlist, name="watchlist"),
    path("closed_listings", views.closed_listings, name="closed_listings")
]


# If the user is signed in and is the one who created the listing,
# the user should have the ability to “close” the auction from this page,
# which makes the highest bidder the winner of the auction and makes the listing no longer active.
#
#
# If a user is signed in on a closed listing page, and the user has won that auction, the page should say so.
#
#
# Users who are signed in should be able to add comments to the listing page.
# The listing page should display all comments that have been made on the listing.
