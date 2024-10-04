from django.shortcuts import render,redirect
from .models import Product,Orders,OrderUpdate,Contact
from django.contrib import messages
from math import ceil
import ast
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.decorators import login_required
# Create your views here.

# paytm
from ekartapp import keys
#for paytm integration import  below modules
import json
from django.views.decorators.csrf import csrf_exempt
from PayTm import Checksum
MERCHANT_KEY=keys.MK
# ___________


def index(request):
    allProds=[]
    catprods=Product.objects.values('category','id')
    cats={item['category'] for item in catprods}
    print(cats)
    for cat in cats:
        prod=Product.objects.filter(category=cat)
        n=len(prod) #if it is 3 category from the samr product it shows 3
        nSlides=n//4 + ceil((n/4)-(n//4))
        print(nSlides)
        allProds.append([prod,range(1,nSlides),nSlides])
    
    print(allProds)
    params={"allProds":allProds}
    return render(request,'index.html',params)

def about(request):
    return render(request,'about.html')


def checkout(request):
    if not request.user.is_authenticated:
        messages.warning(request,"Login & Try Again")
        return redirect('/auth/login') 
    if request.method=="POST":
        items_json = request.POST.get('itemsJson', '')
        name = request.POST.get('name', '')
        amount = request.POST.get('amt')
        email = request.POST.get('email', '')
        address1 = request.POST.get('address1', '')
        address2 = request.POST.get('address2','')
        city = request.POST.get('city', '')
        state = request.POST.get('state', '')
        zip_code = request.POST.get('zip_code', '')
        phone = request.POST.get('phone', '')  

        # logic to update stock and save profit amount in database table Order
        profit=[]
        dataitems=ast.literal_eval(items_json)#{"item1":[1,"product",1000]}.....
        for i in dataitems.values():
            print(i[0],i[1],i[2]) #stock,productname,amount
            getProductname = Product.objects.get(product_name=i[1])
            
        # Handle the case where the product does not exist  
        profitamount=int(i[2])*int(i[0])-int(getProductname.actualprice)*int(i[0])
        profit.append(profitamount)
        getProductname.stock=getProductname.stock-int(i[0])
        getProductname.save()
        
        # final order the items
        profit=sum(profit)
        Order = Orders(items_json=items_json,name=name,amount=amount, email=email, address1=address1,address2=address2,city=city,state=state,zip_code=zip_code,phone=phone,profit=profit)
        Order.save()            
        update = OrderUpdate(order_id=Order.order_id,update_des="the order has been placed")
        update.save()

        #update the order id payment status in database orders tables 
        id = Order.order_id
        # oid=str(id)
        # filter1= Orders.objects.filter(order_id=oid)
        # for post1 in filter1:
        #         post1.oid=oid
        #         post1.amountpaid="CASH ON DELIVERY"
        #         post1.paymentstatus="UN PAID"
        #         post1.save()

        # email_subject="Ordered Placed "
        # message=f' Hello {name}\nYour Ordered is Placed with order id {oid}\n\n\nOrdered Items are\n{items_json}\n\nTotal Amount to be Paid {amount}\n we will soon deliver your ordered on below address\n\nAddress:\n{address1}\n{address2}\n{city}\n{state}\n{zip_code}\n{phone}\n\nYou can track your orders at http://127.0.0.1:8000/profile'
        # email_message = EmailMessage(email_subject,message,settings.EMAIL_HOST_USER,[email])
        # email_message.send()
        # messages.success(request,"Order is placed....")


    # paytm integration code is below
        thank=True
        orid=str(id) + "Flizy"
        param_dict ={
            'MID' : keys.MID,
            'ORDER_ID': orid,
            'TXN_AMOUNT':str(amount),
            'CUST_ID' : email,
            'INDUSTRY_TYPE_ID' : 'Retail',
            'WEBSITE':'WEBSTAGING', #it is for testing
            "CHANNEL_ID" : 'WEB',
            "CHANNEL_URL": 'http://127.0.0.1:8000/handlerequest/'

        } # indha function oda paytm user ku poidum

        param_dict['CHECKSUMHASH'] = Checksum.generate_checksum(param_dict,MERCHANT_KEY)
        return render(request,'paytm.html',{'param_dict':param_dict})


    return render(request,'checkout.html')


@csrf_exempt
def handlerequest(request):
    #paytm will send you post request here
    form =request.POST
    response_dict={}
    for i in form.keys():
        if i =='CHECKSUMHASH':
            checksum =form[i]
        else:
            response_dict[i] =form[i] # it store checksome value

    verify =Checksum.verify_checksum(response_dict,MERCHANT_KEY,checksum)
    if verify:
        if response_dict['RESPCODE'] =="01":
            print('order Successful')
            a=response_dict['ORDERID']
            b=response_dict['TXNAMOUNT']
            rid=a.replace("Flizy","")

            print(rid)
            filter2=Orders.objects.filter(order_id=rid)
            print(filter2)
            print(a,b)
            for post1 in filter2:
                post1.oid=a
                post1.amountpaid=b
                post1.paymentstatus="PAID"
                post1.save()
            print("run agede function")
        else:
            print('order was Not Succesfull because' + response_dict ['RESPMSG'])
        return render(request,'paymentstatus.html', {'response_dict':response_dict})








