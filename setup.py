from setuptools import setup, find_packages

setup(
    name='autopasscrack',
    version='0.1.0',
    description='Auto brute force web login forms with password list',
    author='Your Name',
    packages=find_packages(),  # 只要這一行
    install_requires=[
        'selenium'
    ],
    entry_points={
        'console_scripts': [
            'autopasscrack=autopasscrack.cli:main'
        ]
    },
    python_requires='>=3.7',
)