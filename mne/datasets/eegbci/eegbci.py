# Authors: Martin Billinger <martin.billinger@tugraz.at>
#          Daniel McCloy <dan@mccloy.info>
# License: BSD Style.

import os
from os import path as op
import re
import pkg_resources

from ..utils import _get_path, _do_path_update
from ...utils import _fetch_file, _url_to_local_path, verbose, deprecated
from ...utils.check import _soft_import

pooch = _soft_import('pooch', 'dataset downloading', True)


EEGMI_URL = 'https://physionet.org/files/eegmmidb/1.0.0/'


@deprecated('mne.datasets.eegbci.data_path() is deprecated and will be removed'
            ' in version 0.24. Use mne.datasets.eegbci.load_data() instead.')
@verbose
def data_path(url, path=None, force_update=False, update_path=None,
              verbose=None):
    """Get path to local copy of EEGMMI dataset URL.

    This is a low-level function useful for getting a local copy of a
    remote EEGBCI dataset [1]_ which is available at PhysioNet [2]_.

    Parameters
    ----------
    url : str
        The dataset to use.
    path : None | str
        Location of where to look for the EEGBCI data storing location.
        If None, the environment variable or config parameter
        ``MNE_DATASETS_EEGBCI_PATH`` is used. If it doesn't exist, the
        "~/mne_data" directory is used. If the EEGBCI dataset
        is not found under the given path, the data
        will be automatically downloaded to the specified folder.
    force_update : bool
        Force update of the dataset even if a local copy exists.
    update_path : bool | None
        If True, set the MNE_DATASETS_EEGBCI_PATH in mne-python
        config to the given path. If None, the user is prompted.
    %(verbose)s

    Returns
    -------
    path : list of str
        Local path to the given data file. This path is contained inside a list
        of length one, for compatibility.

    Notes
    -----
    For example, one could do:

        >>> from mne.datasets import eegbci
        >>> url = 'http://www.physionet.org/physiobank/database/eegmmidb/'
        >>> eegbci.data_path(url, os.getenv('HOME') + '/datasets') # doctest:+SKIP

    This would download the given EEGBCI data file to the 'datasets' folder,
    and prompt the user to save the 'datasets' path to the mne-python config,
    if it isn't there already.

    References
    ----------
    .. [1] Schalk, G., McFarland, D.J., Hinterberger, T., Birbaumer, N.,
           Wolpaw, J.R. (2004) BCI2000: A General-Purpose Brain-Computer
           Interface (BCI) System. IEEE TBME 51(6):1034-1043
    .. [2] Goldberger AL, Amaral LAN, Glass L, Hausdorff JM, Ivanov PCh,
           Mark RG, Mietus JE, Moody GB, Peng C-K, Stanley HE. (2000)
           PhysioBank, PhysioToolkit, and PhysioNet: Components of a New
           Research Resource for Complex Physiologic Signals.
           Circulation 101(23):e215-e220
    """  # noqa: E501
    key = 'MNE_DATASETS_EEGBCI_PATH'
    name = 'EEGBCI'
    path = _get_path(path, key, name)
    destination = _url_to_local_path(url, op.join(path, 'MNE-eegbci-data'))
    destinations = [destination]

    # Fetch the file
    if not op.isfile(destination) or force_update:
        if op.isfile(destination):
            os.remove(destination)
        if not op.isdir(op.dirname(destination)):
            os.makedirs(op.dirname(destination))
        _fetch_file(url, destination, print_destination=False)

    # Offer to update the path
    _do_path_update(path, update_path, key, name)
    return destinations


