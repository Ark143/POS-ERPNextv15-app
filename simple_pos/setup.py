from setuptools import setup, find_packages

setup(
    name="simple_pos",
    version="0.0.1",
    description="Simple Point of Sale Application for ERPNext v15",
    author="Ark143",
    author_email="support@example.com",
    packages=find_packages(),
    install_requires=[
        "frappe>=15.0.0",
        "erpnext>=15.0.0",
    ],
    zip_safe=False,
    include_package_data=True,
)
