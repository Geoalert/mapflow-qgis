from .collection import ProvidersDict
from .provider import Provider, CRS, SourceType, BasicAuth
from .proxy_provider import ProxyProvider, MaxarProxyProvider
from .default import SentinelProvider, MaxarSecureWatchProxyProvider, MaxarVividProxyProvider, MapboxProvider
from .xyz_provider import XYZProvider, MaxarProvider, TMSProvider, QuadkeyProvider
from .factory import create_provider