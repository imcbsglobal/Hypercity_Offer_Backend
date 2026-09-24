from django.db import models


class SynctoolBase(models.Model):
    id = models.BigAutoField(primary_key=True)

    class Meta:
        abstract = True


class AccMaster(SynctoolBase):
    code = models.CharField(max_length=30)
    name = models.CharField(max_length=250)
    place = models.CharField(max_length=60, null=True, blank=True)
    exregnodate = models.CharField(max_length=30, null=True, blank=True)
    super_code = models.CharField(max_length=5, null=True, blank=True)
    phone2 = models.CharField(max_length=60, null=True, blank=True)
    client_id = models.CharField(max_length=50, db_index=True)
    synced_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'acc_master_sync'
        ordering = ['code']
        unique_together = [('code', 'client_id')]

    def __str__(self):
        return f"{self.code} - {self.name} [{self.client_id}]"


class Misel(SynctoolBase):
    firm_name = models.CharField(max_length=150, null=True, blank=True)
    address1 = models.CharField(max_length=50, null=True, blank=True)
    client_id = models.CharField(max_length=50, db_index=True)
    synced_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'misel_sync'
        ordering = ['id']
        unique_together = [('firm_name', 'client_id')]

    def __str__(self):
        return f"{self.firm_name} [{self.client_id}]"


class AccInvMast(SynctoolBase):
    slno = models.BigIntegerField()
    invdate = models.DateField(null=True, blank=True)
    customerid = models.CharField(max_length=30, null=True, blank=True)
    nettotal = models.DecimalField(max_digits=16, decimal_places=3, null=True, blank=True)
    client_id = models.CharField(max_length=50, db_index=True)
    synced_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = 'acc_invmast_sync'
        ordering = ['-invdate', '-slno']
        unique_together = [('slno', 'client_id')]

    def __str__(self):
        return f"Invoice {self.slno} | {self.customerid} | {self.client_id}"