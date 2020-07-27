from src.PFModel import PFModel
import data


class Conus(PFModel):

    def __init__(self, local_path, manifest_path=None, version=1):
        """ Information about the CONUS dataset we are working with

        @param local_path: path on system where conus inputs live
        @param manifest: a file containing the keys and values for CONUS input required_files
        @param version: the conus version to create
        """
        if manifest_path is None:
            manifest_path = data.conus_manifest
        super().__init__('conus', local_path, manifest_path, version)
        # self.mask_array = self.mask_tif.ReadAsArray()
        # had to do this because conus1 mask is all 0's
        if self.version == 1:
            self.mask_array = self.get_domain_mask() + 1
