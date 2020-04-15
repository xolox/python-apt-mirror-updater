# Automated, robust apt-get mirror selection for Debian and Ubuntu.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: April 15, 2020
# URL: https://apt-mirror-updater.readthedocs.io

"""Test suite for the ``apt-mirror-updater`` package."""

# Standard library modules.
import decimal
import logging
import os
import time

# External dependencies.
from executor import execute
from executor.contexts import LocalContext
from humanfriendly.testing import TestCase, run_cli
from stopit import TimeoutException

# Modules included in our package.
from apt_mirror_updater import AptMirrorUpdater, normalize_mirror_url
from apt_mirror_updater.cli import main
from apt_mirror_updater.http import fetch_url
from apt_mirror_updater.releases import (
    DEBIAN_KEYRING_CURRENT,
    UBUNTU_KEYRING_CURRENT,
    UBUNTU_KEYRING_REMOVED,
    coerce_release,
    discover_releases,
    ubuntu_keyring_updated,
)

# Initialize a logger for this module.
logger = logging.getLogger(__name__)


class AptMirrorUpdaterTestCase(TestCase):

    """:mod:`unittest` compatible container for the :mod:`apt_mirror_updater` test suite."""

    def check_debian_mirror(self, url):
        """Ensure the given URL looks like a Debian mirror URL."""
        if not self.is_debian_mirror(url):
            msg = "Invalid Debian mirror URL! (%r)"
            raise AssertionError(msg % url)

    def check_mirror_url(self, url):
        """Check whether the given URL looks like a mirror URL for the system running the test suite."""
        if not hasattr(self, 'context'):
            self.context = LocalContext()
        if self.context.distributor_id == 'debian':
            self.check_debian_mirror(url)
        elif self.context.distributor_id == 'ubuntu':
            self.check_ubuntu_mirror(url)
        else:
            raise Exception("Unsupported platform!")

    def check_ubuntu_mirror(self, url):
        """Ensure the given URL looks like a Ubuntu mirror URL."""
        if not self.is_ubuntu_mirror(url):
            msg = "Invalid Ubuntu mirror URL! (%r)"
            raise AssertionError(msg % url)

    def is_debian_mirror(self, url):
        """Check whether the given URL looks like a Debian mirror URL."""
        return self.is_mirror_url(url, '/dists/stable/Release.gpg', b'-----BEGIN PGP SIGNATURE-----')

    def is_mirror_url(self, base_url, stable_resource, expected_content):
        """Validate a given mirror URL based on a stable resource URL and its expected response."""
        base_url = normalize_mirror_url(base_url)
        if base_url.startswith(('http://', 'https://')):
            if not hasattr(self, 'mirror_cache'):
                self.mirror_cache = {}
            cache_key = (base_url, stable_resource, expected_content)
            if cache_key not in self.mirror_cache:
                try:
                    # Look for a file with a stable filename (assumed to always be available).
                    resource_url = base_url + stable_resource
                    response = fetch_url(resource_url)
                    # Check the contents of the response.
                    if expected_content in response:
                        logger.info("URL %s served expected content.", resource_url)
                        self.mirror_cache[cache_key] = True
                    else:
                        logger.warning("URL %s didn't serve expected content!", resource_url)
                        self.mirror_cache[cache_key] = False
                except TimeoutException:
                    logger.warning("URL %s reported timeout, not failing test suite on this ..")
                    self.mirror_cache[cache_key] = True
                except Exception:
                    logger.warning("URL %s triggered exception!", resource_url, exc_info=True)
                    self.mirror_cache[cache_key] = False
            return self.mirror_cache[cache_key]
        return False

    def is_ubuntu_mirror(self, url):
        """
        Check whether the given URL looks like a Ubuntu mirror URL.

        This is a bit convoluted because different mirrors forbid access to
        different resources (resulting in HTTP 403 responses) apparently based
        on individual webmaster's perceptions of what expected clients
        (apt-get) should and shouldn't be accessing :-).
        """
        if url == 'http://ubuntu.cs.utah.edu/ubuntu':
            # This mirror intermittently serves 404 errors on arbitrary URLs.
            # Apart from that it does look to contain the expected directory
            # layout. Seems like they're load balancing between good and bad
            # servers (where the bad servers have a broken configuration).
            return True
        # At the time of writing the following test seems to work on all
        # mirrors apart from the exceptions noted in this method.
        if self.is_mirror_url(url, '/project/ubuntu-archive-keyring.gpg', b'ftpmaster@ubuntu.com'):
            return True
        # The mirror http://mirrors.codec-cluster.org/ubuntu fails the above
        # test because of a 403 response so we have to compensate. Because
        # other mirrors may behave similarly in the future this is implemented
        # as a generic test (not based on the mirror URL).
        return self.is_mirror_url(url, '/dists/devel/Release.gpg', b'-----BEGIN PGP SIGNATURE-----')

    def test_debian_mirror_discovery(self):
        """Test the discovery of Debian mirror URLs."""
        from apt_mirror_updater.backends.debian import discover_mirrors
        mirrors = discover_mirrors()
        assert len(mirrors) > 10
        for candidate in mirrors:
            self.check_debian_mirror(candidate.mirror_url)

    def test_ubuntu_mirror_discovery(self):
        """Test the discovery of Ubuntu mirror URLs."""
        from apt_mirror_updater.backends.ubuntu import discover_mirrors
        mirrors = discover_mirrors()
        assert len(mirrors) > 10
        for candidate in mirrors:
            self.check_ubuntu_mirror(candidate.mirror_url)

    def test_adaptive_mirror_discovery(self):
        """Test the discovery of mirrors for the current type of system."""
        updater = AptMirrorUpdater()
        assert len(updater.available_mirrors) > 10
        for candidate in updater.available_mirrors:
            self.check_mirror_url(candidate.mirror_url)

    def test_mirror_ranking(self):
        """Test the ranking of discovered mirrors."""
        updater = AptMirrorUpdater()
        # Make sure that multiple discovered mirrors are available.
        assert sum(m.is_available for m in updater.ranked_mirrors) > 10

    def test_best_mirror_selection(self):
        """Test the selection of a "best" mirror."""
        updater = AptMirrorUpdater()
        self.check_mirror_url(updater.best_mirror)

    def test_current_mirror_discovery(self):
        """Test that the current mirror can be extracted from ``/etc/apt/sources.list``."""
        exit_code, output = run_cli(main, '--find-current-mirror')
        assert exit_code == 0
        self.check_mirror_url(output.strip())

    def test_dumb_update(self):
        """Test that our dumb ``apt-get update`` wrapper works."""
        if os.getuid() != 0:
            return self.skipTest("root privileges required to opt in")
        updater = AptMirrorUpdater()
        # Remove all existing package lists.
        updater.clear_package_lists()
        # Verify that package lists aren't available.
        assert not have_package_lists()
        # Run `apt-get update' to download the package lists.
        updater.dumb_update()
        # Verify that package lists are again available.
        assert have_package_lists()

    def test_smart_update(self):
        """
        Test that our smart ``apt-get update`` wrapper works.

        Currently this test simply ensures coverage of the happy path.
        Ideally it will evolve to test the handled edge cases as well.
        """
        if os.getuid() != 0:
            return self.skipTest("root privileges required to opt in")
        updater = AptMirrorUpdater()
        # Remove all existing package lists.
        updater.clear_package_lists()
        # Verify that package lists aren't available.
        assert not have_package_lists()
        # Run `apt-get update' to download the package lists.
        updater.smart_update()
        # Verify that package lists are again available.
        assert have_package_lists()

    def test_discover_releases(self):
        """Test that release discovery works properly."""
        releases = discover_releases()
        # Check that a reasonable number of Debian and Ubuntu releases was discovered.
        assert len([r for r in releases if r.distributor_id == 'debian']) > 10
        assert len([r for r in releases if r.distributor_id == 'ubuntu']) > 10
        # Check that LTS releases of Debian as well as Ubuntu were discovered.
        assert any(r.distributor_id == 'debian' and r.is_lts for r in releases)
        assert any(r.distributor_id == 'ubuntu' and r.is_lts for r in releases)
        # Sanity check against duplicate releases.
        assert sum(r.series == 'bionic' for r in releases) == 1
        assert sum(r.series == 'jessie' for r in releases) == 1
        # Sanity check some known LTS releases.
        assert any(r.series == 'bionic' and r.is_lts for r in releases)
        assert any(r.series == 'stretch' and r.is_lts for r in releases)

    def test_coerce_release(self):
        """Test the coercion of release objects."""
        # Test coercion of short code names.
        assert coerce_release('lucid').version == decimal.Decimal('10.04')
        assert coerce_release('woody').distributor_id == 'debian'
        # Test coercion of version numbers.
        assert coerce_release('10.04').series == 'lucid'

    def test_keyring_selection(self):
        """Make sure keyring selection works as intended."""
        # Check Debian keyring selection.
        lenny = coerce_release('lenny')
        assert lenny.keyring_file == DEBIAN_KEYRING_CURRENT
        # Check Ubuntu <= 12.04 keyring selection.
        precise = coerce_release('precise')
        if ubuntu_keyring_updated():
            assert precise.keyring_file == UBUNTU_KEYRING_REMOVED
        else:
            assert precise.keyring_file == UBUNTU_KEYRING_CURRENT
        # Check Ubuntu > 12.04 keyring selection.
        bionic = coerce_release('bionic')
        assert bionic.keyring_file == UBUNTU_KEYRING_CURRENT

    def test_debian_lts_eol_date(self):
        """
        Regression test for `issue #5`_.

        .. _issue #5: https://github.com/xolox/python-apt-mirror-updater/issues/5
        """
        updater = AptMirrorUpdater(
            distributor_id='debian',
            distribution_codename='jessie',
            architecture='amd64',
        )
        eol_expected = (time.time() >= 1593468000)
        assert updater.release_is_eol == eol_expected


def have_package_lists():
    """
    Check if apt's package lists are available.

    :returns: :data:`True` when package lists are available,
              :data:`False` otherwise.

    This function checks that the output of ``apt-cache show python`` contains
    a ``Filename: ...`` key/value pair which indicates that apt knows where to
    download the package archive that installs the ``python`` package.
    """
    return 'Filename:' in execute('apt-cache', 'show', 'python', check=False, capture=True)
