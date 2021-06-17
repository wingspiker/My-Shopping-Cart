from django.shortcuts import render
from django.http import HttpResponse
from .models import Product,Contact,Orders,orderUpdate
from math import ceil
import json
import re
from django.views.decorators.csrf import csrf_exempt
import paytmchecksum
MERCHANT_KEY = 'kbzk1DSbJiV_O3p5'

def index(request):
    products = Product.objects.all()
    n = len(products)
    nslides = n//4 + ceil((n/4) - (n//4))
    allprods = []
    allcats ={i['category'] for i in Product.objects.values('category')}
    for cat in allcats:
        prod = Product.objects.filter(category=cat)
        n = len(prod)
        nslides = n // 4 + ceil((n / 4) - (n // 4))
        allprods.append([prod,range(1,nslides),nslides])

    params = {'allprods':allprods}
    return render(request,'shop/index.html',params)

def SearchMatch(query,item):
    '''Return True only when query match item name or catgory or desc'''
    if query in item.desc.lower() or query in item.product_name.lower() or query in item.category.lower():
        return True
    else:
        return False

def search(request):
    query = request.GET.get('search')
    query = query.lower()
    products = Product.objects.all()
    n = len(products)
    nslides = n//4 + ceil((n/4) - (n//4))
    allprods = []
    allcats ={i['category'] for i in Product.objects.values('category')}
    for cat in allcats:
        prodtemp = Product.objects.filter(category=cat)
        prod = [item for item in prodtemp if SearchMatch(query,item)]
        n = len(prod)
        nslides = n // 4 + ceil((n / 4) - (n // 4))
        if len(prod) !=0:
           allprods.append([prod,range(1,nslides),nslides])

    params = {'allprods':allprods,'msg':""}
    if len(allprods) == 0 or len(query)<4:
        print("hii")
        params = {'allprods':[],'msg':"Please make sure you enter relevant search query."}
    return render(request,'shop/index.html',params)

def about(request):
    return render(request,'shop/about.html')

def contact(request):
    thank = False
    if request.method == "POST":
        name = request.POST.get('name','')
        email = request.POST.get('email','')
        phone = request.POST.get('phone','')
        desc = request.POST.get('desc','')
        contact = Contact(name=name,email = email,phone =phone,desc = desc)
        contact.save()
        thank = True
    return render(request,'shop/contact.html',{'thank':thank})

def tracker(request):
    if request.method == "POST":
        order_id = request.POST.get('orderid', '')
        email = request.POST.get('email', '')
        try:
            order = Orders.objects.filter(order_id=order_id, email=email)
            if len(order)>0:
                update = orderUpdate.objects.filter(order_id=order_id)
                updates = []
                for item in update:
                    updates.append({'text':item.update_desc,'time':item.timestamp})
                response = json.dumps({"status":"success","updates":updates,"itemJson": order[0].items_json}, default=str)
                return HttpResponse(response)
            else:
                return HttpResponse('{"status":"noitem"}')
        except Exception as e:
            return HttpResponse('{"status":"error"}')
    return render(request,'shop/tracker.html')


def productview(request, myid):
    # Fetch The product using Id
    product = Product.objects.filter(id= myid)
    return render(request,'shop/productview.html',{'product':product[0]})

def checkout(request):
    if request.method == "POST":
        items_json = request.POST.get('itemsjson','')
        amount = request.POST.get('amount','')
        name = request.POST.get('name','')
        email = request.POST.get('email','')
        address = request.POST.get('address','') + " " + request.POST.get('address2','')
        city = request.POST.get('city','')
        state = request.POST.get('state','')
        zipcode = request.POST.get('zipcode','')
        phone = request.POST.get('phone', '')
        order = Orders(items_json=items_json,amount=amount,name=name,email = email,address =address,city = city,state=state,zip_code=zipcode,phone=phone)
        order.save()
        update = orderUpdate(order_id = order.order_id,update_desc = "The Order has been placed")
        update.save()
        thanks = True
        id = order.order_id
        #return render(request, 'shop/checkout.html',{'thank':thanks,'id':id})

        param_dict = {
                    'MID':'WorldP64425807474247',
                    'ORDER_ID':str(order.order_id),
                    'TXN_AMOUNT': str(amount),
                    'CUST_ID':email,
                    'INDUSTRY_TYPE_ID':'Retail',
                    'WEBSITE': "WEBSTAGING",
                    'CHANNEL_ID':'WEB',
                    'CALLBACK_URL':'http://127.0.0.1:8000/shop/handlerequest/',
                }
        param_dict['CHECKSUMHASH'] =  paytmchecksum.generateSignature(param_dict, MERCHANT_KEY)
        return render(request, 'shop/paytm.html',{'param_dict':param_dict})
    return render(request,'shop/checkout.html')

@csrf_exempt
def handlerequest(request):
    # Paytm send post request here
    form = request.POST
    response_dict={}
    for i in form.keys():
        response_dict[i] = form[i]
        if i == 'CHECKSUMHASH':
            checksum = form[i]
    verify = paytmchecksum.verifySignature(response_dict,MERCHANT_KEY,checksum)
    if verify:
        if response_dict['RESPCODE'] == '01':
            print("Order Successful")
        else:
            print("Order was not successful because " + response_dict['RESPMSG'])
    return render(request,'shop/paymentstatus.html',{'response':response_dict})