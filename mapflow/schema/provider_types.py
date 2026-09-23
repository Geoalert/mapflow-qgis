from enum import Enum


class StrEnum(str, Enum):
    pass


class SourceType(StrEnum):
    xyz = 'xyz'
    tms = 'tms'
    quadkey = 'quadkey'
    local = 'local'

    @property
    def requires_crs(self):
        return self.value in (self.xyz, self.tms, self.quadkey)


class CRS(StrEnum):
    web_mercator = 'EPSG:3857'
    world_mercator = 'EPSG:3395'


class BasicAuth:
    def __init__(self, login: str = "", password: str = ""):  # nosec B107  # empty default, not a secret
        if not isinstance(login, str) or not isinstance(password, str):
            raise TypeError("Login and password must be string")
        self.login = login
        self.password = password

    def __iter__(self):
        # to convert to tuple/list
        yield self.login
        yield self.password

    def __bool__(self):
        return bool(self.login) or bool(self.password)

    def __str__(self):
        return f'{self.login}:{self.password}'
