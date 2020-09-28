from setuptools import setup

setup(
    name = 'imagemachine',
    version = '0.1',
    packages = ['imagemachine'],
    install_requires=[
        'click'
    ],
    entry_points = {
        'console_scripts': [
            'im = imagemachine.__main__:main'
        ]
})