@verbose
def load_data(subject, runs, path=None, force_update=False, update_path=None,
              base_url=EEGMI_URL, verbose=None):  # noqa: D301
    """Get paths to local copies of EEGBCI dataset files.

    This will fetch data for the EEGBCI dataset :footcite:`SchalkEtAl2004`,
    which is also available at PhysioNet :footcite:`GoldbergerEtAl2000`.

    Parameters
    ----------
    subject : int
        The subject to use. Can be in the range of 1-109 (inclusive).
    runs : int | list of int
        The runs to use. The runs correspond to:

        =========  ===================================
        run        task
        =========  ===================================
        1          Baseline, eyes open
        2          Baseline, eyes closed
        3, 7, 11   Motor execution: left vs right hand
        4, 8, 12   Motor imagery: left vs right hand
        5, 9, 13   Motor execution: hands vs feet
        6, 10, 14  Motor imagery: hands vs feet
        =========  ===================================

    path : None | str
        Location of where to look for the EEGBCI data storing location.
        If None, the environment variable or config parameter
        ``MNE_DATASETS_EEGBCI_PATH`` is used. If it doesn't exist, the
        "~/mne_data" directory is used. If the EEGBCI dataset
        is not found under the given path, the data
        will be automatically downloaded to the specified folder.
    force_update : bool
        Force update of the dataset even if a local copy exists.
    update_path : bool | None
        If True, set the MNE_DATASETS_EEGBCI_PATH in mne-python
        config to the given path. If None, the user is prompted.
    %(verbose)s

    Returns
    -------
    paths : list
        List of local data paths of the given type.

    Notes
    -----
    For example, one could do:

        >>> from mne.datasets import eegbci
        >>> eegbci.load_data(1, [4, 10, 14],\
                             os.getenv('HOME') + '/datasets') # doctest:+SKIP

    This would download runs 4, 10, and 14 (hand/foot motor imagery) runs from
    subject 1 in the EEGBCI dataset to the 'datasets' folder, and prompt the
    user to save the 'datasets' path to the  mne-python config, if it isn't
    there already.

    References
    ----------
    .. footbibliography::
    """
    if not hasattr(runs, '__iter__'):
        runs = [runs]

    # get local storage path
    config_key = 'MNE_DATASETS_EEGBCI_PATH'
    folder = 'MNE-eegbci-data'
    name = 'EEGBCI'
    path = _get_path(path, config_key, name)
    # extract path parts
    pattern = r'(?:https?://.*)(files)/(eegmmidb)/(\d+\.\d+\.\d+)/?'
    match = re.compile(pattern).match(base_url)
    if match is None:
        raise ValueError('base_url does not match the expected EEGMI folder '
                         'structure. Please notify MNE-Python developers.')
    base_path = op.join(path, folder, *match.groups())
    # create the download manager
    fetcher = pooch.create(
        path=base_path,
        base_url=base_url,
        version=None,   # Data versioning is decoupled from MNE-Python version.
        registry=None,  # Registry is loaded from file, below.
        retry_if_failed=2  # 2 retries = 3 total attempts
    )
    # load the checksum registry
    registry = pkg_resources.resource_stream(
        'mne', op.join('data', 'eegbci_checksums.txt'))
    fetcher.load_registry(registry)
    # fetch the file(s)
    data_paths = []
    for run in runs:
        file_part = f'S{subject:03d}/S{subject:03d}R{run:02d}.edf'
        destination = op.join(base_path, file_part)
        if force_update and op.isfile(destination):
            os.remove(destination)
        data_paths.append(fetcher.fetch(file_part))
        # update path in config if desired
        _do_path_update(path, update_path, config_key, name)
    return data_paths


def standardize(raw):
    """Standardize channel positions and names.

    Parameters
    ----------
    raw : instance of Raw
        The raw data to standardize. Operates in-place.
    """
    rename = dict()
    for name in raw.ch_names:
        std_name = name.strip('.')
        std_name = std_name.upper()
        if std_name.endswith('Z'):
            std_name = std_name[:-1] + 'z'
        if std_name.startswith('FP'):
            std_name = 'Fp' + std_name[2:]
        rename[name] = std_name
    raw.rename_channels(rename)
