# -*- coding: utf-8 -*-

def classFactory(iface):
    from .geoalert import Geoalert
    return Geoalert(iface)
