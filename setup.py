from setuptools import find_packages, setup

setup(
    name='tarpey.dev',
    version='2020.5.7',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'flask',
    ],
)