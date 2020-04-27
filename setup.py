from setuptools import find_packages, setup

setup(
    name='tarpey.dev',
    version='?.?.?',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'flask',
    ],
)