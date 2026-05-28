import datetime
from django.utils import timezone
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from .models import *
from .forms import *


def index(request):
    all_listings = Listing.objects.filter(active=True)
    print(all_listings)
    return render(request, "auctions/index.html", {
        "all_listings": all_listings
    })


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")


@login_required
def create_listing(request):
    if request.method == "GET":
        return render(request, "auctions/create_listing.html", {
            "form": ListingForm()
        })
    elif request.method == "POST":
        form = ListingForm(request.POST)
        if form.is_valid():
            listing = form.save(commit=False)
            listing.owner = request.user
            listing.current_price = listing.starting_bid

            category = form.cleaned_data.get('category')
            if category:
                listing.category = category
            else:
                new_category = form.cleaned_data.get('new_category')
                if new_category:
                    category, created = Category.objects.get_or_create(name=new_category)
                    listing.category = category

            listing.save()
            bid = Bid()
            bid.listing = listing
            bid.bid = listing.starting_bid
            bid.bidder = listing.owner
            bid.timestamp = datetime.datetime.now()
            bid.save()
            return redirect('index')
        else:
            return render(request, "auctions/create_listing.html", {
                "form": form
            })


@login_required
def view_listing(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id)
    owner = listing.owner  # donor who created the listing
 
    if request.method == "GET":
        if not listing.active:
            messages.info(request, "This listing is no longer available.", extra_tags="listing")
 
        commentform = CommentForm()
        comments = Comment.objects.filter(listing=listing).all()
 
        return render(request, "auctions/view_listing.html", {
            "listing": listing,
            "owner": owner,
            "bool2": request.user == owner,        # True if viewer is the donor
            "activity": listing.active,
            "commentform": commentform,
            "comments": comments,
        })
 
    elif request.method == "POST":
        action = request.POST.get("action")
 
        # --- Rider accepts pickup ---
        if action == "claim":
            if request.user == owner:
                messages.error(request, "You can't accept pickup of your own donation.", extra_tags="listing")
                return redirect(reverse("view_listing", args=[listing_id]))
 
            if hasattr(listing, "acceptance"):
                messages.error(request, "This listing has already been accepted by a rider.", extra_tags="listing")
                return redirect(reverse("view_listing", args=[listing_id]))
 
            PickupAcceptance.objects.create(
                listing=listing,
                rider=request.user,
            )
            listing.active = False
            listing.save()
            messages.success(request, "Pickup accepted! Connect with the donor to arrange collection.", extra_tags="listing")
            return redirect(reverse("view_listing", args=[listing_id]))
 
        # --- Donor closes / marks as picked up ---
        elif action == "close":
            if request.user == owner:
                listing.active = False
                listing.save()
                if hasattr(listing, "acceptance"):
                    listing.acceptance.completed = True
                    listing.acceptance.completed_at = timezone.now()
                    listing.acceptance.save()
            return redirect(reverse("view_listing", args=[listing_id]))
 
        # --- Comment ---
        else:
            form2 = CommentForm(request.POST)
            if form2.is_valid():
                comment = form2.save(commit=False)
                comment.commenter = request.user
                comment.listing = listing
                comment.save()
            return redirect(reverse("view_listing", args=[listing_id]))
 



@login_required()
def category(request):
    list = Category.objects.all()
    return render(request, "auctions/category.html", {
        "list": list
    })


@login_required()
def cat(request, cat):
    cat = Category.objects.filter(name=cat).first()
    listings = Listing.objects.filter(category=cat, active=True).all()
    return render(request, "auctions/cat.html", {
        "list": listings,
        "cat":cat
    })

@login_required()
def watchlist(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        listing_id = request.POST.get('listing_id')

        if action == 'change' and listing_id:
            listing = get_object_or_404(Listing, id=listing_id)

            watchlist_item, created = Watchlist.objects.get_or_create(user=request.user, listing=listing)
            if not created:
                watchlist_item.delete()
                messages.success(request, "Removed from your watchlist.", extra_tags="wishlist")
            else:
                messages.success(request, "Added to your watchlist.", extra_tags="wishlist")

            return redirect(reverse('view_listing', args=[listing_id]))
    elif request.method == 'GET':
        user = request.user
        watchlist = Watchlist.objects.filter(user=user).all()
        return render(request, "auctions/watchlist.html", {
            "watchlist": watchlist,
            "user": user
        })

@login_required()
def closed_listings(request):
    listings = Listing.objects.filter(active=False).all()
    return render(request, "auctions/closed_listings.html", {
        "closed_listings": listings
    })



@login_required
def my_pickups(request):
    accepted = PickupAcceptance.objects.filter(
        rider=request.user
    ).select_related("listing", "listing__owner", "listing__category").order_by("-accepted_at")
 
    pending = [p for p in accepted if not p.completed]
    completed = [p for p in accepted if p.completed]
 
    return render(request, "auctions/my_pickups.html", {
        "pending": pending,
        "completed": completed,
    })
 
 
@login_required
def complete_pickup(request, acceptance_id):
    if request.method == "POST":
        acceptance = get_object_or_404(PickupAcceptance, id=acceptance_id, rider=request.user)
        acceptance.completed = True
        acceptance.completed_at = timezone.now()
        acceptance.save()
    return redirect("my_pickups")
