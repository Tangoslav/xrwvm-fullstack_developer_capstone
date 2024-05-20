from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
import logging
import json
from django.views.decorators.csrf import csrf_exempt
from .models import CarMake, CarModel
from .restapis import get_request, analyze_review_sentiments, post_review

# Get an instance of a logger
logger = logging.getLogger(__name__)

@csrf_exempt
def login_user(request):
    data = json.loads(request.body)
    username = data['userName']
    password = data['password']
    user = authenticate(username=username, password=password)
    data = {"userName": username}
    if user is not None:
        login(request, user)
        data = {"userName": username, "status": "Authenticated"}
    return JsonResponse(data)

@csrf_exempt
def logout_request(request):
    username = request.user.username
    logout(request)
    data = {"userName": username}
    return JsonResponse(data)

@csrf_exempt
def registration(request):
    context = {}
    data = json.loads(request.body)
    username = data['userName']
    password = data['password']
    first_name = data['firstName']
    last_name = data['lastName']
    email = data['email']
    username_exist = False
    try:
        User.objects.get(username=username)
        username_exist = True
    except User.DoesNotExist:
        logger.debug(f"{username} is a new user")
    if not username_exist:
        user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name, password=password, email=email)
        login(request, user)
        data = {"userName": username, "status": "Authenticated"}
        return JsonResponse(data)
    else:
        data = {"userName": username, "error": "Already Registered"}
        return JsonResponse(data)

@csrf_exempt
def get_cars(request):
    count = CarMake.objects.filter().count()
    if count == 0:
        initiate()
        logger.debug("No CarMakes found, initializing data.")
    else:
        logger.debug(f"Found {count} CarMakes in the database.")

    car_models = CarModel.objects.select_related('car_make')
    cars = [{"CarModel": car_model.name, "CarMake": car_model.car_make.name} for car_model in car_models]
    
    if not cars:
        logger.debug("No cars found in the database.")
    else:
        logger.debug(f"Found {len(cars)} cars in the database.")

    return JsonResponse({"CarModels": cars})

def initiate():
    car_make_data = [
        {"name": "NISSAN", "description": "Great cars. Japanese technology"},
        {"name": "Mercedes", "description": "Great cars. German technology"},
        {"name": "Audi", "description": "Great cars. German technology"},
        {"name": "Kia", "description": "Great cars. Korean technology"},
        {"name": "Toyota", "description": "Great cars. Japanese technology"},
    ]

    car_make_instances = []
    for data in car_make_data:
        car_make_instances.append(CarMake.objects.create(name=data['name'], description=data['description']))

    car_model_data = [
        {"name": "Pathfinder", "car_type": "SUV", "year": 2023, "car_make": car_make_instances[0]},
        {"name": "Qashqai", "car_type": "SUV", "year": 2023, "car_make": car_make_instances[0]},
        {"name": "XTRAIL", "car_type": "SUV", "year": 2023, "car_make": car_make_instances[0]},
        {"name": "A-Class", "car_type": "SUV", "year": 2023, "car_make": car_make_instances[1]},
        {"name": "C-Class", "car_type": "SUV", "year": 2023, "car_make": car_make_instances[1]},
        {"name": "E-Class", "car_type": "SUV", "year": 2023, "car_make": car_make_instances[1]},
        {"name": "A4", "car_type": "SUV", "year": 2023, "car_make": car_make_instances[2]},
        {"name": "A5", "car_type": "SUV", "year": 2023, "car_make": car_make_instances[2]},
        {"name": "A6", "car_type": "SUV", "year": 2023, "car_make": car_make_instances[2]},
        {"name": "Sorrento", "car_type": "SUV", "year": 2023, "car_make": car_make_instances[3]},
        {"name": "Carnival", "car_type": "SUV", "year": 2023, "car_make": car_make_instances[3]},
        {"name": "Cerato", "car_type": "Sedan", "year": 2023, "car_make": car_make_instances[3]},
        {"name": "Corolla", "car_type": "Sedan", "year": 2023, "car_make": car_make_instances[4]},
        {"name": "Camry", "car_type": "Sedan", "year": 2023, "car_make": car_make_instances[4]},
        {"name": "Kluger", "car_type": "SUV", "year": 2023, "car_make": car_make_instances[4]},
    ]

    for data in car_model_data:
        CarModel.objects.create(
            name=data['name'],
            car_make=data['car_make'],
            car_type=data['car_type'],
            year=data['year'],
            dealer_id=1  # Set a default dealer_id or update as per your data
        )

def get_dealerships(request, state="All"):
    if(state == "All"):
        endpoint = "/fetchDealers"
    else:
        endpoint = "/fetchDealers/"+state
    dealerships = get_request(endpoint)
    return JsonResponse({"status":200,"dealers":dealerships})

def get_dealer_details(request, dealer_id):
    if(dealer_id):
        endpoint = "/fetchDealer/"+str(dealer_id)
        dealership = get_request(endpoint)
        return JsonResponse({"status":200,"dealer":dealership})
    else:
        return JsonResponse({"status":400,"message":"Bad Request"})

def get_dealer_reviews(request, dealer_id):
    # if dealer id has been provided
    if(dealer_id):
        endpoint = "/fetchReviews/dealer/"+str(dealer_id)
        reviews = get_request(endpoint)
        for review_detail in reviews:
            response = analyze_review_sentiments(review_detail['review'])
            print(response)
            review_detail['sentiment'] = response['sentiment']
        return JsonResponse({"status":200,"reviews":reviews})
    else:
        return JsonResponse({"status":400,"message":"Bad Request"})

def add_review(request):
    if(request.user.is_anonymous == False):
        data = json.loads(request.body)
        try:
            response = post_review(data)
            return JsonResponse({"status":200})
        except:
            return JsonResponse({"status":401,"message":"Error in posting review"})
    else:
        return JsonResponse({"status":403,"message":"Unauthorized"})