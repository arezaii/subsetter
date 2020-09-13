import os
import logging
import yaml
import errno
import parflow.subset.data as data
import parflow.subset.utils.io as file_io_tools


class ParflowDomain:

    def __init__(self, name, local_path, manifest_file=None, version=1):
        """ Information about the ParFlow model and dataset we are working with

        @param name: the name of the Model to create
        @param local_path: path on system where ALL model inputs live
        @param manifest_file: a file containing the keys and values for Model input required_files
        @param version: the Model version to create (optional)
        """
        self.name = name
        self.version = version
        self.local_path = local_path
        self.manifest_file = manifest_file
        self.required_files = {}
        self.optional_files = {}
        if self.manifest_file is not None:
            self._read_manifest(self.required_files, self.optional_files)
        self.check_inputs_exist()
        self.check_destination()
        self.mask_tif = None
        self.mask_array = None

    def _load_domain_tif(self, domain_mask_key='DOMAIN_MASK'):
        tif_filename = os.path.join(self.local_path, self.required_files.get(domain_mask_key))
        self.mask_tif = file_io_tools.read_geotiff(tif_filename)
        self.mask_array = file_io_tools.read_file(tif_filename)

    def get_domain_mask(self, domain_mask_key='DOMAIN_MASK'):
        """ get the domain full_dim_mask array

        @param domain_mask_key: key in yaml file which defines the domain full_dim_mask
        @return: numpy array for the domain full_dim_mask
        """
        if self.mask_array is None:
            self._load_domain_tif(domain_mask_key)
        return self.mask_array

    def get_domain_tif(self, domain_mask_key='DOMAIN_MASK'):
        """ get the domain full_dim_mask tif as a gdal geotif object

        @param domain_mask_key: key in yaml file which defines the domain full_dim_mask
        @return: gdal object for the domain full_dim_mask
        """
        if self.mask_tif is None:
            self._load_domain_tif(domain_mask_key)
        return self.mask_tif

    def check_inputs_exist(self):
        """ Look for each input file to see if it exists

        @return: None
        """
        # check for required files
        required_missing = self._identify_missing_inputs(self.required_files)
        if len(required_missing) > 0:
            logging.error(f'could not locate required model input file(s) {required_missing}')
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), required_missing)
        # check for optional files
        optional_missing = self._identify_missing_inputs(self.optional_files)
        if len(optional_missing) > 0:
            logging.warning(f'could not locate optional model input file(s) {optional_missing}')
        return None

    def _identify_missing_inputs(self, file_dict):
        """ Identify any missing files from the file dictionary

        @param file_dict: dictionary mapping the input file and filenames for the model
        @return: list of missing files
        """
        missing = []
        for name, file_name in file_dict.items():
            file_path = os.path.join(self.local_path, file_name)
            if not os.path.isfile(file_path):
                missing.append(file_path)
        return missing

    def check_destination(self):
        """ make sure the local folder to store inputs exists

        @return: None if folder exists
        @raise: FileNotFoundError if folder does not exist
        """
        if not os.path.isdir(self.local_path):
            msg = self.local_path
            logging.exception(msg)
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), msg)
        return None

    def _read_manifest(self, required_file_dict, optional_file_dict):
        """ read a manifest file in yaml format like so:
        <model>:
            <ver>:
                required_files:
                    <file mappings>
                optional_files:
                    <file mappings>

        @param required_file_dict: domain file dict to update
        @param optional_file_dict: optional_files data dict to update
        @return: None
        @raise AttributeError if required_files key is missing
        """
        with open(self.manifest_file, 'r') as manifest_file:
            yml = yaml.safe_load_all(manifest_file)
            for doc in yml:
                model_dict = doc.get(self.name).get(self.version)
                try:
                    for input_name, file_name in model_dict.get('required_files').items():
                        required_file_dict.update({input_name: file_name})
                except AttributeError as err:
                    logging.error(f'required file definitions not found in manifest {self.manifest_file} for model '
                                  f'{self.name}, version {self.version}')
                    raise err
                try:
                    for input_name, file_name in model_dict.get('optional_files').items():
                        optional_file_dict.update({input_name: file_name})
                except AttributeError:
                    logging.warning(f'optional file definitions not found in manifest {self.manifest_file} for model '
                                    f'{self.name}, version {self.version}')

    def __repr__(self):
        return f'{self.__class__.__name__}(name={self.name!r}, version={self.version!r}, ' \
               f'manifest={self.manifest_file}, local_path={self.local_path}, )'


class Conus(ParflowDomain):

    def __init__(self, local_path, manifest_file=None, version=1):
        """ Information about the CONUS dataset we are working with

        @param local_path: path on system where conus inputs live
        @param manifest_file: a file containing the keys and values for CONUS input required_files
        @param version: the conus version to create
        """
        if manifest_file is None:
            manifest_file = data.conus_manifest
        super().__init__('conus', local_path, manifest_file, version)
        # self.mask_array = self.mask_tif.ReadAsArray()
        # had to do this because conus1 full_dim_mask is all 0's
        if self.version == 1:
            self.mask_array = self.get_domain_mask() + 1