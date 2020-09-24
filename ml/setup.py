from setuptools import setup

setup(
    name = 'imagemachine',
    version = '0.1',
    packages = ['imagemachine'],
    install_requires=[
        'Click'
    ],
    entry_points = {
        'console_scripts': [
            'im = imagemachine.__main__:main'
        ]
})