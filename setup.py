from setuptools import setup

setup(
    name="honey",
    version="0.1.1",
    long_description=__doc__,
    packages=["honey"],
    zip_safe=False,
    install_requires=[
        "Flask>=0.8",
        "Flask-WTF>=0.6",
        "Jinja2>=2.6",
        "WTForms>=1.0.1",
        "Werkzeug>=0.8.3",
        "anyjson>=0.3.1",
        "distribute>=0.6.24",
        "flup",
        "mongokit>=0.7.2",
        "pymongo>=2.1.1",
        ],
    include_package_data = True,
    package_data = {
        "": ["*.txt"],
        "honey": ["static/*", "templates/*"]
        }
)


