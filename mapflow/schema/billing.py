from enum import Enum


class BillingType(str, Enum):
    credits = 'CREDITS'
    area = 'AREA'
    none = 'NONE'