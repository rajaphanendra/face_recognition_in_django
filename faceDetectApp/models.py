from django.db import models

# Create your models here.
class User(models.Model):
    """
    Model to store user information.
    """
    uid = models.CharField(max_length=20, primary_key=True, unique=True)
    name = models.CharField(max_length=100)
    image_path = models.CharField(max_length=255)  # Path to the user's image
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.uid} - {self.name}"


class Attendance(models.Model):
    """
    Model to store attendance information.
    """
    uid = models.CharField(max_length=20)  # Links to User.uid
    name = models.CharField(max_length=100)  # User's name
    in_time = models.DateTimeField(null=True, blank=True)
    out_time = models.DateTimeField(null=True, blank=True)
    date = models.DateField(auto_now_add=True)  # Date of the attendance
    authentication_type = models.CharField(
        max_length=50,
        choices=[("Face", "Face"), ("Manual", "Manual")],
        default="Face"
    )

    def __str__(self):
        return f"{self.name} ({self.uid}) - {self.date}"
