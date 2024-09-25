import datetime

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
    if request.method == "GET":
        listing = get_object_or_404(Listing, id=listing_id)
        bid = Bid.objects.filter(listing=listing).order_by('-timestamp').first()
        num_bids = Bid.objects.filter(listing=listing).count()
        bidder = bid.bidder

        form = BidForm()
        if request.user == bidder:
            bool = True
        else:
            bool = False
        firstbid = Bid.objects.filter(listing=listing).order_by('timestamp').first()
        owner = firstbid.bidder
        if request.user == owner:
            bool2 = True
        else:
            bool2 = False
        if not listing.active:
            messages.info(request, "THIS LISTING IS CLOSED", extra_tags="listing")
            if request.user == bidder:
                messages.info(request, "YOU ARE THE WINNER", extra_tags="listing")
            else:
                messages.info(request, "YOU ARE NOT THE WINNER", extra_tags="listing")
        commentform = CommentForm()
        comments = Comment.objects.filter(listing=listing).all()
        return render(request, "auctions/view_listing.html", {
            "listing": listing,
            "bid": bid,
            "no_of_bids": num_bids,
            "owner": owner,
            "form": form,
            "bool": bool,
            "bool2": bool2,
            "activity": listing.active,
            "commentform": commentform,
            "comments": comments
    })
    elif request.method == "POST":
        form = BidForm(request.POST)
        form2 = CommentForm(request.POST)
        if form.is_valid():
            bid = form.save(commit=False)
            bid.listing = Listing.objects.filter(id=listing_id, active=True).first()
            if bid.bid <= bid.listing.current_price:
                messages.error(request, "Bid Must Be Higher Than Current Bid", extra_tags="incorrect_bid")
                return redirect(reverse("view_listing",args=[listing_id]))
            bid.bidder = request.user
            bid.save()
            listing = Listing.objects.filter(id=listing_id).first()
            listing.current_price = bid.bid
            listing.save()
        elif ("action","close") in request.POST.items():
            listing_id = request.POST.get('listing_id')
            listing = Listing.objects.filter(id=listing_id).first()
            listing.active = False
            listing.save()
        elif form2.is_valid():
            comment = form2.save(commit=False)
            comment.commenter = request.user
            comment.listing = Listing.objects.filter(id=listing_id).first()
            comment.save()
        return redirect(reverse('view_listing', args=[listing_id]))


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