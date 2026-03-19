from license_management import __name__ as package_name


def test_package_importable() -> None:
    assert package_name == "license_management"
