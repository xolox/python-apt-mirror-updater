# Automated, robust apt-get mirror selection for Debian and Ubuntu.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: April 16, 2020
# URL: https://apt-mirror-updater.readthedocs.io

"""
Support for `Elementary OS`_ package archive mirror selection.

Elementary OS is based on Ubuntu LTS releases and as such this module is a very
thin wrapper for the :mod:`apt_mirror_updater.backends.ubuntu` module.

.. _Elementary OS: https://en.wikipedia.org/wiki/Elementary_OS
"""

# Standard library modules.
import datetime
import decimal

# Modules included in our package.
from apt_mirror_updater.backends import ubuntu
from apt_mirror_updater.releases import Release

# Public identifiers that require documentation.
__all__ = (
    'KNOWN_RELEASES',
    'OLD_RELEASES_URL',
    'SECURITY_URL',
    'discover_mirrors',
    'generate_sources_list',
)

OLD_RELEASES_URL = ubuntu.OLD_RELEASES_URL
"""Alias for :attr:`apt_mirror_updater.backends.ubuntu.OLD_RELEASES_URL`."""

SECURITY_URL = ubuntu.SECURITY_URL
"""Alias for :attr:`apt_mirror_updater.backends.ubuntu.SECURITY_URL`."""

discover_mirrors = ubuntu.discover_mirrors
"""Alias for :func:`apt_mirror_updater.backends.ubuntu.discover_mirrors`."""

generate_sources_list = ubuntu.generate_sources_list
"""Alias for :func:`apt_mirror_updater.backends.ubuntu.generate_sources_list`."""

KNOWN_RELEASES = [
    Release(
        codename='Jupiter',
        created_date=datetime.date(2011, 3, 31),
        distributor_id='elementary',
        upstream_distributor_id='ubuntu',
        upstream_series='maverick',
        upstream_version=decimal.Decimal('10.10'),
        is_lts=False,
        series='jupiter',
        version=decimal.Decimal('0.1'),
    ),
    Release(
        codename='Luna',
        created_date=datetime.date(2013, 8, 10),
        distributor_id='elementary',
        upstream_distributor_id='ubuntu',
        upstream_series='precise',
        upstream_version=decimal.Decimal('12.04'),
        is_lts=False,
        series='luna',
        version=decimal.Decimal('0.2'),
    ),
    Release(
        codename='Freya',
        created_date=datetime.date(2015, 4, 11),
        distributor_id='elementary',
        upstream_distributor_id='ubuntu',
        upstream_series='trusty',
        upstream_version=decimal.Decimal('14.04'),
        is_lts=False,
        series='freya',
        version=decimal.Decimal('0.3'),
    ),
    Release(
        codename='Loki',
        created_date=datetime.date(2016, 9, 9),
        distributor_id='elementary',
        upstream_distributor_id='ubuntu',
        upstream_series='xenial',
        upstream_version=decimal.Decimal('16.04'),
        is_lts=False,
        series='loki',
        version=decimal.Decimal('0.4'),
    ),
    Release(
        codename='Juno',
        created_date=datetime.date(2018, 10, 16),
        distributor_id='elementary',
        upstream_distributor_id='ubuntu',
        upstream_series='bionic',
        upstream_version=decimal.Decimal('18.04'),
        is_lts=False,
        series='juno',
        version=decimal.Decimal('5.0'),
    ),
    Release(
        codename='Hera',
        created_date=datetime.date(2019, 12, 3),
        distributor_id='elementary',
        upstream_distributor_id='ubuntu',
        upstream_series='bionic',
        upstream_version=decimal.Decimal('18.04'),
        is_lts=False,
        series='hera',
        version=decimal.Decimal('5.1'),
    ),
]
"""
List of :class:`.Release` objects corresponding to known elementary OS
releases based on the summary table on the following web page:
https://en.wikipedia.org/wiki/Elementary_OS#Summary_table
"""
