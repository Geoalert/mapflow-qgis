# -*- coding: utf-8 -*-

def classFactory(iface):
    #
    from .energy_geoalert import EnergyGeoalert
    return EnergyGeoalert(iface)
