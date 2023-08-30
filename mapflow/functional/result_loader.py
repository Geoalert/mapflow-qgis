from ..entity.processing import Processing


class ResultLoader:
    def __init__(self, processing: Processing, http):
        self.processing = processing
        self.raster_tilejson = None
        self.vector_tilejson = None
        self.raster_layer = None
        self.vector_layer = None
        self.http = http

    def __call__(self):
        """ Entrypoint """
        self.get_raster_tilejson()

    def get_raster_tilejson(self):
        pass

    def get_vector_tilejson(self, response):
        pass
