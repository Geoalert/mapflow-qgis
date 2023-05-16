from enum import Enum

class BillingType(str, Enum):
    credits = 'credits'
    area = 'area'
    none = 'none'