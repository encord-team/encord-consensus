import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name='encord-consensus',
    version='0.0.11',
    author='Encord',
    author_email='support@encord.com',
    description='Tool for consensus on Encord.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/encord-team/encord-consensus',
    license='MIT',
    packages=setuptools.find_packages(),
    install_requires=[
        'encord==0.1.83',
        'streamlit==1.23.1',
        'pydantic==2.0.3',
        'python-dotenv'
    ],
    entry_points={
        'console_scripts': [
            'encord-consensus=encord_consensus.launcher:launch',
        ],
    },
)
