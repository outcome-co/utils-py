import pytest
from outcome.utils import semver


@pytest.fixture(scope='module')
def basic_version():
    return '0.1.0'


@pytest.fixture(scope='module')
def upgraded_major_version():
    return '1.0.0'


@pytest.fixture(scope='module')
def upgraded_minor_version():
    return '0.2.0'


@pytest.fixture(scope='module')
def upgraded_patch_version():
    return '0.1.1'


class TestSemverCompatibility:
    def test_incompatible(self, basic_version, upgraded_major_version):
        compatibility = semver.compatibility(basic_version, upgraded_major_version)
        assert compatibility == semver.Compatibility.incompatible

    def test_compatible_minor(self, basic_version, upgraded_minor_version):
        compatibility = semver.compatibility(basic_version, upgraded_minor_version)
        assert compatibility == semver.Compatibility.compatible

    def test_compatible_patch(self, basic_version, upgraded_patch_version):
        compatibility = semver.compatibility(basic_version, upgraded_patch_version)
        assert compatibility == semver.Compatibility.compatible

    def test_compatible_equal(self, basic_version):
        compatibility = semver.compatibility(basic_version, basic_version)
        assert compatibility == semver.Compatibility.compatible


class TestSemverAreCompatible:
    def test_incompatible(self, basic_version, upgraded_major_version):
        assert not semver.are_compatible(basic_version, upgraded_major_version)

    def test_compatible_minor(self, basic_version, upgraded_minor_version):
        assert semver.are_compatible(basic_version, upgraded_minor_version)

    def test_compatible_patch(self, basic_version, upgraded_patch_version):
        assert semver.are_compatible(basic_version, upgraded_patch_version)

    def test_compatible_equal(self, basic_version):
        assert semver.are_compatible(basic_version, basic_version)
