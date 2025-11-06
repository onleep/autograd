from config import DB_NAME, DB_PASS
from tortoise import Tortoise, fields
from tortoise.models import Model


class Offers(Model):
    id = fields.IntField(primary_key=True)
    autoru_id = fields.IntField(unique=True)
    autoru_hash = fields.CharField(max_length=8, index=True)
    mark = fields.CharField(max_length=100)
    model = fields.CharField(max_length=100)
    price = fields.FloatField()
    year = fields.IntField()
    mileage = fields.IntField()
    color = fields.CharField(max_length=100, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)


class Photos(Model):
    id = fields.IntField(primary_key=True)
    autoru = fields.ForeignKeyField('models.Offers', to_field='autoru_id')
    autoru_id: int  # created by autoru key
    name = fields.CharField(max_length=100)
    url = fields.CharField(unique=True, max_length=255)
    status = fields.IntField(default=0, index=True)
    created_at = fields.DatetimeField(auto_now_add=True, index=True)
    updated_at = fields.DatetimeField(auto_now=True)


class Attributes(Model):
    id = fields.IntField(primary_key=True)
    autoru = fields.OneToOneField('models.Offers', to_field='autoru_id')
    autoru_id: int  # created by autoru key
    region = fields.CharField(max_length=255, null=True)
    custom_cleared = fields.BooleanField()
    owners = fields.IntField()
    tags = fields.JSONField(null=True)
    predicted_prices = fields.JSONField(null=True)
    description = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)


class Specifications(Model):
    id = fields.IntField(primary_key=True)
    autoru = fields.OneToOneField('models.Offers', to_field='autoru_id')
    autoru_id: int  # created by autoru key
    base = fields.JSONField(null=True)
    general = fields.JSONField(null=True)
    sizes = fields.JSONField(null=True)
    volume_and_mass = fields.JSONField(null=True)
    transmission = fields.JSONField(null=True)
    suspension_and_brakes = fields.JSONField(null=True)
    performance_indicators = fields.JSONField(null=True)
    engine = fields.JSONField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)


async def dbinit():
    await Tortoise.init(
        db_url=f'mysql://root:{DB_PASS}@mysql/{DB_NAME}',
        modules={'models': ['database.mysql']},
    )
    await Tortoise.generate_schemas()


async def dbclose():
    await Tortoise.close_connections()
