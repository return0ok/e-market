from datetime import timezone, datetime

from django.db import models
import uuid
# Create your models here.

from apps.common.managers import GetOrNoneManager, IsDeletedManager

class BaseModel(models.Model):
    """
        A base model class that includes common fields and methods for all models.

        Attributes:
            id (UUIDField): Unique identifier for the model instance.
            created_at (DateTimeField): Timestamp when the instance was created.
            updated_at (DateTimeField): Timestamp when the instance was last updated.
    """

    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    objects = GetOrNoneManager()

    class Meta:
        abstract = True

class IsDeletedModel(BaseModel):
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-id']  # New
        abstract = True

    objects = IsDeletedManager()

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        # self.deleted_at = timezone.now()  # - xatolik AttributeError: type object 'datetime.timezone' has no attribute 'now'
        self.deleted_at = datetime.now()

        self.save(update_fields=["is_deleted", "deleted_at"])

    def hard_delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
