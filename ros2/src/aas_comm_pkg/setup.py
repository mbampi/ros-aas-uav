from setuptools import find_packages, setup

package_name = 'aas_comm_pkg'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='matheusdbampi',
    maintainer_email='matheusbampi@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'aas_gateway = aas_comm_pkg.aas_gateway:main',
            'pub_sample = aas_comm_pkg.pub_sample:main',
        ],
    },
)
