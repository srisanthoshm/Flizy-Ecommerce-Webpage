from ekartapp import views
from django.urls import path

urlpatterns = [
    path('',views.index,name="index"),
    path('about/',views.about,name="about"),
    path('contact/',views.contact,name="contact"),
    path('checkout/',views.checkout,name="checkout"),
    path('profile/',views.profile,name="profile"),
    path('search/',views.search,name="search"),
    path('cancelorder/<id>',views.cancel,name="cancel"),
    path('dashboard/',views.dashboard,name='dashboard'),
    path('dashboard/addproduct',views.addproducts,name="addproduct"),
    path('dashboard/editProduct/<id>/',views.editproduct,name="editproduct"),
    path('dashboard/deleteProduct/<id>',views.deleteproduct,name="deleteproduct"),

    # paytm integration
    path('handlerequest/',views.handlerequest,name="HandleRequest"),
]
