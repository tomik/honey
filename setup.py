from setuptools import setup

setup(
    name="honey",
    version="0.1.1",
    long_description=__doc__,
    packages=["honey"],
    zip_safe=False,
    install_requires=[
        "Fabric>=1.4.1",
        "Flask>=0.8",
        "Flask-WTF>=0.6",
        "WTForms>=1.0.1",
        "distribute>=0.6.24",
        "flup",
        "mongokit>=0.7.2"
        ],
    include_package_data = True,
    package_data = {
        "": ["*.txt"],
        "honey": ["static/*", "templates/*"]
        }
)


