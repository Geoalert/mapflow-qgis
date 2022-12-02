
MAXAR_META_URL = ""

MAXAR_REQUEST_BODY = """<?xml version="1.0" encoding="utf-8"?>
    <GetFeature 
        service="wfs" 
        version="1.1.0"
        outputFormat="json"
        xmlns="http://www.opengis.net/wfs" 
        xmlns:ogc="http://www.opengis.net/ogc">
        <Query typeName="DigitalGlobe:FinishedFeature" srsName="EPSG:4326">
        <PropertyName>productType</PropertyName>
        <PropertyName>source</PropertyName>
        <PropertyName>colorBandOrder</PropertyName>
        <PropertyName>cloudCover</PropertyName>
        <PropertyName>offNadirAngle</PropertyName>
        <PropertyName>acquisitionDate</PropertyName>
        <PropertyName>geometry</PropertyName>
        <ogc:Filter>
            <ogc:And>
                <ogc:PropertyIsBetween>
                    <ogc:PropertyName>acquisitionDate</ogc:PropertyName>
                    <ogc:LowerBoundary>
                        <ogc:Literal>{from_}</ogc:Literal>
                    </ogc:LowerBoundary>
                    <ogc:UpperBoundary>
                        <ogc:Literal>{to}</ogc:Literal>
                    </ogc:UpperBoundary>
                </ogc:PropertyIsBetween>
                <ogc:Or>
                    <ogc:PropertyIsLessThanOrEqualTo>
                        <ogc:PropertyName>cloudCover</ogc:PropertyName>
                        <ogc:Literal>{max_cloud_cover}</ogc:Literal>
                    </ogc:PropertyIsLessThanOrEqualTo>
                    <ogc:PropertyIsNull>
                        <ogc:PropertyName>cloudCover</ogc:PropertyName>
                    </ogc:PropertyIsNull>
                </ogc:Or>
                <ogc:Intersects>
                    <ogc:PropertyName>geometry</ogc:PropertyName>
                    {geometry}
                </ogc:Intersects>
            </ogc:And>
        </ogc:Filter>
        <ogc:SortBy>
            <ogc:SortProperty>
                <ogc:PropertyName>acquisitionDate</ogc:PropertyName>
                <ogc:SortOrder>DESC</ogc:SortOrder>
            </ogc:SortProperty>
        </ogc:SortBy>
        </Query>
    </GetFeature>"""
