from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

# Create your models here.
class User(AbstractUser):
    # User Information
    admin_status = models.BooleanField(default=False)
    email = models.EmailField(unique=True, blank=True)
    phone_number = models.CharField(max_length=17, blank=True)

    # Specify related_name for reverse relationships
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',  # Specify a custom related name
        blank=True
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_permissions',  # Specify a custom related name
        blank=True
    )

    USERNAME_FIELD = "email"  # Use email for authentication, don't need a username
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    def is_admin(self):
        return self.admin_status
class Task(models.Model):
    STATUS_CHOICES = (
        ('SUBMITTED', 'Submitted'),
        ('CONFIRMED', 'Confirmed'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    )

    TASK_TYPE_CHOICES = (
        ('HVACSI', 'HVAC: System Installation'),
        ('HVACDI', 'HVAC: Ductwork Installation'),
        ('HVACTI', 'HVAC: Thermostat Installation'),
        ('FAUCET', 'Plumbing: Faucet Installation'),
        ('SINK', 'Plumbing: Sink Installation'),
        ('TOILET', 'Plumbing: Toilet Installation'),
        ('TANK_WATER_HEATER', 'Tank Water Heater Installation/Maintenance'),
        ('TANKLESS_WATER_HEATER', 'Tankless Water Heater Installation/Maintenance')
    )

    RATING_CHOICES = (
        (5, 'Superb'),
        (4, 'Great'),
        (3, 'Good'),
        (2, 'OK'),
        (1, 'Unsatisfied')
    )
 
    # Task Client Details
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="service_requests")
    email = models.EmailField(blank=True)
    phone_number = models.CharField(max_length=17, blank=True)
    client_update_date = models.DateTimeField(null=True, blank=True)

    # Time Intervals
    status = models.CharField(max_length=15, default="SUBMITTED", choices=STATUS_CHOICES)
    submission_date = models.DateTimeField(null=True, blank=True)
    confirmed_date = models.DateTimeField(null=True, blank=True)
    payment_date = models.DateTimeField(null=True, blank=True)
    completed_date = models.DateTimeField(null=True, blank=True)
    cancelled_date = models.DateTimeField(null=True, blank=True)
    scheduled_date = models.DateTimeField(max_length=500, null=True, blank=True)
    
    # Task Details
    service_type = models.CharField(max_length=50, choices=TASK_TYPE_CHOICES)
    description = models.CharField(max_length=500)
    notes = models.CharField(max_length=500, blank=True)
    admin_update_date = models.DateTimeField(null=True, blank=True)
    # task_address = models.CharField()

    # Payment Details
    paid = models.BooleanField(default=False)
    payment_date = models.DateTimeField(null=True, blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

    # Task Review
    review_rating = models.IntegerField(choices=RATING_CHOICES, null=True)
    review_text = models.CharField(max_length=500, null=True)
    review_date = models.DateTimeField(null=True, blank=True)

    def as_dict(self):
        task_dict = {}
        task_dict['request_name'] = self.user.get_full_name()
        task_dict['email'] = self.email
        task_dict['phone_number'] = self.phone_number
        task_dict['status'] = self.status
        task_dict['submission_date'] = self.submission_date
        task_dict['payment_date'] = self.payment_date
        task_dict['completed_date'] = self.completed_date
        task_dict['confirmed_date'] = self.confirmed_date
        task_dict['scheduled_date'] = self.scheduled_date
        task_dict['service_type'] = self.service_type
        task_dict['description'] = self.description
        task_dict['notes'] = self.notes
        task_dict['updated_date'] = self.updated_date
        # task_dict['task_address'] = self.task_address
        task_dict['review_rating'] = self.review_rating
        task_dict['review_text'] = self.review_text 
        task_dict['review_date'] = self.review_date 

        return task_dict
    
    def update_time(self):
        match self.status:
            case 'SUBMITTED': 
                self.submission_date = timezone.now()
            case 'CANCELLED':
                self.cancelled_date = timezone.now()
            case 'COMPLETED':
                self.completed_date = timezone.now()