def search(request):
    query=request.GET['search']

    if len(query) >70:
        allprods=Product.objects.none()
    else:
        allprodsTitle=Product.objects.filter(product_name__icontains=query)
        allprodscontent=Product.objects.filter(category__icontains=query)
        allprodsdesc=Product.objects.filter(desc__icontains=query)
        allprods=allprodsTitle.union(allprodscontent).union(allprodsdesc)

    if allprods.count()==0:
        messages.warning(request,"No Search Results")
    
    print(allprods)
    params={'allprods':allprods,'query':query}

    return render(request,'search.html',params)





def profile(request):
    if not request.user.is_authenticated: 
        messages.warning(request,"Login & Tryagain")
        return redirect("/auth/login/")

    currert_user=request.user.username
    print(currert_user)
    items=Orders.objects.filter(email=currert_user)
    ouid=""
    for i in items:
        myoid=i.oid
        ouid=myoid

    try: 
        status=OrderUpdate.objects.filter(order_id=int(ouid))
        context={'items':items,'status':status}
        return render(request,"profile.html",context)
    except:
        pass
    
    return render(request,"profile.html")

def cancel(request,id):
    order=Orders.objects.filter(order_id=id)
    orderup=OrderUpdate.objects.filter(order_id=id)
    order.delete()
    orderup.delete()

    messages.success(request,"Order Sucessfully Deleted")
    return redirect('/profile')

@login_required
@permission_required('ekartapp.read_product',raise_exception=True)
def dashboard(request):
    product=Product.objects.all()
    total=product.count()
    context={'product':product,'total':total}
    return render(request,'dashboard.html',context)

@login_required
@permission_required('ekartapp.add_product',raise_exception=True)
def addproducts(request):
    if request.method=="POST":
        name=request.POST.get('pname')
        fy=request.FILES['file']
        fy=request.FILES['file']
        category=request.POST.get('category')
        sub_cat=request.POST.get('sub-category')
        description=request.POST.get('desc')
        price=request.POST.get('price')
        stock=request.POST.get('stock')
        paprice=request.POST.get('paprice')
        query=Product(product_name=name,image=fy,category=category,subcategory=sub_cat,price=price,
                    desc=description,stock=stock,actualprice=paprice,)
        query.save()
        # data={'query':query}
        messages.info(request, "Added Product Successfully")
        return redirect('/dashboard')
    return render(request,"addproduct.html")

@login_required
@permission_required('ekartapp.delete_product',raise_exception=True)
def deleteproduct(request,id):
    query=Product.objects.get(id=id)
    query.delete()
    messages.success(request,'Product Deleted Successfully')
    return redirect('/dashboard')

@login_required 
@permission_required('ekartapp.edit_product',raise_exception=True)
def editproduct(request,id):
    edit=Product.objects.get(id=id)
    context={'edit':edit}
    try:
        if request.method=="POST":
            name=request.POST['pname']
            fy=request.FILES['cur_image']
            category=request.POST['category']
            sub_category=request.POST['sub-category']
            desc=request.POST['desc']
            price=request.POST['price']
            stock=request.POST['stock']
            paprice=request.POST['paprice']
            change=Product.objects.get(id=id)
            change.product_name=name
            change.category=category
            change.subcategory=sub_category
            change.desc=desc
            change.price=price
            change.stock=stock
            change.actualprice=paprice
            change.image=fy
            change.save()
            messages.success(request,"Products Successfully updated")
            return redirect('/dashboard')
    except:
        if request.method=="POST":
            name=request.POST['pname']
            category=request.POST['category']
            sub_category=request.POST['sub-category']
            desc=request.POST['desc']
            price=request.POST['price']
            stock=request.POST['stock']
            paprice=request.POST['paprice']
            change=Product.objects.get(id=id)
            change.product_name=name
            change.category=category
            change.subcategory=sub_category
            change.desc=desc
            change.price=price
            change.stock=stock
            change.actualprice=paprice
            change.save()
            messages.success(request,"Products Successfully updated")
            return redirect('/dashboard')

    return render(request,"editproduct.html",context)



def contact(request):
    if request.method=="POST":
        name=request.POST.get('name')
        Email=request.POST.get('email')
        desc=request.POST.get('desc')
        phoneno=request.POST.get('number')
        query=Contact(name=name,email=Email,desc=desc,
                      phonenumber=phoneno)
        query.save()
        messages.success(request,"We Will Reach You Soon")
    return render(request,'contact.html')