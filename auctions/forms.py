from django import forms
from .models import *


class ListingForm(forms.ModelForm):
    new_category = forms.CharField(required=False, max_length=100, label='OR Create a new category', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter new category'}))

    class Meta:
        model = Listing
        fields = ['title', 'description', 'starting_bid', 'image', 'category', 'new_category']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'starting_bid': forms.NumberInput(attrs={'class': 'form-control'}),
            'image': forms.URLInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super(ListingForm, self).__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.all()
        self.fields['category'].required = False


class BidForm(forms.ModelForm):
    class Meta:
        model = Bid
        fields = ['bid']
        widgets = {
            'bid': forms.TextInput(attrs={'class': 'form-control', 'placeholder':'Your Bid'}),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['comment']
        widgets = {
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows':'4 '}),
        }